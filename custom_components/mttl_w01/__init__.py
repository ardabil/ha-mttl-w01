"""Home Assistant Integration for LG / Jinheung MTTL-W01 Power Strip."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_POLL_INTERVAL, CONF_PORT, DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DOMAIN
from .tcp_server import MTTLServer

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MTTL-W01 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))
    poll_interval = entry.options.get(
        CONF_POLL_INTERVAL, entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    )

    server = MTTLServer(port=port, poll_interval=poll_interval)
    await server.start()

    hass.data[DOMAIN][entry.entry_id] = server

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        server: MTTLServer = hass.data[DOMAIN].pop(entry.entry_id)
        await server.stop()
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
