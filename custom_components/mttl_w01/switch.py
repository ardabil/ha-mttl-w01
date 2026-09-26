"""Switch platform for LG / Jinheung MTTL-W01 Power Strip."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .tcp_server import MTTLDevice, MTTLServer

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MTTL-W01 switch platform."""
    server: MTTLServer = hass.data[DOMAIN][entry.entry_id]
    known_devices: set[str] = set()

    @callback
    def on_device_event(device: MTTLDevice) -> None:
        if device.mac not in known_devices:
            known_devices.add(device.mac)
            new_switches = [
                MTTLRelaySwitch(server, device.mac, ch)
                for ch in range(1, 5)
            ]
            async_add_entities(new_switches)

    # Process any already connected devices
    for dev in server.devices.values():
        on_device_event(dev)

    entry.async_on_unload(server.register_listener(on_device_event))


class MTTLRelaySwitch(SwitchEntity):
    """Representation of an MTTL-W01 outlet relay."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, server: MTTLServer, mac: str, outlet: int) -> None:
        self._server = server
        self._mac = mac.upper()
        self._outlet = outlet
        self._attr_unique_id = f"mttl_{self._mac.lower()}_outlet_{outlet}"
        self._attr_name = f"Outlet {outlet}"

    @property
    def device_info(self) -> DeviceInfo:
        device = self._server.devices.get(self._mac)
        model = device.model if device else "MTTL-W01"
        sw_version = device.firmware if device else "1.0"
        return DeviceInfo(
            identifiers={(DOMAIN, self._mac)},
            name=f"MTTL {self._mac[-7:]}",
            manufacturer="LG / Jinheung",
            model=model,
            sw_version=sw_version,
        )

    @property
    def is_on(self) -> bool | None:
        device = self._server.devices.get(self._mac)
        if device and self._outlet in device.outlets:
            return device.outlets[self._outlet]["state"]
        return None

    @property
    def available(self) -> bool:
        device = self._server.devices.get(self._mac)
        return device is not None and device.online

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._server.async_set_relay(self._mac, self._outlet, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._server.async_set_relay(self._mac, self._outlet, False)

    async def async_added_to_hass(self) -> None:
        """Register state update listener."""
        @callback
        def on_update(device: MTTLDevice) -> None:
            if device.mac == self._mac:
                self.async_write_ha_state()

        self.async_on_remove(self._server.register_listener(on_update))
