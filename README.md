# 🏷️ Pi Badge – E-Ink Namensschild mit Web-Interface

> 💡 **Dieses Projekt ist in Zusammenarbeit mit [Claude](https://claude.ai) (KI-Assistent von Anthropic) entstanden.**

Ein web-basierter Editor für ein E-Ink-Namensschild auf Basis des **Raspberry Pi Zero 2W** und einem **Waveshare 2.13" E-Ink Display**. Inhalte werden bequem über den Browser gepflegt und direkt aufs Display geschrieben. Einträge werden in einer SQLite-Datenbank gespeichert und können jederzeit wiederverwendet werden.

---

## 📸 Was macht dieses Projekt?

Du rufst `http://badge.local:5000` im Browser auf, gibst Name, Titel und eine Info-Zeile ein – optional mit Bild – und schickst das Layout mit einem Klick aufs Display. Das Bild bleibt dank E-Ink-Technologie auch ohne Stromversorgung erhalten.

---

## 🔧 Hardware

- Raspberry Pi Zero 2W
- Waveshare 2.13" E-Ink HAT (250×122px, SPI, V2 oder V3)

Das Display wird direkt auf die GPIO-Pins gesteckt – keine weitere Verkabelung nötig.

---

## ✨ Features

- Web-Interface unter `http://badge.local:5000`
- Felder: **Name**, **Titel**, **Info**
- Rotation wählbar: 0°, 90°, 180°, 270°
- Bild-Upload mit automatischer Konvertierung (S/W, max. 60×60px)
- Live-Vorschau im Browser (4× skaliert)
- Einträge speichern, bearbeiten, löschen und direkt aufs Display schicken
- Persistenz via SQLite
- Läuft als Systemd-Service – startet automatisch nach Reboot

---

## 🚀 Installation

### 1. Raspberry Pi OS Lite installieren

Mit dem **Raspberry Pi Imager** (64-bit Lite empfohlen). Vor dem Flashen im Imager vorkonfigurieren:

- Hostname: `badge`
- SSH aktivieren
- WLAN-Zugangsdaten eintragen
- Benutzer anlegen (z.B. `badge`)

Nach dem Start erreichbar via:

```bash
ssh badge@badge.local
```

### 2. SPI aktivieren

```bash
sudo raspi-config
# → Interface Options → SPI → Enable
sudo reboot
```

Prüfen ob SPI aktiv ist:

```bash
ls /dev/spi*
# Erwartet: /dev/spidev0.0 und /dev/spidev0.1
```

### 3. Abhängigkeiten installieren

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git python3-pil libopenjp2-7 fonts-dejavu-core swig liblgpio-dev

# Waveshare Library holen
git clone https://github.com/waveshare/e-Paper.git

# Virtualenv anlegen
python3 -m venv ~/badge-env
source ~/badge-env/bin/activate

# Python-Pakete installieren
pip install -r requirements.txt

# Waveshare Library ins Virtualenv installieren
cd ~/e-Paper/RaspberryPi_JetsonNano/python
pip install .
cd ~
```

### 4. Repository klonen

```bash
git clone https://github.com/kekZiger/raspberry-pi-badge-e-ink.git ~/badge-app
cd ~/badge-app
```

### 5. Fonts kopieren

```bash
mkdir -p ~/badge-app/fonts
cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf ~/badge-app/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf ~/badge-app/fonts/
```

### 6. Display testen

```bash
source ~/badge-env/bin/activate
cd ~/e-Paper/RaspberryPi_JetsonNano/python/examples
python3 epd_2in13_V3_test.py
```

Wenn das Demo durchläuft und etwas auf dem Display erscheint, ist die Hardware bereit.

### 7. Display-Version in app.py prüfen

Je nach deinem Display-Modell in `app.py` anpassen:

```python
from waveshare_epd import epd2in13_V3  # oder epd2in13_V2
```

### 8. Systemd-Service einrichten

Wenn dein Benutzername **nicht** `badge` ist, passe den Pfad in `badge.service` vorher an.

```bash
sudo cp ~/badge-app/badge.service /etc/systemd/system/badge.service
sudo systemctl daemon-reload
sudo systemctl enable badge
sudo systemctl start badge
```

Status prüfen:

```bash
sudo systemctl status badge
```

Logs bei Problemen:

```bash
journalctl -u badge.service -n 50 --no-pager
```

---

## 🖥️ Bedienung

1. Browser öffnen: **`http://badge.local:5000`**
2. Name, Titel und Info eingeben
3. Rotation wählen (0° / 90° / 180° / 270°)
4. Optional ein Bild hochladen – wird automatisch konvertiert
5. **Vorschau** – zeigt das Layout 4× skaliert im Browser
6. **Speichern** – legt den Eintrag in der Datenbank ab
7. **▶ Anzeigen** – schreibt den Eintrag aufs Display
8. **✏️ Bearbeiten** – lädt den Eintrag zurück in den Editor
9. **✕ Löschen** – entfernt den Eintrag

---

## 📁 Projektstruktur

```
badge-app/
├── app.py                  # Flask-App, Display-Rendering, API
├── requirements.txt        # Python-Abhängigkeiten
├── badge.service           # Systemd-Service-Definition
├── .gitignore
├── fonts/                  # DejaVu-Fonts (nicht im Repo, siehe Installation)
├── static/
│   └── uploads/            # Temporäre Upload-Ablage
└── templates/
    └── index.html          # Web-Interface
```

---

## 🗺️ Geplante Erweiterungen

- [ ] Hardware-Button zum Durchschalten zwischen gespeicherten Einträgen
- [ ] QR-Code-Generierung via `qrcode`-Library
- [ ] Vorlagen / Kategorien

---

## 📦 Abhängigkeiten

- **Flask** – Web-Server
- **Pillow** – Bild-Rendering & Konvertierung
- **gpiozero / lgpio** – GPIO-Ansteuerung
- **waveshare-epd** – Display-Treiber (via separatem `git clone`)
- **SQLite3** – Datenpersistenz (Python built-in)
