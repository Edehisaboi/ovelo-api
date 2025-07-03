from typing import Dict, Any

from api.services.tmdb.model import MovieDetails
from .base import DocumentBuilder


class MovieDocumentBuilder(DocumentBuilder[MovieDetails]):
    """Builder for movie documents."""
    def build(self, movie: MovieDetails) -> Dict[str, Any]:
        """Build a movie document from MovieDetails."""
        self._update_timestamp()
        
        base_doc = self._get_base_document()
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
            "transcript_chunks": [
                {
                    "index": chunk.index,
                    "text": chunk.text,
                    "embedding": chunk.embedding
                }
                for chunk in movie.transcript_chunks
            ] if hasattr(movie, 'transcript_chunks') else [],
            "embedding_model":    movie.embedding_model if hasattr(movie, 'embedding_model') else None,
            **base_doc
        }
        


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