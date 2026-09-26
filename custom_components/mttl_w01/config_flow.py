"""Config Flow for LG / Jinheung MTTL-W01 Power Strip."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_POLL_INTERVAL, CONF_PORT, DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DOMAIN


class MTTLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MTTL-W01."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="MTTL-W01 TCP Bridge",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return MTTLOptionsFlow(config_entry)


class MTTLOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for MTTL-W01."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PORT,
                    default=self.config_entry.options.get(
                        CONF_PORT, self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
                    ),
                ): int,
                vol.Required(
                    CONF_POLL_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_POLL_INTERVAL,
                        self.config_entry.data.get(
                            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                        ),
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
