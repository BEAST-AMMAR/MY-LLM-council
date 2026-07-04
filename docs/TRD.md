# Technical Requirements Document (TRD)
## Project Name: LLM Council (v4.0 Enterprise Edition)

### 1. System Architecture
The application is built using a decoupled, highly secure architecture:
- **Backend**: FastAPI (Python) handles API routes, WebSocket streaming, authentication, rate-limiting, and the AI orchestration.
- **Frontend**: Next.js (React) handles the user interface, media capture (camera, mic), and WebSocket communication.
- **AI Orchestration**: LangGraph coordinates the multi-agent debate flow, passing state between agents.
- **Database**: SQLite (via SQLAlchemy) stores user credentials, custom agents, and configuration state.
- **Vector Store**: ChromaDB is used for long-term memory retrieval and storing past debate precedents.

### 2. Tech Stack
#### 2.1 Backend
- **Framework**: FastAPI
- **Server**: Uvicorn
- **AI Framework**: LangChain & LangGraph
- **ORM**: SQLAlchemy
- **Database**: SQLite (`llm_council.db`)
- **Authentication**: JWT tokens (OAuth2 Password Bearer) with strict 60-minute expiration.
- **Security**: `slowapi` for API rate-limiting. Pydantic models for strict input validation.
- **WebSockets**: Native FastAPI WebSockets for real-time streaming of tokens and media context, with 5MB payload limits.

#### 2.2 Frontend
- **Framework**: Next.js (React)
- **Styling**: Tailwind CSS / Vanilla CSS
- **Media APIs**: HTML5 Canvas, `getUserMedia` (Video), Web Speech API (Audio/Speech recognition).
- **Communication**: HTTP REST (Auth, Health, Agents), WebSockets (Debate streaming).

### 3. Core Components

#### 3.1 LangGraph Debate Engine (`debate_graph.py`)
- Manages the state of the debate (`messages`, `round_count`, `max_rounds`, `current_topic`, `session_id`, `personality`).
- Agents are nodes in the graph. The edges dictate the flow: User Prompt -> Independent Agent Analysis -> Debate Round -> Judge Verdict.
- Includes a robust search fallback mechanism (DuckDuckGo -> Tavily).
- Integrated `stream_callback` to send intermediate tokens via WebSocket to the frontend.

#### 3.2 Hybrid Model Adapter (`adapter.py`)
- **Cloud Mode**: Uses the `openai` SDK pointing to OpenRouter's API endpoints to route queries to free tier models (Llama 3, Qwen, Gemini, DeepSeek, Mistral).
- **Local Mode**: Loads models directly from the local filesystem (`/models/*.gguf`) for offline, private execution.
- Handles model fallback logic gracefully.

#### 3.3 WebSocket Manager (`server.py`)
- Establishes persistent connections per client with memory-leak prevention.
- Routes actions based on JSON payloads:
  - `convene`: Starts a standard debate.
  - `branch`: Injects alternative context into the debate.
  - `audio_stream` / `video_stream` / `file_drop`: Stores multimodal context in a global dictionary keyed by `session_id`.

#### 3.4 Security & Authentication Module (`auth.py`, `limiter.py`, `database.py`)
- Standard JWT implementation with secure runtime secret generation via Python's `secrets` module.
- Strict Pydantic validators enforce password complexity and string length bounds.
- `slowapi` decorators protect endpoints from brute-force attempts.
- SQLAlchemy models for Users and Custom Agents.

### 4. API Endpoints
- **REST**:
  - `GET /api/health`: Returns server status and current adapter mode.
  - `POST /api/mode`: Sets the hybrid adapter mode (`local` or `cloud`).
  - `POST /api/auth/token`: Generates JWT tokens for authentication (Rate-Limited).
  - `POST /api/auth/register`: Registers a new user (Rate-Limited).
  - `GET /api/agents` & `POST /api/agents`: Manage custom agents.
- **WebSocket**:
  - `ws://<host>:<port>/ws/debate/{room_id}`: Main bidirectional stream.

### 5. Deployment & Execution
- **Environment**: Configured via `ml_engine/.env`.
- **Startup Script**: Moved to `scripts/start.bat` for Windows users to easily launch the Uvicorn server and Next.js frontend concurrently.
- **Port**: Defaults to `8001` for the backend, `3000` for the frontend.
