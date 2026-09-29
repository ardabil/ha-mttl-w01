"""TCP Device Server for LG / Jinheung MTTL-W01 Power Strip."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Callable

_LOGGER = logging.getLogger(__name__)

BOOTINFO_REGEX = re.compile(
    r"^up:bootinfo:([^;\r\n]+);([0-9a-fA-F]{12});([0-9a-fA-F]{12});([^;\r\n]+);connect$"
)
ONOFF_EVENT_REGEX = re.compile(r"^up:(?:event:)?onoff:([1-4]):(on|off)$")
POWER_REPORT_REGEX = re.compile(r"^up:power_report:([1-4]):(-?\d+)$")
QUERY_REGEX = re.compile(r"^up:query:(-?\d+)$")


class MTTLDevice:
    """Represents a connected MTTL-W01 smart plug."""

    def __init__(
        self,
        mac: str,
        model: str,
        firmware: str,
        ip_address: str,
        writer: asyncio.StreamWriter,
    ) -> None:
        self.mac = mac.upper()
        self.model = model
        self.firmware = firmware
        self.ip_address = ip_address
        self.writer = writer
        self.online = True
        self.voltage_v: float | None = None
        self.total_current_a: float | None = None
        self.wifi_rssi: int | None = None
        self.outlets: dict[int, dict[str, Any]] = {
            i: {
                "channel": i,
                "state": False,
                "power_w": 0.0,
                "current_a": 0.0,
                "energy_kwh": 0.0,
                "temperature_c": 0.0,
            }
            for i in range(1, 5)
        }

    def update_outlet_relay(self, channel: int, on: bool) -> None:
        if channel in self.outlets:
            self.outlets[channel]["state"] = on

    def update_getinfo_data(self, channel_data: list[dict[str, Any]]) -> None:
        total_curr = 0.0
        for data in channel_data:
            ch = data["channel"]
            if ch in self.outlets:
                self.outlets[ch]["state"] = data["state"]
                self.outlets[ch]["power_w"] = data["power_w"]
                self.outlets[ch]["energy_kwh"] = data["energy_kwh"]
                self.outlets[ch]["temperature_c"] = data["temperature_c"]
                if "current_a" in data:
                    self.outlets[ch]["current_a"] = data["current_a"]
                    total_curr += data["current_a"]
                elif not data.get("state"):
                    self.outlets[ch]["current_a"] = 0.0
                elif self.outlets[ch].get("current_a", 0.0) > 0:
                    total_curr += self.outlets[ch]["current_a"]
                elif data.get("state") and data["power_w"] > 0 and self.voltage_v:
                    calc_curr = round(data["power_w"] / self.voltage_v, 3)
                    self.outlets[ch]["current_a"] = calc_curr
                    total_curr += calc_curr
                else:
                    self.outlets[ch]["current_a"] = 0.0
        if "voltage_v" in channel_data[0] if channel_data else False:
            self.voltage_v = channel_data[0].get("voltage_v")
        if total_curr > 0 or self.total_current_a is None:
            self.total_current_a = round(total_curr, 3)


class MTTLServer:
    """Async TCP Server handling MTTL-W01 devices."""

    def __init__(self, port: int = 10086, poll_interval: int = 10) -> None:
        self.port = port
        self.poll_interval = poll_interval
        self.server: asyncio.Server | None = None
        self.devices: dict[str, MTTLDevice] = {}
        self.listeners: list[Callable[[MTTLDevice], None]] = []
        self._poll_task: asyncio.Task | None = None
        self._tasks: set[asyncio.Task] = set()

    def _create_task(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def register_listener(self, callback: Callable[[MTTLDevice], None]) -> Callable[[], None]:
        """Register a callback for state changes."""
        self.listeners.append(callback)

        def remove():
            if callback in self.listeners:
                self.listeners.remove(callback)

        return remove

    def _notify(self, device: MTTLDevice) -> None:
        for callback in self.listeners:
            try:
                callback(device)
            except Exception as err:
                _LOGGER.exception("Error in listener callback: %s", err)

    async def start(self) -> None:
        """Start the TCP server."""
        self.server = await asyncio.start_server(
            self._handle_client,
            host="0.0.0.0",
            port=self.port,
        )
        _LOGGER.info("MTTL-W01 TCP Server listening on port %s", self.port)
        self._poll_task = self._create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop the TCP server."""
        if self._poll_task:
            self._poll_task.cancel()
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for dev in list(self.devices.values()):
            if not dev.writer.is_closing():
                dev.writer.close()
        self.devices.clear()

    async def async_set_relay(self, mac: str, outlet: int, on: bool) -> bool:
        """Send on/off command to an outlet."""
        device = self.devices.get(mac.upper())
        if not device or not device.online or device.writer.is_closing():
            _LOGGER.warning("Device %s is offline, cannot send command", mac)
            return False

        cmd = f"up:onoff:{outlet}:{'on' if on else 'off'}\r\n"
        try:
            device.writer.write(cmd.encode("ascii"))
            await device.writer.drain()
            device.update_outlet_relay(outlet, on)
            self._notify(device)
            return True
        except Exception as err:
            _LOGGER.error("Failed to send relay command to %s: %s", mac, err)
            return False

    async def _poll_device(self, device: MTTLDevice) -> None:
        """Poll telemetry from a connected device."""
        if not device.online or device.writer.is_closing():
            return
        try:
            # 1. Core telemetry (Watt, kWh, Temp, State per channel)
            device.writer.write(b"up:getinfo:all\r\n")
            await device.writer.drain()
            await asyncio.sleep(0.05)

            # 2. Native hardware RMS Voltage (mV)
            device.writer.write(b"up:power_report:1:vol\r\n")
            await device.writer.drain()
            await asyncio.sleep(0.05)

            # 3. Native hardware Current per channel (mA)
            for ch in range(1, 5):
                device.writer.write(f"up:power_report:{ch}:current\r\n".encode("ascii"))
                await device.writer.drain()
                await asyncio.sleep(0.05)

            # 4. Wi-Fi signal strength
            device.writer.write(b"up:query:wifirssi\r\n")
            await device.writer.drain()
        except Exception as err:
            _LOGGER.debug("Error polling %s: %s", device.mac, err)

    async def _poll_loop(self) -> None:
        """Periodically poll all connected devices."""
        while True:
            await asyncio.sleep(self.poll_interval)
            for device in list(self.devices.values()):
                if device.online and not device.writer.is_closing():
                    await self._poll_device(device)

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer = writer.get_extra_info("peername")
        ip = peer[0] if peer else "unknown"
        _LOGGER.debug("New TCP connection from %s", ip)
        current_device: MTTLDevice | None = None
        buffer = ""

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                _LOGGER.debug("RAW INCOMING BYTES from %s: %r", ip, data)
                buffer += data.decode("ascii", errors="ignore")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    _LOGGER.debug("RAW MTTL FRAME from %s: %s", ip, line)

                    # 1. Bootinfo frame
                    boot_match = BOOTINFO_REGEX.match(line)
                    if boot_match:
                        model = boot_match.group(1)
                        mac = boot_match.group(2).upper()
                        firmware = boot_match.group(4)
                        _LOGGER.info("Registered MTTL device %s (%s) from %s", mac, model, ip)

                        if mac in self.devices:
                            old_dev = self.devices[mac]
                            if old_dev.writer != writer and not old_dev.writer.is_closing():
                                old_dev.writer.close()

                        current_device = MTTLDevice(mac, model, firmware, ip, writer)
                        self.devices[mac] = current_device
                        self._notify(current_device)

                        # Request immediate telemetry
                        self._create_task(self._poll_device(current_device))
                        continue

                    if not current_device:
                        continue

                    # 2. Getinfo frame
                    if line.startswith("up:getinfo:"):
                        outlets_data = self._parse_getinfo(line)
                        if outlets_data:
                            current_device.update_getinfo_data(outlets_data)
                            self._notify(current_device)
                        continue

                    # 3. Native power_report frame (voltage mV or outlet current mA)
                    power_report_match = POWER_REPORT_REGEX.match(line)
                    if power_report_match:
                        ch = int(power_report_match.group(1))
                        raw_val = int(power_report_match.group(2))
                        if raw_val >= 50000:
                            # Voltage in millivolts -> Volts (e.g. 224500 -> 224.5V)
                            current_device.voltage_v = round(raw_val / 1000.0, 1)
                        else:
                            # Current in milliamps -> Amperes (e.g. 1450 -> 1.45A)
                            current_device.outlets[ch]["current_a"] = round(max(0, raw_val) / 1000.0, 3)
                            current_device.total_current_a = round(
                                sum(
                                    current_device.outlets[i].get("current_a", 0.0)
                                    for i in current_device.outlets
                                ),
                                3,
                            )
                        self._notify(current_device)
                        continue

                    # 4. Query frame (e.g. wifirssi)
                    query_match = QUERY_REGEX.match(line)
                    if query_match:
                        current_device.wifi_rssi = int(query_match.group(1))
                        self._notify(current_device)
                        continue

                    # 5. Relay change event
                    onoff_match = ONOFF_EVENT_REGEX.match(line)
                    if onoff_match:
                        outlet = int(onoff_match.group(1))
                        on = onoff_match.group(2) == "on"
                        current_device.update_outlet_relay(outlet, on)
                        self._notify(current_device)
                        continue

        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.debug("Client connection error for %s: %s", ip, err)
        finally:
            if current_device:
                current_device.online = False
                self._notify(current_device)
            if not writer.is_closing():
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    def _parse_getinfo(self, frame: str) -> list[dict[str, Any]] | None:
        try:
            payload = frame[len("up:getinfo:") :]
            parts = payload.split(":")
            if len(parts) != 8:
                return None

            result = []
            for i in range(0, len(parts), 2):
                ch = int(parts[i])
                fields = parts[i + 1].split(";")
                if len(fields) != 12:
                    return None

                relay_on = fields[1].lower() == "on"
                power_mw = int(fields[5]) if fields[5].isdigit() else 0
                energy_wh = int(fields[6], 16) if len(fields[6]) == 8 else 0
                temp_c = float(fields[11]) if fields[11].replace("-", "").isdigit() else 0.0

                result.append(
                    {
                        "channel": ch,
                        "state": relay_on,
                        "power_w": round(power_mw / 1000.0, 2),
                        "energy_kwh": round(energy_wh / 1000.0, 3),
                        "temperature_c": temp_c,
                    }
                )
            return result
        except Exception as err:
            _LOGGER.debug("Failed to parse getinfo frame '%s': %s", frame, err)
            return None
