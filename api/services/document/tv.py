from typing import Dict, Any
from api.services.tmdb.model import TVDetails
from .base import DocumentBuilder

class TVDocumentBuilder(DocumentBuilder[TVDetails]):
    """Builder for TV documents."""
    
    def build(self, tv: TVDetails) -> Dict[str, Any]:
        """Build a TV document from TVDetails."""
        self._update_timestamp()
        
        base_doc = self._get_base_document()
        return {
            "tmdb_id":            tv.id,
            "adult":              tv.adult,
            "name":               tv.name,
            "original_name":      tv.original_name,
            "overview":           tv.overview,
            "poster_path":        tv.poster_path,
            "backdrop_path":      tv.backdrop_path,
            "first_air_date":     tv.first_air_date,
            "last_air_date":      tv.last_air_date,
            "number_of_seasons":  tv.number_of_seasons,
            "number_of_episodes": tv.number_of_episodes,
            "genres":             [g.name for g in tv.genres],
            "spoken_languages":   [
                {
                    "iso_639_1":    lang.iso_639_1,
                    "name":         lang.name,
                    "english_name": lang.english_name
                }
                for lang in tv.spoken_languages
            ],
            "origin_country":     tv.origin_country,
            "external_ids":       {
                "imdb_id":        tv.external_ids.imdb_id,
                "facebook_id":    tv.external_ids.facebook_id,
                "instagram_id":   tv.external_ids.instagram_id,
                "twitter_id":     tv.external_ids.twitter_id
            },
            "status":             tv.status,
            "tagline":            tv.tagline,
            "in_production":      tv.in_production,
            "vote_average":       tv.vote_average,
            "vote_count":         tv.vote_count,
            "cast":               [
                {
                    "name":                 member.name,
                    "character":            member.character,
                    "known_for_department": member.known_for_department
                }
                for member in tv.credits.cast
            ],
            "crew":               [
                {
                    "name":         member.name,
                    "job":          member.job,
                    "department":   member.department
                }
                for member in tv.credits.crew
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
                    for img in tv.images.backdrops
                ],
                "posters": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in tv.images.posters
                ],
                "logos": [
                    {
                        "aspect_ratio": img.aspect_ratio,
                        "file_path":    img.file_path,
                        "height":       img.height,
                        "width":        img.width,
                        "iso_639_1":    img.iso_639_1
                    }
                    for img in tv.images.logos
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
                for video in tv.videos.results
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
                for country, providers in tv.watch_providers.results.items()
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
                for season in tv.seasons
            ],
            "embedding_model":    tv.embedding_model if hasattr(tv, 'embedding_model') else None,
            **base_doc
        }
        
        