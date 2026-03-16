# Facial & Voice Recognition Car Security System
### Fully Offline — No Internet Required at Runtime

---

## Project Structure

```
car_security/
│
├── main.py                           # Entry point — runs the full pipeline
│
├── config/
│   └── settings.py                   # All constants (pins, thresholds, paths)
│
├── core/
│   ├── face_capture.py               # Stage 1 — best frame selection
│   ├── face_recognition_engine.py    # Stage 2 — face embedding comparison
│   ├── voice_capture.py              # Stage 3A — mic recording via pyaudio
│   └── voice_recognition_engine.py   # Stage 3B — SpeechBrain offline verify
│
├── hardware/
│   ├── relay.py                      # Stage 5 — GPIO relay for ignition
│   ├── buzzer.py                     # Stage 4 — GPIO buzzer alarm
│   └── serial_comm.py                # Stage 4 — UART to ESP32
│
├── enrollment/
│   ├── enroll_face.py                # Run once — saves owner face embedding
│   └── enroll_voice.py               # Run once — saves owner voice embedding
│
├── setup/
│   ├── download_models.py            # Downloads SpeechBrain model to disk
│   ├── download_packages.py          # Downloads pip .whl files for offline install
│   └── check_offline.py              # Verifies system is 100% offline-ready
│
├── esp32/
│   └── car_security_esp32.ino        # ESP32 firmware (Arduino IDE)
│
├── utils/
│   └── logger.py                     # Rotating file + console logger
│
├── models/
│   └── ecapa_tdnn/                   # SpeechBrain model (pre-downloaded)
│
├── data/                             # Stores owner embeddings
│   ├── owner_face.npy
│   └── owner_voice.pt
│
├── packages/                         # Offline pip .whl files (optional)
├── logs/
└── requirements.txt
```

---

## Offline Setup — Step by Step

### On a machine WITH internet (laptop/PC — do this ONCE)

**Step 1 — Clone/copy project and install packages**
```bash
pip install -r requirements.txt
```

**Step 2 — Download SpeechBrain ECAPA model to disk (~85 MB)**
```bash
python setup/download_models.py
```
This saves the model into `models/ecapa_tdnn/`. After this, the system
never needs internet again.

**Step 3 — (Optional) Download all pip wheels for fully offline RPi install**
```bash
python setup/download_packages.py
```
Saves `.whl` files into `packages/`. Useful if the RPi has never had internet.

**Step 4 — Copy entire project folder to RPi4 via USB / SCP**
```bash
scp -r car_security/ pi@<rpi-ip>:~/
```

---

### On the Raspberry Pi 4 (no internet needed from here)

**Step 5 — Enable camera + UART**
```bash
sudo raspi-config
# Interface Options → Camera → Enable
# Interface Options → Serial → Disable login shell, Enable hardware serial
sudo reboot
```

**Step 6 — Install system dependencies**
```bash
sudo apt update
sudo apt install -y python3-pip libatlas-base-dev portaudio19-dev \
    cmake libboost-all-dev libopenblas-dev liblapack-dev python3-dev
```

**Step 7 — Install Python packages (offline from wheels if no internet)**
```bash
# If internet available on RPi:
pip install -r requirements.txt --break-system-packages

# If completely offline (requires Step 3 above):
pip install --no-index --find-links=packages/ -r requirements.txt --break-system-packages
```

**Step 8 — Run offline readiness check**
```bash
python setup/check_offline.py
```
All checks must pass before proceeding.

**Step 9 — Enroll owner face**
```bash
python enrollment/enroll_face.py
```
Press SPACE 5 times to capture. Saves `data/owner_face.npy`.

**Step 10 — Enroll owner voice**
```bash
python enrollment/enroll_voice.py
```
Speak a consistent phrase 5 times. Saves `data/owner_voice.pt`.

**Step 11 — Flash ESP32**
Open `esp32/car_security_esp32.ino` in Arduino IDE.
- Install library: TinyGPS++ (Library Manager)
- Set `OWNER_PHONE` to owner's number with country code
- Board: ESP32 Dev Module → Upload

**Step 12 — Run**
```bash
python main.py
```

---

## What Works Offline vs What Needs Internet

| Component | Offline? | Notes |
|---|---|---|
| Face recognition (dlib) | YES | Pure local inference |
| Voice recognition (SpeechBrain) | YES | Model pre-downloaded to models/ |
| GPS location | YES | NEO-6M hardware, no internet |
| SMS alert | YES | SIM800L uses GSM cellular (not WiFi) |
| Relay / Buzzer / GPIO | YES | Pure hardware |
| pip install | YES | After Step 3, uses local .whl files |
| Model download | ONCE | Only needed during setup |

---

## Hardware Connections

### Raspberry Pi 4 GPIO (BCM numbering)
| Component      | RPi Pin        | GPIO |
|----------------|----------------|------|
| Relay IN       | Pin 11         | 17   |
| Buzzer +       | Pin 13         | 27   |
| Green LED      | Pin 15         | 22   |
| ESP32 RX←TX    | Pin 8  (TX)    | 14   |
| ESP32 TX→RX    | Pin 10 (RX)    | 15   |
| RPi Camera v2  | CSI port       | —    |
| USB Microphone | USB port       | —    |

### ESP32 UART Connections
| Device     | ESP32 GPIO | Direction |
|------------|-----------|-----------|
| RPi TX     | GPIO3 (RX0)| → ESP32   |
| RPi RX     | GPIO1 (TX0)| ← ESP32   |
| NEO-6M TX  | GPIO16(RX2)| → ESP32   |
| NEO-6M RX  | GPIO17(TX2)| ← ESP32   |
| SIM800L TX | GPIO4 (RX1)| → ESP32   |
| SIM800L RX | GPIO2 (TX1)| ← ESP32   |

---

## Authentication Flow

```
Camera (30 frames) → Best frame (Laplacian score)
         ↓
  Face recognition (dlib 128-d embedding, local)
         ↓
   Score ≥ 55%? ──YES──► Relay closes → Car unlocks
         │
        NO
         ↓
  USB mic records 3s clip
         ↓
  SpeechBrain ECAPA-TDNN (local model in models/)
         ↓
   Score ≥ 75%? ──YES──► Relay closes → Car unlocks
         │
        NO
         ↓
  Buzzer ON + "LOC" → ESP32 → GPS → SIM800L → SMS
```

---

## Thresholds (config/settings.py)

| Parameter              | Default | Notes                        |
|------------------------|---------|------------------------------|
| FACE_MATCH_THRESHOLD   | 0.55    | Euclidean dist — lower=stricter |
| VOICE_MATCH_THRESHOLD  | 0.75    | Cosine sim — higher=stricter |
| FACE_MAX_RETRIES       | 3       | Before falling to voice      |
| AUDIO_RECORD_SECONDS   | 3       | Voice clip length            |
| REARM_DELAY            | 10      | Seconds before re-arm        |
