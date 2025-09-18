## Ovelo-API – Media vRecognition API

FastAPI application that identifies movies and TV shows in real time from an audio/video stream. It streams frames and audio over WebSocket, performs hybrid retrieval over transcripts, integrates actor signals, and returns a single matched media payload.

### Highlights

- Real‑time WebSocket pipeline with safe connection lifecycle management
- Hybrid retrieval (MongoDB Atlas Vector + Full‑text)
- Actor signal via AWS Rekognition; speech‑to‑text via AWS Transcribe
- External metadata enrichment (TMDb); LLM‑assisted decision fallback (OpenAI)
- Clean dependency injection; structured logging to console and file

---

### Getting Started

#### Prerequisites

- Python 3.11+
- MongoDB Atlas (or compatible) with Vector Search and connection string
- Credentials/API keys: AWS (Transcribe, Rekognition), TMDb, OpenSubtitles, OpenAI

#### Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Run the API

```powershell
python main.py
# → http://localhost:8000/ (docs at /docs)
```

Optional (direct uvicorn):

```powershell
python -m uvicorn application.app:application --host 0.0.0.0 --port 8000 --reload
```

---

### Environment Variables (.env)

Required:

- OPENAI_API_KEY
- TMDB_API_KEY
- OPENSUBTITLES_API_KEY
- MONGODB_URL
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY

Useful/Optional (see `application/core/config.py` for defaults):

- AWS_REGION, AWS_STT_LANGUAGE
- TMDB_LANGUAGE, TMDB_REGION
- OPENAI_LLM_MODEL, OPENAI_EMBEDDING_MODEL
- COMET_API_KEY, COMET_PROJECT
- LOG_LEVEL, DEBUG_MODE

---

### API Reference

#### REST (HTTP)

- POST `/v1/api/search/videos`

  - Body (JSON): `{ "query": str, "type": "all"|"movie"|"tv", "limit": int }`
  - Text search across DB; falls back to TMDb results when needed.

- GET `/health`
  - Basic service status.

#### WebSocket (Real‑time Identification)

- URL: `/v1/ws/identify`
- Server assigns `connection_id`, processes streamed messages, returns a single `result`, then closes.
- Accepted messages:
  - Ping: `{ "type": "ping" }`
  - Frame: `{ "type": "frame", "data": { "frame": { "data": "<base64>" } } }`
  - Audio: `{ "type": "audio", "data": { "audio": { "data": "<base64>" } } }`

---

### Logging

- Loguru to console and `logs/ovelo-api.log`

---

### Development

- Interactive API docs: `http://localhost:8000/docs`

---

### Common Issues

- Ensure `.env` is complete; missing keys will cause startup/runtime errors
- Vector search requires indexes in MongoDB Atlas (see `config.py`)
- WebSocket payloads must include base64 `frame`/`audio` data
