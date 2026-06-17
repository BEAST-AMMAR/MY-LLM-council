# LLM Council — Complete Build Plan

## Summary
General-purpose multi-agent AI council. 4 agents + 1 judge debate ANY question.
Inputs: text, image upload, live webcam capture, voice command.
All models free via OpenRouter. JARVIS/EDITH-style premium UI.

## Stack
- **Backend**: FastAPI + sse-starlette (SSE streaming)
- **AI**: OpenRouter free tier via `openai` SDK
- **Frontend**: HTML/CSS/JS (no framework) — JARVIS holographic aesthetic

## Agents (all free on OpenRouter)
| Role | Name | Model | Vision |
|------|------|-------|--------|
| Philosopher | Sage | `meta-llama/llama-3.2-11b-vision-instruct:free` | ✅ |
| Logician | Analyst | `qwen/qwen2.5-vl-7b-instruct:free` | ✅ |
| Visionary | Strategist | `google/gemini-2.0-flash-exp:free` | ✅ |
| Challenger | Skeptic | `mistralai/mistral-7b-instruct:free` | ❌ |
| **Judge** | **Judge** | `deepseek/deepseek-r1:free` | ❌ |

## Debate Flow
1. **Round 1**: All 4 agents independently analyze (with image if provided)
2. **Round 2+**: Agents see all prior responses, argue/challenge each other
3. **Judge**: Reads full transcript, delivers unbiased verdict + confidence level + rerun decision

## Input Modes
- Text prompt (always)
- Image upload (file picker)
- Webcam capture (getUserMedia → canvas → base64)
- Voice (Web Speech API → transcription → text field)

## Output
- Real-time streaming debate (SSE)
- Judge's TTS verdict (Web SpeechSynthesis)
- Export as JSON/Markdown

## Files
```
LLM council/
├── backend/
│   ├── __init__.py
│   ├── app.py          ← FastAPI + SSE
│   └── council.py      ← Debate engine
├── frontend/
│   ├── index.html      ← JARVIS UI
│   ├── style.css       ← Holographic theme
│   └── script.js       ← Voice/webcam/SSE
├── .env.example
├── requirements.txt
└── start.bat
```
