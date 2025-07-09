from .face_detector import FaceDetector

# Create singleton instances
face_detector = FaceDetector()

__all__ = [
    "FaceDetector",
    "face_detector"
] 