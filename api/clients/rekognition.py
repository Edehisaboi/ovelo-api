from typing import Dict, Any, List
from pydantic import BaseModel

import boto3
from botocore.config import Config

from config import get_logger

logger = get_logger(__name__)


class CelebrityRecognitionResult(BaseModel):
    """Model for celebrity recognition results."""
    name: str
    confidence: float
    bounding_box: dict

class RecognitionResponse(BaseModel):
    """Model for the recognition response."""
    celebrities: List[CelebrityRecognitionResult]


class RekognitionClient:
    """Client for AWS Rekognition service."""
    
    def __init__(self):
        """Initialize the Rekognition client with retry configuration."""
        config = Config(
            retries=dict(
                max_attempts=3
            )
        )
        self._client = boto3.client(
            'rekognition',
            config=config,
            region_name='us-east-2',
        )
    
    def recognize_actor(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Recognize celebrities in an image using Amazon Rekognition.
        
        Args:
            image_bytes: The image bytes to analyze
            
        Returns:
            Dict containing celebrity recognition results with the following structure:
            {
                'CelebrityFaces': [
                    {
                        'Name': str,
                        'MatchConfidence': float,
                        'Face': {
                            'BoundingBox': {
                                'Width': float,
                                'Height': float,
                                'Left': float,
                                'Top': float
                            }
                        }
                    }
                ]
            }
        """
        try:
            response = self._client.recognize_celebrities(
                Image={'Bytes': image_bytes}
            )
            return self._format_response(response)

        except Exception as e:
            logger.error(f"Error recognizing celebrities: {str(e)}")
            raise


    @staticmethod
    def _format_response(response: Dict[str, Any]) -> RecognitionResponse:
        # Extract relevant information
        if 'CelebrityFaces' in response:
            results = []
            for celebrity in response['CelebrityFaces']:
                results.append(CelebrityRecognitionResult(
                    name=celebrity['Name'],
                    confidence=celebrity['MatchConfidence'],
                    bounding_box=celebrity['Face']['BoundingBox']
                ))