"""The Wiener Linien Monitor integration."""

from asyncio import timeout
import logging

import aiohttp
import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "wiener_linien_monitor"

API_ENDPOINT = "http://www.wienerlinien.at/ogd_realtime/monitor"
TRAFFIC_INFO_ENDPOINT = "http://www.wienerlinien.at/ogd_realtime/trafficInfoList"

FETCH_DEPARTURES_SERVICE_NAME = "fetch_departures"
FETCH_DEPARTURES_SCHEMA = vol.Schema(
    {
        vol.Required("stop_id"): str,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    session = async_get_clientsession(hass)

    async def fetch_departures(call: ServiceCall) -> ServiceResponse:
        """Fetch new state data for the sensor."""
        stop_id = call.data["stop_id"]

        try:
            url = f"{API_ENDPOINT}?stopId={stop_id}"
            async with timeout(10):
                response = await session.get(url)
                data = await response.json()

            if not data.get("data", {}).get("monitors"):
                _LOGGER.warning("No monitor data for stop %s", stop_id)
                return {"message": "No data"}

            monitors = data["data"]["monitors"]
            departures = []
            stop_name = "Unknown"

            if monitors:
                # Get stop name from first monitor
                stop_name = (
                    monitors[0]
                    .get("locationStop", {})
                    .get("properties", {})
                    .get("title", "Unknown")
                )

                # Process all lines and departures
                for monitor in monitors:
                    lines = monitor.get("lines", [])
                    for line in lines:
                        line_departures = line.get("departures", {}).get(
                            "departure", []
                        )
                        for departure in line_departures:
                            dep_time = departure.get("departureTime", {})
                            vehicle = departure.get("vehicle", {})

                            departure_info = {
                                "line": line.get("name"),
                                "direction": line.get("towards"),
                                "platform": line.get("platform"),
                                "time_planned": dep_time.get("timePlanned"),
                                "time_real": dep_time.get("timeReal"),
                                "countdown": dep_time.get("countdown"),
                                "barrier_free": vehicle.get("barrierFree", False),
                                "folding_ramp": vehicle.get("foldingRamp", False),
                                "type": vehicle.get("type"),
                            }
                            departures.append(departure_info)

            # Sort by countdown
            departures.sort(key=lambda x: x.get("countdown", 999))

            return {
                "departures_count": len(departures),
                "stop_id": stop_id,
                "stop_name": stop_name,
                "departures": departures,
                "server_time": data.get("message", {}).get("serverTime"),
            }

            # ADD THIS SECTION - Fetch traffic info (disturbances):
            # comment that out for now. TODO: Refactor that later
            # await self._fetch_traffic_info()

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching data for stop %s: %s", stop_id, err)
            return {"message": "No data"}
        except Exception as err:
            _LOGGER.error("Unexpected error for stop %s: %s", stop_id, err)
            return {"message": "No data"}

    hass.services.async_register(
        DOMAIN,
        FETCH_DEPARTURES_SERVICE_NAME,
        fetch_departures,
        schema=FETCH_DEPARTURES_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True
