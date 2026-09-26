"""Sensor platform for LG / Jinheung MTTL-W01 Power Strip."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
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
    """Set up the MTTL-W01 sensor platform."""
    server: MTTLServer = hass.data[DOMAIN][entry.entry_id]
    known_devices: set[str] = set()

    @callback
    def on_device_event(device: MTTLDevice) -> None:
        if device.mac not in known_devices:
            known_devices.add(device.mac)
            new_sensors = []
            for ch in range(1, 5):
                new_sensors.extend(
                    [
                        MTTLPowerSensor(server, device.mac, ch),
                        MTTLEnergySensor(server, device.mac, ch),
                        MTTLTemperatureSensor(server, device.mac, ch),
                    ]
                )
            async_add_entities(new_sensors)

    for dev in server.devices.values():
        on_device_event(dev)

    entry.async_on_unload(server.register_listener(on_device_event))


class MTTLBaseSensor(SensorEntity):
    """Base class for MTTL sensors."""

    _attr_has_entity_name = True

    def __init__(self, server: MTTLServer, mac: str, outlet: int) -> None:
        self._server = server
        self._mac = mac.upper()
        self._outlet = outlet

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
    def available(self) -> bool:
        device = self._server.devices.get(self._mac)
        return device is not None and device.online

    async def async_added_to_hass(self) -> None:
        """Register state update listener."""
        @callback
        def on_update(device: MTTLDevice) -> None:
            if device.mac == self._mac:
                self.async_write_ha_state()

        self.async_on_remove(self._server.register_listener(on_update))


class MTTLPowerSensor(MTTLBaseSensor):
    """Power sensor in Watts."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, server: MTTLServer, mac: str, outlet: int) -> None:
        super().__init__(server, mac, outlet)
        self._attr_unique_id = f"mttl_{self._mac.lower()}_power_{outlet}"
        self._attr_name = f"Outlet {outlet} Power"

    @property
    def native_value(self) -> float | None:
        device = self._server.devices.get(self._mac)
        if device and self._outlet in device.outlets:
            return device.outlets[self._outlet]["power_w"]
        return None


class MTTLEnergySensor(MTTLBaseSensor):
    """Energy sensor in kWh."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, server: MTTLServer, mac: str, outlet: int) -> None:
        super().__init__(server, mac, outlet)
        self._attr_unique_id = f"mttl_{self._mac.lower()}_energy_{outlet}"
        self._attr_name = f"Outlet {outlet} Energy"

    @property
    def native_value(self) -> float | None:
        device = self._server.devices.get(self._mac)
        if device and self._outlet in device.outlets:
            return device.outlets[self._outlet]["energy_kwh"]
        return None


class MTTLTemperatureSensor(MTTLBaseSensor):
    """Temperature sensor in Celsius."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, server: MTTLServer, mac: str, outlet: int) -> None:
        super().__init__(server, mac, outlet)
        self._attr_unique_id = f"mttl_{self._mac.lower()}_temp_{outlet}"
        self._attr_name = f"Outlet {outlet} Temperature"

    @property
    def native_value(self) -> float | None:
        device = self._server.devices.get(self._mac)
        if device and self._outlet in device.outlets:
            return device.outlets[self._outlet]["temperature_c"]
        return None
