"""
config/settings.py — All configurable parameters in one place
"""

import os

class Settings:
    # ── Paths ──────────────────────────────────────────────────────────────
    BASE_DIR              = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR              = os.path.join(BASE_DIR, "data")
    OWNER_FACE_EMBEDDING  = os.path.join(DATA_DIR, "owner_face.npy")
    OWNER_VOICE_EMBEDDING = os.path.join(DATA_DIR, "owner_voice.pt")
    LOG_FILE              = os.path.join(BASE_DIR, "logs", "system.log")

    # ── Camera ─────────────────────────────────────────────────────────────
    CAMERA_INDEX          = 0          # RPi Cam v2 via /dev/video0
    FRAME_WIDTH           = 640
    FRAME_HEIGHT          = 480
    FRAME_BUFFER_SIZE     = 30         # frames to evaluate for best shot
    MIN_FACE_AREA         = 8000       # px² — ignore tiny/far faces

    # ── Face Recognition ───────────────────────────────────────────────────
    FACE_MATCH_THRESHOLD  = 0.55       # cosine distance (lower = stricter)
    FACE_MAX_RETRIES      = 3

    # ── Audio ──────────────────────────────────────────────────────────────
    AUDIO_SAMPLE_RATE     = 16000      # Hz — required by SpeechBrain
    AUDIO_CHANNELS        = 1
    AUDIO_RECORD_SECONDS  = 3
    AUDIO_CHUNK           = 1024

    # ── Voice Recognition ──────────────────────────────────────────────────
    VOICE_MATCH_THRESHOLD = 0.75       # cosine similarity (higher = stricter)
    # Local path — model must be pre-downloaded with setup/download_models.py
    # NEVER points to HuggingFace at runtime — fully offline
    SPEECHBRAIN_MODEL_DIR = os.path.join(BASE_DIR, "models", "ecapa_tdnn")

    # ── GPIO Pins (BCM numbering) ───────────────────────────────────────────
    RELAY_GPIO_PIN        = 17
    BUZZER_GPIO_PIN       = 27
    LED_GPIO_PIN          = 22

    # ── Serial (RPi → ESP32) ───────────────────────────────────────────────
    SERIAL_PORT           = "/dev/ttyS0"   # UART0 on RPi4
    SERIAL_BAUD           = 9600

    # ── Timing ─────────────────────────────────────────────────────────────
    REARM_DELAY           = 10         # seconds before system re-arms
    BUZZER_DURATION       = 30         # seconds buzzer stays ON
    RELAY_UNLOCK_DURATION = 5          # seconds relay stays open
