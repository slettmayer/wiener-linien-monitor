"""The Wiener Linien Monitor integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import async_fetch_departures
from .const import (
    CONF_MAX_DEPARTURES,
    CONF_STOPS,
    DEFAULT_MAX_DEPARTURES,
    DOMAIN,
    FETCH_DEPARTURES_SERVICE_NAME,
    OEBB_SEARCH_STATION_SERVICE_NAME,
    OEBB_STATION_BOARD_SERVICE_NAME,
    OEBB_TRIP_SEARCH_SERVICE_NAME,
)
from .coordinator import WienerLinienDataUpdateCoordinator
from .oebb_api import (
    async_oebb_search_station,
    async_oebb_station_board,
    async_oebb_trip_search,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

FETCH_DEPARTURES_SCHEMA = vol.Schema(
    {
        vol.Required("stop_id"): vol.Coerce(str),
    }
)


def _require_one_of(*keys: str) -> vol.All:
    """Voluptuous validator: at least one of the given keys must be present."""

    def _validator(data: dict) -> dict:
        if not any(data.get(k) for k in keys):
            raise vol.Invalid(f"At least one of {', '.join(keys)} is required")
        return data

    return _validator


OEBB_SEARCH_STATION_SCHEMA = vol.Schema(
    {
        vol.Required("query"): str,
        vol.Optional("max_results", default=10): vol.All(int, vol.Range(min=1, max=50)),
    }
)

OEBB_STATION_BOARD_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional("station_id"): vol.Coerce(str),
            vol.Optional("station_name"): str,
            vol.Optional("board_type", default="DEP"): vol.In(["DEP", "ARR"]),
            vol.Optional("max_journeys", default=10): vol.All(
                int, vol.Range(min=1, max=50)
            ),
        }
    ),
    _require_one_of("station_id", "station_name"),
)

OEBB_TRIP_SEARCH_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional("from_station_id"): vol.Coerce(str),
            vol.Optional("from_station_name"): str,
            vol.Optional("to_station_id"): vol.Coerce(str),
            vol.Optional("to_station_name"): str,
            vol.Optional("max_connections", default=5): vol.All(
                int, vol.Range(min=1, max=10)
            ),
            vol.Optional("time"): str,
            vol.Optional("time_mode", default="departure"): vol.In(
                ["departure", "arrival"]
            ),
        }
    ),
    _require_one_of("from_station_id", "from_station_name"),
    _require_one_of("to_station_id", "to_station_name"),
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration (YAML and service registration)."""
    hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)

    async def fetch_departures(call: ServiceCall) -> ServiceResponse:
        """Fetch departures for a given stop ID."""
        stop_id = call.data["stop_id"]
        return await async_fetch_departures(session, stop_id)

    hass.services.async_register(
        DOMAIN,
        FETCH_DEPARTURES_SERVICE_NAME,
        fetch_departures,
        schema=FETCH_DEPARTURES_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def oebb_search_station(call: ServiceCall) -> ServiceResponse:
        """Search OeBB stations by name."""
        return await async_oebb_search_station(
            session,
            call.data["query"],
            call.data.get("max_results", 10),
        )

    hass.services.async_register(
        DOMAIN,
        OEBB_SEARCH_STATION_SERVICE_NAME,
        oebb_search_station,
        schema=OEBB_SEARCH_STATION_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def oebb_station_board(call: ServiceCall) -> ServiceResponse:
        """Fetch OeBB station departures or arrivals."""
        return await async_oebb_station_board(
            session,
            station_id=call.data.get("station_id"),
            station_name=call.data.get("station_name"),
            board_type=call.data.get("board_type", "DEP"),
            max_journeys=call.data.get("max_journeys", 10),
        )

    hass.services.async_register(
        DOMAIN,
        OEBB_STATION_BOARD_SERVICE_NAME,
        oebb_station_board,
        schema=OEBB_STATION_BOARD_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def oebb_trip_search(call: ServiceCall) -> ServiceResponse:
        """Search OeBB train connections."""
        return await async_oebb_trip_search(
            session,
            from_station_id=call.data.get("from_station_id"),
            from_station_name=call.data.get("from_station_name"),
            to_station_id=call.data.get("to_station_id"),
            to_station_name=call.data.get("to_station_name"),
            max_connections=call.data.get("max_connections", 5),
            time=call.data.get("time"),
            time_mode=call.data.get("time_mode", "departure"),
        )

    hass.services.async_register(
        DOMAIN,
        OEBB_TRIP_SEARCH_SERVICE_NAME,
        oebb_trip_search,
        schema=OEBB_TRIP_SEARCH_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wiener Linien Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    stops: list[str] = entry.options.get(CONF_STOPS, entry.data.get(CONF_STOPS, []))
    max_departures: int = entry.options.get(CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES)

    coordinators: dict[str, WienerLinienDataUpdateCoordinator] = {}
    for stop_id in stops:
        coordinator = WienerLinienDataUpdateCoordinator(hass, stop_id)
        await coordinator.async_config_entry_first_refresh()
        coordinators[stop_id] = coordinator

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinators": coordinators,
        "max_departures": max_departures,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
