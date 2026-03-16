"""
setup/download_models.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run this ONCE on any machine that has internet access.
It downloads the SpeechBrain ECAPA-TDNN speaker model and
saves it into  models/ecapa_tdnn/  inside the project folder.

After running, copy the entire  car_security/  folder to the
Raspberry Pi — it will work fully offline from that point.

Usage (on internet-connected machine):
    pip install speechbrain torch torchaudio
    python setup/download_models.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings

def download_models():
    settings   = Settings()
    model_dir  = settings.SPEECHBRAIN_MODEL_DIR

    print("=" * 60)
    print("  SpeechBrain ECAPA-TDNN — Offline Model Downloader")
    print("=" * 60)

    if os.path.isdir(model_dir) and os.listdir(model_dir):
        print(f"\n  Model already exists at:\n  {model_dir}")
        ans = input("\n  Re-download? (y/N): ").strip().lower()
        if ans != "y":
            print("  Skipping. Model is ready.")
            return

    os.makedirs(model_dir, exist_ok=True)
    print(f"\n  Downloading to: {model_dir}")
    print("  (This is ~85 MB — may take a few minutes)\n")

    try:
        from speechbrain.inference.speaker import SpeakerRecognition

        # Download with source=HuggingFace, savedir=local folder
        # After this call the folder is self-contained — no internet needed
        model = SpeakerRecognition.from_hparams(
            source   = "speechbrain/spkrec-ecapa-voxceleb",
            savedir  = model_dir,
            run_opts = {"device": "cpu"},
        )

        # Verify the key files exist
        required = ["hyperparams.yaml", "embedding_model.ckpt",
                    "mean_var_norm_emb.ckpt", "classifier.ckpt"]
        missing = [f for f in required if not any(
            f in fname for fname in os.listdir(model_dir)
        )]

        if missing:
            print(f"\n  WARNING: some files may be missing: {missing}")
        else:
            print("\n  All model files verified.")

        print(f"\n  Model saved to: {model_dir}")
        print("\n  You can now copy the entire project to the RPi.")
        print("  The system will load the model from disk — no internet needed.")

    except ImportError:
        print("\n  ERROR: speechbrain not installed.")
        print("  Run:  pip install speechbrain torch torchaudio")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Download failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Done. Model is ready for offline use.")
    print("=" * 60)

if __name__ == "__main__":
    download_models()
