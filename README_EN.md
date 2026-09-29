# Multi Tap Jinheung (4-Gang Smart Power Strip)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ardabil&repository=ha-mttl-w01&category=integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![Validate with hassfest](https://img.shields.io/badge/hassfest-passing-brightgreen.svg)](https://github.com/home-assistant/core)

[Bahasa Indonesia](README.md) | **English**

A pure Python native Home Assistant (HACS) integration for **Multi Tap Jinheung** (LG U+ MTTL-W01 4-Gang Smart Power Strip). It connects directly via local TCP socket protocol (port `10086`) without requiring any Matter bridge or MQTT broker.

---

## 🌟 Features

- **4 Independent Outlets:** Instant ON/OFF control for outlets 1 through 4 via local push.
- **Native RMS Voltage (V):** Reads real dynamic RMS AC Voltage directly from the hardware metering chip via native command `up:power_report:1:vol`.
- **Native RMS Current (A):** Reads real physical current per outlet and calculated total current (A) via native command `up:power_report:<ch>:current`.
- **Real-Time Active Power (W):** Per-outlet real-time power consumption in Watts.
- **Accumulated Energy (kWh):** Per-outlet energy consumption tracking, fully compatible with the *Home Assistant Energy Dashboard*.
- **Internal PCB Temperature (°C):** Internal temperature monitoring for overheat protection.
- **Wi-Fi Signal Strength (RSSI):** Monitors strip Wi-Fi connection quality (dBm) via `up:query:wifirssi`.
- **Auto-Discovery:** Automatically detects new strips when they connect to the Home Assistant TCP server.
- **100% Stock Firmware Support:** Works out of the box on **factory stock firmware (1.0.66)**. **No firmware modification or flashing required!**

---

## 📦 Installation via HACS

### 1. Add Custom Repository in HACS
1. In Home Assistant, navigate to **HACS** -> **Integrations**.
2. Click the three dots menu (⋮) in the top-right corner -> select **Custom repositories**.
3. Enter the Repository URL:
   ```text
   https://github.com/ardabil/ha-mttl-w01
   ```
4. Select Type: **Integration** -> Click **Add**.
5. Find **Multi Tap Jinheung** -> Click **Download**.
6. Restart Home Assistant.

### 2. Add Integration in Home Assistant
1. Go to **Settings** -> **Devices & Services** -> **Integrations**.
2. Click **+ Add Integration** -> Search for **Multi Tap Jinheung**.
3. Click **Submit** (keep default port `10086`).

---

## 🔌 Wi-Fi Setup & Pairing (Connect to Home Assistant)

The smart power strip needs your local 2.4 GHz Wi-Fi credentials and your **Home Assistant IP** so it can stream telemetry to port `10086`.

### 1. Enter Pairing Mode (SoftAP)
1. Plug the Jinheung MTTL-W01 into an AC outlet.
2. Press and hold the main physical power button for **10 seconds** until the Wi-Fi LED blinks rapidly.
3. Connect your laptop or smartphone Wi-Fi to the strip's access point:
   - **SSID:** `TONLY_TAP_XXXXXXX`
   - **Password:** `LGU_XXXXXXX`

### 2. Send Network Configuration
Use either of the following setup tools:

* **Option A: Using PC / Laptop (GUI Tool)**
  - 🪟 **[Download Windows Setup Tool (.exe)](https://github.com/ttaengz/mttl-w01-matterbridge/raw/main/tools/setup_wifi_gui_windows.exe)**
  - 🍏 **[Download macOS Setup Tool (.zip)](https://github.com/ttaengz/mttl-w01-matterbridge/raw/main/tools/setup_wifi_gui_macos.zip)**
  - Open the application, enter your 2.4 GHz Wi-Fi SSID, Wi-Fi Password, and your **Home Assistant IP**.
  - Click **Start Wi-Fi setup**.

* **Option B: Using Android Smartphone (APK)**
  - 📱 **[Download MTTL-W01 Provisioner APK](https://github.com/af950833/mttl_w01/raw/main/web/downloads/MTTL-W01-Provisioner.apk)**
  - Install the APK, select your 2.4 GHz Wi-Fi SSID, enter your password and HA IP, then click **Provision**.

Once the strip automatically reboots (LED stops blinking), it will connect directly to Home Assistant, and all outlets and sensors will appear automatically!

---

## 📜 Credits & References
- **Protocol & Setup Tools:** [ttaengz/mttl-w01-matterbridge](https://github.com/ttaengz/mttl-w01-matterbridge)
- **Home Assistant Native HACS Integration:** [ardabil](https://github.com/ardabil)
