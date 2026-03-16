"""
setup/check_offline.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run this on the Raspberry Pi to verify the system is
100% ready to operate offline before disconnecting internet.

Usage:  python setup/check_offline.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}[PASS]{RESET} {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}[WARN]{RESET} {msg}")

def check(label, condition, fix_msg=""):
    if condition:
        ok(label)
        return True
    else:
        fail(label)
        if fix_msg:
            print(f"         {YELLOW}→ {fix_msg}{RESET}")
        return False

def main():
    settings = Settings()
    all_pass = True

    print(f"\n{BOLD}Car Security System — Offline Readiness Check{RESET}")
    print("=" * 52)

    # ── 1. Python packages ─────────────────────────────────────────────────
    print(f"\n{BOLD}Python packages{RESET}")
    pkgs = {
        "cv2":          "opencv-python",
        "face_recognition": "face-recognition",
        "pyaudio":      "pyaudio",
        "torch":        "torch",
        "torchaudio":   "torchaudio",
        "speechbrain":  "speechbrain",
        "serial":       "pyserial",
        "numpy":        "numpy",
    }
    for mod, pkg in pkgs.items():
        try:
            __import__(mod)
            ok(f"{pkg}")
        except ImportError:
            fail(f"{pkg} — run: pip install {pkg} --break-system-packages")
            all_pass = False

    try:
        import RPi.GPIO
        ok("RPi.GPIO")
    except ImportError:
        warn("RPi.GPIO not found — OK if testing on non-RPi machine")

    # ── 2. SpeechBrain model on disk ───────────────────────────────────────
    print(f"\n{BOLD}SpeechBrain model (offline){RESET}")
    model_dir   = settings.SPEECHBRAIN_MODEL_DIR
    model_files = ["hyperparams.yaml", "embedding_model.ckpt"]
    dir_exists  = os.path.isdir(model_dir) and bool(os.listdir(model_dir))
    all_pass &= check(
        f"Model directory exists: {model_dir}",
        dir_exists,
        "Run: python setup/download_models.py  (needs internet once)"
    )
    if dir_exists:
        for f in model_files:
            found = any(f in fname for fname in os.listdir(model_dir))
            all_pass &= check(f"  File present: {f}", found)

    # ── 3. Owner embeddings ────────────────────────────────────────────────
    print(f"\n{BOLD}Owner biometric embeddings{RESET}")
    all_pass &= check(
        f"Face embedding: owner_face.npy",
        os.path.exists(settings.OWNER_FACE_EMBEDDING),
        "Run: python enrollment/enroll_face.py"
    )
    all_pass &= check(
        f"Voice embedding: owner_voice.pt",
        os.path.exists(settings.OWNER_VOICE_EMBEDDING),
        "Run: python enrollment/enroll_voice.py"
    )

    # ── 4. Hardware checks ─────────────────────────────────────────────────
    print(f"\n{BOLD}Hardware / system{RESET}")
    all_pass &= check(
        "Camera device /dev/video0",
        os.path.exists("/dev/video0"),
        "Enable camera: sudo raspi-config → Interface → Camera"
    )
    all_pass &= check(
        "Serial port /dev/ttyS0 (UART for ESP32)",
        os.path.exists("/dev/ttyS0"),
        "Enable UART: sudo raspi-config → Interface → Serial"
    )

    # ── 5. Verify model loads from disk (no network) ───────────────────────
    print(f"\n{BOLD}Offline model load test{RESET}")
    if dir_exists:
        try:
            import socket
            # Temporarily block to simulate no internet
            original_getaddrinfo = socket.getaddrinfo
            def block_dns(*args, **kwargs):
                raise OSError("Network blocked for test")
            socket.getaddrinfo = block_dns
            try:
                from speechbrain.inference.speaker import SpeakerRecognition
                SpeakerRecognition.from_hparams(
                    source   = model_dir,
                    savedir  = model_dir,
                    run_opts = {"device": "cpu"},
                )
                ok("SpeechBrain loads from local disk (no network needed)")
            finally:
                socket.getaddrinfo = original_getaddrinfo
        except Exception as e:
            fail(f"Model load test failed: {e}")
            all_pass = False
    else:
        warn("Skipping model load test — model not yet downloaded")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 52)
    if all_pass:
        print(f"{GREEN}{BOLD}  ALL CHECKS PASSED — System is fully offline ready.{RESET}")
    else:
        print(f"{RED}{BOLD}  SOME CHECKS FAILED — Fix issues above before deploying.{RESET}")
    print()


if __name__ == "__main__":
    main()
