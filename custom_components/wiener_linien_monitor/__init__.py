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
)
from .coordinator import WienerLinienDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

FETCH_DEPARTURES_SCHEMA = vol.Schema(
    {
        vol.Required("stop_id"): vol.Coerce(str),
    }
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
