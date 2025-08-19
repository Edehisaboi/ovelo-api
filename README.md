## Moovio Real‑time Media vRecognition API

This is a FastAPI application that identifies movies and TV shows in real time from an audio/video stream. It combines:

- Live speech‑to‑text transcription (AWS Transcribe)
- Celebrity/actor recognition from frames (AWS Rekognition)
- Hybrid semantic search over transcripts (MongoDB Atlas Vector + Full‑text)
- External metadata enrichment (TMDb)
- Deterministic and LLM‑assisted decision logic

The system streams audio and frames over a WebSocket, constructs a retrieval‑augmented context using vector search, and decides the best match, returning a concise media payload.

### Highlights

- Real‑time WebSocket pipeline with safe connection lifecycle management
- Hybrid retrieval across movie and TV transcript chunks
- Actor signal integration to boost candidate scores
- Two decision modes: rules‑based and LLM‑assisted
- Clean dependency injection and singletons for external clients
- Structured logging to file and console

---

### Architecture Overview

At a high level, the identification pipeline is a LangGraph state machine composed of nodes and conditional edges:

- Nodes: `transcriber` → `retriever` → `filter` → `cast_lookup|cast_matcher` → `booster` (optional) → `decider|ai_decider` → `metadata`
- Conditional routing based on state (presence of transcript, candidates, actors, and match)
- Output: a single result payload or a graceful end signal

Key components:

- API layer: FastAPI routes (HTTP + WebSocket)
- vRecognition service: LangGraph workflow, agents, prompts, and chains
- Data layer: MongoDB collections manager, vector/hybrid retrievers, aggregation queries
- External clients: AWS (Transcribe, Rekognition), TMDb, OpenAI embeddings

---

### Directory Structure (trimmed)

```text
application/
  app.py                       # FastAPI app (routers, middleware, handlers)
  api/
    __init__.py
    v1/
      __init__.py
      endpoints/
        http/search.py         # Search + vector search HTTP endpoints
        ws/vRecognition.py     # WebSocket endpoint for real‑time identification
      ws_manager.py            # ConnectionManager for WebSockets
  core/
    config.py                  # Pydantic settings (env‑driven)
    dependencies.py            # Singletons (DB, clients, WS manager)
    logging.py                 # Loguru configuration
  services/
    vRecognition/
      graph.py                 # Graph builders (rules/LMM variants)
      edges.py                 # Conditional edge functions
      state.py                 # Shared state shape
      chains.py, prompts.py    # LLM chain + prompt templates
      agents/                  # Nodes: Transcriber, Retriever, Cast*, Decider, Metadata, Booster
  utils/
    agents.py, rate_limiter.py, document.py
external/clients/              # AWS, TMDb, embeddings, OpenSubtitles (client wrappers)
infrastructure/database/       # Mongo manager, collection wrapper, indexes, queries
main.py                        # Uvicorn entrypoint
```

---

### Getting Started

#### Prerequisites

- Python 3.11+
- MongoDB Atlas (or compatible) with Vector Search
- AWS credentials for Transcribe and Rekognition
- TMDb API key
- OpenAI API key (embeddings and optional LLM decisioning)
- (Optional) Comet/Opik credentials for prompt tracking

#### Installation

```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell
pip install -r requirements.txt
```

#### Configuration

Create a `.env` file in the project root and set at least:

```env
# OpenAI / LLM
OPENAI_API_KEY=...
OPENAI_LLM_MODEL=gpt-4.1-2025-04-14

# TMDb
TMDB_API_KEY=...

# OpenSubtitles (optional for ingestion workflows)
OPENSUBTITLES_API_KEY=...

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# MongoDB
MONGODB_URL=mongodb+srv://...
MONGODB_DB=moovzmatch

# (Optional) Prompt monitoring via Opik/Comet ML
COMET_API_KEY=...
COMET_PROJECT=Moovio-API

# Feature flags / tuning (sane defaults provided)
DEBUG_MODE=false
ENABLE_RATE_LIMITING=true
```

#### Run the API

```bash
python main.py
# → http://localhost:8000/ (docs at /docs)
```

---

### API Reference

#### REST (HTTP)

- POST `/v1/api/search`

  - Body: `{ "query": str, "limit": int = 1, "include_movies": bool = true, "include_tv": bool = true }`
  - Behavior: Text search across DB; if results are insufficient, falls back to TMDb and (optionally) ingests results.

- POST `/v1/api/vector-search`
  - Body: `{ "query": str }`
  - Behavior: Hybrid vector search over movie/TV transcript chunks; returns normalized documents.

#### WebSocket (Real‑time Identification)

- URL: `/v1/ws/identify`
- Lifecycle: server assigns `connection_id`, processes streamed messages, returns a single `result` payload, then closes.
- Accepted messages:
  - Ping: `{ "type": "ping" }`
  - Frame: `{ "type": "frame", "data": { "frame": { "data": "<base64>" } } }`
  - Audio: `{ "type": "audio", "data": { "audio": { "data": "<base64>" } } }`
- Server responses include a final payload like:

```json
{
  "type": "result",
  "success": true,
  "data": {
    "id": "...",
    "title": "...",
    "posterUrl": "...",
    "year": "...",
    "genre": "...",
    "description": "...",
    "tmdbRating": 7.8,
    "duration": 123,
    "identifiedAt": "2025-01-01T12:34:56Z"
  }
}
```

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

Two graph variants are available in `application/services/vRecognition/graph.py`:

- Rules‑based: `create_vrecognition_graph` (uses `CastMatcher` + score `Booster` + deterministic `Decider`)
- LLM‑assisted: `create_ai_vrecognition_graph` (uses `CastLookup` + `ai_decider_node` with OpenAI)

Important nodes:

- `Transcriber` — manages STT stream and emits normalized transcript, actor list
- `Retriever` — hybrid search across movie and TV chunks
- `Filter` — selects top‑K per media id; either produces `(Document, score)` or `Document` only
- `CastMatcher`/`CastLookup` — actor presence/match lookup against DB by media id
- `Booster` — applies actor‑based bonus to candidate scores
- `Decider`/`ai_decider_node` — final match decision (persistence windows or LLM tooling)
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

- Logging via Loguru (`application/core/logging.py`), output to console and `logs/moovzmatch.log`
- Optional Opik/Comet prompt monitoring (`application/services/vRecognition/opik.py`), enabled when `COMET_API_KEY` and `COMET_PROJECT` are set

---

### Development & Testing

- Interactive API docs: `http://localhost:8000/docs`
- WebSocket utilities: `scripts/test_websocket_client.py`
- Examples for connection manager behaviour: `scripts/test_connection_manager_singleton.py`

---

### Common Issues

- Ensure `.env` is complete; missing keys for AWS/TMDb/OpenAI will cause startup/runtime errors
- Vector search requires indexes in MongoDB Atlas; verify index names match `config.py`
- WebSocket payloads must include base64 data for `frame` and `audio` message types

---

### License

Proprietary – internal use only (update as appropriate).
