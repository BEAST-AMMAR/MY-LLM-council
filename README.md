# 🏛️ LLM Council v3.0

> Multi-agent AI debate system. 4 LLMs argue. 1 judge decides. Voice, image & webcam supported.

## 📚 Project Documentation
Comprehensive project documentation is available in the repository:
- [Product Requirements Document (PRD)](./PRD.md)
- [Technical Requirements Document (TRD)](./TRD.md)
- [Project Details](./Project_Details.md)
- [Project Report](./Project_Report.md)

## 🚀 Quick Start

### 1. Get your free OpenRouter API key
→ [openrouter.ai/keys](https://openrouter.ai/keys) (free, no credit card needed)

### 2. Setup `.env`
```bash
copy .env.example .env
# Edit .env — paste your OPENROUTER_API_KEY
```

### 3. Run
```bash
start.bat          # Windows — one-click launch
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

## ⚖️ Council Members

| Agent | Model | Strength | Vision |
|-------|-------|----------|--------|
| **Sage** | Llama 3.2 11B Vision | Philosophical reasoning | ✅ |
| **Analyst** | Qwen 2.5 VL 7B | Logic & evidence | ✅ |
| **Strategist** | Gemini 2.0 Flash | Strategic thinking | ✅ |
| **Skeptic** | Mistral 7B | Devil's advocate | ❌ |
| **Judge** | DeepSeek R1 | Final reasoning | ❌ |

## ⚙️ Architecture (v3.0)
- **Backend**: FastAPI + LangGraph + WebSockets.
- **Frontend**: Next.js (React) + Tailwind CSS.
- **Database**: SQLite (User Auth & Config).
- **Execution**: Hybrid Adapter supports both **Cloud** (OpenRouter) and **Local** (.gguf) models.

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
- If the backend returns connection errors, check that `start.bat` successfully booted both the `8001` FastAPI port and the `3000` Next.js port.
