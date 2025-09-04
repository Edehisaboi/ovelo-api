## Ovelo-API – Media vRecognition API

This is a FastAPI application that identifies movies and TV shows in real time from an audio/video stream. It combines:

- Live speech‑to‑text transcription (AWS Transcribe)
- Celebrity/actor recognition from frames (AWS Rekognition)
- Hybrid semantic search over transcripts (MongoDB Atlas Vector + Full‑text)
- External metadata enrichment (TMDb)
- Deterministic flow with LLM‑assisted decision fallback

The system streams audio and frames over a WebSocket, constructs a retrieval‑augmented context using vector + text search, and decides the best match, returning a concise media payload.

### Highlights

- Real‑time WebSocket pipeline with safe connection lifecycle management
- Hybrid retrieval across movie and TV transcript chunks
- Actor signal integration to boost candidate scores
- Clean dependency injection and singletons for external clients
- Structured logging to file and console

---

### Architecture Overview

At a high level, the identification pipeline is a LangGraph state machine composed of nodes and conditional edges:

- Nodes: `transcriber` → `retriever` → `filter` → `cast_lookup` → `booster` (optional) → `decider` → `metadata`
- Conditional routing based on state (presence of transcript, candidates, actors, and match)
- Output: a single result payload or a graceful end signal

Key components:

- API layer: FastAPI routes (HTTP + WebSocket)
- vRecognition service: LangGraph workflow, agents, prompts, and chains
- Data layer: MongoDB collections manager, vector/hybrid retrievers, aggregation queries
- External clients: AWS (Transcribe, Rekognition), TMDb, OpenAI embeddings

---

---

### Getting Started

#### Prerequisites

- Python 3.11+
- MongoDB Atlas (or compatible) with Vector Search
- MongoDB connection string (MONGODB_URL)
- AWS credentials for Transcribe and Rekognition
- TMDb API key
- OpenSubtitles API key
- OpenAI API key (embeddings and LLM decisioning)
- (Optional) Comet/Opik credentials for prompt tracking

#### Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
```

Alternative (uvicorn directly):
```powershell
python -m uvicorn application.app:application --host 0.0.0.0 --port 8000 --reload
```

#### Run the API

```powershell
python main.py
# → http://localhost:8000/ (docs at /docs)
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

Useful/Optional (see application/core/config.py for defaults):
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
  - Behavior: Text search across DB; if results are insufficient, falls back to TMDb results (no ingestion by default in this route).

- GET `/health`
  - Returns basic service status.

#### WebSocket (Real‑time Identification)

- URL: `/v1/ws/identify`
- Lifecycle: server assigns `connection_id`, processes streamed messages, returns a single `result` payload, then closes.
- Accepted messages:
  - Ping: `{ "type": "ping" }`
  - Frame: `{ "type": "frame", "data": { "frame": { "data": "<base64>" } } }`
  - Audio: `{ "type": "audio", "data": { "audio": { "data": "<base64>" } } }`

Minimal WS client (Python, for reference):

```python
import asyncio, json, websockets

async def run():
    async with websockets.connect("ws://localhost:8000/v1/ws/identify") as ws:
        msg = await ws.recv()  # {type: connected, connection_id: ...}
        await ws.send(json.dumps({"type": "ping"}))
        # send frames and audio chunks as needed
        # await ws.send(json.dumps({"type": "frame", "data": {"frame": {"data": b64}}}))
        # await ws.send(json.dumps({"type": "audio", "data": {"audio": {"data": b64}}}))
        result = await ws.recv()
        print(result)

asyncio.run(run())
```

---

### vRecognition Pipeline (LangGraph)

The graph is defined in `application/services/vRecognition/graph.py` as `create_vrecognition_graph`. The `Decider` node performs a threshold check and falls back to an OpenAI LLM chain when needed.

Important nodes:

- `Transcriber` — manages STT stream and emits normalized transcript, actor list
- `Retriever` — hybrid search across movie and TV chunks
- `Filter` — selects top‑K per media id; either produces `(Document, score)` or `Document` only
- `CastLookup` — actor presence/match lookup against DB by media id
- `Booster` — applies actor‑based bonus to candidate scores
- `Decider` — final match decision (threshold + LLM tooling)
- `Metadata` — fetches final payload fields from DB

---

### Data & Storage

- Central manager: `infrastructure/database/mongodb.py` (`MongoCollectionsManager`)
  - Initializes Motor client, collection wrappers, and LangChain hybrid retrievers
  - Provides `perform_hybrid_search`, normalized insert helpers for movies/TV
- Collections (configurable in `application/core/config.py`):
  - Movies: `movies`, `movie_chunks`, `movie_watch_providers`
  - TV: `tv_shows`, `tv_seasons`, `tv_episodes`, `tv_chunks`, `tv_watch_providers`

Index initialization is automatic when requested; hybrid retrievers require embedding configuration.

---

### Logging & Observability

- Logging via Loguru (`application/core/logging.py`), output to console and `logs/ovelo-api.log`
- Optional Opik/Comet prompt monitoring (`application/services/vRecognition/opik.py`), enabled when `COMET_API_KEY` and `COMET_PROJECT` are set

---

### Development & Testing

- Interactive API docs: `http://localhost:8000/docs`
- You can use the minimal WS client above to exercise the real‑time identification flow.

---

### Common Issues

- Ensure `.env` is complete; missing keys for AWS/TMDb/OpenAI/OpenSubtitles/MongoDB will cause startup/runtime errors
- Vector search requires indexes in MongoDB Atlas; verify index names match `config.py`
- WebSocket payloads must include base64 data for `frame` and `audio` message types

---

### License

Proprietary – internal use only (update as appropriate).
