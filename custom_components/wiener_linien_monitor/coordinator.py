"""DataUpdateCoordinator for the Wiener Linien Monitor integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import async_fetch_departures
from .const import DOMAIN, MIN_TIME_BETWEEN_UPDATES

_LOGGER = logging.getLogger(__name__)


class WienerLinienDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch departure data for a single stop."""

    def __init__(self, hass: HomeAssistant, stop_id: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{stop_id}",
            update_interval=MIN_TIME_BETWEEN_UPDATES,
        )
        self.stop_id = stop_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API."""
        session = async_get_clientsession(self.hass)
        result = await async_fetch_departures(session, self.stop_id)

        if "message" in result:
            # Return previous data if available, otherwise return the error
            if self.data is not None:
                return self.data
            return result

        return result
