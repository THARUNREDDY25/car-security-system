"""
enrollment/enroll_face.py
Run ONCE before deployment to capture and save the owner's face embedding.
Usage:  python enrollment/enroll_face.py
"""

import cv2
import numpy as np
import face_recognition
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings


def enroll_face():
    settings = Settings()
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    cap = cv2.VideoCapture(settings.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  settings.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)

    print("=== Face Enrollment ===")
    print("Look directly at the camera. Press SPACE to capture. Press Q to quit.")

    embeddings = []

    while len(embeddings) < 5:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model="hog")

        # Draw box around detected face for visual feedback
        display = frame.copy()
        for (top, right, bottom, left) in locations:
            cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 0), 2)

        cv2.putText(display,
                    f"Samples: {len(embeddings)}/5 — SPACE to capture",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.imshow("Enroll Face", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' ') and locations:
            enc = face_recognition.face_encodings(rgb, locations)
            if enc:
                embeddings.append(enc[0])
                print(f"  Sample {len(embeddings)} captured.")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(embeddings) == 0:
        print("No samples captured. Aborting.")
        return

    # Average all samples for a robust embedding
    mean_embedding = np.mean(embeddings, axis=0)
    np.save(settings.OWNER_FACE_EMBEDDING, mean_embedding)
    print(f"\n✓ Face embedding saved to {settings.OWNER_FACE_EMBEDDING}")
    print(f"  Averaged from {len(embeddings)} samples.")


if __name__ == "__main__":
    enroll_face()
