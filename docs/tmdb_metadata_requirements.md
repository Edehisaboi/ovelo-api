# TMDB Metadata Requirements

This document outlines the essential metadata we need to collect from TMDB for our movie and TV show identification system.

## Core Movie Data
```json
{
  "id": "integer",
  "title": "string",
  "original_title": "string",
  "release_date": "date",
  "runtime": "integer",
  "overview": "string",
  "poster_path": "string",
  "backdrop_path": "string",
  "genres": [
    {
      "id": "integer",
      "name": "string"
    }
  ],
  "origin_country": ["string"],
  "imdb_id": "string",
  "spoken_languages": [
    {
      "iso_639_1": "string",
      "name": "string",
      "english_name": "string"
    }
  ],
  "status": "string"
}
```

## TV Show Data
```json
{
  "id": "integer",
  "name": "string",
  "original_name": "string",
  "first_air_date": "date",
  "last_air_date": "date",
  "number_of_seasons": "integer",
  "number_of_episodes": "integer",
  "episode_run_time": ["integer"],
  "overview": "string",
  "poster_path": "string",
  "backdrop_path": "string",
  "genres": [
    {
      "id": "integer",
      "name": "string"
    }
  ],
  "origin_country": ["string"],
  "imdb_id": "string",
  "spoken_languages": [
    {
      "iso_639_1": "string",
      "name": "string",
      "english_name": "string"
    }
  ],
  "status": "string",
  "seasons": [
    {
      "id": "integer",
      "season_number": "integer",
      "episode_count": "integer",
      "name": "string",
      "overview": "string",
      "poster_path": "string",
      "air_date": "date",
      "episodes": [
        {
          "id": "integer",
          "name": "string",
          "overview": "string",
          "still_path": "string",
          "air_date": "date",
          "episode_number": "integer",
          "runtime": "integer"
        }
      ]
    }
  ]
}
```

## Cast and Crew
```json
{
  "cast": [
    {
      "id": "integer",
      "name": "string",
      "character": "string",
      "profile_path": "string",
      "order": "integer"
    }
  ],
  "crew": [
    {
      "id": "integer",
      "name": "string",
      "job": "string",
      "department": "string",
      "profile_path": "string"
    }
  ]
}
```

## Media Assets
```json
{
  "images": {
    "posters": [
      {
        "file_path": "string",
        "width": "integer",
        "height": "integer",
        "aspect_ratio": "float",
        "iso_639_1": "string",
        "vote_average": "float",
        "vote_count": "integer"
      }
    ],
    "backdrops": [
      {
        "file_path": "string",
        "width": "integer",
        "height": "integer",
        "aspect_ratio": "float",
        "iso_639_1": "string",
        "vote_average": "float",
        "vote_count": "integer"
      }
    ],
    "logos": [
      {
        "file_path": "string",
        "width": "integer",
        "height": "integer",
        "aspect_ratio": "float",
        "iso_639_1": "string",
        "vote_average": "float",
        "vote_count": "integer"
      }
    ]
  },
  "videos": {
    "results": [
      {
        "id": "string",
        "key": "string",
        "name": "string",
        "site": "string",
        "size": "integer",
        "type": "string",
        "official": "boolean",
        "published_at": "string",
        "iso_639_1": "string",
        "iso_3166_1": "string"
      }
    ]
  }
}
```

## Additional Context
```json
{
  "popularity": "float",
  "vote_average": "float",
  "vote_count": "integer",
  "tagline": "string",
  "keywords": [
    {
      "id": "integer",
      "name": "string"
    }
  ],
  "homepage": "string"
}
```

## Watch Providers
```json
{
  "id": "integer",
  "results": {
    "US": {
      "link": "string",
      "flatrate": [
        {
          "logo_path": "string",
          "provider_id": "integer",
          "provider_name": "string",
          "display_priority": "integer"
        }
      ]
    }
  }
}
```

## Usage Notes

1. **Cast Data**: We'll primarily focus on the top 5-10 actors in the cast list, as they are most likely to appear in significant scenes.

2. **Crew Data**: We'll prioritize directors and cinematographers as they have the most influence on the visual style of the film.

3. **Images**: We'll need multiple sizes of images for different use cases:
   - Thumbnails for quick identification
   - High-resolution images for detailed scene matching
   - Backdrops for visual context

4. **Keywords**: These will be particularly useful for improving our scene matching accuracy.

5. **TV Show Specific**: 
   - We'll need to handle both show-level and episode-level identification
   - Season and episode numbers are crucial for precise scene matching
   - Episode stills are particularly valuable for scene matching

6. **Watch Providers**:
   - Focus on subscription services (flatrate) for streaming availability
   - Primary providers to include:
     - Netflix
     - Amazon Prime
     - Disney+
     - Hulu
     - HBO Max
     - Apple TV+
     - Peacock
     - Paramount+
   - Provider information should be updated daily
   - Show only active streaming availability
   - Consider implementing region-based provider filtering
   - Note: Data provided by JustWatch (attribution required)

7. **Videos and Trailers**:
   - Prioritize official trailers for the best quality
   - Support multiple video types (trailers, teasers, clips)
   - Consider language and region preferences
   - YouTube integration for direct playback
   - Cache video metadata for quick access

## Implementation Considerations

1. We should implement caching for frequently accessed metadata to reduce API calls.

2. The metadata should be stored in a structured format in our database for quick retrieval.

3. We should implement a system to periodically update the metadata to ensure it stays current.

4. Consider implementing a fallback system for when certain metadata is unavailable.

5. For TV shows, we need to implement efficient episode lookup and season management.

6. Watch provider data should be:
   - Updated daily to ensure accuracy
   - Filtered to show only flatrate (subscription) providers
   - Prioritized by display_priority field
   - Region-aware to show relevant services
   - Include proper JustWatch attribution

7. Consider implementing a system to handle different regional availability of content.

8. Video data should be filtered to prioritize:
   - Official trailers
   - Highest quality available
   - Most recent uploads
   - User's preferred language 