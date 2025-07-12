from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date


class SearchResult(BaseModel):
    tmdb_id:        int = Field(alias="id")
    title:          Optional[str] = None  # For movies
    name:           Optional[str] = None   # For TV shows
    overview:       str
    poster_path:    Optional[str] = None
    backdrop_path:  Optional[str] = None
    media_type:     Optional[str] = None  # it's only provided for multi-search results
    release_date:   Optional[date | str] = None  # For movies
    first_air_date: Optional[date | str] = None  # For TV shows
    vote_average:   float
    vote_count:     int

class SearchResults(BaseModel):
    page:           int
    results:        List[SearchResult]
    total_pages:    int
    total_results:  int

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

class CrewMember(BaseModel):
    name:           str
    job:            str
    department:     str

class MovieCredits(BaseModel):
    cast:   List[CastMember]
    crew:   List[CrewMember]

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
    episodes:       Optional[List['Episode']] = None


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
    tmdb_id:            int = Field(alias="id")
    adult:              bool
    title:              str
    original_title:     str
    homepage:           str
    overview:           str
    poster_path:        Optional[str] = None
    backdrop_path:      Optional[str] = None
    release_date:       Optional[datetime] = None
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
    watch_providers:    WatchProviders = Field(alias="watch/providers")
    transcript_chunks:  Optional[List[TranscriptChunk]] = None
    embedding_model:    Optional[str] = None
    vote_average:       float
    vote_count:         int

class TVDetails(BaseModel):
    tmdb_id:            int = Field(alias="id")
    adult:              bool
    name:               str
    original_name:      str
    homepage:           Optional[str] = None
    overview:           str
    poster_path:        Optional[str] = None
    backdrop_path:      Optional[str] = None
    first_air_date:     Optional[date] = None
    last_air_date:      Optional[date] = None
    number_of_seasons:  int
    number_of_episodes: int
    genres:             List[Genre]
    seasons:            List[Season]
    status:             str
    tagline:            Optional[str] = None
    credits:            MovieCredits
    images:             MovieImages
    videos:             MovieVideos
    watch_providers:    WatchProviders = Field(alias="watch/providers")
    embedding_model:    Optional[str] = None
    external_ids:       ExternalID
    origin_country:     List[str]
    original_language:  str
    spoken_languages:   List[SpokenLanguage]
    vote_average:       float
    vote_count:         int