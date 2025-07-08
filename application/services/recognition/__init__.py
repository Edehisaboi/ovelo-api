from .face_detector import FaceDetector
from external.clients.rekognition import RekognitionClient

# Create singleton instances
face_detector = FaceDetector()
rekognition_client = RekognitionClient()

__all__ = [
    "FaceDetector",
    "RekognitionClient",
    "face_detector",
    "rekognition_client"
] 