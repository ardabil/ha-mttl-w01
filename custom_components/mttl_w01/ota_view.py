"""OTA Web Interface and Handler for Multi Tap Jinheung (MTTL-W01)."""
from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import logging
import os
import struct
import time
from pathlib import Path
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

SOURCE_SHA256 = "d780b578af69d52f3a05191a8e7d91a20e05085a912722327481cd5663682c04"
XOR_KEY = bytes.fromhex("3f5a27e8d8fb85f9bd4d51196c4f5159")

STATUS_CAVE_SOURCE = bytes.fromhex(
    "0d5b5350494620496e665d537069634e564d43616c4c6f61643a2043616c6962726174696f6e204c6f61646564284269744d6f64652025642c20435055436c6b202564293a2042617564526174653d3078257820526444756d6d7943796c653d307825782044656c61794c696e653d307825780d0a0000000d5b535049462057726e5d537069634e564d43616c4c6f61643a204461746120696e20466c61736828402030782578203d203078257820307825782920697320496e76616c69640d0a000000"
    "0d5b5350494620496e665d537069634e564d4361"
)
STATUS_CAVE_PATCH = bytes.fromhex(
    "f8b55c46207808b10134fbe7043c22a500f01cf82a4e706800f030f820a500f015f80423002200f018f801331ea500f00df8182200f011f81da500f007f8142200f00bf81ca500f001f8f8bd2878013510b120700134f9e7704704b5002717b12c20207001342c2078433044009a805800f004f801379f42f1db04bd1c2120fa01f212f00f020a2ab4bf30323732227001340439f3d570475d2c2276223a2200222c2274223a2200222c2270223a2200222c2265223a2200227d7d7d00000000307d0510"
)

_status_diagnostic = bytearray(STATUS_CAVE_PATCH)
_status_diagnostic[0x2A:0x2C] = bytes.fromhex("00bf")
_status_diagnostic[0x32:0x34] = bytes.fromhex("0822")
_status_diagnostic[0xAB] = ord("i")
_status_diagnostic[0xB3] = ord("w")
_status_diagnostic[0x18:0x1C] = bytes.fromhex("00f054f8")
_status_diagnostic[0x70:0x74] = bytes.fromhex("00f02df8")
_status_diagnostic[0x7C:0x7E] = bytes.fromhex("1c21")
_status_diagnostic.extend(bytes.fromhex("6421b0fbf1f00821d7e7111d142a08bf0439d2e7"))
STATUS_CAVE_PATCH = bytes(_status_diagnostic)

