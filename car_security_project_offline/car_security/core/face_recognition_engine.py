"""
core/face_recognition_engine.py — Stage 2
Loads the pre-enrolled owner face embedding and
compares it against the live face crop using cosine distance.
"""

import numpy as np
import face_recognition
import logging
import os

logger = logging.getLogger("face_recognition_engine")


class FaceRecognitionEngine:
    def __init__(self, settings):
        self.settings  = settings
        self.threshold = settings.FACE_MATCH_THRESHOLD
        self.owner_embedding = self._load_embedding()

    # ── Public API ──────────────────────────────────────────────────────────

    def verify(self, face_rgb: np.ndarray) -> tuple[bool, float]:
        """
        Given a cropped face RGB array, compute its 128-d embedding
        and compare against the stored owner embedding.

        Returns:
            (matched: bool, distance: float)
            distance = 0.0 means identical, > threshold means no match
        """
        encodings = face_recognition.face_encodings(face_rgb)

        if not encodings:
            logger.warning("No encodings extracted from face crop.")
            return False, 1.0

        live_encoding = encodings[0]

        # face_recognition uses Euclidean distance internally
        # 0.6 is the library's recommended threshold
        distance = float(face_recognition.face_distance(
            [self.owner_embedding], live_encoding
        )[0])

        matched = distance <= self.threshold
        logger.info("Face distance: %.4f | Threshold: %.2f | Match: %s",
                    distance, self.threshold, matched)
        return matched, distance

    # ── Private helpers ─────────────────────────────────────────────────────

    def _load_embedding(self) -> np.ndarray:
        path = self.settings.OWNER_FACE_EMBEDDING
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Owner face embedding not found at {path}. "
                "Run enrollment/enroll_face.py first."
            )
        embedding = np.load(path)
        logger.info("Owner face embedding loaded from %s", path)
        return embedding
