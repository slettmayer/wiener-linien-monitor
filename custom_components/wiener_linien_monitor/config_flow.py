"""Config flow for the Wiener Linien Monitor integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_MAX_DEPARTURES,
    CONF_STOPS,
    DEFAULT_MAX_DEPARTURES,
    DEFAULT_NAME,
    DOMAIN,
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required("name", default=DEFAULT_NAME): str,
        vol.Required(CONF_STOPS): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STOPS): str,
        vol.Required(CONF_MAX_DEPARTURES, default=DEFAULT_MAX_DEPARTURES): int,
    }
)


class WienerLinienMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wiener Linien Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            stops_raw = user_input[CONF_STOPS]
            stops = [s.strip() for s in stops_raw.split(",") if s.strip()]

            if not stops:
                errors[CONF_STOPS] = "no_stops"
            elif not all(s.isdigit() for s in stops):
                errors[CONF_STOPS] = "invalid_stop_id"
            else:
                await self.async_set_unique_id(user_input["name"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        CONF_STOPS: stops,
                    },
                    options={
                        CONF_MAX_DEPARTURES: DEFAULT_MAX_DEPARTURES,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return WienerLinienMonitorOptionsFlow(config_entry)


class WienerLinienMonitorOptionsFlow(OptionsFlow):
    """Handle options flow for Wiener Linien Monitor."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            stops_raw = user_input[CONF_STOPS]
            stops = [s.strip() for s in stops_raw.split(",") if s.strip()]

            if not stops:
                errors[CONF_STOPS] = "no_stops"
            elif not all(s.isdigit() for s in stops):
                errors[CONF_STOPS] = "invalid_stop_id"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_STOPS: stops,
                        CONF_MAX_DEPARTURES: user_input[CONF_MAX_DEPARTURES],
                    },
                )

        current_stops = self._config_entry.options.get(
            CONF_STOPS,
            self._config_entry.data.get(CONF_STOPS, []),
        )
        current_max = self._config_entry.options.get(
            CONF_MAX_DEPARTURES, DEFAULT_MAX_DEPARTURES
        )

        if isinstance(current_stops, list):
            stops_str = ", ".join(current_stops)
        else:
            stops_str = current_stops

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOPS, default=stops_str): str,
                    vol.Required(CONF_MAX_DEPARTURES, default=current_max): int,
                }
            ),
            errors=errors,
        )
