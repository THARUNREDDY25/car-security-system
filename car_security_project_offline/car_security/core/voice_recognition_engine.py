"""
core/voice_recognition_engine.py — Stage 3 (Part B)
Uses SpeechBrain ECAPA-TDNN to extract a speaker embedding
from the recorded clip and compare it against the enrolled owner voice.

FULLY OFFLINE — loads model from local disk only.
Run setup/download_models.py once (with internet) before deploying.
"""

import torch
import torchaudio
import logging
import os

logger = logging.getLogger("voice_recognition_engine")


class VoiceRecognitionEngine:
    def __init__(self, settings):
        self.settings        = settings
        self.threshold       = settings.VOICE_MATCH_THRESHOLD
        self.model           = self._load_model_offline()
        self.owner_embedding = self._load_owner_embedding()

    # ── Public API ──────────────────────────────────────────────────────────

    def verify(self, wav_path: str) -> tuple[bool, float]:
        """
        Encode the wav clip and compare cosine similarity
        against the enrolled owner voice embedding.
        Returns (matched: bool, similarity: float)
        """
        live_embedding = self._encode(wav_path)
        similarity     = self._cosine_similarity(live_embedding,
                                                  self.owner_embedding)
        matched = similarity >= self.threshold

        logger.info("Voice similarity: %.4f | Threshold: %.2f | Match: %s",
                    similarity, self.threshold, matched)

        if os.path.exists(wav_path):
            os.remove(wav_path)

        return matched, float(similarity)

    # ── Private helpers ─────────────────────────────────────────────────────

    def _load_model_offline(self):
        """
        Load ECAPA-TDNN strictly from local model directory.
        Raises clear error if model not pre-downloaded.
        No network calls are made at any point.
        """
        from speechbrain.inference.speaker import SpeakerRecognition

        model_dir = self.settings.SPEECHBRAIN_MODEL_DIR

        if not os.path.isdir(model_dir) or not os.listdir(model_dir):
            raise RuntimeError(
                f"\n\nSpeechBrain model not found at: {model_dir}\n"
                "Run this once on a machine WITH internet:\n"
                "    python setup/download_models.py\n"
                "Then copy the full project folder to the RPi.\n"
            )

        logger.info("Loading SpeechBrain ECAPA-TDNN from local disk: %s",
                    model_dir)

        # source = local path, download_only=False prevents any HuggingFace call
        model = SpeakerRecognition.from_hparams(
            source      = model_dir,
            savedir     = model_dir,
            run_opts    = {"device": "cpu"},
        )

        logger.info("SpeechBrain model loaded (offline).")
        return model

    def _encode(self, wav_path: str) -> torch.Tensor:
        signal, fs = torchaudio.load(wav_path)
        if fs != self.settings.AUDIO_SAMPLE_RATE:
            resampler = torchaudio.transforms.Resample(
                orig_freq = fs,
                new_freq  = self.settings.AUDIO_SAMPLE_RATE,
            )
            signal = resampler(signal)
        embedding = self.model.encode_batch(signal)
        return embedding.squeeze()

    def _load_owner_embedding(self) -> torch.Tensor:
        path = self.settings.OWNER_VOICE_EMBEDDING
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Owner voice embedding not found at: {path}\n"
                "Run enrollment/enroll_voice.py first."
            )
        embedding = torch.load(path, map_location="cpu")
        logger.info("Owner voice embedding loaded from %s", path)
        return embedding

    @staticmethod
    def _cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
        a = a / (a.norm() + 1e-8)
        b = b / (b.norm() + 1e-8)
        return float(torch.dot(a, b))
