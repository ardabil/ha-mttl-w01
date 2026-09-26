# LG / Jinheung MTTL-W01 Home Assistant Integration (HACS)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![Validate with hassfest](https://img.shields.io/badge/hassfest-passing-brightgreen.svg)](https://github.com/home-assistant/core)

Integrasi Native Home Assistant (HACS) berbasis Python murni untuk colokan pintar 4 lubang **LG / Jinheung MTTL-W01**.

---

## 🚀 Keunggulan Dibandingkan Matter / Add-on
- **100% Native Python:** Berjalan langsung di dalam Home Assistant Core (tanpa butuh Docker container terpisah).
- **Sangat Hemat Resource:** Konsumsi RAM hanya **~2-5 MB** (dibandingkan ~200MB pada add-on Docker).
- **Tanpa Test DCL:** Tidak perlu mengaktifkan pengaturan Test DCL pada Matter Server.
- **Komunikasi Langsung:** Direct local socket TCP (Port 10086) dengan latency nol.
- **Real-time Push:** Respon instan saat tombol fisik ditekan secara manual.

---

## 🌟 Fitur (Features)
- **4 Saklar Independen:** Kontrol ON/OFF untuk masing-masing outlet 1 sampai 4.
- **Sensor Daya Realtime:** Pembacaan Watt (W) setiap outlet.
- **Sensor Energi Akumulasi:** Pembacaan Total kWh per outlet (kompatibel dengan HA Energy Dashboard).
- **Sensor Suhu:** Pemantauan suhu internal colokan (°C).
- **Auto-Discovery:** Otomatis mendeteksi perangkat saat terhubung ke IP Home Assistant.

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
5. Cari **LG / Jinheung MTTL-W01 Smart Power Strip** -> Klik **Download**.
6. Restart Home Assistant.

### 2. Tambahkan Integrasi di Home Assistant
1. Buka **Settings** -> **Devices & Services** -> **Integrations**.
2. Klik **+ Add Integration** -> Cari **LG / Jinheung MTTL-W01**.
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

## 📜 Credits
- Protocol analysis: [ttaengz/mttl-w01-matterbridge](https://github.com/ttaengz/mttl-w01-matterbridge) & [omarKmekkawy](https://github.com/omarKmekkawy/Korean_LG_TCL_MTTL-w01_power-strip)
- Home Assistant Native Integration: [ardabil](https://github.com/ardabil)
