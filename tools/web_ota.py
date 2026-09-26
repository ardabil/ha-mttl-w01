#!/usr/bin/env python3
"""Multi Tap Jinheung (MTTL-W01) Web-based OTA Firmware Tool."""

import base64
import hashlib
import http.server
import ipaddress
import json
import logging
import os
import queue
import socket
import socketserver
import struct
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

WEB_PORT = 8088
OTA_PORT = 80
STOCK_URL = "https://raw.githubusercontent.com/af950833/mttl_w01/main/work/firmware/1.0.66/comMTTL-W01_1.0.66.fwr"
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

current_events = queue.Queue()
active_ota_data = None
ota_in_progress = False

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

def build_patched(raw_bytes: bytes, server_ip: str) -> bytes:
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


class OtaFileHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global active_ota_data
        if self.path != "/ota.bin" or not active_ota_data:
            self.send_error(404)
            return
        data = active_ota_data
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()

        sent = 0
        for offset in range(0, len(data), 512):
            chunk = data[offset:offset + 512]
            self.wfile.write(chunk)
            self.wfile.flush()
            sent += len(chunk)
            pct = int(sent * 100 / len(data))
            current_events.put({"progress": pct, "log": f"Streaming OTA chunk {sent}/{len(data)} bytes ({pct}%)"})
            time.sleep(0.005)
        current_events.put({"progress": 100, "status": "completed", "log": "Upload firmware selesai! Menunggu colokan reboot."})


class WebDashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            # Read from ota_view HTML template
            from custom_components.mttl_w01.ota_view import HTML_TEMPLATE
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif self.path == "/api/mttl_w01/ota/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            ev = {"status": "idle", "progress": 0, "log": ""}
            try:
                ev = current_events.get_nowait()
            except queue.Empty:
                pass
            self.wfile.write(json.dumps(ev).encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        global active_ota_data, ota_in_progress
        if self.path == "/api/mttl_w01/ota/start":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            params = json.loads(body.decode("utf-8"))
            fw_version = params.get("version", "1.0.68")
            target_ip = params.get("target_ip", "192.168.1.1")

            def _worker():
                global active_ota_data, ota_in_progress
                ota_in_progress = True
                try:
                    current_events.put({"progress": 10, "log": f"Mengunduh file base firmware 1.0.66..."})
                    req = urllib.request.Request(STOCK_URL)
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        raw = resp.read()

                    if fw_version == "1.0.68":
                        current_events.put({"progress": 30, "log": "Mem-patch firmware menjadi versi 1.0.68 (Expanded V/I/W/T)..."})
                        active_ota_data = build_patched(raw, "192.168.1.100")
                    else:
                        active_ota_data = raw

                    current_events.put({"progress": 50, "log": f"Menghubungi target {target_ip}:30300..."})

                    # Connect and send up:ota
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        s.connect((target_ip, 30300))
                        local_ip = s.getsockname()[0]

                    with socket.create_connection((target_ip, 30300), timeout=5) as sock:
                        sock.sendall(f"up:ota:{local_ip}\r\n".encode("ascii"))
                        current_events.put({"progress": 60, "log": f"Perintah OTA terkirim: up:ota:{local_ip}"})

                except Exception as err:
                    current_events.put({"status": "error", "error": str(err), "log": f"Error: {err}"})
                finally:
                    ota_in_progress = False

            threading.Thread(target=_worker, daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started", "message": "OTA worker started"}).encode("utf-8"))


def main():
    print(f"==================================================")
    print(f"  Multi Tap Jinheung (MTTL-W01) Web OTA Tool")
    print(f"==================================================")
    print(f"Starting Web Dashboard on http://localhost:{WEB_PORT} ...")

    # Start Port 80 OTA file server
    try:
        ota_server = socketserver.TCPServer(("", OTA_PORT), OtaFileHandler)
        threading.Thread(target=ota_server.serve_forever, daemon=True).start()
        print(f"[*] OTA HTTP Server active on port {OTA_PORT}")
    except PermissionError:
        print(f"[!] Warning: Port 80 requires root/admin privilege for actual flashing.")

    # Start Web UI Server
    web_server = socketserver.TCPServer(("", WEB_PORT), WebDashboardHandler)
    print(f"[*] Web UI ready at http://localhost:{WEB_PORT}")
    try:
        webbrowser.open(f"http://localhost:{WEB_PORT}")
    except Exception:
        pass
    web_server.serve_forever()


if __name__ == "__main__":
    main()
