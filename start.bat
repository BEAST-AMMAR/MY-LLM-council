@echo off
echo Starting LLM Council Project...

echo 1. Starting ML Engine (Backend)...
start "LLM Council - ML Engine" cmd /k "cd ml_engine && call .venv\Scripts\activate && python -m uvicorn server:app --host 0.0.0.0 --port 8001"

echo 2. Starting Next.js App (Frontend)...
start "LLM Council - Frontend" cmd /k "cd frontend && npm run dev"

echo Project Launched! The Frontend should be available at http://localhost:3000 shortly.
pause
