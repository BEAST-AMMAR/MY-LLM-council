# 🏛️ LLM Council v2.0

> Multi-agent AI debate system. 4 LLMs argue. 1 judge decides. Voice, image & webcam supported.

## Quick Start

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
# OR manually:
python -m uvicorn backend.app:app --port 8000 --reload
```

Open **http://localhost:8000** in Chrome (for full voice support).

---

## How It Works

```
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

## Council Members

| Agent | Model | Strength | Vision |
|-------|-------|----------|--------|
| **Sage** | Llama 3.2 11B Vision | Philosophical reasoning | ✅ |
| **Analyst** | Qwen 2.5 VL 7B | Logic & evidence | ✅ |
| **Strategist** | Gemini 2.0 Flash | Strategic thinking | ✅ |
| **Skeptic** | Mistral 7B | Devil's advocate | ❌ |
| **Judge** | DeepSeek R1 | Final reasoning | ❌ |

All models are **100% free** via OpenRouter.

## Input Modes

- **Text** — Type any question or topic
- **Image** — Upload a photo; vision agents analyze it
- **Webcam** — Capture a live frame from your camera
- **Voice** — Speak your question (uses Chrome's Web Speech API)

## Output

- Real-time streaming debate (visible as it happens)
- Judge's verdict with **HIGH / MEDIUM / LOW** confidence
- **Text-to-speech** readout of the verdict (JARVIS-style)
- Export to **JSON** or **Markdown**
- Option to **rerun** if judge flags insufficient evidence

## Reliability Notes

- Each council member now has **multiple OpenRouter model fallbacks**. If one model is unavailable, the backend auto-switches to the next model.
- Judge also has fallback models; if all judge models fail, the app emits a safe LOW-confidence fallback verdict with `RERUN: YES`.
- Frontend now distinguishes:
      - camera/mic permission errors,
      - browser compatibility limitations,
      - speech-service network errors,
      - backend connection issues.

## Camera & Mic Troubleshooting

- Use **Chrome desktop** for best Web Speech and camera behavior.
- Open app on `localhost` or `127.0.0.1` (secure-context requirement for media APIs).
- If camera fails:
      - allow camera permission for the site,
      - close apps using camera (Zoom/Meet/etc.),
      - retry after refreshing.
- If mic shows "network" error:
      - this usually means speech recognition service issue (not Wi-Fi),
      - retry after a few seconds, or type your question manually.
