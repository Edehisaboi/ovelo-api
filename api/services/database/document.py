from typing import List, Dict, Union, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from api.services.tmdb.models import Season as TMDVSeason, Episode as TMDVEpisode


class VectorEmbedding(BaseModel):
    vector:     List[float]
    timestamp:  datetime


class TranscriptChunk(BaseModel):
    index:      int
    text:       str
    embedding:  VectorEmbedding


class DocumentEpisode(TMDVEpisode):
    transcript_chunks: List[TranscriptChunk]


# Update Season's episodes field to use DocumentEpisode
class DocumentSeason(TMDVSeason):
    episodes: List[DocumentEpisode]
DocumentSeason.model_rebuild()


class MediaDocument:
    """
    MediaDocument class to construct either a movie or TV show document
    ready for insertion into MongoDB.
    """

    def __init__(self):
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

    def movie_document(
        self,
        tmdb_id:            int,
        title:              str,
        original_title:     str,
        original_language:  str,
        overview:           str,
        poster_path:        Optional[str],
        backdrop_path:      Optional[str],
        release_date:       Optional[datetime],
        runtime:            Optional[int],
        genres:             List[Dict[str, Union[int, str]]],
        spoken_languages:   List[Dict[str, str]],
        origin_country:     List[str],
        imdb_id:            Optional[str],
        status:             str,
        cast:               List[Dict[str, Union[int, str]]],
        crew:               List[Dict[str, Union[int, str]]],
        images:             Dict[str, List[Dict[str, Union[float, int, str]]]],
        videos:             List[Dict[str, Union[str, bool]]],
        watch_providers:    Dict[str, Dict[str, List[Dict[str, Union[int, str]]]]],
        transcript_chunks:  List[TranscriptChunk],
        embedding_model:    str
    ) -> Dict:
        """
        Construct a movie document for MongoDB insertion.
        
        Args:
            tmdb_id:            TMDB movie ID
            title:              Movie title
            original_title:     Original movie title
            overview:           Movie overview
            poster_path:        Path to poster image
            backdrop_path:      Path to backdrop image
            release_date:       Movie release date
            runtime:            Movie runtime in minutes
            genres:             List of genres
            spoken_languages:   List of spoken languages
            origin_country:     List of origin countries
            imdb_id:            IMDB ID
            status:             Movie status
            cast:               List of cast members
            crew:               List of crew members
            images:             Movie images (posters, backdrops)
            videos:             List of videos (trailers, etc.)
            watch_providers:    Watch provider information
            transcript_chunks:  List of transcript chunks with embeddings
            embedding_model:    Name of the embedding model used
            
        Returns:
            Dict: Movie document ready for MongoDB insertion
        """
        return {
            "tmdb_id":            tmdb_id,
            "title":              title,
            "original_title":     original_title,
            "overview":           overview,
            "poster_path":        poster_path,
            "backdrop_path":      backdrop_path,
            "release_date":       release_date,
            "runtime":            runtime,
            "genres":             genres,
            "original_language":  original_language,
            "spoken_languages":   spoken_languages,
            "origin_country":     origin_country,
            "imdb_id":            imdb_id,
            "status":             status,
            "cast":               cast,
            "crew":               crew,
            "images":             images,
            "videos":             videos,
            "watch_providers":    watch_providers,
            "transcript_chunks":  [
                {
                    "index":      chunk.index,
                    "text":       chunk.text,
                    "embedding":  {
                        "vector":     chunk.embedding.vector,
                        "timestamp":  chunk.embedding.timestamp
                    }
                }
                for chunk in transcript_chunks
            ],
            "embedding_model":    embedding_model,
            "created_at":         self.created_at,
            "updated_at":         self.updated_at
        }

    def tv_show_document(
        self,
        tmdb_id:            int,
        name:               str,
        original_name:      str,
        overview:           str,
        poster_path:        Optional[str],
        backdrop_path:      Optional[str],
        first_air_date:     Optional[datetime],
        last_air_date:      Optional[datetime],
        number_of_seasons:  int,
        number_of_episodes: int,
        episode_run_time:   List[int],
        genres:             List[Dict[str, Union[int, str]]],
        spoken_languages:   List[Dict[str, str]],
        origin_country:     List[str],
        imdb_id:            Optional[str],
        status:             str,
        cast:               List[Dict[str, Union[int, str]]],
        crew:               List[Dict[str, Union[int, str]]],
        images:             Dict[str, List[Dict[str, Union[float, int, str]]]],
        videos:             List[Dict[str, Union[str, bool]]],
        watch_providers:    Dict[str, Dict[str, List[Dict[str, Union[int, str]]]]],
        seasons:            List[DocumentSeason],
        embedding_model:    str
    ) -> Dict:
        """
        Construct a TV show document for MongoDB insertion.
        
        Args:
            tmdb_id:            TMDB TV show ID
            name:               TV show name
            original_name:      Original TV show name
            overview:           TV show overview
            poster_path:        Path to poster image
            backdrop_path:      Path to backdrop image
            first_air_date:     First air date
            last_air_date:      Last air date
            number_of_seasons:  Number of seasons
            number_of_episodes: Number of episodes
            episode_run_time:   List of episode run times
            genres:             List of genres
            spoken_languages:   List of spoken languages
            origin_country:     List of origin countries
            imdb_id:            IMDB ID
            status:             TV show status
            cast:               List of cast members
            crew:               List of crew members
            images:             TV show images (posters, backdrops)
            videos:             List of videos (trailers, etc.)
            watch_providers:    Watch provider information
            seasons:            List of seasons with episodes and their transcript chunks
            embedding_model:    Name of the embedding model used
            
        Returns:
            Dict: TV show document ready for MongoDB insertion
        """
        return {
            "tmdb_id":            tmdb_id,
            "name":               name,
            "original_name":      original_name,
            "overview":           overview,
            "poster_path":        poster_path,
            "backdrop_path":      backdrop_path,
            "first_air_date":     first_air_date,
            "last_air_date":      last_air_date,
            "number_of_seasons":  number_of_seasons,
            "number_of_episodes": number_of_episodes,
            "episode_run_time":   episode_run_time,
            "genres":             genres,
            "spoken_languages":   spoken_languages,
            "origin_country":     origin_country,
            "imdb_id":            imdb_id,
            "status":             status,
            "cast":               cast,
            "crew":               crew,
            "images":             images,
            "videos":             videos,
            "watch_providers":    watch_providers,
            "seasons":            [
                {
                    "id":             season.id,
                    "season_number":  season.season_number,
                    "name":           season.name,
                    "overview":       season.overview,
                    "poster_path":    season.poster_path,
                    "air_date":       season.air_date,
                    "episode_count":  season.episode_count,
                    "episodes":       [
                        {
                            "id":                 episode.id,
                            "episode_number":     episode.episode_number,
                            "name":               episode.name,
                            "overview":           episode.overview,
                            "air_date":           episode.air_date,
                            "runtime":            episode.runtime,
                            "transcript_chunks":  [
                                {
                                    "index":      chunk.index,
                                    "text":       chunk.text,
                                    "embedding":  {
                                        "vector":     chunk.embedding.vector,
                                        "timestamp":  chunk.embedding.timestamp
                                    }
                                }
                                for chunk in episode.transcript_chunks
                            ]
                        }
                        for episode in season.episodes
                    ]
                }
                for season in seasons
            ],
            "embedding_model":    embedding_model,
            "created_at":         self.created_at,
            "updated_at":         self.updated_at
        }

"""
TMDB API Response Formats

This file documents the structure of responses from various TMDB API endpoints.
All responses are in JSON format.


# Movie Details Response
MOVIE_DETAILS = {
    "id": 550,  # int
    "title": "Fight Club",  # string
    "original_title": "Fight Club",  # string
    "overview": "A movie about...",  # string
    "poster_path": "/poster.jpg",  # string
    "backdrop_path": "/backdrop.jpg",  # string
    "release_date": "1999-10-15",  # string (YYYY-MM-DD)
    "runtime": 139,  # int (minutes)
    "vote_average": 8.4,  # float
    "vote_count": 20000,  # int
    "popularity": 100.0,  # float
    "genres": [  # array of objects
        {"id": 18, "name": "Drama"},
        {"id": 53, "name": "Thriller"}
    ],
    "production_companies": [  # array of objects
        {
            "id": 508,
            "name": "Regency Enterprises",
            "logo_path": "/logo.png",
            "origin_country": "US"
        }
    ],
    "production_countries": [  # array of objects
        {
            "iso_3166_1": "US",
            "name": "United States of America"
        }
    ],
    "spoken_languages": [  # array of objects
        {
            "iso_639_1": "en",
            "name": "English"
        }
    ],
    "budget": 63000000,  # int
    "revenue": 100853753,  # int
    "status": "Released",  # string
    "tagline": "A movie tagline",  # string
    "imdb_id": "tt0137523",  # string
    "homepage": "https://example.com",  # string
    "belongs_to_collection": {  # object or null
        "id": 10,
        "name": "Collection Name",
        "poster_path": "/poster.jpg",
        "backdrop_path": "/backdrop.jpg"
    }
}

# Movie Credits Response
MOVIE_CREDITS = {
    "id": 550,  # int
    "cast": [  # array of objects
        {
            "id": 819,
            "name": "Edward Norton",
            "character": "The Narrator",
            "profile_path": "/profile.jpg",
            "order": 0
        }
    ],
    "crew": [  # array of objects
        {
            "id": 7467,
            "name": "David Fincher",
            "job": "Director",
            "department": "Directing",
            "profile_path": "/profile.jpg"
        }
    ]
}

# Movie Images Response
MOVIE_IMAGES = {
    "id": 550,  # int
    "backdrops": [  # array of objects
        {
            "aspect_ratio": 1.778,
            "file_path": "/backdrop.jpg",
            "height": 1080,
            "width": 1920,
            "iso_639_1": "en",
            "vote_average": 5.5,
            "vote_count": 1
        }
    ],
    "posters": [  # array of objects
        {
            "aspect_ratio": 0.667,
            "file_path": "/poster.jpg",
            "height": 1500,
            "width": 1000,
            "iso_639_1": "en",
            "vote_average": 5.5,
            "vote_count": 1
        }
    ],
    "logos": [  # array of objects
        {
            "aspect_ratio": 2.833,
            "file_path": "/logo.png",
            "height": 300,
            "width": 850,
            "iso_639_1": "en",
            "vote_average": 5.5,
            "vote_count": 1
        }
    ]
}

# Movie Videos Response
MOVIE_VIDEOS = {
    "id": 550,  # int
    "results": [  # array of objects
        {
            "id": "533ec654c3a36854480003eb",
            "key": "SUXWAEX2jlg",
            "name": "Trailer 1",
            "site": "YouTube",
            "size": 1080,
            "type": "Trailer"
        }
    ]
}

# TV Show Details Response
TV_DETAILS = {
    "id": 1399,  # int
    "name": "Game of Thrones",  # string
    "original_name": "Game of Thrones",  # string
    "overview": "A TV show about...",  # string
    "poster_path": "/poster.jpg",  # string
    "backdrop_path": "/backdrop.jpg",  # string
    "first_air_date": "2011-04-17",  # string (YYYY-MM-DD)
    "last_air_date": "2019-05-19",  # string (YYYY-MM-DD)
    "number_of_seasons": 8,  # int
    "number_of_episodes": 73,  # int
    "vote_average": 8.3,  # float
    "vote_count": 10000,  # int
    "popularity": 100.0,  # float
    "genres": [  # array of objects
        {"id": 10765, "name": "Sci-Fi & Fantasy"},
        {"id": 18, "name": "Drama"}
    ],
    "created_by": [  # array of objects
        {
            "id": 9813,
            "name": "David Benioff",
            "profile_path": "/profile.jpg"
        }
    ],
    "networks": [  # array of objects
        {
            "id": 49,
            "name": "HBO",
            "logo_path": "/logo.png",
            "origin_country": "US"
        }
    ],
    "production_companies": [  # array of objects
        {
            "id": 76043,
            "name": "HBO",
            "logo_path": "/logo.png",
            "origin_country": "US"
        }
    ],
    "seasons": [  # array of objects
        {
            "id": 3627,
            "name": "Season 1",
            "overview": "Season 1 overview",
            "poster_path": "/poster.jpg",
            "season_number": 1,
            "air_date": "2011-04-17",
            "episode_count": 10
        }
    ],
    "status": "Ended",  # string
    "type": "Scripted",  # string
    "in_production": False,  # boolean
    "languages": ["en"],  # array of strings
    "origin_country": ["US"],  # array of strings
    "homepage": "https://example.com"  # string
}

# Person Details Response
PERSON_DETAILS = {
    "id": 976,  # int
    "name": "Jason Statham",  # string
    "biography": "Actor biography...",  # string
    "birthday": "1967-07-26",  # string (YYYY-MM-DD)
    "deathday": None,  # string or null
    "place_of_birth": "Shirebrook, Derbyshire, England, UK",  # string
    "profile_path": "/profile.jpg",  # string
    "popularity": 100.0,  # float
    "imdb_id": "nm0005458",  # string
    "homepage": "https://example.com",  # string
    "also_known_as": [  # array of strings
        "Jason Statham"
    ]
}

# Person Movie Credits Response
PERSON_MOVIE_CREDITS = {
    "id": 976,  # int
    "cast": [  # array of objects
        {
            "id": 550,
            "title": "Fight Club",
            "character": "Character Name",
            "poster_path": "/poster.jpg",
            "release_date": "1999-10-15",
            "vote_average": 8.4,
            "vote_count": 20000
        }
    ],
    "crew": [  # array of objects
        {
            "id": 550,
            "title": "Fight Club",
            "job": "Director",
            "department": "Directing",
            "poster_path": "/poster.jpg",
            "release_date": "1999-10-15",
            "vote_average": 8.4,
            "vote_count": 20000
        }
    ]
}

# Search Results Response (Multi)
SEARCH_RESULTS = {
    "page": 1,  # int
    "results": [  # array of objects
        {
            "id": 550,
            "media_type": "movie",  # string: "movie", "tv", or "person"
            "title": "Fight Club",  # for movies
            "name": "Game of Thrones",  # for TV shows
            "overview": "Overview text...",
            "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg",
            "profile_path": "/profile.jpg",  # for people
            "release_date": "1999-10-15",  # for movies
            "first_air_date": "2011-04-17",  # for TV shows
            "vote_average": 8.4,
            "vote_count": 20000,
            "popularity": 100.0
        }
    ],
    "total_pages": 1000,  # int
    "total_results": 20000  # int
}

# Watch Providers Response
WATCH_PROVIDERS = {
    "id": 550,  # int
    "results": {  # object
        "US": {  # country code
            "link": "https://www.themoviedb.org/movie/550-fight-club/watch",
            "flatrate": [  # array of objects
                {
                    "display_priority": 0,
                    "logo_path": "/logo.png",
                    "provider_id": 8,
                    "provider_name": "Netflix"
                }
            ],
            "rent": [  # array of objects
                {
                    "display_priority": 0,
                    "logo_path": "/logo.png",
                    "provider_id": 2,
                    "provider_name": "Apple TV"
                }
            ],
            "buy": [  # array of objects
                {
                    "display_priority": 0,
                    "logo_path": "/logo.png",
                    "provider_id": 2,
                    "provider_name": "Apple TV"
                }
            ]
        }
    }
}

"""

