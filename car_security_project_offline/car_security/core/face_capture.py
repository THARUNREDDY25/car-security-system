"""
core/face_capture.py — Stage 1
Captures N frames from RPi Camera v2 and returns
the single best (largest + sharpest) face crop.
"""

import cv2
import numpy as np
import face_recognition
import logging

logger = logging.getLogger("face_capture")


class FaceCapture:
    def __init__(self, settings):
        self.settings = settings
        self.cap = cv2.VideoCapture(settings.CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  settings.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera. Check connection.")
        logger.info("Camera initialized.")

    # ── Public API ──────────────────────────────────────────────────────────

    def get_best_frame(self) -> np.ndarray | None:
        """
        Grab FRAME_BUFFER_SIZE frames, score each one, return
        the RGB numpy array of the best detected face.
        Returns None if no face found in any frame.
        """
        best_frame  = None
        best_score  = -1

        for _ in range(self.settings.FRAME_BUFFER_SIZE):
            ret, bgr_frame = self.cap.read()
            if not ret:
                continue

            rgb_frame  = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            score, face_rgb = self._score_frame(rgb_frame)

            if score > best_score:
                best_score = score
                best_frame = face_rgb

        if best_frame is None:
            logger.warning("No face found across %d frames.",
                           self.settings.FRAME_BUFFER_SIZE)
        else:
            logger.info("Best frame score: %.2f", best_score)

        return best_frame

    # ── Private helpers ─────────────────────────────────────────────────────

    def _score_frame(self, rgb_frame: np.ndarray):
        """
        Detect faces in frame. Score by:
          - Face bounding box area (bigger = closer)
          - Laplacian variance of face ROI (higher = sharper)
        Returns (score, cropped_face_rgb) or (-1, None) if no face.
        """
        locations = face_recognition.face_locations(rgb_frame, model="hog")
        if not locations:
            return -1, None

        # Pick the largest face in the frame
        best_loc   = max(locations, key=lambda loc: self._bbox_area(loc))
        top, right, bottom, left = best_loc
        area       = self._bbox_area(best_loc)

        if area < self.settings.MIN_FACE_AREA:
            return -1, None  # Face too small / too far

        face_roi   = rgb_frame[top:bottom, left:right]
        sharpness  = self._laplacian_variance(face_roi)
        score      = area * 0.5 + sharpness * 0.5  # weighted combined score

        return score, face_roi

    @staticmethod
    def _bbox_area(loc) -> int:
        top, right, bottom, left = loc
        return (bottom - top) * (right - left)

    @staticmethod
    def _laplacian_variance(roi: np.ndarray) -> float:
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def release(self):
        self.cap.release()
