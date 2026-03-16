"""
enrollment/enroll_voice.py
Run ONCE before deployment to capture and save the owner's voice embedding.
FULLY OFFLINE — loads model from models/ecapa_tdnn/ on local disk.
Run setup/download_models.py first (needs internet, one time only).

Usage:  python enrollment/enroll_voice.py
"""

import pyaudio
import wave
import torch
import torchaudio
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings


def record_sample(settings: Settings, sample_num: int) -> str:
    pa      = pyaudio.PyAudio()
    chunk   = settings.AUDIO_CHUNK
    rate    = settings.AUDIO_SAMPLE_RATE
    seconds = settings.AUDIO_RECORD_SECONDS

    input(f"  Press ENTER to record sample {sample_num}/5 "
          f"(say a unique phrase for {seconds}s)...")

    stream = pa.open(
        format            = pyaudio.paInt16,
        channels          = settings.AUDIO_CHANNELS,
        rate              = rate,
        input             = True,
        frames_per_buffer = chunk,
    )
    print("  Recording... speak now!")
    frames = [stream.read(chunk) for _ in range(int(rate / chunk * seconds))]
    stream.stop_stream()
    stream.close()
    pa.terminate()
    print("  Done.")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(settings.AUDIO_CHANNELS)
        wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))
    return tmp.name


def enroll_voice():
    settings  = Settings()
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    model_dir = settings.SPEECHBRAIN_MODEL_DIR

    print("=== Voice Enrollment (offline) ===")

    if not os.path.isdir(model_dir) or not os.listdir(model_dir):
        print(f"\nERROR: SpeechBrain model not found at:\n  {model_dir}")
        print("\nRun this once on a machine WITH internet, then copy project to RPi:")
        print("    python setup/download_models.py")
        sys.exit(1)

    print(f"  Loading ECAPA-TDNN from: {model_dir}")
    from speechbrain.inference.speaker import SpeakerRecognition
    model = SpeakerRecognition.from_hparams(
        source   = model_dir,
        savedir  = model_dir,
        run_opts = {"device": "cpu"},
    )
    print("  Model loaded (offline).\n")
    print("You will record 5 voice samples. Speak clearly each time.\n")

    embeddings = []
    for i in range(1, 6):
        wav_path = record_sample(settings, i)
        signal, fs = torchaudio.load(wav_path)
        if fs != settings.AUDIO_SAMPLE_RATE:
            resampler = torchaudio.transforms.Resample(
                orig_freq=fs, new_freq=settings.AUDIO_SAMPLE_RATE
            )
            signal = resampler(signal)
        emb = model.encode_batch(signal).squeeze()
        embeddings.append(emb)
        os.remove(wav_path)
        print(f"  Sample {i} encoded.")

    mean_emb = torch.stack(embeddings).mean(dim=0)
    torch.save(mean_emb, settings.OWNER_VOICE_EMBEDDING)
    print(f"\n  Voice embedding saved to {settings.OWNER_VOICE_EMBEDDING}")
    print(f"  Averaged from 5 samples.")


if __name__ == "__main__":
    enroll_voice()
