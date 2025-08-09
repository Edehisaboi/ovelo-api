import base64
import binascii
from typing import Dict, Any, List
from pydantic import BaseModel

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError, ParamValidationError

from application.core.logging import get_logger
from application.core.config import settings

logger = get_logger(__name__)


class BoundingBox(BaseModel):
    """Model for bounding box coordinates."""
    Width:  float
    Height: float
    Left:   float
    Top:    float


class CelebrityRecognitionResult(BaseModel):
    """Model for celebrity recognition results."""
    name: str
    confidence: float
    bounding_box: BoundingBox


class RecognitionResponse(BaseModel):
    """Model for the recognition response."""
    celebrities: List[CelebrityRecognitionResult]


class RekognitionClient:
    """Async client for AWS Rekognition service."""

    def __init__(self):
        """Initialize the Rekognition session and config."""
        self._config = Config(retries={"max_attempts": 2})
        self._region = settings.AWS_REGION
        self._access_key = settings.AWS_ACCESS_KEY_ID
        self._secret_key = settings.AWS_SECRET_ACCESS_KEY

        # Prepare aioboto3 session and client placeholder
        self._session = aioboto3.Session()
        self._client = None  # Will be set in __aenter__

    async def __aenter__(self):
        """Enter async context: instantiate the Rekognition client."""
        self._client = await self._session.client(
            "rekognition",
            region_name=self._region,
            config=self._config,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
        ).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context: clean up the client."""
        await self._client.__aexit__(exc_type, exc, tb)

    async def recognize_actors(self, image_base64: str) -> RecognitionResponse:
        """Asynchronously recognize celebrities in an image using Amazon Rekognition.
        Args:
            image_base64: Base-64-encoded image data
        Returns:
            RecognitionResponse containing a list of recognized celebrities"""
        if self._client is None:
            raise RuntimeError("Rekognition client not initialized; use 'async with RekognitionClient()'")

        image_bytes = self._base64_to_bytes(image_base64)

        try:
            response = await self._client.recognize_celebrities(Image={"Bytes": image_bytes})
        except ParamValidationError as e:
            logger.error("Invalid input parameters: %s", str(e))
            raise ValueError("Invalid image parameters for Rekognition call")
        except ClientError as e:
            logger.error("AWS Rekognition API error: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error recognizing celebrities: %s", str(e))
            raise

        return self._format_response(response)

    @staticmethod
    def _base64_to_bytes(frame_b64: str) -> bytes:
        """Convert a Base-64 encoded image file to bytes."""
        # Strip data URL prefix if present
        if isinstance(frame_b64, str) and frame_b64.startswith("data:"):
            frame_b64 = frame_b64.split(",", 1)[1]

        # Fix missing padding (common in streamed chunks)
        missing = (-len(frame_b64)) % 4
        if missing:
            frame_b64 += "=" * missing

        # Decode Base-64 string to bytes
        try:
            frame_bytes = base64.b64decode(frame_b64.strip())
        except binascii.Error:
            logger.error("Invalid Base-64 string provided")
            raise ValueError("Invalid Base-64 image data")

        # Enforce size limit
        if len(frame_bytes) > settings.AWS_MAX_IMAGE_BYTES:
            logger.error("Image size exceeds 5 MB limit: %d bytes", len(frame_bytes))
            raise ValueError("Image size exceeds the 5 MB limit for Rekognition")

        return frame_bytes

    @staticmethod
    def _format_response(response: Dict[str, Any]) -> RecognitionResponse:
        """Format the AWS Rekognition response into a RecognitionResponse object."""
        faces = response.get("CelebrityFaces", [])
        results: List[CelebrityRecognitionResult] = []

        for celeb in faces:
            try:
                name = celeb["Name"]
                confidence = celeb["MatchConfidence"]
                bbox = celeb["Face"]["BoundingBox"]
            except KeyError as e:
                logger.error("Missing expected key in response: %s", str(e))
                continue

            results.append(
                CelebrityRecognitionResult(
                    name=name,
                    confidence=confidence,
                    bounding_box=BoundingBox(**bbox),
                )
            )

        if not results:
            logger.info("No celebrities recognized in the image")

        return RecognitionResponse(celebrities=results)
