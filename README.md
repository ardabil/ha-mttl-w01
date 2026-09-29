# Multi Tap Jinheung / Stop Kontak Smart (4-Gang Smart Power Strip)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ardabil&repository=ha-mttl-w01&category=integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![Validate with hassfest](https://img.shields.io/badge/hassfest-passing-brightgreen.svg)](https://github.com/home-assistant/core)

Integrasi Native Home Assistant (HACS) berbasis Python murni untuk **Multi Tap Jinheung / Stop Kontak Smart** (LG U+ MTTL-W01 4-Gang Smart Power Strip). Berjalan langsung menggunakan protokol TCP socket lokal (port `10086`) tanpa memerlukan perantara Matter bridge ataupun broker MQTT.

---

## 🌟 Fitur (Features)

- **4 Saklar Independen:** Kontrol ON/OFF untuk masing-masing outlet 1 sampai 4 dengan respons instan (*local push*).
- **Sensor Tegangan Riil (Volt):** Membaca nilai RMS Voltage dinamis aktual dari chip metering hardware melalui perintah *native* `up:power_report:1:vol`.
- **Sensor Arus Riil (Ampere):** Membaca arus fisik per outlet dan total arus keseluruhan (A) secara langsung melalui perintah *native* `up:power_report:<ch>:current`.
- **Sensor Daya Realtime:** Pembacaan konsumsi daya aktif (Watt) setiap outlet.
- **Sensor Energi Akumulasi:** Pembacaan akumulasi energi berjalan per outlet (kWh), kompatibel penuh dengan *Home Assistant Energy Dashboard*.
- **Sensor Suhu Internal:** Pemantauan suhu internal PCB (°C) untuk keamanan proteksi overheat.
- **Sensor Sinyal Wi-Fi (RSSI):** Pemantauan kualitas sinyal nirkabel smart power strip (dBm) via `up:query:wifirssi`.
- **Auto-Discovery:** Otomatis mendeteksi perangkat baru ketika smart power strip terhubung ke port TCP Home Assistant.
- **100% Native Firmware Bawaan:** Berfungsi penuh pada **firmware bawaan pabrik (1.0.66)**. **Tidak perlu memodifikasi atau mem-flash firmware sama sekali!**

---

## 📦 Cara Instalasi via HACS

### 1. Tambahkan Custom Repository di HACS
1. Di Home Assistant, buka menu **HACS** -> **Integrations**.
2. Klik menu titik tiga (⋮) di kanan atas -> pilih **Custom repositories**.
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

## 🔌 Setup Wi-Fi Smart Power Strip (Pairing ke Home Assistant)

Smart power strip ini membutuhkan konfigurasi SSID Wi-Fi rumah dan IP Home Assistant Anda agar dapat mengalirkan data ke port `10086`.

### 1. Masuk ke Mode Pairing (SoftAP)
1. Hubungkan Jinheung MTTL-W01 ke sumber listrik.
2. Tekan dan tahan tombol fisik utama selama **10 detik** sampai lampu LED Wi-Fi berkedip cepat.
3. Sambungkan Wi-Fi laptop atau smartphone Anda ke access point smart power strip:
   - **SSID:** `TONLY_TAP_XXXXXXX`
   - **Password:** `LGU_XXXXXXX`

### 2. Kirim Konfigurasi Jaringan
Gunakan salah satu alat bantu di bawah ini:

* **Pilihan A: Menggunakan PC/Laptop (GUI Tool)**
  - 🪟 **[Download Setup Tool Windows (.exe)](https://github.com/ttaengz/mttl-w01-matterbridge/raw/main/tools/setup_wifi_gui_windows.exe)**
  - 🍏 **[Download Setup Tool macOS (.zip)](https://github.com/ttaengz/mttl-w01-matterbridge/raw/main/tools/setup_wifi_gui_macos.zip)**
  - Buka aplikasi, masukkan SSID Wi-Fi 2.4 GHz, Password Wi-Fi rumah, dan **IP Home Assistant** Anda.
  - Klik **Start Wi-Fi setup**.

* **Pilihan B: Menggunakan Smartphone Android (APK)**
  - 📱 **[Download MTTL-W01 Provisioner APK](https://github.com/af950833/mttl_w01/raw/main/web/downloads/MTTL-W01-Provisioner.apk)**
  - Pasang di Android, pilih SSID Wi-Fi 2.4 GHz, masukkan password, lalu klik **Provision**.

Setelah smart power strip reboot otomatis (LED berhenti berkedip), perangkat akan langsung terhubung ke Home Assistant dan seluruh saklar serta sensor akan otomatis muncul!

---

## 📜 Credits & Referensi
- **Protokol & Setup Tools:** [ttaengz/mttl-w01-matterbridge](https://github.com/ttaengz/mttl-w01-matterbridge)
- **Home Assistant Native HACS Integration:** [ardabil](https://github.com/ardabil)
