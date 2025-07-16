from typing import Dict, Any, List
from pydantic import BaseModel

import boto3
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
    name:       str
    confidence: float
    bounding_box: BoundingBox


class RecognitionResponse(BaseModel):
    """Model for the recognition response."""
    celebrities: List[CelebrityRecognitionResult]


class RekognitionClient:
    """Client for AWS Rekognition service."""

    def __init__(self):
        """Initialize the Rekognition client with retry configuration."""
        config = Config(
            retries=dict(
                max_attempts=2,
            )
        )
        self._client = boto3.client(
            'rekognition',
            config=config,
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    def recognize_actors(self, image_bytes: bytes) -> RecognitionResponse:
        """
        Recognize celebrities in an image using Amazon Rekognition.

        Args:
            image_bytes: The image bytes to analyze

        Returns:
            RecognitionResponse containing a list of recognized celebrities

        Raises:
            ValueError: If the input image bytes are invalid
            Exception: If the AWS Rekognition API call fails
        """
        if not image_bytes or not isinstance(image_bytes, bytes):
            logger.error("Invalid or empty image bytes provided")
            raise ValueError("Image bytes must be non-empty and of type bytes")

        try:
            response = self._client.recognize_celebrities(
                Image={'Bytes': image_bytes}
            )
            return self._format_response(response)
        except ParamValidationError as e:
            logger.error(f"Invalid input parameters: {str(e)}")
            raise ValueError("Invalid image data provided")
        except ClientError as e:
            logger.error(f"AWS API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error recognizing celebrities: {str(e)}")
            raise

    @staticmethod
    def _format_response(response: Dict[str, Any]) -> RecognitionResponse:
        """Format the AWS Rekognition response into a RecognitionResponse object."""
        if 'CelebrityFaces' not in response:
            logger.warning("No CelebrityFaces found in response")
            return RecognitionResponse(celebrities=[])

        results = []
        for celebrity in response['CelebrityFaces']:
            if not all(key in celebrity for key in ['Name', 'MatchConfidence', 'Face']):
                logger.error(f"Invalid celebrity data: {celebrity}")
                continue
            if 'BoundingBox' not in celebrity['Face']:
                logger.error(f"Missing BoundingBox in celebrity data: {celebrity}")
                continue
            results.append(CelebrityRecognitionResult(
                name=celebrity['Name'],
                confidence=celebrity['MatchConfidence'],
                bounding_box=BoundingBox(**celebrity['Face']['BoundingBox'])
            ))
        return RecognitionResponse(celebrities=results) 