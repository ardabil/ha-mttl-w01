# Multi Tap Jinheung (Home Assistant Integration)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ardabil&repository=ha-mttl-w01&category=integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![Validate with hassfest](https://img.shields.io/badge/hassfest-passing-brightgreen.svg)](https://github.com/home-assistant/core)

Integrasi Native Home Assistant (HACS) berbasis Python murni untuk colokan pintar 4 lubang **Multi Tap Jinheung** (LG MTTL-W01).

---

## 🌟 Fitur (Features)
- **4 Saklar Independen:** Kontrol ON/OFF untuk masing-masing outlet 1 sampai 4.
- **Sensor Tegangan (Volt):** Pembacaan voltase listrik (V).
- **Sensor Arus (Ampere):** Pembacaan arus listrik per outlet dan total arus (A).
- **Sensor Daya Realtime:** Pembacaan Watt (W) setiap outlet.
- **Sensor Energi Akumulasi:** Pembacaan Total kWh per outlet (kompatibel dengan HA Energy Dashboard).
- **Sensor Suhu:** Pemantauan suhu internal colokan (°C).
- **Auto-Discovery:** Otomatis mendeteksi perangkat saat terhubung ke IP Home Assistant.
- **Dukungan Semua Versi Firmware:** Kompatibel dengan firmware bawaan pabrik (1.0.66) maupun custom firmware modifikasi (1.0.68).

---

## 📦 Cara Instalasi via HACS

### 1. Tambahkan Custom Repository di HACS
1. Di Home Assistant, buka menu **HACS** -> **Integrations**.
2. Klik titik 3 di kanan atas -> pilih **Custom repositories**.
3. Masukkan Repository URL:
   ```text
   https://github.com/ardabil/ha-mttl-w01
   ```
4. Pilih Type: **Integration** -> Klik **Add**.
5. Cari **Multi Tap Jinheung** -> Klik **Download**.
6. Restart Home Assistant.

### 2. Tambahkan Integrasi di Home Assistant
1. Buka **Settings** -> **Devices & Services** -> **Integrations**.
2. Klik **+ Add Integration** -> Cari **Multi Tap Jinheung**.
3. Klik **Submit** (gunakan port default `10086`).

---

## 🔌 Setup Wi-Fi Colokan (Khusus Pengguna Baru)

1. Tekan dan tahan tombol utama colokan selama **10 detik** sampai lampu Wi-Fi berkedip cepat (Mode SoftAP).
2. Konek laptop/PC ke Wi-Fi colokan `TONLY_TAP_XXXXXXX` (Password: `LGU_XXXXXXX`).
3. Jalankan aplikasi setup GUI:
   - 🪟 **[Download Setup Tool Windows (.exe)](https://github.com/ttaengz/mttl-w01-matterbridge/raw/main/tools/setup_wifi_gui_windows.exe)**
   - 🍏 **[Download Setup Tool macOS (.zip)](https://github.com/ttaengz/mttl-w01-matterbridge/raw/main/tools/setup_wifi_gui_macos.zip)**
4. Masukkan nama Wi-Fi rumah, password, dan **IP Home Assistant** Anda.
5. Klik **Start Wi-Fi setup**. Setelah colokan reboot, perangkat akan otomatis terhubung ke Home Assistant!

---

## ⚡ Panduan Upgrade Custom Firmware (Opsional: Unlock Sensor Fisik V & A)

Integrasi ini **langsung berfungsi pada firmware bawaan pabrik (1.0.66)**. Jika Anda ingin membuka sensor pembacaan voltase dan arus fisik murni dari chip metering hardware colokan, Anda dapat melakukan upgrade ke custom firmware patched (1.0.68).

### 📥 Download File Firmware & Flasher
- **Firmware Bawaan (Stock 1.0.66):** [comMTTL-W01_1.0.66.fwr](https://raw.githubusercontent.com/af950833/mttl_w01/main/work/firmware/1.0.66/comMTTL-W01_1.0.66.fwr) *(Sumber: Server Resmi LG U+ via af950833)*
- **Custom Firmware Patched (1.0.68):** [comMTTL-W01_1.0.68_patched.fwr](https://raw.githubusercontent.com/af950833/mttl_w01/main/work/firmware/1.0.68/comMTTL-W01_1.0.68.fwr) *(Sumber: af950833/mttl_w01)*
- **Tool Flashing GUI Windows:** [ota_gui_windows.exe](https://github.com/ttaengz/mttl-w01-matterbridge/raw/main/tools/ota_gui_windows.exe)

### 🚀 Cara Flashing Firmware via Wi-Fi (SoftAP):
1. Tekan tahan tombol fisik colokan selama **10 detik** hingga LED Wi-Fi berkedip cepat.
2. Sambungkan Wi-Fi laptop/PC ke `TONLY_TAP_XXXXXXX` (Password: `LGU_XXXXXXX`).
3. Buka **PowerShell as Administrator**, lalu matikan service Windows yang mengunci Port 80:
   ```powershell
   net stop http /y
   ```
4. Buka aplikasi **`ota_gui_windows.exe`** (Run as Administrator), pilih file `comMTTL-W01_1.0.68_patched.fwr`, lalu klik **Start OTA**.
5. Tunggu hingga transfer $100\%$ dan colokan reboot otomatis (sekitar 30 detik).
6. Sambungkan kembali ke Wi-Fi `TONLY_TAP_XXXXXXX` dan jalankan **`setup_wifi_gui_windows.exe`** untuk mengarahkan colokan ke Wi-Fi rumah & IP Home Assistant.

---

## 📜 Credits & Referensi
- **Firmware & Reverse Engineering:** [af950833/mttl_w01](https://github.com/af950833/mttl_w01) (Penyedia firmware stock 1.0.66 & pembuat patch 1.0.68).
- **Protokol & Setup Tools:** [ttaengz/mttl-w01-matterbridge](https://github.com/ttaengz/mttl-w01-matterbridge).
- **Home Assistant Native HACS Integration:** [ardabil](https://github.com/ardabil).
