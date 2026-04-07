"""The Wiener Linien Monitor integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import async_fetch_departures
from .const import DOMAIN, FETCH_DEPARTURES_SERVICE_NAME

_LOGGER = logging.getLogger(__name__)

FETCH_DEPARTURES_SCHEMA = vol.Schema(
    {
        vol.Required("stop_id"): str,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
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