"""
movie_id = 668489
append_to_response = "credits,images,videos,watch/providers"

Response:


{
  "adult": false,
  "backdrop_path": "/65MVgDa6YjSdqzh7YOA04mYkioo.jpg",
  "belongs_to_collection": null,
  "budget": 90000000,
  "genres": [
    {
      "id": 28,
      "name": "Action"
    },
    {
      "id": 80,
      "name": "Crime"
    },
    {
      "id": 53,
      "name": "Thriller"
    }
  ],
  "homepage": "https://www.netflix.com/title/81330790",
  "id": 668489,
  "imdb_id": "tt14123284",
  "origin_country": [
    "GB"
  ],
  "original_language": "en",
  "original_title": "Havoc",
  "overview": "When a drug heist swerves lethally out of control, a jaded cop fights his way through a corrupt city's criminal underworld to save a politician's son.",
  "popularity": 120.0599,
  "poster_path": "/r46leE6PSzLR3pnVzaxx5Q30yUF.jpg",
  "production_companies": [
    {
      "id": 12142,
      "logo_path": "/rPnEeMwxjI6rYMGqkWqIWwIJXxi.png",
      "name": "XYZ Films",
      "origin_country": "US"
    },
    {
      "id": 93637,
      "logo_path": "/aW4weh0t8yUm2e62w4t3KlKJsLX.png",
      "name": "Severn Screen",
      "origin_country": "GB"
    },
    {
      "id": 110036,
      "logo_path": null,
      "name": "One More One Productions",
      "origin_country": "GB"
    }
  ],
  "production_countries": [
    {
      "iso_3166_1": "GB",
      "name": "United Kingdom"
    },
    {
      "iso_3166_1": "US",
      "name": "United States of America"
    }
  ],
  "release_date": "2025-04-25",
  "revenue": 0,
  "runtime": 107,
  "spoken_languages": [
    {
      "english_name": "English",
      "iso_639_1": "en",
      "name": "English"
    },
    {
      "english_name": "Cantonese",
      "iso_639_1": "cn",
      "name": "广州话 / 廣州話"
    }
  ],
  "status": "Released",
  "tagline": "No law. Only disorder.",
  "title": "Havoc",
  "video": false,
  "vote_average": 6.514,
  "vote_count": 642,
  "credits": {
    "cast": [
      {
        "adult": false,
        "gender": 2,
        "id": 2524,
        "known_for_department": "Acting",
        "name": "Tom Hardy",
        "original_name": "Tom Hardy",
        "popularity": 19.516,
        "profile_path": "/d81K0RH8UX7tZj49tZaQhZ9ewH.jpg",
        "cast_id": 3,
        "character": "Walker",
        "credit_id": "602fe85cefe37c003ebd75f6",
        "order": 0
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2234003,
        "known_for_department": "Acting",
        "name": "Jessie Mei Li",
        "original_name": "Jessie Mei Li",
        "popularity": 2.875,
        "profile_path": "/t7LmlgmjsqGNRj0sA4tthejP3yI.jpg",
        "cast_id": 11,
        "character": "Ellie",
        "credit_id": "60da4b7e955c65005dca6a64",
        "order": 1
      },
      {
        "adult": false,
        "gender": 2,
        "id": 18082,
        "known_for_department": "Acting",
        "name": "Timothy Olyphant",
        "original_name": "Timothy Olyphant",
        "popularity": 5.6406,
        "profile_path": "/7pHmRHE2wBNC9cBgNIRCBqFLoyZ.jpg",
        "cast_id": 9,
        "character": "Vincent",
        "credit_id": "60da4b3717c443005e826c64",
        "order": 2
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2178,
        "known_for_department": "Acting",
        "name": "Forest Whitaker",
        "original_name": "Forest Whitaker",
        "popularity": 6.7774,
        "profile_path": "/4w7l5JUwnwFNBy7J93ZwYN1nihm.jpg",
        "cast_id": 8,
        "character": "Lawrence Beaumont",
        "credit_id": "6058c8d3af2da80076123996",
        "order": 3
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1684648,
        "known_for_department": "Acting",
        "name": "Justin Cornwell",
        "original_name": "Justin Cornwell",
        "popularity": 1.1637,
        "profile_path": "/xFmMBP5qtAiLDpbrziXOYdAkK7.jpg",
        "cast_id": 10,
        "character": "Charlie",
        "credit_id": "60da4b5125b9550046b88274",
        "order": 4
      },
      {
        "adult": false,
        "gender": 1,
        "id": 3140018,
        "known_for_department": "Acting",
        "name": "Quelin Sepulveda",
        "original_name": "Quelin Sepulveda",
        "popularity": 1.9529,
        "profile_path": "/oNXfeaVbilHgKafs2ovn9XffG3g.jpg",
        "cast_id": 16,
        "character": "Mia",
        "credit_id": "60da4dcd0b7316005dda03b6",
        "order": 5
      },
      {
        "adult": false,
        "gender": 2,
        "id": 40481,
        "known_for_department": "Acting",
        "name": "Luis Guzmán",
        "original_name": "Luis Guzmán",
        "popularity": 4.0093,
        "profile_path": "/kSdxUckOJj9R5VKrLUnRy14YhNV.jpg",
        "cast_id": 13,
        "character": "Raul",
        "credit_id": "60da4c3cb7fbbd005ef5db84",
        "order": 6
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1297561,
        "known_for_department": "Acting",
        "name": "Sunny Pang",
        "original_name": "Sunny Pang",
        "popularity": 3.5883,
        "profile_path": "/tEhFEmOLwnoHcX0PJhzSLWr0Dw2.jpg",
        "cast_id": 14,
        "character": "Ching",
        "credit_id": "60da4c573fe160005be18636",
        "order": 7
      },
      {
        "adult": false,
        "gender": 1,
        "id": 130761,
        "known_for_department": "Acting",
        "name": "Yeo Yann Yann",
        "original_name": "楊雁雁",
        "popularity": 1.5664,
        "profile_path": "/ncOxEFlrrR35kVZW5MgA1uGTUMx.jpg",
        "cast_id": 12,
        "character": "Tsui's Mother",
        "credit_id": "60da4b99955c65002fa0ca0f",
        "order": 8
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1131590,
        "known_for_department": "Acting",
        "name": "Michelle Waterson-Gomez",
        "original_name": "Michelle Waterson-Gomez",
        "popularity": 0.6363,
        "profile_path": "/md1i3J0MwQLNYzbMkmTsFAaQL5X.jpg",
        "cast_id": 15,
        "character": "Assassin",
        "credit_id": "60da4c8205f9cf002b6f24a6",
        "order": 9
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2010190,
        "known_for_department": "Acting",
        "name": "Jim Caesar",
        "original_name": "Jim Caesar",
        "popularity": 0.7214,
        "profile_path": "/u9fLardUfWyxmrV3tuK4JDsPk2O.jpg",
        "cast_id": 25,
        "character": "Wes",
        "credit_id": "618c741735d1bc0043341d3b",
        "order": 10
      },
      {
        "adult": false,
        "gender": 3,
        "id": 3304729,
        "known_for_department": "Acting",
        "name": "Xelia Mendes-Jones",
        "original_name": "Xelia Mendes-Jones",
        "popularity": 0.5858,
        "profile_path": "/pUr1bvy2XFWpN1xgLaTfsQ1CvC6.jpg",
        "cast_id": 39,
        "character": "Johnny",
        "credit_id": "618c750addd52d0026c4abf5",
        "order": 11
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1040481,
        "known_for_department": "Acting",
        "name": "Lockhart Ogilvie",
        "original_name": "Lockhart Ogilvie",
        "popularity": 0.6132,
        "profile_path": "/jlNSvUw6xJb08r2y7mm0GJc9ynw.jpg",
        "cast_id": 85,
        "character": "Undercover Cop",
        "credit_id": "680b5f378bcea66a86aadc7b",
        "order": 12
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1231651,
        "known_for_department": "Acting",
        "name": "Richard Harrington",
        "original_name": "Richard Harrington",
        "popularity": 1.8293,
        "profile_path": "/yRiMMz91LC4EgrRpbsaw80T1XM1.jpg",
        "cast_id": 17,
        "character": "Jake",
        "credit_id": "618c7385e7414600439949cc",
        "order": 13
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2179424,
        "known_for_department": "Acting",
        "name": "Serhat Metin",
        "original_name": "Serhat Metin",
        "popularity": 0.9236,
        "profile_path": "/iTAxqP85XYt9MxcNhYvHVWMwOJy.jpg",
        "cast_id": 24,
        "character": "Cortez",
        "credit_id": "618c7408d768fe00929d62fc",
        "order": 14
      },
      {
        "adult": false,
        "gender": 2,
        "id": 563560,
        "known_for_department": "Acting",
        "name": "Gordon Alexander",
        "original_name": "Gordon Alexander",
        "popularity": 3.9349,
        "profile_path": "/d7Z5Rbctu6Jj9WmJJgrMHk8mhK6.jpg",
        "cast_id": 21,
        "character": "Hayes",
        "credit_id": "618c73c3cca7de00298c5231",
        "order": 15
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1376873,
        "known_for_department": "Acting",
        "name": "John Cummins",
        "original_name": "John Cummins",
        "popularity": 0.4398,
        "profile_path": "/b3gBWD1IWDB5GT9SRHDvrSnWwog.jpg",
        "cast_id": 23,
        "character": "Jimmy",
        "credit_id": "618c73fa7ac82900434d3d75",
        "order": 16
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1627685,
        "known_for_department": "Acting",
        "name": "Megan Lockhurst",
        "original_name": "Megan Lockhurst",
        "popularity": 0.6449,
        "profile_path": "/xOzS8hzdlmIhN0yvc7KBtcBIgxo.jpg",
        "cast_id": 86,
        "character": "News Anchor",
        "credit_id": "680b602e41a382d6a089b6f8",
        "order": 17
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2845635,
        "known_for_department": "Acting",
        "name": "Jade Ogugua",
        "original_name": "Jade Ogugua",
        "popularity": 0.4554,
        "profile_path": "/fAry36wuty3REC1cOIohOH8qh4g.jpg",
        "cast_id": 87,
        "character": "Advisor",
        "credit_id": "680b6072e92f940ca69d45b0",
        "order": 18
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2189085,
        "known_for_department": "Acting",
        "name": "Jack Morris",
        "original_name": "Jack Morris",
        "popularity": 1.0856,
        "profile_path": "/wi8qypkEV64ZLzdOGp5ecotBGsI.jpg",
        "cast_id": 45,
        "character": "Meth Head Man",
        "credit_id": "621eb0528c7b0f006df8a0a9",
        "order": 19
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2977460,
        "known_for_department": "Acting",
        "name": "Gareth Tidball",
        "original_name": "Gareth Tidball",
        "popularity": 0.3313,
        "profile_path": "/uqhFXcfgjNDdbCGk5cflwE5ioEV.jpg",
        "cast_id": 88,
        "character": "Apartment Woman",
        "credit_id": "680b61b7778b4626739d53dd",
        "order": 20
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1072105,
        "known_for_department": "Acting",
        "name": "Narges Rashidi",
        "original_name": "Narges Rashidi",
        "popularity": 0.9251,
        "profile_path": "/fCh3rJkIKvvTfLQa8y1UClyNC3R.jpg",
        "cast_id": 52,
        "character": "Helena",
        "credit_id": "630e6d51e7c0970092d5c072",
        "order": 21
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2595174,
        "known_for_department": "Acting",
        "name": "Astrid Fox-Sahan",
        "original_name": "Astrid Fox-Sahan",
        "popularity": 0.1813,
        "profile_path": "/ldHTnBtMqvQe4UqY5x6CkZAffQB.jpg",
        "cast_id": 41,
        "character": "Emmy",
        "credit_id": "618c751dcb6db5008d61d829",
        "order": 22
      },
      {
        "adult": false,
        "gender": 2,
        "id": 3596312,
        "known_for_department": "Crew",
        "name": "Alan Leong",
        "original_name": "Alan Leong",
        "popularity": 1.9853,
        "profile_path": null,
        "cast_id": 89,
        "character": "Triad Doorman",
        "credit_id": "680b621841a382d6a089b788",
        "order": 23
      },
      {
        "adult": false,
        "gender": 2,
        "id": 3304725,
        "known_for_department": "Acting",
        "name": "Jeremy Ang Jones",
        "original_name": "Jeremy Ang Jones",
        "popularity": 0.5412,
        "profile_path": "/gx9971PQUC2TFUdbSbAP3A8booE.jpg",
        "cast_id": 34,
        "character": "Tsui",
        "credit_id": "618c749ecf62cd00421a7a89",
        "order": 24
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1743494,
        "known_for_department": "Acting",
        "name": "Aaron Ly",
        "original_name": "Aaron Ly",
        "popularity": 0.3697,
        "profile_path": "/gGLhwphjXvn1bVGQ53ifXaeyzTp.jpg",
        "cast_id": 46,
        "character": "Ching's Lieutenant",
        "credit_id": "621eb0f56f31af006cabd5b9",
        "order": 25
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1445522,
        "known_for_department": "Acting",
        "name": "Jennifer Armour",
        "original_name": "Jennifer Armour",
        "popularity": 0.2142,
        "profile_path": "/57JFvr3Uuxlh7HmVmPcv54votVW.jpg",
        "cast_id": 22,
        "character": "Patrol Cop (Tsui's)",
        "credit_id": "618c73db0f0da5006526ac4d",
        "order": 26
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1198147,
        "known_for_department": "Acting",
        "name": "Clarence Smith",
        "original_name": "Clarence Smith",
        "popularity": 0.7264,
        "profile_path": "/7HhMsotc0XXt9r0XGt6dwRCpsGM.jpg",
        "cast_id": 90,
        "character": "Detective (Tsui's)",
        "credit_id": "680b62df778b4626739d54ff",
        "order": 27
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1941275,
        "known_for_department": "Acting",
        "name": "Albert Tang",
        "original_name": "Albert Tang",
        "popularity": 0.7455,
        "profile_path": "/i8wGIoHtdTO4m3Fb4hgjeZI89zG.jpg",
        "cast_id": 28,
        "character": "Bullied Chinatown Old Man",
        "credit_id": "618c7443d768fe00677d1def",
        "order": 28
      },
      {
        "adult": false,
        "gender": 2,
        "id": 67212,
        "known_for_department": "Acting",
        "name": "Tom Wu",
        "original_name": "Tom Wu",
        "popularity": 2.2756,
        "profile_path": "/qBQAerjLCCglXIyMURUj3hPpiCM.jpg",
        "cast_id": 18,
        "character": "Wong",
        "credit_id": "618c7395d6d64d008fedf88d",
        "order": 29
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1474690,
        "known_for_department": "Acting",
        "name": "Jill Winternitz",
        "original_name": "Jill Winternitz",
        "popularity": 0.9192,
        "profile_path": "/bBfmth2C93OkyYir6w8qxjmHpiR.jpg",
        "cast_id": 19,
        "character": "Angela",
        "credit_id": "618c73a21cfe3a008d568f65",
        "order": 30
      },
      {
        "adult": false,
        "gender": 1,
        "id": 3304723,
        "known_for_department": "Acting",
        "name": "Stacy Sobieski",
        "original_name": "Stacy Sobieski",
        "popularity": 0.2541,
        "profile_path": "/oDDU9ivC8GkdSKSlv4tSd85cxBC.jpg",
        "cast_id": 31,
        "character": "Hospital Doctor",
        "credit_id": "618c746da313b8002a9792a6",
        "order": 31
      },
      {
        "adult": false,
        "gender": 2,
        "id": 3616434,
        "known_for_department": "Acting",
        "name": "Odimegwu Okoye",
        "original_name": "Odimegwu Okoye",
        "popularity": 0.2981,
        "profile_path": "/tHKOF0r6H1v1pv4haYc87gjjznH.jpg",
        "cast_id": 91,
        "character": "Police Officer - Police Station",
        "credit_id": "680b635f15a1d5a614ab60a4",
        "order": 32
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1239745,
        "known_for_department": "Acting",
        "name": "Sharon D. Clarke",
        "original_name": "Sharon D. Clarke",
        "popularity": 1.4368,
        "profile_path": "/uNWPeItDgQvUDBJuY0M6ZegylrE.jpg",
        "cast_id": 92,
        "character": "Captain",
        "credit_id": "680b637f778b4626739d5669",
        "order": 33
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2261088,
        "known_for_department": "Acting",
        "name": "Jon-Scott Clark",
        "original_name": "Jon-Scott Clark",
        "popularity": 0.447,
        "profile_path": "/a5lBJJ4Gnj34Kb1K5w5I8XxCYlP.jpg",
        "cast_id": 30,
        "character": "Ticket Guy",
        "credit_id": "618c745acf62cd00421a79e4",
        "order": 34
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5395382,
        "known_for_department": "Acting",
        "name": "Kage Jakubiec",
        "original_name": "Kage Jakubiec",
        "popularity": 0.0398,
        "profile_path": null,
        "cast_id": 93,
        "character": "Medusa DJ",
        "credit_id": "680b64b141a382d6a089b941",
        "order": 35
      },
      {
        "adult": false,
        "gender": 1,
        "id": 5395392,
        "known_for_department": "Acting",
        "name": "Samya De Meo",
        "original_name": "Samya De Meo",
        "popularity": 0.0507,
        "profile_path": "/mA7GWdHvaAa9HFOy8rWb1nRSJ2Z.jpg",
        "cast_id": 94,
        "character": "Hospital Receptionist",
        "credit_id": "680b65a36aa1f90c7daa9994",
        "order": 36
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5395476,
        "known_for_department": "Acting",
        "name": "Adam Bendall",
        "original_name": "Adam Bendall",
        "popularity": 0.051,
        "profile_path": null,
        "cast_id": 100,
        "character": "Paramedic (uncredited)",
        "credit_id": "680b70edd148a82b0d9cffba",
        "order": 37
      },
      {
        "adult": false,
        "gender": 0,
        "id": 3304728,
        "known_for_department": "Acting",
        "name": "Arun Kapur",
        "original_name": "Arun Kapur",
        "popularity": 0.3128,
        "profile_path": "/fpYncuywNb0p98HVUIiNLnKFcGt.jpg",
        "cast_id": 37,
        "character": "Hotel Attendee (uncredited)",
        "credit_id": "618c74ef8c7b0f0066f48519",
        "order": 38
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1615064,
        "known_for_department": "Acting",
        "name": "Atul Sharma",
        "original_name": "Atul Sharma",
        "popularity": 1.2825,
        "profile_path": "/ArCswhLKzGJW6viP1uiF82wQLiX.jpg",
        "cast_id": 20,
        "character": "Doctor (uncredited)",
        "credit_id": "618c73b48c7b0f004396e134",
        "order": 39
      },
      {
        "adult": false,
        "gender": 0,
        "id": 3304726,
        "known_for_department": "Acting",
        "name": "Bailey Cameron",
        "original_name": "Bailey Cameron",
        "popularity": 0.1624,
        "profile_path": "/rKutcj3Gni5X10ZJvqOtp5th1Q6.jpg",
        "cast_id": 35,
        "character": "Joey (uncredited)",
        "credit_id": "618c74b5cca7de00298c53ee",
        "order": 40
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2651389,
        "known_for_department": "Acting",
        "name": "Christopher Ashman",
        "original_name": "Christopher Ashman",
        "popularity": 0.1446,
        "profile_path": "/1UHRc4JdsI53gCzTkLF3XfX5rk1.jpg",
        "cast_id": 38,
        "character": "Crime Scene Photographer (uncredited)",
        "credit_id": "618c75000f0da5002aef94bf",
        "order": 41
      },
      {
        "adult": false,
        "gender": 2,
        "id": 101037,
        "known_for_department": "Acting",
        "name": "Christopher Maleki",
        "original_name": "Christopher Maleki",
        "popularity": 2.114,
        "profile_path": "/7X8ziMt2wm9atI9T6sEWEShutie.jpg",
        "cast_id": 109,
        "character": "Zak (uncredited)",
        "credit_id": "680b7ae6d148a82b0d9d0598",
        "order": 42
      },
      {
        "adult": false,
        "gender": 2,
        "id": 3161798,
        "known_for_department": "Acting",
        "name": "Dan Brothers",
        "original_name": "Dan Brothers",
        "popularity": 0.1774,
        "profile_path": "/iYqgKE6Ca79cgN4UHYmFTPhqXH1.jpg",
        "cast_id": 33,
        "character": "Police Officer (uncredited)",
        "credit_id": "618c7492a313b80042ddf443",
        "order": 43
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5395436,
        "known_for_department": "Acting",
        "name": "Daniel Joseph Woolf",
        "original_name": "Daniel Joseph Woolf",
        "popularity": 1.5126,
        "profile_path": "/6ByL2ls4L9Yfu3iybua80bcgGTz.jpg",
        "cast_id": 99,
        "character": "Junkyard Worker (uncredited)",
        "credit_id": "680b6a07f3cf6d66d79d5639",
        "order": 44
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2559089,
        "known_for_department": "Acting",
        "name": "Darryl Bradford",
        "original_name": "Darryl Bradford",
        "popularity": 0.4224,
        "profile_path": null,
        "cast_id": 95,
        "character": "Driver (uncredited)",
        "credit_id": "680b673d63c5f9522989c312",
        "order": 45
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1371452,
        "known_for_department": "Acting",
        "name": "David Cheung",
        "original_name": "David Cheung",
        "popularity": 1.9081,
        "profile_path": "/z5Xkb20AgnBPUs01J7J2lykIPyR.jpg",
        "cast_id": 103,
        "character": "Triad (uncredited)",
        "credit_id": "680b7442bfbdf1f8c589e75e",
        "order": 46
      },
      {
        "adult": false,
        "gender": 0,
        "id": 3304722,
        "known_for_department": "Acting",
        "name": "Emma Kaler",
        "original_name": "Emma Kaler",
        "popularity": 0.15,
        "profile_path": "/wzoJUy3cn3eb7Vh9khGfEx2DBFF.jpg",
        "cast_id": 26,
        "character": "Driver (uncredited)",
        "credit_id": "618c7422cf62cd002afd302d",
        "order": 47
      },
      {
        "adult": false,
        "gender": 0,
        "id": 3304727,
        "known_for_department": "Acting",
        "name": "Eric Sirakian",
        "original_name": "Eric Sirakian",
        "popularity": 0.1989,
        "profile_path": "/c7iAsbuZCiZX7lx4XiWS25kyDOA.jpg",
        "cast_id": 36,
        "character": "Hotel Concierge (uncredited)",
        "credit_id": "618c74cacb6db50062414c4b",
        "order": 48
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1952370,
        "known_for_department": "Crew",
        "name": "Erol Mehmet",
        "original_name": "Erol Mehmet",
        "popularity": 2.0089,
        "profile_path": "/ms3JH2RbJVbdOtv105JEzikNHZQ.jpg",
        "cast_id": 110,
        "character": "Policeman (uncredited)",
        "credit_id": "680b7b07d148a82b0d9d05a1",
        "order": 49
      },
      {
        "adult": false,
        "gender": 2,
        "id": 3221949,
        "known_for_department": "Acting",
        "name": "George Gjiggy Francis",
        "original_name": "George Gjiggy Francis",
        "popularity": 0.2344,
        "profile_path": null,
        "cast_id": 105,
        "character": "Greyhound Driver (uncredited)",
        "credit_id": "680b7593271ecb3ae08a765f",
        "order": 50
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1641878,
        "known_for_department": "Acting",
        "name": "Joe David Walters",
        "original_name": "Joe David Walters",
        "popularity": 1.9068,
        "profile_path": "/bTJ2AMhLoxwwgwt5xYrwlhRLs4e.jpg",
        "cast_id": 29,
        "character": "D.A. Collins (uncredited)",
        "credit_id": "618c74500f0da50044e4f736",
        "order": 51
      },
      {
        "adult": false,
        "gender": 2,
        "id": 4578995,
        "known_for_department": "Acting",
        "name": "Matthew Lee",
        "original_name": "Matthew Lee",
        "popularity": 0.2594,
        "profile_path": "/eHSSfymqqNiz4EgjYkRjKJo0hDO.jpg",
        "cast_id": 108,
        "character": "Hospital Patient (uncredited)",
        "credit_id": "680b7954271ecb3ae08a787e",
        "order": 52
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5074806,
        "known_for_department": "Acting",
        "name": "Maurizio Posteraro",
        "original_name": "Maurizio Posteraro",
        "popularity": 0.0664,
        "profile_path": "/6LypuNRlCGMfo5hc5Nliy5FwNv7.jpg",
        "cast_id": 96,
        "character": "Security Guard (uncredited)",
        "credit_id": "680b67bc6aa1f90c7daa9ca1",
        "order": 53
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5395504,
        "known_for_department": "Acting",
        "name": "Mikey Fantham",
        "original_name": "Mikey Fantham",
        "popularity": 0.0357,
        "profile_path": "/wbnXgBGpp3MEUIkwOkm9StOkoQ4.jpg",
        "cast_id": 104,
        "character": "Hotel Guest (uncredited)",
        "credit_id": "680b74c8d148a82b0d9d01f6",
        "order": 54
      },
      {
        "adult": false,
        "gender": 1,
        "id": 3857260,
        "known_for_department": "Acting",
        "name": "Nicole Joseph",
        "original_name": "Nicole Joseph",
        "popularity": 0.9713,
        "profile_path": "/oHnwEAiDtry7hEYX7qvyQFLO9Ax.jpg",
        "cast_id": 107,
        "character": "Maggie (uncredited)",
        "credit_id": "680b78f9bfbdf1f8c589e87c",
        "order": 55
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5395553,
        "known_for_department": "Acting",
        "name": "Oliver Harnett",
        "original_name": "Oliver Harnett",
        "popularity": 0.0143,
        "profile_path": null,
        "cast_id": 106,
        "character": "Police Officer (uncredited)",
        "credit_id": "680b78d3bfbdf1f8c589e86a",
        "order": 56
      },
      {
        "adult": false,
        "gender": 0,
        "id": 2545138,
        "known_for_department": "Acting",
        "name": "Patrick Loh",
        "original_name": "Patrick Loh",
        "popularity": 1.1427,
        "profile_path": "/y1Sl5TyvP8P1SFz9DiDz0XV6YlB.jpg",
        "cast_id": 98,
        "character": "Angry Driver (uncredited)",
        "credit_id": "680b68da41a382d6a089bc45",
        "order": 57
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2990663,
        "known_for_department": "Acting",
        "name": "Pino Maiello",
        "original_name": "Pino Maiello",
        "popularity": 0.27,
        "profile_path": null,
        "cast_id": 53,
        "character": "Junkyard Worker (uncredited)",
        "credit_id": "630e6db2ae26be00915e7470",
        "order": 58
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5395483,
        "known_for_department": "Acting",
        "name": "Richard Chan",
        "original_name": "Richard Chan",
        "popularity": 0.0755,
        "profile_path": "/ufl5HIXMsQuvmMoY8GlVQ86sdTG.jpg",
        "cast_id": 102,
        "character": "Triad (uncredited)",
        "credit_id": "680b7311e92f940ca69d4ef8",
        "order": 59
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1879461,
        "known_for_department": "Acting",
        "name": "Richard Pepper",
        "original_name": "Richard Pepper",
        "popularity": 0.319,
        "profile_path": "/sYYxriSIskzlajp6BBmoEXaPnRp.jpg",
        "cast_id": 27,
        "character": "Jerry Richardson (uncredited)",
        "credit_id": "618c74302dc9dc00885c1ff4",
        "order": 60
      },
      {
        "adult": false,
        "gender": 2,
        "id": 3111047,
        "known_for_department": "Acting",
        "name": "Rui Shang",
        "original_name": "Rui Shang",
        "popularity": 0.1863,
        "profile_path": "/vOR273NxXtymxIQ6fZORLgyo7yb.jpg",
        "cast_id": 97,
        "character": "Triad (uncredited)",
        "credit_id": "680b67f0d148a82b0d9cf0c4",
        "order": 61
      },
      {
        "adult": false,
        "gender": 2,
        "id": 5274317,
        "known_for_department": "Acting",
        "name": "Sam Byrne",
        "original_name": "Sam Byrne",
        "popularity": 0.1882,
        "profile_path": "/bjN35bCzjg71MEeIDyKZ6o9CcyB.jpg",
        "cast_id": 101,
        "character": "Lawrence Security (uncredited)",
        "credit_id": "680b71368bcea66a86aaee81",
        "order": 62
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1368017,
        "known_for_department": "Acting",
        "name": "Timothy Hornor",
        "original_name": "Timothy Hornor",
        "popularity": 0.8198,
        "profile_path": "/8W8EGTDlvYOhcdP2ZirrdNil8LY.jpg",
        "cast_id": 32,
        "character": "Harold (uncredited)",
        "credit_id": "618c747aa313b80042ddf404",
        "order": 63
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2452580,
        "known_for_department": "Acting",
        "name": "Volenté Lloyd",
        "original_name": "Volenté Lloyd",
        "popularity": 0.3196,
        "profile_path": "/1sF7We3J3DFMUQtnpiHpFD5oHGv.jpg",
        "cast_id": 40,
        "character": "Prostitute (uncredited)",
        "credit_id": "618c75130f0da5006526b07b",
        "order": 64
      }
    ],
    "crew": [
      {
        "adult": false,
        "gender": 2,
        "id": 1776295,
        "known_for_department": "Directing",
        "name": "Liam Lock",
        "original_name": "Liam Lock",
        "popularity": 0.4884,
        "profile_path": null,
        "credit_id": "621ebebd9f1be7006b81ce1e",
        "department": "Directing",
        "job": "First Assistant Director"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1969647,
        "known_for_department": "Directing",
        "name": "James McGeown",
        "original_name": "James McGeown",
        "popularity": 0.2623,
        "profile_path": null,
        "credit_id": "621ebed877b1fb006cfa7a1d",
        "department": "Directing",
        "job": "Second Assistant Director"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 2666601,
        "known_for_department": "Art",
        "name": "Joelle Rumbelow",
        "original_name": "Joelle Rumbelow",
        "popularity": 0.154,
        "profile_path": null,
        "credit_id": "621ebea612aabc0042b11845",
        "department": "Art",
        "job": "Set Decoration"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 67203,
        "known_for_department": "Art",
        "name": "Sam Stokes",
        "original_name": "Sam Stokes",
        "popularity": 0.6622,
        "profile_path": null,
        "credit_id": "621ebe938a88b2006dd5576a",
        "department": "Art",
        "job": "Supervising Art Director"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 1753307,
        "known_for_department": "Art",
        "name": "Faye Boustead",
        "original_name": "Faye Boustead",
        "popularity": 0.115,
        "profile_path": null,
        "credit_id": "621ebe776f31af001cd692ee",
        "department": "Art",
        "job": "Art Direction"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 3532449,
        "known_for_department": "Crew",
        "name": "Julia Schunevitsch",
        "original_name": "Julia Schunevitsch",
        "popularity": 3.0863,
        "profile_path": "/iCGvMtqjwsyLBYRGjY11wbmml9.jpg",
        "credit_id": "653ee7fc109cd0012cffdd44",
        "department": "Crew",
        "job": "Stunt Double"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 3277669,
        "known_for_department": "Production",
        "name": "Sarah Dibsdall",
        "original_name": "Sarah Dibsdall",
        "popularity": 0.127,
        "profile_path": null,
        "credit_id": "618c7f3b20e6a500443a4856",
        "department": "Production",
        "job": "Producer"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 1014915,
        "known_for_department": "Production",
        "name": "Kelly Valentine Hendry",
        "original_name": "Kelly Valentine Hendry",
        "popularity": 0.8945,
        "profile_path": "/iod9xHLq1KN1mmpVuj9SRuY7Nxc.jpg",
        "credit_id": "618c7f5bb076e50043e9da30",
        "department": "Production",
        "job": "Casting"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 24260,
        "known_for_department": "Costume & Make-Up",
        "name": "Claire Pritchard",
        "original_name": "Claire Pritchard",
        "popularity": 1.0105,
        "profile_path": "/9yoXqLnATg2qzE4DORtYDdGzp6c.jpg",
        "credit_id": "6627e4ba221ba6017c175411",
        "department": "Costume & Make-Up",
        "job": "Makeup & Hair"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 4671407,
        "known_for_department": "Sound",
        "name": "Elis Howell Griffiths",
        "original_name": "Elis Howell Griffiths",
        "popularity": 0.0978,
        "profile_path": null,
        "credit_id": "66283a09e295b401879d2922",
        "department": "Sound",
        "job": "Sound Mixer"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 2933756,
        "known_for_department": "Sound",
        "name": "Joss Colin",
        "original_name": "Joss Colin",
        "popularity": 0.0831,
        "profile_path": null,
        "credit_id": "662839f54a4bf6018876ac67",
        "department": "Sound",
        "job": "Boom Operator"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 2475870,
        "known_for_department": "Sound",
        "name": "Andre Harihandoyo",
        "original_name": "Andre Harihandoyo",
        "popularity": 0.3774,
        "profile_path": null,
        "credit_id": "662839fe63d937014a71fb0a",
        "department": "Sound",
        "job": "Dialogue Editor"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 18184,
        "known_for_department": "Directing",
        "name": "Xavier Gens",
        "original_name": "Xavier Gens",
        "popularity": 1.2979,
        "profile_path": "/zZ2ZtJeBq0yXB1Z5hSztarGt1yN.jpg",
        "credit_id": "66283a3462f335014bd85c91",
        "department": "Directing",
        "job": "Second Unit Director"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 2544817,
        "known_for_department": "Sound",
        "name": "Adrian Yew Erman",
        "original_name": "Adrian Yew Erman",
        "popularity": 0.3847,
        "profile_path": null,
        "credit_id": "66283a124a4bf6018876ac6a",
        "department": "Sound",
        "job": "ADR Recording Engineer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 215913,
        "known_for_department": "Crew",
        "name": "Jacob Tomuri",
        "original_name": "Jacob Tomuri",
        "popularity": 2.3218,
        "profile_path": "/f0jPDz0beDrLsmXWAnfXZqwHqFO.jpg",
        "credit_id": "664d2bd4084d09c4579ee373",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2244034,
        "known_for_department": "Crew",
        "name": "Adrian Derrick-Palmer",
        "original_name": "Adrian Derrick-Palmer",
        "popularity": 1.9178,
        "profile_path": "/6lTrbZ7Vf19QNl3gJhkFoJ7vtS8.jpg",
        "credit_id": "6674be92f6e2406a570f21c1",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2441229,
        "known_for_department": "Crew",
        "name": "Oleg Podobin",
        "original_name": "Oleg Podobin",
        "popularity": 1.661,
        "profile_path": null,
        "credit_id": "668d99c4deed32c745d58975",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2769366,
        "known_for_department": "Crew",
        "name": "Christina Petrou",
        "original_name": "Christina Petrou",
        "popularity": 2.1396,
        "profile_path": "/dC7JHx7Q9qKa4YqdCZVvqYTUTSP.jpg",
        "credit_id": "668d9f7dfdf0326f62659752",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2494084,
        "known_for_department": "Production",
        "name": "Juliette Woodcock",
        "original_name": "Juliette Woodcock",
        "popularity": 0.1896,
        "profile_path": null,
        "credit_id": "649f35cd8d52c900adab2bb0",
        "department": "Production",
        "job": "Unit Production Manager"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 1742983,
        "known_for_department": "Visual Effects",
        "name": "Danny Hargreaves",
        "original_name": "Danny Hargreaves",
        "popularity": 0.7382,
        "profile_path": null,
        "credit_id": "649f3638d6590b00fec25d88",
        "department": "Visual Effects",
        "job": "Special Effects Supervisor"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1492511,
        "known_for_department": "Production",
        "name": "Stephanie Whonsetler",
        "original_name": "Stephanie Whonsetler",
        "popularity": 0.3801,
        "profile_path": null,
        "credit_id": "649f36033af9290144f0c5f2",
        "department": "Production",
        "job": "Executive In Charge Of Production"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1187862,
        "known_for_department": "Costume & Make-Up",
        "name": "Sian Jenkins",
        "original_name": "Sian Jenkins",
        "popularity": 0.5715,
        "profile_path": null,
        "credit_id": "649f359cedeb4300aec43c5d",
        "department": "Costume & Make-Up",
        "job": "Costume Design"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 3016421,
        "known_for_department": "Production",
        "name": "Matt Levin",
        "original_name": "Matt Levin",
        "popularity": 0.3934,
        "profile_path": null,
        "credit_id": "649f35f085867800ebb614db",
        "department": "Production",
        "job": "Executive In Charge Of Production"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 3373875,
        "known_for_department": "Production",
        "name": "Imogen Arthur",
        "original_name": "Imogen Arthur",
        "popularity": 0.1203,
        "profile_path": null,
        "credit_id": "649f3677edeb43013a695675",
        "department": "Visual Effects",
        "job": "Visual Effects Production Manager"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 142026,
        "known_for_department": "Camera",
        "name": "Matt Flannery",
        "original_name": "Matt Flannery",
        "popularity": 0.4651,
        "profile_path": "/rRr8KI04EmvS8KyVxGmB6QWted.jpg",
        "credit_id": "64abed99e24b93013aba2b09",
        "department": "Camera",
        "job": "Director of Photography"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 2031514,
        "known_for_department": "Crew",
        "name": "Phoebe Robinson-Galvin",
        "original_name": "Phoebe Robinson-Galvin",
        "popularity": 1.8293,
        "profile_path": "/nA7VqrZaY2ogcEt4890BOddVb08.jpg",
        "credit_id": "66c8b1032ff52224b78f14f7",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 234621,
        "known_for_department": "Crew",
        "name": "Alexander Bracq",
        "original_name": "Alexander Bracq",
        "popularity": 1.8549,
        "profile_path": "/bX55S9X9XHeL6HGuzrehJhqJpcQ.jpg",
        "credit_id": "66c68fe28b26f60aa6908250",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1486976,
        "known_for_department": "Crew",
        "name": "Christina Low",
        "original_name": "Christina Low",
        "popularity": 2.7199,
        "profile_path": "/c8mwAXsOPFxM6sXSVozUU0mEolJ.jpg",
        "credit_id": "66c3e879d2033884581abda6",
        "department": "Crew",
        "job": "Stunt Driver"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 142013,
        "known_for_department": "Directing",
        "name": "Gareth Evans",
        "original_name": "Gareth Evans",
        "popularity": 1.6318,
        "profile_path": "/2skpocnewERTPODPNvwgL5czLzG.jpg",
        "credit_id": "5e348fbdac8e6b0015c2a074",
        "department": "Directing",
        "job": "Director"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 142013,
        "known_for_department": "Directing",
        "name": "Gareth Evans",
        "original_name": "Gareth Evans",
        "popularity": 1.6318,
        "profile_path": "/2skpocnewERTPODPNvwgL5czLzG.jpg",
        "credit_id": "602fe8784ccc50003ca66be8",
        "department": "Production",
        "job": "Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1001662,
        "known_for_department": "Production",
        "name": "Aram Tertzakian",
        "original_name": "Aram Tertzakian",
        "popularity": 1.3613,
        "profile_path": "/plxkz2z01MyuDkP68TrUm3x8EY2.jpg",
        "credit_id": "602fe8b532cc2b004184e0a3",
        "department": "Production",
        "job": "Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 2524,
        "known_for_department": "Acting",
        "name": "Tom Hardy",
        "original_name": "Tom Hardy",
        "popularity": 19.516,
        "profile_path": "/d81K0RH8UX7tZj49tZaQhZ9ewH.jpg",
        "credit_id": "602fe88dcede69003f4c2ebc",
        "department": "Production",
        "job": "Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1095910,
        "known_for_department": "Writing",
        "name": "Ed Talfan",
        "original_name": "Ed Talfan",
        "popularity": 0.584,
        "profile_path": "/vUtTWBUdMKMMjbrYWemIBbem9IG.jpg",
        "credit_id": "602fe8a2d207f30040955147",
        "department": "Production",
        "job": "Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1992656,
        "known_for_department": "Crew",
        "name": "Cristian Knight",
        "original_name": "Cristian Knight",
        "popularity": 2.8434,
        "profile_path": "/8Vm03kiiiOoTlSJOrdmu7UlVyzR.jpg",
        "credit_id": "6775509f5b8f422b6012c0f0",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 15221,
        "known_for_department": "Sound",
        "name": "Tyler Bates",
        "original_name": "Tyler Bates",
        "popularity": 2.7172,
        "profile_path": "/vZiif8NFGpzCw5TWbagXIWygQM1.jpg",
        "credit_id": "677727e26d7ca00e787244bc",
        "department": "Sound",
        "job": "Original Music Composer"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 4307843,
        "known_for_department": "Editing",
        "name": "Sara Jones",
        "original_name": "Sara Jones",
        "popularity": 0.2474,
        "profile_path": null,
        "credit_id": "6777280f6d7ca00e787244c4",
        "department": "Editing",
        "job": "Editor"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 995066,
        "known_for_department": "Editing",
        "name": "Matt Platts-Mills",
        "original_name": "Matt Platts-Mills",
        "popularity": 0.5101,
        "profile_path": null,
        "credit_id": "6777281c82cce15a7674900b",
        "department": "Editing",
        "job": "Editor"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 2149037,
        "known_for_department": "Art",
        "name": "Tom Pearce",
        "original_name": "Tom Pearce",
        "popularity": 0.4478,
        "profile_path": null,
        "credit_id": "6777284f55d4b38f93667fb1",
        "department": "Art",
        "job": "Production Design"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1359416,
        "known_for_department": "Crew",
        "name": "Laura Swift",
        "original_name": "Laura Swift",
        "popularity": 4.4473,
        "profile_path": "/eMYeKkEYIQ2MCdw4puoHWo65xnn.jpg",
        "credit_id": "678e82b41c341c88996df2dc",
        "department": "Crew",
        "job": "Stunt Double"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 552394,
        "known_for_department": "Acting",
        "name": "Jack Wong Wai-Leung",
        "original_name": "Jack Wong Wai-Leung",
        "popularity": 1.017,
        "profile_path": "/gMNmPS6ljXJPkeiTpQrIPGCwdy2.jpg",
        "credit_id": "679067fe3479c48ccb28a9cc",
        "department": "Crew",
        "job": "Stunts"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 142013,
        "known_for_department": "Directing",
        "name": "Gareth Evans",
        "original_name": "Gareth Evans",
        "popularity": 1.6318,
        "profile_path": "/2skpocnewERTPODPNvwgL5czLzG.jpg",
        "credit_id": "6806dc27e3fac2f9028a2ced",
        "department": "Writing",
        "job": "Writer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1185945,
        "known_for_department": "Sound",
        "name": "Aria Prayogi",
        "original_name": "Aria Prayogi",
        "popularity": 0.571,
        "profile_path": "/yTQgRrtz0nJcysgF1k6SHOwUe5a.jpg",
        "credit_id": "6822c9f464e941df734b4943",
        "department": "Sound",
        "job": "Music"
      }
    ]
  },
  "images": {
    "backdrops": [],
    "logos": [],
    "posters": []
  },
  "videos": {
    "results": [
      {
        "iso_639_1": "en",
        "iso_3166_1": "US",
        "name": "Tom Hardy and Gareth Evans break down brutal fight scene from Havoc - Shot by Shot",
        "key": "_824u8P3tj8",
        "site": "YouTube",
        "size": 1080,
        "type": "Featurette",
        "official": true,
        "published_at": "2025-05-02T13:00:00.000Z",
        "id": "681583004eddcd14be96867d"
      },
      {
        "iso_639_1": "en",
        "iso_3166_1": "US",
        "name": "Official Trailer",
        "key": "6txjTWLoSc8",
        "site": "YouTube",
        "size": 1080,
        "type": "Trailer",
        "official": true,
        "published_at": "2025-04-07T15:00:01.000Z",
        "id": "67f3fc98ddf9194387d98ae8"
      },
      {
        "iso_639_1": "en",
        "iso_3166_1": "US",
        "name": "Official Teaser",
        "key": "HAQfDRvrU0s",
        "site": "YouTube",
        "size": 2160,
        "type": "Teaser",
        "official": true,
        "published_at": "2025-02-26T16:00:01.000Z",
        "id": "67bf3dca15b47f5e7e3d595f"
      }
    ]
  },
  "watch/providers": {
    "results": {
      "AD": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AD",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "AE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "AG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "AL": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AL",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "AO": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AO",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 4
          }
        ]
      },
      "AR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "AT": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AT",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "AU": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AU",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 49
          }
        ]
      },
      "AZ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=AZ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 2
          }
        ]
      },
      "BA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "BB": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BB",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "BE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "BG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "BH": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BH",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "BM": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BM",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "BO": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BO",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "BR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 2
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 43
          }
        ]
      },
      "BS": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BS",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "BY": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BY",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 5
          }
        ]
      },
      "BZ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=BZ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 7
          }
        ]
      },
      "CA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 109
          }
        ]
      },
      "CH": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CH",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "CI": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CI",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "CL": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CL",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "CM": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CM",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 4
          }
        ]
      },
      "CO": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CO",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 2
          }
        ]
      },
      "CR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "CU": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CU",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "CV": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CV",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "CY": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CY",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 7
          }
        ]
      },
      "CZ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=CZ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "DE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=DE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 101
          }
        ]
      },
      "DK": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=DK",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "DO": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=DO",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "DZ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=DZ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "EC": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=EC",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "EE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=EE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "EG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=EG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "ES": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=ES",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 61
          }
        ]
      },
      "FI": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=FI",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "FJ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=FJ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "FR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=FR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 73
          }
        ]
      },
      "GB": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GB",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 96
          }
        ]
      },
      "GF": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GF",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "GG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "GH": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GH",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "GI": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GI",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "GQ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GQ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "GR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "GT": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=GT",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "HK": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=HK",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "HN": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=HN",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "HR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=HR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "HU": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=HU",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "ID": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=ID",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "IE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=IE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "IL": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=IL",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "IN": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=IN",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "IQ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=IQ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "IS": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=IS",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "IT": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=IT",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 62
          }
        ]
      },
      "JM": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=JM",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "JO": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=JO",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "JP": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=JP",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 26
          }
        ]
      },
      "KE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=KE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "KR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=KR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 27
          }
        ]
      },
      "KW": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=KW",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "LB": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=LB",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "LC": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=LC",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "LI": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=LI",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "LT": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=LT",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "LU": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=LU",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 8
          }
        ]
      },
      "LV": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=LV",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "LY": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=LY",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "MA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "MC": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MC",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "MD": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MD",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "ME": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=ME",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 4
          }
        ]
      },
      "MG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 4
          }
        ]
      },
      "MK": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MK",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "ML": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=ML",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 5
          }
        ]
      },
      "MT": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MT",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "MU": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MU",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "MX": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MX",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 8
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 44
          }
        ]
      },
      "MY": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MY",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "MZ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=MZ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "NE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=NE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "NG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=NG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "NI": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=NI",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 11
          }
        ]
      },
      "NL": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=NL",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "NO": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=NO",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "NZ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=NZ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "OM": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=OM",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "PA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "PE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "PF": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PF",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "PH": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PH",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "PK": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PK",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "PL": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PL",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "PS": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PS",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "PT": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PT",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "PY": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=PY",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "QA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=QA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "RO": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=RO",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "RS": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=RS",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "SA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "SC": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SC",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "SE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "SG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "SI": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SI",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "SK": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SK",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "SM": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SM",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "SN": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SN",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "SV": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=SV",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "TC": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TC",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "TD": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TD",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 4
          }
        ]
      },
      "TH": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TH",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 1
          }
        ]
      },
      "TN": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TN",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "TR": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TR",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 2
          }
        ]
      },
      "TT": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TT",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "TW": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TW",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "TZ": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=TZ",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "UA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=UA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "UG": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=UG",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "US": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=US",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          },
          {
            "logo_path": "/dpR8r13zWDeUR0QkzWidrdMxa56.jpg",
            "provider_id": 1796,
            "provider_name": "Netflix Standard with Ads",
            "display_priority": 175
          }
        ]
      },
      "UY": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=UY",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "VE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=VE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "YE": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=YE",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "ZA": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=ZA",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "ZM": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=ZM",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 0
          }
        ]
      },
      "ZW": {
        "link": "https://www.themoviedb.org/movie/668489-havoc/watch?locale=ZW",
        "flatrate": [
          {
            "logo_path": "/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg",
            "provider_id": 8,
            "provider_name": "Netflix",
            "display_priority": 5
          }
        ]
      }
    }
  }
}
"""



