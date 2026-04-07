"""Sensor platform for the Wiener Linien Monitor integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle

from .api import async_fetch_departures
from .const import (
    CONF_MAX_DEPARTURES,
    CONF_STOPS,
    DEFAULT_MAX_DEPARTURES,
    DEFAULT_NAME,
    MIN_TIME_BETWEEN_UPDATES,
    TRAFFIC_INFO_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_STOPS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(
            CONF_MAX_DEPARTURES, default=DEFAULT_MAX_DEPARTURES
        ): cv.positive_int,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Wiener Linien sensor."""
    name: str = config[CONF_NAME]
    stops: list[str] = config[CONF_STOPS]
    max_departures: int = config[CONF_MAX_DEPARTURES]

    session = async_get_clientsession(hass)

    sensors = [
        WienerLinienSensor(name, stop_id, session, max_departures)
        for stop_id in stops
    ]
    async_add_entities(sensors, True)


class WienerLinienSensor(SensorEntity):
    """Representation of a Wiener Linien sensor."""

    _attr_icon = "mdi:bus-clock"

    def __init__(
        self,
        name: str,
        stop_id: str,
        session: aiohttp.ClientSession,
        max_departures: int,
    ) -> None:
        """Initialize the sensor."""
        self._attr_name = f"{name} {stop_id}"
        self._attr_unique_id = f"wienerlinien_{stop_id}"
        self._stop_id = stop_id
        self._session = session
        self._max_departures = max_departures
        self._attr_native_value: int | None = None
        self._attr_extra_state_attributes: dict[str, Any] = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        result = await async_fetch_departures(self._session, self._stop_id)

        if "message" in result:
            return

        self._attr_native_value = result["departures_count"]
        self._attr_extra_state_attributes = {
            "stop_id": self._stop_id,
            "stop_name": result["stop_name"],
            "departures": result["departures"][: self._max_departures],
            "server_time": result["server_time"],
        }

    async def _fetch_traffic_info(self) -> None:
        """Fetch traffic information (disturbances) for this stop."""
        import asyncio

        try:
            lines_at_stop = list(
                {
                    dep["line"]
                    for dep in self._attr_extra_state_attributes.get(
                        "departures", []
                    )
                    if dep.get("line")
                }
            )

            if not lines_at_stop:
                self._attr_extra_state_attributes["traffic_info"] = []
                return

            line_params = "&".join(
                [f"relatedLine={line}" for line in lines_at_stop]
            )
            url = f"{TRAFFIC_INFO_ENDPOINT}?{line_params}&relatedStop={self._stop_id}"

            async with asyncio.timeout(10):
                response = await self._session.get(url)
                traffic_data = await response.json()

            traffic_info = []

            if traffic_data.get("data", {}).get("trafficInfos"):
                for info in traffic_data["data"]["trafficInfos"]:
                    traffic_info.append(
                        {
                            "title": info.get("title", ""),
                            "description": info.get("description", ""),
                            "time": info.get("time", {}).get("start", ""),
                            "priority": info.get("priority", ""),
                            "related_lines": info.get("relatedLines", []),
                            "related_stops": info.get("relatedStops", []),
                        }
                    )

            self._attr_extra_state_attributes["traffic_info"] = traffic_info

            for dep in self._attr_extra_state_attributes.get("departures", []):
                dep["disturbances"] = [
                    ti
                    for ti in traffic_info
                    if dep["line"] in ti.get("related_lines", [])
                ]

        except Exception as err:
            _LOGGER.warning(
                "Could not fetch traffic info for stop %s: %s",
                self._stop_id,
                err,
            )
            self._attr_extra_state_attributes["traffic_info"] = []
