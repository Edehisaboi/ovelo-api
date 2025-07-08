moovzmatch/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app initialization
│   ├── core/                     # Core application components
│   │   ├── __init__.py
│   │   ├── config.py             # Settings and configuration
│   │   ├── dependencies.py       # Dependency injection
│   │   └── logging.py            # Logging configuration
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── v1/                   # API versioning
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/        # API endpoints/routes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── stt.py        # Speech-to-text endpoints
│   │   │   │   └── search.py     # Search endpoints
│   │   │   └── router.py         # API router configuration
│   │   └── dependencies.py       # API-specific dependencies
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── media/                # Media-related services
│   │   │   ├── __init__.py
│   │   │   ├── search.py         # Search service
│   │   │   ├── ingestion.py      # Data ingestion service
│   │   │   └── cache.py          # Caching service
│   │   ├── transcription/        # Speech-to-text services
│   │   │   ├── __init__.py
│   │   │   ├── stt_service.py    # STT service
│   │   │   └── models.py         # STT models
│   │   ├── embeddings/           # Vector embedding services
│   │   │   ├── __init__.py
│   │   │   └── embedding_service.py
│   │   ├── subtitles/            # Subtitle processing
│   │   │   ├── __init__.py
│   │   │   ├── processor.py      # Subtitle processor
│   │   │   ├── parser.py         # SRT parser
│   │   │   ├── chunker.py        # Text chunker
│   │   │   └── validator.py      # Subtitle validator
│   │   ├── recognition/          # Face/celebrity recognition
│   │   │   ├── __init__.py
│   │   │   └── face_detector.py  # Face detection service
│   │   └── database/             # Database services
│   │       ├── __init__.py
│   │       ├── mongodb.py        # MongoDB wrapper
│   │       ├── indexes.py        # Index management
│   │       └── queries.py        # Database queries
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── media.py              # Media models (Movie, TV)
│   │   ├── search.py             # Search models
│   │   ├── subtitles.py          # Subtitle models
│   │   └── common.py             # Common/shared models
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── media.py              # Media schemas
│   │   ├── search.py             # Search schemas
│   │   └── api.py                # API request/response schemas
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py               # Base repository
│   │   ├── media_repository.py   # Media data access
│   │   └── search_repository.py  # Search data access
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── rate_limiter.py       # Rate limiting utilities
│       └── helpers.py            # General helper functions
├── external/                     # External API integrations
│   ├── __init__.py
│   ├── clients/                  # API clients
│   │   ├── __init__.py
│   │   ├── base.py               # Base API client
│   │   ├── openai_client.py      # OpenAI client
│   │   ├── tmdb_client.py        # TMDb client
│   │   ├── opensubtitles_client.py # OpenSubtitles client
│   │   └── rekognition_client.py # AWS Rekognition client
│   └── adapters/                 # API response adapters
│       ├── __init__.py
│       ├── tmdb_adapter.py       # TMDb response adapter
│       └── opensubtitles_adapter.py # OpenSubtitles adapter
├── infrastructure/               # Infrastructure components
│   ├── __init__.py
│   ├── database/                 # Database infrastructure
│   │   ├── __init__.py
│   │   ├── connection.py         # Database connection
│   │   └── migrations/           # Database migrations
│   └── cache/                    # Caching infrastructure
│       ├── __init__.py
│       └── redis_cache.py        # Redis cache implementation
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── unit/                     # Unit tests
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   ├── test_models/
│   │   └── test_utils/
│   ├── integration/              # Integration tests
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   └── test_database/
│   ├── fixtures/                 # Test fixtures
│   │   ├── __init__.py
│   │   └── data/
│   └── conftest.py               # Pytest configuration
├── docs/                         # Documentation
│   ├── api/                      # API documentation
│   ├── deployment/               # Deployment guides
│   └── development/              # Development guides
├── scripts/                      # Utility scripts
│   ├── setup.py                  # Setup script
│   ├── migrate.py                # Database migration script
│   └── seed.py                   # Database seeding script
├── docker/                       # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── .env.example                  # Environment variables example
├── .gitignore
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── pyproject.toml                # Project configuration
├── README.md
└── Makefile                      # Build/deployment commands