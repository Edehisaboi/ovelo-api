from typing import Optional, Literal, Dict, Any
from typing_extensions import TypedDict

from langchain_core.documents import Document

from application.core.logging import get_logger

logger = get_logger(__name__)


class Error(TypedDict):
    type:    Literal["systemError"]
    message: str
    node:    str

class MediaResult(TypedDict):
    id:           Optional[str]
    title:        Optional[str]
    posterUrl:    Optional[str]
    year:         Optional[str]
    director:     Optional[str]
    genre:        Optional[str]
    description:  Optional[str]
    trailerUrl:   Optional[str]
    tmdbRating:   Optional[float]
    imdbRating:   Optional[float]
    duration:     Optional[int]
    identifiedAt: str
    source:       Optional[str]

class StreamResponse(TypedDict):
    success:        bool
    sessionId:      str
    result:         Optional[MediaResult]
    confidence:     Optional[float]
    processingTime: Optional[float]
    alternatives:   Optional[list[MediaResult]]
    error:          Optional[str]

class MediaResultPayload(TypedDict):
    type: str
    data: StreamResponse

class State(TypedDict):
    transcript:    Optional[str]
    actors:        Optional[list[str]]
    error:         Optional[Error]

    start_time:    Optional[float]

    documents:     Optional[list[Document]]
    candidates:    Optional[list[tuple[Document, float]]]

    actor_matches: Optional[Dict[str, Dict[str, Any]]]

    match:         Optional[str]

    metadata:      Optional[MediaResultPayload]

    end:           bool

