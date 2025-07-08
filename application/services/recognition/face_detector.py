from typing import List

import cv2
import numpy as np
#import face_recognition


class FaceDetector:
    def __init__(self, min_size=30, tolerance=0.6, track_seen_faces=False):
        """
        Initialize the face detector.

        Args:
            min_size: Minimum face size (in pixels) to detect
            tolerance: Similarity threshold for known face matching
            track_seen_faces: If True, skip processing previously seen faces
        """
        self.track_seen_faces = track_seen_faces
        self.tolerance = tolerance
        self.min_size = min_size

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        self.known_encodings: List[np.ndarray] = []

    def detect_new_faces(self, frame: np.ndarray) -> List[np.ndarray]:
        """
        Detect and crop faces from the frame.
        Optionally, skip duplicates if track_seen_faces is True.

        Args:
            frame: Input video frame

        Returns:
            List of cropped face images (possibly empty)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(self.min_size, self.min_size)
        )

        if len(faces) == 0:
            return []  # No faces found → skip

        new_faces = []

        for (x, y, w, h) in faces:
            face_img = frame[y:y + h, x:x + w]

            try:
                face_resized = cv2.resize(face_img, (224, 224))

                if not self.track_seen_faces:
                    new_faces.append(face_resized)

                # TODO: Uncomment when face tracking is implemented
                #     continue
                #
                # encodings = face_recognition.face_encodings(face_resized)
                # if not encodings:
                #     continue
                #
                # encoding = encodings[0]
                #
                # if not self._is_known_face(encoding):
                #     self.known_encodings.append(encoding)
                #     new_faces.append(face_resized)

            except Exception():
                continue  # Skip faulty frame or encoding issues

        return new_faces

    # def _is_known_face(self, encoding: np.ndarray) -> bool:
    #     """
    #     Compare encoding with known encodings.
    #
    #     Returns:
    #         True if face has already been seen.
    #     """
    #     if not self.known_encodings:
    #         return False
    #     distances = face_recognition.face_distance(self.known_encodings, encoding)
    #     return np.any(distances < self.tolerance) 