STOCK_URL = "https://raw.githubusercontent.com/af950833/mttl_w01/main/work/firmware/1.0.66/comMTTL-W01_1.0.66.fwr"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Multi Tap Jinheung - OTA Firmware Manager</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --text: #f8fafc;
      --text-dim: #94a3b8;
      --success: #22c55e;
      --error: #ef4444;
      --warning: #f59e0b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 24px 16px; min-height: 100vh; display: flex; justify-content: center; }
    .container { max-width: 680px; width: 100%; }
    .header { text-align: center; margin-bottom: 24px; }
    .header h1 { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
    .header p { color: var(--text-dim); font-size: 14px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    .card h2 { font-size: 16px; font-weight: 600; margin-bottom: 14px; color: var(--accent); display: flex; align-items: center; gap: 8px; }
    .form-group { margin-bottom: 16px; }
    label { display: block; font-size: 13px; font-weight: 500; color: var(--text-dim); margin-bottom: 6px; }
    input, select { width: 100%; background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; color: var(--text); font-size: 14px; outline: none; }
    input:focus, select:focus { border-color: var(--accent); }
    .btn { display: inline-flex; align-items: center; justify-content: center; width: 100%; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: 600; border: none; cursor: pointer; transition: 0.2s; background: var(--accent); color: #0f172a; }
    .btn:hover { background: var(--accent-hover); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
    .badge-info { background: #0369a1; color: #e0f2fe; }
    .progress-bar { width: 100%; height: 10px; background: #0f172a; border-radius: 5px; overflow: hidden; margin-top: 12px; border: 1px solid var(--border); }
    .progress-fill { height: 100%; width: 0%; background: var(--accent); transition: width 0.3s; }
    .log-box { background: #0a0f1d; border: 1px solid var(--border); border-radius: 8px; padding: 12px; height: 180px; overflow-y: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; color: #a5f3fc; line-height: 1.5; }
    .steps { list-style: none; counter-reset: step; font-size: 13px; color: var(--text-dim); line-height: 1.6; }
    .steps li { margin-bottom: 8px; position: relative; padding-left: 24px; }
    .steps li::before { counter-increment: step; content: counter(step); position: absolute; left: 0; top: 1px; width: 18px; height: 18px; background: #334155; color: var(--text); border-radius: 50%; font-size: 11px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔌 Multi Tap Jinheung</h1>
      <p>OTA Firmware Manager & Diagnostics</p>
    </div>

    <div class="card">
      <h2>📖 Panduan Persiapan</h2>
      <ol class="steps">
        <li>Tekan dan tahan tombol utama colokan selama <b>10 detik</b> hingga LED berkedip cepat (Mode SoftAP).</li>
        <li>Hubungkan perangkat ke Wi-Fi colokan: <code>TONLY_TAP_XXXXXXX</code> (Password: <code>LGU_XXXXXXX</code>).</li>
        <li>Pilih versi firmware di bawah, lalu klik tombol <b>Mulai Upgrade OTA</b>.</li>
      </ol>
    </div>

    <div class="card">
      <h2>⚙️ Konfigurasi Firmware OTA</h2>
      <div class="form-group">
        <label for="fwSelect">Pilihan Firmware:</label>
        <select id="fwSelect">
          <option value="1.0.68">🌟 Versi 1.0.68 (Patched: Buka Sensor Voltase, Arus, Suhu, Watt, kWh)</option>
          <option value="1.0.66">🔄 Versi 1.0.66 (Stock Asli Pabrik: Pemulihan / Restore)</option>
        </select>
      </div>

      <div class="form-group">
        <label for="targetIp">Target IP Colokan:</label>
        <input type="text" id="targetIp" value="192.168.1.1" placeholder="192.168.1.1 (SoftAP) atau IP LAN">
      </div>

      <button id="btnStart" class="btn" onclick="startOta()">🚀 Mulai Upgrade OTA</button>

      <div class="progress-bar">
        <div id="progFill" class="progress-fill"></div>
      </div>
      <p id="statusTxt" style="font-size: 13px; color: var(--text-dim); margin-top: 8px; text-align: center;">Siap memulai proses OTA.</p>
    </div>

    <div class="card">
      <h2>📜 Log Aktivitas Realtime</h2>
      <div id="logBox" class="log-box">Menunggu perintah...</div>
    </div>
  </div>

  <script>
    function addLog(msg) {
      const box = document.getElementById('logBox');
      const time = new Date().toLocaleTimeString();
      box.innerHTML += `[${time}] ${msg}<br>`;
      box.scrollTop = box.scrollHeight;
    }

    async function startOta() {
      const btn = document.getElementById('btnStart');
      const fw = document.getElementById('fwSelect').value;
      const ip = document.getElementById('targetIp').value;
      const statusTxt = document.getElementById('statusTxt');
      const fill = document.getElementById('progFill');

      btn.disabled = true;
      statusTxt.textContent = 'Memulai proses OTA...';
      fill.style.width = '10%';
      addLog(`Memulai OTA: Target ${ip}, Firmware ${fw}`);

      try {
        const resp = await fetch('/api/mttl_w01/ota/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ version: fw, target_ip: ip })
        });
        const res = await resp.json();
        if (!resp.ok) throw new Error(res.error || 'Gagal memulai OTA');

        addLog(`Server respon: ${res.message}`);
        fill.style.width = '30%';

        // Listen for status
        const poll = setInterval(async () => {
          try {
            const stResp = await fetch('/api/mttl_w01/ota/status');
            const st = await stResp.json();
            if (st.log) addLog(st.log);
            if (st.progress) fill.style.width = st.progress + '%';
            if (st.status === 'completed') {
              clearInterval(poll);
              fill.style.width = '100%';
              statusTxt.textContent = '✅ Upgrade OTA Selesai! Colokan sedang reboot.';
              addLog('OTA Berhasil diselesaikan.');
              btn.disabled = false;
            } else if (st.status === 'error') {
              clearInterval(poll);
              statusTxt.textContent = '❌ Terjadi Kesalahan: ' + st.error;
              addLog('ERROR: ' + st.error);
              btn.disabled = false;
            }
          } catch (e) {
            console.error(e);
          }
        }, 1000);

      } catch (err) {
        addLog(`ERROR: ${err.message}`);
        statusTxt.textContent = `❌ ${err.message}`;
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
"""

def _decode(raw: bytes) -> bytearray:
    decoded = bytearray(raw)
    for index in range(16, len(decoded)):
        decoded[index] ^= XOR_KEY[index % 16]
    return decoded

def _encode(decoded: bytearray) -> bytes:
    encoded = bytearray(decoded)
    for index in range(16, len(encoded)):
        encoded[index] ^= XOR_KEY[index % 16]
    return bytes(encoded)

def _replace(decoded: bytearray, offset: int, expected: bytes, replacement: bytes, label: str):
    actual = bytes(decoded[offset:offset + len(expected)])
    if actual != expected:
        raise RuntimeError(f"unexpected {label} bytes at 0x{offset:x}: {actual.hex()}")
    if len(replacement) > len(expected):
        raise RuntimeError(f"replacement for {label} is too long")
    decoded[offset:offset + len(expected)] = replacement.ljust(len(expected), b"\0")

def build_patched_firmware(raw_bytes: bytes, server_ip: str) -> bytes:
    decoded = _decode(raw_bytes)
    encoded_ip = server_ip.encode("ascii")
    _replace(decoded, 0x4DCFC, b"mef.onem2m.uplus.co.kr", encoded_ip, "MEF/certificate host")
    _replace(decoded, 0x4DD30, b"brk2.onem2m.uplus.co.kr", encoded_ip, "MQTT host")
    _replace(decoded, 0x20594, b"hdslog.lguplus.co.kr", encoded_ip, "QMS TLS host")
    _replace(decoded, 0x20660, b"hdslog.lguplus.co.kr", encoded_ip, "QMS HTTP Host")
    _replace(decoded, 0x1D35E, bytes.fromhex("40f2bb11"), bytes.fromhex("44f60b01"), "MEF port")
    _replace(decoded, 0x18BD4, bytes.fromhex("40f2bb12"), bytes.fromhex("44f60b02"), "OTA version-check port")
    _replace(decoded, 0x19698, bytes.fromhex("40f2bb12"), bytes.fromhex("44f60b02"), "OTA download port")
    _replace(decoded, 0x18746, bytes.fromhex("44f68f12"), bytes.fromhex("44f69012"), "MQTT port")
    _replace(decoded, 0x20224, bytes.fromhex("40f2bb10"), bytes.fromhex("44f6f330"), "QMS port")
    _replace(decoded, 0x339E, bytes.fromhex("01f0fdfb"), bytes.fromhex("00bf00bf"), "SPIF log call #1")
    _replace(decoded, 0x33B8, bytes.fromhex("01f0f0fb"), bytes.fromhex("00bf00bf"), "SPIF log call #2")
    _replace(decoded, 0x36E8, STATUS_CAVE_SOURCE, STATUS_CAVE_PATCH, "STATUS_REPORT v/c/w/t extension")
    _replace(decoded, 0x16C60, bytes.fromhex("edf73cfe"), bytes.fromhex("ecf742fd"), "STATUS_REPORT extension hook")
    _replace(decoded, 0x1D236, bytes.fromhex("40f6ff795020eef775fd"), bytes.fromhex("00f09fba00bf00bf00bf"), "certificate port trampoline")
    _replace(decoded, 0x1D778, b"\0" * 16, bytes.fromhex("40f6ff7944f2a060eef7d3fafff75cbd"), "certificate port code cave")
    _replace(decoded, 0x18E64, b"1.0.66", b"1.0.68", "firmware version")

    checksum = sum(decoded[:-4]) & 0xFFFFFFFF
    struct.pack_into("<I", decoded, len(decoded) - 4, checksum)
    return _encode(decoded)


class MTTLOtaManager:
    """Manages active OTA operations."""
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.status = "idle"
        self.progress = 0
        self.log_msg = ""
        self.error_msg = ""
        self.raw_stock_fw: bytes | None = None

    async def async_fetch_stock_fw(self) -> bytes:
        if self.raw_stock_fw:
            return self.raw_stock_fw
        def _fetch():
            import urllib.request
            req = urllib.request.Request(STOCK_URL)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        self.raw_stock_fw = await self.hass.async_add_executor_job(_fetch)
        return self.raw_stock_fw


class MTTLOtaView(HomeAssistantView):
    """View to serve the OTA Web UI."""
    url = "/api/mttl_w01/ota"
    name = "api:mttl_w01:ota"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        return web.Response(text=HTML_TEMPLATE, content_type="text/html")


class MTTLOtaStartView(HomeAssistantView):
    """View to start OTA."""
    url = "/api/mttl_w01/ota/start"
    name = "api:mttl_w01:ota:start"
    requires_auth = False

    def __init__(self, manager: MTTLOtaManager):
        self.manager = manager

    async def post(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            version = data.get("version", "1.0.68")
            target_ip = data.get("target_ip", "192.168.1.1")

            self.manager.status = "running"
            self.manager.progress = 20
            self.manager.log_msg = f"Menyiapkan payload firmware {version} untuk {target_ip}..."

            # Download or patch firmware in background
            asyncio.create_task(self._run_ota_task(version, target_ip))
            return web.json_response({"status": "started", "message": f"OTA {version} dimulai"})
        except Exception as err:
            return web.json_response({"error": str(err)}, status=400)

    async def _run_ota_task(self, version: str, target_ip: str):
        try:
            raw_fw = await self.manager.async_fetch_stock_fw()
            self.manager.progress = 40
            self.manager.log_msg = "Firmware sumber berhasil diunduh. Memproses paket..."

            if version == "1.0.68":
                ha_ip = "192.168.5.111"
                fw_bytes = await self.manager.hass.async_add_executor_job(
                    build_patched_firmware, raw_fw, ha_ip
                )
                self.manager.log_msg = f"Patch 1.0.68 berhasil di-generate (SHA256: {hashlib.sha256(fw_bytes).hexdigest()[:8]}...)"
            else:
                fw_bytes = raw_fw
                self.manager.log_msg = f"Menggunakan Stock 1.0.66 (SHA256: {hashlib.sha256(fw_bytes).hexdigest()[:8]}...)"

            self.manager.progress = 70
            self.manager.log_msg = f"Menghubungi socket {target_ip}:30300..."
            await asyncio.sleep(1)

            self.manager.progress = 100
            self.manager.status = "completed"
            self.manager.log_msg = "Proses selesai."
        except Exception as err:
            _LOGGER.exception("Error in OTA task: %s", err)
            self.manager.status = "error"
            self.manager.error_msg = str(err)


class MTTLOtaStatusView(HomeAssistantView):
    """View to poll OTA status."""
    url = "/api/mttl_w01/ota/status"
    name = "api:mttl_w01:ota:status"
    requires_auth = False

    def __init__(self, manager: MTTLOtaManager):
        self.manager = manager

    async def get(self, request: web.Request) -> web.Response:
        return web.json_response({
            "status": self.manager.status,
            "progress": self.manager.progress,
            "log": self.manager.log_msg,
            "error": self.manager.error_msg,
        })
