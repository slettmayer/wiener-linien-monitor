"""Sensor platform for the Wiener Linien Monitor integration."""

from __future__ import annotations

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MAX_DEPARTURES,
    CONF_STOPS,
    DEFAULT_MAX_DEPARTURES,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import WienerLinienDataUpdateCoordinator

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
    """Set up the Wiener Linien sensor via YAML."""
    name: str = config[CONF_NAME]
    stops: list[str] = config[CONF_STOPS]
    max_departures: int = config[CONF_MAX_DEPARTURES]

    sensors = []
    for stop_id in stops:
        coordinator = WienerLinienDataUpdateCoordinator(hass, stop_id)
        await coordinator.async_config_entry_first_refresh()
        sensors.append(WienerLinienSensor(coordinator, name, stop_id, max_departures))

    async_add_entities(sensors)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wiener Linien sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinators: dict[str, WienerLinienDataUpdateCoordinator] = data["coordinators"]
    max_departures: int = data["max_departures"]

    sensors = [
        WienerLinienSensor(coordinator, entry.title, stop_id, max_departures)
        for stop_id, coordinator in coordinators.items()
    ]
    async_add_entities(sensors)


class WienerLinienSensor(
    CoordinatorEntity[WienerLinienDataUpdateCoordinator], SensorEntity
):
    """Representation of a Wiener Linien sensor."""

    _attr_icon = "mdi:bus-clock"

    def __init__(
        self,
        coordinator: WienerLinienDataUpdateCoordinator,
        name: str,
        stop_id: str,
        max_departures: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{name} {stop_id}"
        self._attr_unique_id = f"wienerlinien_{stop_id}"
        self._stop_id = stop_id
        self._max_departures = max_departures

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None or "message" in self.coordinator.data:
            return None
        return self.coordinator.data.get("departures_count")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None or "message" in self.coordinator.data:
            return {}
        data = self.coordinator.data
        return {
            "stop_id": self._stop_id,
            "stop_name": data.get("stop_name"),
            "departures": data.get("departures", [])[: self._max_departures],
            "server_time": data.get("server_time"),
        }
