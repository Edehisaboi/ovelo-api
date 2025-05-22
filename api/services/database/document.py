from typing import List, Dict
from datetime import datetime, timezone
from api.services.tmdb.models import Season, MovieDetails, TVDetails, TranscriptChunk


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
        movie: MovieDetails
    ) -> Dict:
        """
        Construct a movie document for MongoDB insertion.
        
        Args:
            movie: MovieDetails object containing all movie information
            
        Returns:
            Dict: Movie document ready for MongoDB insertion
        """
        return {
            "tmdb_id":            movie.id,
            "adult":              movie.adult,
            "title":              movie.title,
            "original_title":     movie.original_title,
            "overview":           movie.overview,
            "poster_path":        movie.poster_path,
            "backdrop_path":      movie.backdrop_path,
            "release_date":       movie.release_date,
            "runtime":            movie.runtime,
            "genres":             [g.name for g in movie.genres],
            "original_language":  movie.original_language,
            "spoken_languages":   [
                {
                    "iso_639_1":    lang.iso_639_1,
                    "name":         lang.name,
                    "english_name": lang.english_name
                }
                for lang in movie.spoken_languages
            ],
            "origin_country":     movie.origin_country,
            "external_ids":       {
                "imdb_id":        movie.external_ids.imdb_id,
                "facebook_id":    movie.external_ids.facebook_id,
                "instagram_id":   movie.external_ids.instagram_id,
                "twitter_id":     movie.external_ids.twitter_id
            },
            "status":             movie.status,
            "tagline":            movie.tagline,
            "vote_average":       movie.vote_average,
            "vote_count":         movie.vote_count,
            "cast":               [
                {
                    "name":                 member.name,
                    "character":            member.character,
                    "known_for_department": member.known_for_department
                }
                for member in movie.credits.cast
            ],
            "crew":               [
                {
                    "name":         member.name,
                    "job":          member.job,
                    "department":   member.department
                }
                for member in movie.credits.crew
            ],
            "images":             {
                "backdrops": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in movie.images.backdrops
                ],
                "posters": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in movie.images.posters
                ],
                "logos": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in movie.images.logos
                ]
            },
            "videos":             [
                {
                    "key":        video.key,
                    "name":       video.name,
                    "site":       video.site,
                    "size":       video.size,
                    "type":       video.type,
                    "official":   video.official,
                    "iso_639_1":  video.iso_639_1,
                    "iso_3166_1": video.iso_3166_1
                }
                for video in movie.videos.results
            ],
            "watch_providers":    {
                country: {
                    "link": providers.link,
                    "flatrate": [
                        {
                            "display_priority": provider.display_priority,
                            "logo_path":        provider.logo_path,
                            "provider_name":    provider.provider_name
                        }
                        for provider in providers.flatrate
                    ] if providers.flatrate else None
                }
                for country, providers in movie.watch_providers.results.items()
            },
            "transcript_chunks":  movie.transcript_chunks,
            "embedding_model":    movie.embedding_model,
            "created_at":         self.created_at,
            "updated_at":         self.updated_at
        }

    def tv_show_document(
        self,
        tv_show: TVDetails
    ) -> Dict:
        """
        Construct a TV show document for MongoDB insertion.
        
        Args:
            tv_show: TVDetails object containing all TV show information
            
        Returns:
            Dict: TV show document ready for MongoDB insertion
        """
        return {
            "tmdb_id":            tv_show.id,
            "adult":              tv_show.adult,
            "name":               tv_show.name,
            "original_name":      tv_show.original_name,
            "overview":           tv_show.overview,
            "poster_path":        tv_show.poster_path,
            "backdrop_path":      tv_show.backdrop_path,
            "first_air_date":     tv_show.first_air_date,
            "last_air_date":      tv_show.last_air_date,
            "number_of_seasons":  tv_show.number_of_seasons,
            "number_of_episodes": tv_show.number_of_episodes,
            "genres":             [g.name for g in tv_show.genres],
            "spoken_languages":   [
                {
                    "iso_639_1":    lang.iso_639_1,
                    "name":         lang.name,
                    "english_name": lang.english_name
                }
                for lang in tv_show.spoken_languages
            ],
            "origin_country":     tv_show.origin_country,
            "external_ids":       {
                "imdb_id":        tv_show.external_ids.imdb_id,
                "facebook_id":    tv_show.external_ids.facebook_id,
                "instagram_id":   tv_show.external_ids.instagram_id,
                "twitter_id":     tv_show.external_ids.twitter_id
            },
            "status":             tv_show.status,
            "tagline":            tv_show.tagline,
            "in_production":      tv_show.in_production,
            "vote_average":       tv_show.vote_average,
            "vote_count":         tv_show.vote_count,
            "cast":               [
                {
                    "name":                 member.name,
                    "character":            member.character,
                    "known_for_department": member.known_for_department
                }
                for member in tv_show.credits.cast
            ],
            "crew":               [
                {
                    "name":         member.name,
                    "job":          member.job,
                    "department":   member.department
                }
                for member in tv_show.credits.crew
            ],
            "images":             {
                "backdrops": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in tv_show.images.backdrops
                ],
                "posters": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in tv_show.images.posters
                ],
                "logos": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in tv_show.images.logos
                ]
            },
            "videos":             [
                {
                    "key":        video.key,
                    "name":       video.name,
                    "site":       video.site,
                    "size":       video.size,
                    "type":       video.type,
                    "official":   video.official,
                    "iso_639_1":  video.iso_639_1,
                    "iso_3166_1": video.iso_3166_1
                }
                for video in tv_show.videos.results
            ],
            "watch_providers":    {
                country: {
                    "link": providers.link,
                    "flatrate": [
                        {
                            "display_priority": provider.display_priority,
                            "logo_path":        provider.logo_path,
                            "provider_name":    provider.provider_name
                        }
                        for provider in providers.flatrate
                    ] if providers.flatrate else None
                }
                for country, providers in tv_show.watch_providers.results.items()
            },
            "seasons":            [
                {
                    "season_number":  season.season_number,
                    "name":           season.name,
                    "overview":       season.overview,
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
                                    "embedding":  chunk.embedding
                                }
                                for chunk in episode.transcript_chunks
                            ]
                        }
                        for episode in season.episodes
                    ]
                }
                for season in tv_show.seasons
            ],
            "embedding_model":    tv_show.embedding_model,
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
    }
  ],
  "production_countries": [
    {
      "iso_3166_1": "GB",
      "name": "United Kingdom"
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
      "overview": "Modern Family takes a refreshing and funny view of what it means to raise a family in this hectic day and age.  Multi-cultural relationships, adoption, and same-sex marriage are just a few of the timely issues faced by the show's three wildly-diverse broods.  No matter the size or shape, family always comes first in this hilariously "modern" look at life, love, and laughter.",
      "poster_path": "/i1KhQoI391KaEA5fKArrzoTvNDk.jpg",
      "season_number": 1,
      "vote_average": 7.6
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
      }
    }
  }
}
"""