"""
{
  "adult": false,
  "backdrop_path": "/x4lxFIhhrDI4nWtV8osnYwbGESV.jpg",
  "created_by": [
    {
      "id": 1205496,
      "credit_id": "5256da1c19c2956ff60b0d69",
      "name": "Christopher Lloyd",
      "original_name": "Christopher Lloyd",
      "gender": 2,
      "profile_path": "/jqdMLOeJvxp9cvJ3jZDtsoCK9fq.jpg"
    },
    {
      "id": 1215785,
      "credit_id": "5256da1c19c2956ff60b0d63",
      "name": "Steven Levitan",
      "original_name": "Steven Levitan",
      "gender": 2,
      "profile_path": "/xPT11b4ABpd9idTMBpoaaCH801J.jpg"
    }
  ],
  "episode_run_time": [
    25
  ],
  "first_air_date": "2009-09-23",
  "genres": [
    {
      "id": 35,
      "name": "Comedy"
    }
  ],
  "homepage": "http://abc.go.com/shows/modern-family",
  "id": 1421,
  "in_production": false,
  "languages": [
    "en"
  ],
  "last_air_date": "2020-04-08",
  "last_episode_to_air": {
    "id": 2200642,
    "name": "Finale (2)",
    "overview": "The entire family discovers saying goodbye is much harder than it seems.",
    "vote_average": 7.8,
    "vote_count": 14,
    "air_date": "2020-04-08",
    "episode_number": 18,
    "episode_type": "finale",
    "production_code": "BARG18",
    "runtime": 25,
    "season_number": 11,
    "show_id": 1421,
    "still_path": "/7ceJ4Qj0tev5zFHjFsout23p8dN.jpg"
  },
  "name": "Modern Family",
  "next_episode_to_air": null,
  "networks": [
    {
      "id": 2,
      "logo_path": "/2uy2ZWcplrSObIyt4x0Y9rkG6qO.png",
      "name": "ABC",
      "origin_country": "US"
    }
  ],
  "number_of_episodes": 250,
  "number_of_seasons": 11,
  "origin_country": [
    "US"
  ],
  "original_language": "en",
  "original_name": "Modern Family",
  "overview": "The Pritchett-Dunphy-Tucker clan is a wonderfully large and blended family. They give us an honest and often hilarious look into the sometimes warm, sometimes twisted, embrace of the modern family.",
  "popularity": 109.1244,
  "poster_path": "/k5Qg5rgPoKdh3yTJJrLtyoyYGwC.jpg",
  "production_companies": [
    {
      "id": 75003,
      "logo_path": null,
      "name": "Levitan Lloyd Productions",
      "origin_country": "US"
    },
    {
      "id": 1556,
      "logo_path": "/31h94rG9hzjprXoYNy3L1ErUya2.png",
      "name": "20th Century Fox Television",
      "origin_country": "US"
    },
    {
      "id": 122932,
      "logo_path": null,
      "name": "Steven Levitan Prods",
      "origin_country": "US"
    },
    {
      "id": 56390,
      "logo_path": null,
      "name": "Picador Productions",
      "origin_country": "US"
    }
  ],
  "production_countries": [
    {
      "iso_3166_1": "US",
      "name": "United States of America"
    }
  ],
  "seasons": [
    {
      "air_date": null,
      "episode_count": 63,
      "id": 147409,
      "name": "Specials",
      "overview": "",
      "poster_path": "/k6qEnQ8xyQnFvTcULDlrzETQRgs.jpg",
      "season_number": 0,
      "vote_average": 0
    },
    {
      "air_date": "2009-09-23",
      "episode_count": 24,
      "id": 3751,
      "name": "Season 1",
      "overview": "Modern Family takes a refreshing and funny view of what it means to raise a family in this hectic day and age.  Multi-cultural relationships, adoption, and same-sex marriage are just a few of the timely issues faced by the show’s three wildly-diverse broods.  No matter the size or shape, family always comes first in this hilariously “modern” look at life, love, and laughter.",
      "poster_path": "/i1KhQoI391KaEA5fKArrzoTvNDk.jpg",
      "season_number": 1,
      "vote_average": 7.6
    },
    {
      "air_date": "2010-09-22",
      "episode_count": 24,
      "id": 3752,
      "name": "Season 2",
      "overview": "While fledgling fathers Cameron and Mitchell struggle with learning the ropes of parenthood, long-time parents Claire and Phil try to keep the spice in their marriage amid the chaos of raising three challenging children. Meanwhile, family patriarch, Jay, has more than his hands full with his sexy, spirited wife, Gloria, and her sensitive son.",
      "poster_path": "/yvBc8av9K1g5QRtBDnP5xY69jb4.jpg",
      "season_number": 2,
      "vote_average": 7.5
    },
    {
      "air_date": "2011-09-21",
      "episode_count": 24,
      "id": 3753,
      "name": "Season 3",
      "overview": "As the extended Pritchett-Dunphy clan faces an uproariously unpredictable array of family vacations, holiday hassles, troublesome in-laws, and surprising secrets, they still somehow manage to thrive together as one big, loving family a even as they drive each other absolutely insane!",
      "poster_path": "/a4EJOG8VOV02veUIYtu4lX6FVdr.jpg",
      "season_number": 3,
      "vote_average": 7.5
    },
    {
      "air_date": "2012-09-26",
      "episode_count": 24,
      "id": 3755,
      "name": "Season 4",
      "overview": "With Jay and Gloria's baby on the way and Haley going off to college, the entire Pritchett-Dunphy clan faces some major surprises as they bicker and bond over house-flipping headaches, unwanted play dates, and everything from hot-tempered hormones to in utero karaoke.",
      "poster_path": "/pGXlhxw31fPJ6PwvzZdIRgaSHc2.jpg",
      "season_number": 4,
      "vote_average": 7.7
    },
    {
      "air_date": "2013-09-25",
      "episode_count": 24,
      "id": 3756,
      "name": "Season 5",
      "overview": "Wedding bells are ringing in season five of Modern Family. As Cam and Mitchell bicker over plans for their big day, the rest of the family has its hands full adapting to new jobs, new schools, and a new male nanny.  There are babysitting disasters, an anniversary to celebrate, misguided male bonding, and everything from high-stakes poker to high-maintenance in-laws.",
      "poster_path": "/sJ9PqGDvGIOwJfSle62yGGieZC1.jpg",
      "season_number": 5,
      "vote_average": 7.7
    },
    {
      "air_date": "2014-09-24",
      "episode_count": 24,
      "id": 62023,
      "name": "Season 6",
      "overview": "The honeymoon is over, but the laughs continue in season six of Modern Family. As freshly hitched Cam and Mitch acclimate to the realities of wedded bliss, Phil and Claire find their marriage stressed by annoying neighbors, Thanksgiving dinner gone awry and Claire's online snooping. Meanwhile, a spy-camera drone wreaks havoc in Jay and Gloria's backyard and a close call on the highway leads to amusing changes in various members of the Pritchett-Dunphy clan.",
      "poster_path": "/5cUUBx6iUrWFvJ8BmP2d4SATy1G.jpg",
      "season_number": 6,
      "vote_average": 7.4
    },
    {
      "air_date": "2015-09-23",
      "episode_count": 22,
      "id": 68804,
      "name": "Season 7",
      "overview": "Enjoy a new chapter of love and laughter with the Seventh Season of the show. Quackery rules the roost when Phil adopts a trio of orphan ducklings and the rebellious Dunphy kids spread their wings. Meanwhile, Cam and Mitchell face financial hurdles and wild frat boys, Jay and Gloria 1farm2 out Joe2s preschool education and Manny leaps into the dating game. But will the big question finally be answered: are Haley and Andy destined to be together.",
      "poster_path": "/825aF6sf43gIyPsX0oeNNhqMzuH.jpg",
      "season_number": 7,
      "vote_average": 7.4
    },
    {
      "air_date": "2016-09-21",
      "episode_count": 22,
      "id": 78515,
      "name": "Season 8",
      "overview": "The household hilarity continues as the Dunphy clan is wrapping up a Big Apple adventure. Back at home, Claire struggles to keep order at Pritchett's Closets while Phil and Jay go into business together. Gloria's hot sauce business heats up, as Cam and Mitchell deal with their maturing tween, Lily. Meanwhile, Manny and Luke fumble through their senior year of high school.",
      "poster_path": "/coOmsK9sWpScfLDlRXQ2xUJdzZ8.jpg",
      "season_number": 8,
      "vote_average": 7
    },
    {
      "air_date": "2017-09-27",
      "episode_count": 22,
      "id": 91749,
      "name": "Season 9",
      "overview": "The outrageous ninth season revolves around the blended Pritchett-Dunphy-Tucker clan, headed by Jay Pritchett. Jay and his vivacious second wife Gloria are raising their young son Joe and Gloria's college bound son Manny. Meanwhile, Jay's grown daughter Claire and her husband Phil are becoming empty nesters, while Clare's brother Mitchell and his husband Cameron fumble through nurturing their gifted daughter Lily.",
      "poster_path": "/innrJlIzs0mktUCcQaGvMYMu4pk.jpg",
      "season_number": 9,
      "vote_average": 6.8
    },
    {
      "air_date": "2018-09-26",
      "episode_count": 22,
      "id": 108448,
      "name": "Season 10",
      "overview": "As the tenth season kicks off, Jay's slated to be grand marshal in a Fourth of July parade, prompting the Pritchett-Dunphy-Tuckers to set off a few too many fireworks. Phil stumbles into a new career opportunity, while Claire grapples with her potentially changing role in the family. Meanwhile, Gloria obsesses over Manny's relationship and Joe's extracurricular activities. The extended family deals with death, but they also evolve, with more laughs than ever.",
      "poster_path": "/4aksppat5nq4IO08crJwcL2bbrv.jpg",
      "season_number": 10,
      "vote_average": 6.9
    },
    {
      "air_date": "2019-09-25",
      "episode_count": 18,
      "id": 127046,
      "name": "Season 11",
      "overview": "Jay and Gloria are navigating life with their youngest son, Joe, while Manny has headed off to college to explore the world on his own terms. Meanwhile, Claire and Phil have officially lost their status as empty-nesters when Haley started her own family and moved back home with her new husband, Dylan, and a set of twins. Luke, is now looking to his next move; and Alex is learning how to balance life outside of academia. Then there’s Mitchell and Cameron, who are still working to understand their gifted teenage daughter, Lily, and juggle busy careers.",
      "poster_path": "/sMIhyJw2s1PRS8S7UtVnQrHAlNB.jpg",
      "season_number": 11,
      "vote_average": 7.3
    }
  ],
  "spoken_languages": [
    {
      "english_name": "English",
      "iso_639_1": "en",
      "name": "English"
    }
  ],
  "status": "Ended",
  "tagline": "One big (straight, gay, multi-cultural, traditional) happy family.",
  "type": "Scripted",
  "vote_average": 7.873,
  "vote_count": 2958,
  "credits": {
    "cast": [
      {
        "adult": false,
        "gender": 2,
        "id": 18977,
        "known_for_department": "Acting",
        "name": "Ed O'Neill",
        "original_name": "Ed O'Neill",
        "popularity": 3.1404,
        "profile_path": "/4RrxSno3UEtGWuMm4yJoaFzckpL.jpg",
        "character": "Jay Pritchett",
        "credit_id": "5256da1419c2956ff60b0a7b",
        "order": 0
      },
      {
        "adult": false,
        "gender": 1,
        "id": 63522,
        "known_for_department": "Acting",
        "name": "Sofía Vergara",
        "original_name": "Sofía Vergara",
        "popularity": 5.1415,
        "profile_path": "/l79eVtn6bSOaiq7R0UGu60foMrK.jpg",
        "character": "Gloria Delgado-Pritchett",
        "credit_id": "5256da1419c2956ff60b0ac7",
        "order": 1
      },
      {
        "adult": false,
        "gender": 1,
        "id": 31171,
        "known_for_department": "Acting",
        "name": "Julie Bowen",
        "original_name": "Julie Bowen",
        "popularity": 4.591,
        "profile_path": "/5ewqnbPAY0EzZObGHIKU4VsCanD.jpg",
        "character": "Claire Dunphy",
        "credit_id": "5256da1519c2956ff60b0b81",
        "order": 2
      },
      {
        "adult": false,
        "gender": 2,
        "id": 15232,
        "known_for_department": "Acting",
        "name": "Ty Burrell",
        "original_name": "Ty Burrell",
        "popularity": 3.81,
        "profile_path": "/zXrrbvW2ZKHYHbhujDj8aBlO4yx.jpg",
        "character": "Phil Dunphy",
        "credit_id": "5256da1419c2956ff60b0b13",
        "order": 3
      },
      {
        "adult": false,
        "gender": 2,
        "id": 204815,
        "known_for_department": "Acting",
        "name": "Jesse Tyler Ferguson",
        "original_name": "Jesse Tyler Ferguson",
        "popularity": 2.4791,
        "profile_path": "/zeWJZZrCtzUZqyOxOQB4xzuSup1.jpg",
        "character": "Mitchell Pritchett",
        "credit_id": "5256da1519c2956ff60b0b39",
        "order": 4
      },
      {
        "adult": false,
        "gender": 2,
        "id": 156962,
        "known_for_department": "Acting",
        "name": "Eric Stonestreet",
        "original_name": "Eric Stonestreet",
        "popularity": 2.7992,
        "profile_path": "/lz0m88IjLZ8OcEHU2jhPvubcr7k.jpg",
        "character": "Cameron Tucker",
        "credit_id": "5256da1719c2956ff60b0c13",
        "order": 5
      },
      {
        "adult": false,
        "gender": 1,
        "id": 91351,
        "known_for_department": "Acting",
        "name": "Sarah Hyland",
        "original_name": "Sarah Hyland",
        "popularity": 4.4364,
        "profile_path": "/sjwIiQWLMyBQOLhARj1Ww3imDcL.jpg",
        "character": "Haley Dunphy",
        "credit_id": "5256da1519c2956ff60b0bbf",
        "order": 6
      },
      {
        "adult": false,
        "gender": 1,
        "id": 42160,
        "known_for_department": "Acting",
        "name": "Ariel Winter",
        "original_name": "Ariel Winter",
        "popularity": 4.7132,
        "profile_path": "/1h0XaXnieP5CdTAeRGuALBJmD4R.jpg",
        "character": "Alex Dunphy",
        "credit_id": "5256da1719c2956ff60b0c5b",
        "order": 7
      },
      {
        "adult": false,
        "gender": 2,
        "id": 147710,
        "known_for_department": "Acting",
        "name": "Nolan Gould",
        "original_name": "Nolan Gould",
        "popularity": 2.6895,
        "profile_path": "/rnGYwEUairpCPmGIJcIwD86K9rI.jpg",
        "character": "Luke Dunphy",
        "credit_id": "5256da1819c2956ff60b0c83",
        "order": 8
      },
      {
        "adult": false,
        "gender": 2,
        "id": 206737,
        "known_for_department": "Acting",
        "name": "Rico Rodriguez",
        "original_name": "Rico Rodriguez",
        "popularity": 1.8327,
        "profile_path": "/wgx5nThAUqRUVTPgOGsWcwQeaYy.jpg",
        "character": "Manny Delgado",
        "credit_id": "5256da1619c2956ff60b0be7",
        "order": 9
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1224228,
        "known_for_department": "Acting",
        "name": "Aubrey Anderson-Emmons",
        "original_name": "Aubrey Anderson-Emmons",
        "popularity": 0.5213,
        "profile_path": "/rgTjphNXZoHtR8LjGgmT9AvXvcX.jpg",
        "character": "Lily Tucker-Pritchett",
        "credit_id": "5256da1c19c2956ff60b0d07",
        "order": 11
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1676910,
        "known_for_department": "Acting",
        "name": "Jeremy Maguire",
        "original_name": "Jeremy Maguire",
        "popularity": 0.3889,
        "profile_path": "/9ivrqXhtohfeEJXC6g415s3eeRm.jpg",
        "character": "Joe Pritchett",
        "credit_id": "57d31b28c3a3681ff7000de9",
        "order": 13
      },
      {
        "adult": false,
        "gender": 2,
        "id": 967692,
        "known_for_department": "Acting",
        "name": "Reid Ewing",
        "original_name": "Reid Ewing",
        "popularity": 1.0099,
        "profile_path": "/vvehuMULozr81NCCDEql1pWIrvS.jpg",
        "character": "Dylan Marshall",
        "credit_id": "5256da1c19c2956ff60b0d35",
        "order": 14
      }
    ],
    "crew": [
      {
        "adult": false,
        "gender": 2,
        "id": 1215780,
        "known_for_department": "Writing",
        "name": "Jeffrey Richman",
        "original_name": "Jeffrey Richman",
        "popularity": 0.6983,
        "profile_path": "/gUJpSfoxvXlF8VRpUlTardxBA0J.jpg",
        "credit_id": "5256da2519c2956ff60b10e5",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1224216,
        "known_for_department": "Writing",
        "name": "Abraham Higginbotham",
        "original_name": "Abraham Higginbotham",
        "popularity": 0.7154,
        "profile_path": "/9RtTQjuzrSD4bGUfqHm9LGyepP7.jpg",
        "credit_id": "5256da2519c2956ff60b1115",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 590342,
        "known_for_department": "Production",
        "name": "Jeffrey Morton",
        "original_name": "Jeffrey Morton",
        "popularity": 0.3036,
        "profile_path": null,
        "credit_id": "57016af69251416070000579",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1224206,
        "known_for_department": "Writing",
        "name": "Danny Zuker",
        "original_name": "Danny Zuker",
        "popularity": 0.4166,
        "profile_path": "/15DVC0szoo5yweZISpuK459N33g.jpg",
        "credit_id": "5256da2319c2956ff60b0f91",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1224210,
        "known_for_department": "Writing",
        "name": "Paul Corrigan",
        "original_name": "Paul Corrigan",
        "popularity": 1.0616,
        "profile_path": "/1CrWnw3EX1ShQlBRxbFKqSdXvZy.jpg",
        "credit_id": "5256da2319c2956ff60b1025",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1224209,
        "known_for_department": "Writing",
        "name": "Brad Walsh",
        "original_name": "Brad Walsh",
        "popularity": 0.7666,
        "profile_path": "/hnlf6I4UfTRY8mviyhE1fAoGPcQ.jpg",
        "credit_id": "5256da2319c2956ff60b1055",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1205496,
        "known_for_department": "Writing",
        "name": "Christopher Lloyd",
        "original_name": "Christopher Lloyd",
        "popularity": 0.295,
        "profile_path": "/jqdMLOeJvxp9cvJ3jZDtsoCK9fq.jpg",
        "credit_id": "5256da2319c2956ff60b0f61",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1215785,
        "known_for_department": "Writing",
        "name": "Steven Levitan",
        "original_name": "Steven Levitan",
        "popularity": 0.7659,
        "profile_path": "/xPT11b4ABpd9idTMBpoaaCH801J.jpg",
        "credit_id": "5256da2219c2956ff60b0f31",
        "department": "Production",
        "job": "Executive Producer"
      },
      {
        "adult": true,
        "gender": 2,
        "id": 43422,
        "known_for_department": "Camera",
        "name": "James R. Bagdonas",
        "original_name": "James R. Bagdonas",
        "popularity": 1.4,
        "profile_path": "/xiEqsNlhxP1JsYmxumluiqEjR99.jpg",
        "credit_id": "570171449251416070000672",
        "department": "Camera",
        "job": "Director of Photography"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1528193,
        "known_for_department": "Production",
        "name": "Jeff Greenberg",
        "original_name": "Jeff Greenberg",
        "popularity": 0.7079,
        "profile_path": null,
        "credit_id": "5701711c925141607f0005f3",
        "department": "Production",
        "job": "Casting"
      },
      {
        "adult": false,
        "gender": 1,
        "id": 1392978,
        "known_for_department": "Directing",
        "name": "Iwona Sapienza",
        "original_name": "Iwona Sapienza",
        "popularity": 0.4981,
        "profile_path": "/yL6TzbgdgyP9S8lQcqK6HIWWB2n.jpg",
        "credit_id": "570174539251416072000659",
        "department": "Directing",
        "job": "Script Supervisor"
      },
      {
        "adult": false,
        "gender": 0,
        "id": 1148734,
        "known_for_department": "Production",
        "name": "Allen Hooper",
        "original_name": "Allen Hooper",
        "popularity": 0.2917,
        "profile_path": null,
        "credit_id": "57017485c3a36856ab00067f",
        "department": "Production",
        "job": "Casting Associate"
      },
      {
        "adult": false,
        "gender": 2,
        "id": 1396413,
        "known_for_department": "Sound",
        "name": "Dean Okrand",
        "original_name": "Dean Okrand",
        "popularity": 0.9901,
        "profile_path": null,
        "credit_id": "570174b89251416077000754",
        "department": "Sound",
        "job": "Sound Re-Recording Mixer"
      }
    ]
  },
  "external_ids": {
    "imdb_id": "tt1442437",
    "freebase_mid": "/m/05zr0xl",
    "freebase_id": "",
    "tvdb_id": 95011,
    "tvrage_id": 22622,
    "wikidata_id": "Q16756",
    "facebook_id": "ModernFamily",
    "instagram_id": "abcmodernfam",
    "twitter_id": "ModernFam"
  },
  "videos": {
    "results": [
      {
        "iso_639_1": "en",
        "iso_3166_1": "US",
        "name": "The Modern Family Bloopers",
        "key": "ZWXyAW-ayL4",
        "site": "YouTube",
        "size": 1080,
        "type": "Bloopers",
        "official": false,
        "published_at": "2018-08-10T10:16:42.000Z",
        "id": "65ef3585e2586001624cee7b"
      },
      {
        "iso_639_1": "en",
        "iso_3166_1": "US",
        "name": "Modern Family Seasons 1-6 (Trailer)",
        "key": "rbpTUPisA78",
        "site": "YouTube",
        "size": 1080,
        "type": "Trailer",
        "official": false,
        "published_at": "2018-02-15T16:26:57.000Z",
        "id": "657d231f7ad08c06974faa78"
      },
      {
        "iso_639_1": "en",
        "iso_3166_1": "US",
        "name": "Modern Family Season 7 Promo (HD)",
        "key": "U7dLXjZfXV8",
        "site": "YouTube",
        "size": 720,
        "type": "Teaser",
        "official": false,
        "published_at": "2015-09-02T01:50:14.000Z",
        "id": "5caeff0c9251412fa621b572"
      }
    ]
  },
  "watch/providers": {
    "results": {
      "AD": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=AD",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 7
          }
        ]
      },
      "AL": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=AL",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 7
          }
        ]
      },
      "AR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=AR",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "AT": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=AT",
        "buy": [
          {
            "logo_path": "/seGSXajazLMCKGB5hnRCidtjay1.jpg",
            "provider_id": 10,
            "provider_name": "Amazon Video",
            "display_priority": 3
          },
          {
            "logo_path": "/8z7rC8uIDaTM91X0ZfkRf04ydj2.jpg",
            "provider_id": 3,
            "provider_name": "Google Play Movies",
            "display_priority": 7
          },
          {
            "logo_path": "/cBN4jd4wPq6on0kESiTlevqvlnL.jpg",
            "provider_id": 20,
            "provider_name": "maxdome Store",
            "display_priority": 14
          }
        ],
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "AU": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=AU",
        "buy": [
          {
            "logo_path": "/9ghgSC0MA082EL6HLCW3GalykFD.jpg",
            "provider_id": 2,
            "provider_name": "Apple TV",
            "display_priority": 9
          },
          {
            "logo_path": "/5vfrJQgNe9UnHVgVNAwZTy0Jo9o.jpg",
            "provider_id": 68,
            "provider_name": "Microsoft Store",
            "display_priority": 16
          },
          {
            "logo_path": "/9B7l9ZSos54kFrZbliVExt2z9C9.jpg",
            "provider_id": 436,
            "provider_name": "Fetch TV",
            "display_priority": 30
          }
        ],
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "BA": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=BA",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 7
          }
        ]
      },
      "BE": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=BE",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "BG": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=BG",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 16
          }
        ]
      },
      "BO": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=BO",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "BR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=BR",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "BZ": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=BZ",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "CA": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=CA",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ],
        "buy": [
          {
            "logo_path": "/9ghgSC0MA082EL6HLCW3GalykFD.jpg",
            "provider_id": 2,
            "provider_name": "Apple TV",
            "display_priority": 6
          }
        ]
      },
      "CH": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=CH",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ],
        "buy": [
          {
            "logo_path": "/8z7rC8uIDaTM91X0ZfkRf04ydj2.jpg",
            "provider_id": 3,
            "provider_name": "Google Play Movies",
            "display_priority": 5
          },
          {
            "logo_path": "/6AKbY2ayaEuH4zKg2prqoVQ9iaY.jpg",
            "provider_id": 130,
            "provider_name": "Sky Store",
            "display_priority": 15
          }
        ]
      },
      "CL": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=CL",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "CO": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=CO",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "CR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=CR",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "CZ": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=CZ",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "DE": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=DE",
        "buy": [
          {
            "logo_path": "/9ghgSC0MA082EL6HLCW3GalykFD.jpg",
            "provider_id": 2,
            "provider_name": "Apple TV",
            "display_priority": 4
          },
          {
            "logo_path": "/seGSXajazLMCKGB5hnRCidtjay1.jpg",
            "provider_id": 10,
            "provider_name": "Amazon Video",
            "display_priority": 9
          },
          {
            "logo_path": "/cBN4jd4wPq6on0kESiTlevqvlnL.jpg",
            "provider_id": 20,
            "provider_name": "maxdome Store",
            "display_priority": 19
          },
          {
            "logo_path": "/nCsFBTEmlCMc5NA4fwPuluTz6AO.jpg",
            "provider_id": 178,
            "provider_name": "MagentaTV",
            "display_priority": 25
          },
          {
            "logo_path": "/5vfrJQgNe9UnHVgVNAwZTy0Jo9o.jpg",
            "provider_id": 68,
            "provider_name": "Microsoft Store",
            "display_priority": 32
          },
          {
            "logo_path": "/dKh2TJ9lTWV0UIcDQGMnMyQ8AIN.jpg",
            "provider_id": 1993,
            "provider_name": "Videoload",
            "display_priority": 143
          },
          {
            "logo_path": "/xo4zowa5gbKT4z65ZathH6H4Cdg.jpg",
            "provider_id": 2209,
            "provider_name": "Freenet meinVOD",
            "display_priority": 171
          }
        ],
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "DK": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=DK",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "DO": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=DO",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 23
          }
        ]
      },
      "EC": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=EC",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "EE": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=EE",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 22
          }
        ]
      },
      "EG": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=EG",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 44
          }
        ]
      },
      "ES": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=ES",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ]
      },
      "FI": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=FI",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "FR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=FR",
        "buy": [
          {
            "logo_path": "/9ghgSC0MA082EL6HLCW3GalykFD.jpg",
            "provider_id": 2,
            "provider_name": "Apple TV",
            "display_priority": 4
          }
        ],
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ]
      },
      "GB": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=GB",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ],
        "buy": [
          {
            "logo_path": "/9ghgSC0MA082EL6HLCW3GalykFD.jpg",
            "provider_id": 2,
            "provider_name": "Apple TV",
            "display_priority": 4
          },
          {
            "logo_path": "/seGSXajazLMCKGB5hnRCidtjay1.jpg",
            "provider_id": 10,
            "provider_name": "Amazon Video",
            "display_priority": 7
          },
          {
            "logo_path": "/6AKbY2ayaEuH4zKg2prqoVQ9iaY.jpg",
            "provider_id": 130,
            "provider_name": "Sky Store",
            "display_priority": 16
          }
        ]
      },
      "GR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=GR",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 19
          }
        ]
      },
      "GT": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=GT",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ]
      },
      "HK": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=HK",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 31
          }
        ]
      },
      "HN": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=HN",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "HR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=HR",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 29
          }
        ]
      },
      "HU": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=HU",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "ID": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=ID",
        "ads": [
          {
            "logo_path": "/5B0WB5ohGxRtON8qCuCkGgGCO18.jpg",
            "provider_id": 122,
            "provider_name": "Hotstar",
            "display_priority": 3
          }
        ],
        "flatrate": [
          {
            "logo_path": "/5B0WB5ohGxRtON8qCuCkGgGCO18.jpg",
            "provider_id": 122,
            "provider_name": "Hotstar",
            "display_priority": 3
          }
        ]
      },
      "IE": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=IE",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ],
        "buy": [
          {
            "logo_path": "/6AKbY2ayaEuH4zKg2prqoVQ9iaY.jpg",
            "provider_id": 130,
            "provider_name": "Sky Store",
            "display_priority": 9
          }
        ]
      },
      "IN": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=IN",
        "flatrate": [
          {
            "logo_path": "/8b7I3EzWGQqi0Y1sJBmvQPf58Yd.jpg",
            "provider_id": 2336,
            "provider_name": "JioHotstar",
            "display_priority": 5
          },
          {
            "logo_path": "/1tCAM3WVOl0xknuwVc0v1LBWZNV.jpg",
            "provider_id": 614,
            "provider_name": "VI movies and tv",
            "display_priority": 38
          }
        ]
      },
      "IS": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=IS",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ]
      },
      "IT": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=IT",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ]
      },
      "JM": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=JM",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 25
          }
        ]
      },
      "JP": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=JP",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "KR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=KR",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "LC": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=LC",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 13
          }
        ]
      },
      "LI": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=LI",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 24
          }
        ]
      },
      "LT": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=LT",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 23
          }
        ]
      },
      "LU": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=LU",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 3
          }
        ]
      },
      "LV": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=LV",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 22
          }
        ]
      },
      "ME": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=ME",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ]
      },
      "MK": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=MK",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 7
          }
        ]
      },
      "MT": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=MT",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 7
          }
        ]
      },
      "MX": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=MX",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "MY": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=MY",
        "flatrate": [
          {
            "logo_path": "/5B0WB5ohGxRtON8qCuCkGgGCO18.jpg",
            "provider_id": 122,
            "provider_name": "Hotstar",
            "display_priority": 0
          }
        ],
        "ads": [
          {
            "logo_path": "/5B0WB5ohGxRtON8qCuCkGgGCO18.jpg",
            "provider_id": 122,
            "provider_name": "Hotstar",
            "display_priority": 0
          }
        ]
      },
      "NI": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=NI",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "NL": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=NL",
        "buy": [
          {
            "logo_path": "/5vfrJQgNe9UnHVgVNAwZTy0Jo9o.jpg",
            "provider_id": 68,
            "provider_name": "Microsoft Store",
            "display_priority": 15
          }
        ],
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "NO": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=NO",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          },
          {
            "logo_path": "/tpfmd22xEapb1aW2gzjSM5104rx.jpg",
            "provider_id": 431,
            "provider_name": "TV 2 Play",
            "display_priority": 18
          }
        ]
      },
      "NZ": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=NZ",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "PA": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=PA",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 26
          }
        ]
      },
      "PE": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=PE",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "PH": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=PH",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 28
          }
        ]
      },
      "PL": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=PL",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "PT": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=PT",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "PY": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=PY",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "RO": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=RO",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "RS": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=RS",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 7
          }
        ]
      },
      "RU": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=RU",
        "flatrate": [
          {
            "logo_path": "/51wuCkUdkEQTUtB8TrtZzzxp3Tj.jpg",
            "provider_id": 117,
            "provider_name": "Kinopoisk",
            "display_priority": 21
          }
        ],
        "buy": [
          {
            "logo_path": "/51wuCkUdkEQTUtB8TrtZzzxp3Tj.jpg",
            "provider_id": 117,
            "provider_name": "Kinopoisk",
            "display_priority": 21
          }
        ]
      },
      "SE": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=SE",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "SG": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=SG",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "SI": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=SI",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 7
          }
        ]
      },
      "SK": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=SK",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "SM": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=SM",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 24
          }
        ]
      },
      "SV": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=SV",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 26
          }
        ]
      },
      "TH": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=TH",
        "ads": [
          {
            "logo_path": "/5B0WB5ohGxRtON8qCuCkGgGCO18.jpg",
            "provider_id": 122,
            "provider_name": "Hotstar",
            "display_priority": 0
          }
        ],
        "flatrate": [
          {
            "logo_path": "/5B0WB5ohGxRtON8qCuCkGgGCO18.jpg",
            "provider_id": 122,
            "provider_name": "Hotstar",
            "display_priority": 0
          }
        ]
      },
      "TR": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=TR",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 0
          }
        ]
      },
      "TT": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=TT",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 14
          }
        ]
      },
      "TW": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=TW",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 2
          }
        ]
      },
      "US": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=US",
        "flatrate": [
          {
            "logo_path": "/bxBlRPEPpMVDc4jMhSrTf2339DW.jpg",
            "provider_id": 15,
            "provider_name": "Hulu",
            "display_priority": 7
          },
          {
            "logo_path": "/2aGrp1xw3qhwCYvNGAJZPdjfeeX.jpg",
            "provider_id": 386,
            "provider_name": "Peacock Premium",
            "display_priority": 14
          },
          {
            "logo_path": "/cZvP3XsDKlHFhNIyHYCVPStXT5l.jpg",
            "provider_id": 506,
            "provider_name": "TBS",
            "display_priority": 121
          },
          {
            "logo_path": "/drPlq5beqXtBaP7MNs8W616YRhm.jpg",
            "provider_id": 387,
            "provider_name": "Peacock Premium Plus",
            "display_priority": 270
          }
        ],
        "buy": [
          {
            "logo_path": "/seGSXajazLMCKGB5hnRCidtjay1.jpg",
            "provider_id": 10,
            "provider_name": "Amazon Video",
            "display_priority": 5
          },
          {
            "logo_path": "/9ghgSC0MA082EL6HLCW3GalykFD.jpg",
            "provider_id": 2,
            "provider_name": "Apple TV",
            "display_priority": 6
          },
          {
            "logo_path": "/8z7rC8uIDaTM91X0ZfkRf04ydj2.jpg",
            "provider_id": 3,
            "provider_name": "Google Play Movies",
            "display_priority": 15
          },
          {
            "logo_path": "/19fkcOz0xeUgCVW8tO85uOYnYK9.jpg",
            "provider_id": 7,
            "provider_name": "Fandango At Home",
            "display_priority": 36
          }
        ]
      },
      "UY": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=UY",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 26
          }
        ]
      },
      "VE": {
        "link": "https://www.themoviedb.org/tv/1421-modern-family/watch?locale=VE",
        "flatrate": [
          {
            "logo_path": "/97yvRBw1GzX7fXprcF80er19ot.jpg",
            "provider_id": 337,
            "provider_name": "Disney Plus",
            "display_priority": 1
          }
        ]
      }
    }
  }
}
"""