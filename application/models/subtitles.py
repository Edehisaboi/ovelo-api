from pydantic import BaseModel, Field
from typing import Optional, List


class FeatureDetails(BaseModel):
    feature_id:         int
    feature_type:       str
    year:               Optional[int] = None
    title:              Optional[str] = None
    movie_name:         Optional[str] = None
    imdb_id:            Optional[int] = None
    tmdb_id:            Optional[int] = None
    # The following are only present for episodes/TV
    season_number:      Optional[int] = None
    episode_number:     Optional[int] = None
    parent_title:       Optional[str] = None
    parent_tmdb_id:     Optional[int] = None
    parent_imdb_id:     Optional[int] = None

class SubtitleFile(BaseModel):
    file_id:        int
    file_name:      str
    cd_number:      Optional[int] = None
    download_url:   Optional[str] = None
    subtitle_text:  Optional[str] = None

class SubtitleFileInfo(BaseModel):
    subtitle_id:        int
    language:           str
    download_count:     int
    new_download_count: int
    hd:                 bool
    fps:                Optional[float] = None
    from_trusted:       bool
    url:                str
    feature_details:    Optional[FeatureDetails] = None
    files:              List[SubtitleFile]

class SubtitleSearchResult(BaseModel):
    id:         int
    type:       str  # 'subtitle'
    attributes: SubtitleFileInfo

class SubtitleSearchResults(BaseModel):
    results: List[SubtitleSearchResult] = Field(..., alias='data') 