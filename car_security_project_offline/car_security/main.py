"""
main.py — Entry point for Car Security System
Runs on Raspberry Pi 4
"""

import time
import logging
from config.settings import Settings
from core.face_capture import FaceCapture
from core.face_recognition_engine import FaceRecognitionEngine
from core.voice_capture import VoiceCapture
from core.voice_recognition_engine import VoiceRecognitionEngine
from hardware.relay import RelayController
from hardware.buzzer import BuzzerController
from hardware.serial_comm import SerialComm
from utils.logger import setup_logger

logger = setup_logger("main")

def run():
    logger.info("=== Car Security System Starting ===")

    # --- Initialize all modules ---
    settings        = Settings()
    face_capture    = FaceCapture(settings)
    face_engine     = FaceRecognitionEngine(settings)
    voice_capture   = VoiceCapture(settings)
    voice_engine    = VoiceRecognitionEngine(settings)
    relay           = RelayController(settings.RELAY_GPIO_PIN)
    buzzer          = BuzzerController(settings.BUZZER_GPIO_PIN)
    serial_comm     = SerialComm(settings.SERIAL_PORT, settings.SERIAL_BAUD)

    logger.info("All modules initialized. Waiting for person...")

    try:
        while True:
            # ── STAGE 1: Capture best face frame ──────────────────────────
            logger.info("[STAGE 1] Capturing best face frame...")
            best_frame = face_capture.get_best_frame()

            if best_frame is None:
                logger.warning("No face detected in frame buffer. Retrying...")
                time.sleep(1)
                continue

            # ── STAGE 2: Face Recognition ──────────────────────────────────
            logger.info("[STAGE 2] Running face recognition...")
            face_matched, face_score = face_engine.verify(best_frame)
            logger.info(f"  Face score: {face_score:.3f} | Match: {face_matched}")

            if face_matched:
                logger.info("  ✓ Face matched → Unlocking car")
                grant_access(relay, "FACE", logger)
                time.sleep(settings.REARM_DELAY)
                continue

            # ── STAGE 3: Voice Verification ────────────────────────────────
            logger.info("[STAGE 3] Face failed. Prompting for voice...")
            audio_clip = voice_capture.record_clip()

            voice_matched, voice_score = voice_engine.verify(audio_clip)
            logger.info(f"  Voice score: {voice_score:.3f} | Match: {voice_matched}")

            if voice_matched:
                logger.info("  ✓ Voice matched → Unlocking car")
                grant_access(relay, "VOICE", logger)
                time.sleep(settings.REARM_DELAY)
                continue

            # ── STAGE 4: Both failed → Alert ───────────────────────────────
            logger.warning("[STAGE 4] Both checks FAILED → Triggering alert")
            trigger_alert(buzzer, serial_comm, settings, logger)
            time.sleep(settings.REARM_DELAY)

    except KeyboardInterrupt:
        logger.info("System shut down by user.")
    finally:
        relay.cleanup()
        buzzer.cleanup()
        serial_comm.close()


def grant_access(relay: RelayController, method: str, logger):
    relay.unlock()
    logger.info(f"  → Access granted via {method}. Relay opened.")


def trigger_alert(buzzer: BuzzerController, serial_comm: SerialComm,
                  settings: "Settings", logger):
    buzzer.activate(duration=settings.BUZZER_DURATION)
    serial_comm.send_command("LOC")
    logger.info("  → Buzzer activated. LOC command sent to ESP32.")


if __name__ == "__main__":
    run()
