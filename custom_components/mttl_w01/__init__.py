"""Home Assistant Integration for Multi Tap Jinheung."""
from __future__ import annotations

import hashlib
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_POLL_INTERVAL, CONF_PORT, DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DOMAIN
from .tcp_server import MTTLServer

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
]

TELEMETRY_ENDPOINTS = [
    "https://mttl-telemetry.crocus-visor.workers.dev/ping",
    "https://tracking.patratech.my.id/api/mttl/ping",
]


async def _async_send_startup_telemetry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Send anonymous startup ping for installation analytics."""
    try:
        session = async_get_clientsession(hass)
        install_hash = hashlib.sha256(f"mttl_{entry.entry_id}".encode()).hexdigest()[:16]
        params = {
            "id": install_hash,
            "ha": getattr(hass.config, "version", "unknown"),
            "v": "1.2.1",
        }
        for endpoint in TELEMETRY_ENDPOINTS:
            try:
                async with session.get(endpoint, params=params, timeout=5) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                continue
    except Exception:
        # Never break integration startup
        pass


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Multi Tap Jinheung from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))
    poll_interval = entry.options.get(
        CONF_POLL_INTERVAL, entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    )

    server = MTTLServer(port=port, poll_interval=poll_interval)
    hass.data[DOMAIN][entry.entry_id] = server

    await server.start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Send lightweight anonymous startup telemetry in background
    hass.async_create_background_task(
        _async_send_startup_telemetry(hass, entry), "mttl_w01_startup_telemetry"
    )

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
