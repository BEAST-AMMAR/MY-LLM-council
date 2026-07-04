# 🏛️ LLM Council v4.0 (Enterprise Edition)

> Multi-agent AI debate system. 4 LLMs argue. 1 judge decides. Voice, image & webcam supported.

## 📚 Project Documentation
Comprehensive project documentation has been moved to the `docs/` directory to keep the root repository clean:
- [Product Requirements Document (PRD)](./docs/PRD.md)
- [Technical Requirements Document (TRD)](./docs/TRD.md)
- [Project Details](./docs/Project_Details.md)
- [Project Report](./docs/Project_Report.md)

## 🚀 Quick Start

### 1. Get your free OpenRouter API key
→ [openrouter.ai/keys](https://openrouter.ai/keys) (free, no credit card needed)

### 2. Setup `.env`
```bash
copy .env.example ml_engine/.env
# Edit ml_engine/.env — paste your OPENROUTER_API_KEY
# (Optional) Add JWT_SECRET_KEY for persistent sessions
```

### 3. Run
All startup scripts have been moved to the `scripts/` folder.
```bash
cd scripts
start.bat          # Windows — one-click launch for both Frontend & Backend
```

Open **http://localhost:3000** in Chrome (for full voice support).

---

## 🧠 How It Works

```text
Your Input (text / image / webcam / voice)
        ↓
  ┌─────────────────────────────────────┐
  │         COUNCIL CHAMBER             │
  │  ┌────┐  ┌────┐  ┌────┐  ┌────┐   │
  │  │Sage│  │Anlst│  │Strt│  │Skpt│  │
  │  └────┘  └────┘  └────┘  └────┘   │
  │         Round 1 — Independent       │
  │         Round 2 — Debate            │
  │              ↓                      │
  │         ┌─────────┐                 │
  │         │  JUDGE  │ ← DeepSeek R1  │
  │         └─────────┘                 │
  └─────────────────────────────────────┘
        ↓
  Final Verdict (+ TTS voice readout)
```

## ⚖️ Custom Agents & Council Members
In addition to the default Council (Sage, Analyst, Strategist, Skeptic), you can now create **Custom Agents** via the UI. 
Custom agents are persisted in the SQLite database and allow you to define specific System Prompts and roles to tailor the debate to your exact needs.

## ⚙️ Architecture
- **Backend**: FastAPI + LangGraph + WebSockets.
- **Frontend**: Next.js (React) + Tailwind CSS.
- **Database**: SQLite (User Auth & Config).
- **Execution**: Hybrid Adapter supports both **Cloud** (OpenRouter) and **Local** (.gguf) models.
- **Memory**: ChromaDB for Vector Search and Precedent saving.

## 🔒 Security & Enterprise Features
This project has been hardened against common web exploits:
- **Rate Limiting**: Integrated `slowapi` to protect authentication endpoints from brute-force dictionary attacks (5 requests/min per IP).
- **Payload Limits**: Hard limits on WebSocket data streams (5MB max) to prevent memory exhaustion (DoS) via malicious file uploads.
- **Strict Validation**: Pydantic `Field` bounds enforce data sanitization and prevent database bloating on all API endpoints.
- **Secure Secrets**: Securely randomizes the JWT Secret Key via Python's `secrets` module if missing from `.env`, with shortened token lifespans (60 minutes) and strict regex password complexity requirements.

## 📁 Repository Structure
- `frontend/` — Next.js React application
- `ml_engine/` — FastAPI backend, LangGraph logic, and SQLite database
  - `ml_engine/tests/` — Automated test suite
- `docs/` — Core architecture and design documentation
- `scripts/` — Batch scripts for environment setup and application launching

## 🎙️ Input Modes
- **Text** — Type any question or topic
- **Image** — Upload a photo; vision agents analyze it
- **Webcam** — Capture a live frame from your camera
- **Voice** — Speak your question (uses Chrome's Web Speech API)

## 🖨️ Output
- Real-time streaming debate via WebSockets.
- Judge's verdict with **HIGH / MEDIUM / LOW** confidence.
- **Text-to-speech** readout of the verdict (JARVIS-style).
- Option to **branch** timelines mid-debate.

## 🔧 Troubleshooting
- Use **Chrome desktop** for best Web Speech and camera behavior.
- Run on `localhost` or `127.0.0.1` (secure context required for media APIs).
- If the backend returns connection errors, check that the scripts successfully booted both the `8001` FastAPI port and the `3000` Next.js port.
