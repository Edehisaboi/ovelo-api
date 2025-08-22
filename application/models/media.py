from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from bson import ObjectId


class SearchResult(BaseModel):
    tmdb_id:            int = Field(alias="id")
    title:              Optional[str]         = None  # For movies
    name:               Optional[str]         = None  # For TV shows
    overview:           Optional[str]         = None
    poster_path:        Optional[str]         = None
    backdrop_path:      Optional[str]         = None
    media_type:         Optional[str]         = None  # Only provided for multi-search results
    release_date:       Optional[str | date]  = None  # For movies
    first_air_date:     Optional[str | date]  = None  # For TV shows
    vote_average:       Optional[float]       = None
    vote_count:         Optional[int]         = None
    original_language:  Optional[str]         = None
    genres:             Optional[str]         = None
    trailer_link:       Optional[str]         = None

class SearchResults(BaseModel):
    page:           int
    results:        List[SearchResult | None]
    total_pages:    int
    total_results:  int

    @field_validator("results", mode="before")
    def _drop_people(cls, v: Any):
        if isinstance(v, list):
            return [
                it for it in v
                if not (isinstance(it, dict) and it.get("media_type") == "person")
            ]
        return v

class TranscriptChunk(BaseModel):
    index:      int
    text:       str
    embedding:  Optional[List[float]] = None

class Genre(BaseModel):
    name:   str

class SpokenLanguage(BaseModel):
    iso_639_1:      str
    name:           str
    english_name:   str

class CastMember(BaseModel):
    name:           str
    character:      str
    known_for_department: str

class MovieCredits(BaseModel):
    cast:   List[CastMember]

class Image(BaseModel):
    aspect_ratio:   float
    file_path:      str
    height:         int
    width:          int
    iso_639_1:      Optional[str] = None

class MovieImages(BaseModel):
    backdrops:  List[Image]
    posters:    List[Image]
    logos:      List[Image]

class Video(BaseModel):
    key:            str
    name:           str
    site:           str
    size:           int
    type:           str
    official:       bool
    iso_639_1:      Optional[str] = None
    iso_3166_1:     Optional[str] = None

class MovieVideos(BaseModel):
    results:    List[Video]

class Episode(BaseModel):
    name:           str
    overview:       str
    season_number:  int
    episode_number: int
    episode_type:   str
    runtime:        Optional[int] = None
    transcript_chunks:  Optional[List[TranscriptChunk]] = None

class Season(BaseModel):
    name:           str
    overview:       str
    season_number:  int
    episode_count:  Optional[int] = None
    episodes:       List['Episode'] = Field(default_factory=list)

    @model_validator(mode='after')
    def set_episode_count(self):
        if self.episode_count is None:
            self.episode_count = len(self.episodes)
        return self


class WatchProvider(BaseModel):
    display_priority:   int
    logo_path:          str
    provider_name:      str

class CountryWatchProviders(BaseModel):
    link:       str
    flatrate:   Optional[List[WatchProvider]] = None

class WatchProviders(BaseModel):
    results:    Dict[str, CountryWatchProviders]

class ExternalID(BaseModel):
    imdb_id:        Optional[str] = None
    facebook_id:    Optional[str] = None
    instagram_id:   Optional[str] = None
    twitter_id:     Optional[str] = None

class MovieDetails(BaseModel):
    db_id:              Optional[str] = Field(default=None, alias="_id")
    tmdb_id:            int = Field(alias="id")
    adult:              bool
    title:              str
    original_title:     str
    homepage:           str
    overview:           str
    poster_path:        Optional[str] = None
    backdrop_path:      Optional[str] = None
    release_date:       Optional[str | datetime] = None
    runtime:            Optional[int] = None
    genres:             List[Genre]
    original_language:  str
    spoken_languages:   List[SpokenLanguage]
    origin_country:     List[str]
    external_ids:       ExternalID
    status:             str
    tagline:            str
    credits:            MovieCredits
    images:             MovieImages
    videos:             MovieVideos
    watch_providers:    Optional[WatchProviders] = Field(default=None, alias="watch/providers")
    transcript_chunks:  Optional[List[TranscriptChunk]] = None
    embedding_model:    Optional[str] = None
    vote_average:       float
    vote_count:         int
    media_type:         str = "movie"

    @field_validator('db_id', mode='before')
    def convert_objectid_to_str(v):
        if v and isinstance(v, ObjectId):
            return str(v)
        return v

    model_config = ConfigDict(
        populate_by_name=True
    )

class TVDetails(BaseModel):
    db_id:               Optional[str] = Field(default=None, alias="_id")
    tmdb_id:             int = Field(alias="id")
    adult:               bool
    name:                str
    original_name:       str
    homepage:            Optional[str] = None
    overview:            str
    poster_path:         Optional[str] = None
    backdrop_path:       Optional[str] = None
    first_air_date:      Optional[str | date] = None
    last_air_date:       Optional[str | date] = None
    number_of_seasons:   int
    number_of_episodes:  int
    genres:              List[Genre]
    seasons:             Optional[List[Season]] = None
    status:              str
    tagline:             Optional[str] = None
    credits:             MovieCredits
    images:              MovieImages
    videos:              MovieVideos
    watch_providers:     Optional[WatchProviders] = Field(default=None, alias="watch/providers")
    embedding_model:     Optional[str] = None
    external_ids:        ExternalID
    origin_country:      List[str]
    original_language:   str
    spoken_languages:    List[SpokenLanguage]
    vote_average:        float
    vote_count:          int
    media_type:          str = "tv"

    @field_validator('db_id', mode='before')
    def convert_objectid_to_str(v):
        if v and isinstance(v, ObjectId):
            return str(v)
        return v

    model_config = ConfigDict(
        populate_by_name=True
    )