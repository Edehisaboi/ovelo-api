from pydantic import BaseModel, Field
from typing import Optional, List

class SubtitleFile(BaseModel):
    file_id:        int
    file_name:      str
    cd_number:      Optional[int] = None
    download_url:   str
    subtitle_text:  str

class SubtitleFileInfo(BaseModel):
    subtitle_id:        int
    language:           str
    download_count:     int
    new_download_count: int
    hd:                 bool
    fps:                Optional[float] = None
    from_trusted:       bool
    url:                str
    files:              List[SubtitleFile]

class SubtitleSearchResult(BaseModel):
    id:         int
    type:       str  # 'subtitle'
    attributes: SubtitleFileInfo

class SubtitleSearchResults(BaseModel):
    results: List[SubtitleSearchResult] = Field(..., alias='data')
