import os
import sys
import json
import asyncio
from aiohttp import web
import time
from collections import defaultdict
try:
    from llama_cpp import Llama
    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False

# Models Configuration
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
COUNCIL_MODELS = {
    "sage": "llama-3.2-1b-instruct-q4_k_m.gguf",
    "analyst": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
    "strategist": "phi-3-mini-4k-instruct-q4.gguf",
    "skeptic": "gemma-2-2b-it-q4_k_m.gguf",
    "judge": "llama-3.2-3b-instruct-q4_k_m.gguf",
}

# Run in Mock mode if llama-cpp is missing or models are not downloaded
# This allows rapid UI development before the 10GB download completes.
MOCK_MODE = not HAS_LLAMA or not all(os.path.exists(os.path.join(MODELS_DIR, m)) for m in COUNCIL_MODELS.values())

loaded_models = {}

# Simple in-memory rate limiter
RATE_LIMIT_WINDOW = 60 # seconds
RATE_LIMIT_REQUESTS = 20 # max requests per window
rate_limits = defaultdict(list)

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    # clean old requests
    rate_limits[ip] = [req_time for req_time in rate_limits[ip] if now - req_time < RATE_LIMIT_WINDOW]
    if len(rate_limits[ip]) >= RATE_LIMIT_REQUESTS:
        return True
    rate_limits[ip].append(now)
    return False

def load_models():
    if MOCK_MODE:
        print("[WARNING] Running in MOCK_MODE. Local LLM inference will return simulated responses.")
        return
    print("Loading models into memory... This may take a while depending on RAM/VRAM.")
    for agent_id, filename in COUNCIL_MODELS.items():
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            try:
                print(f"Loading {agent_id} ({filename})...")
                # Using 2048 ctx window to save RAM
                loaded_models[agent_id] = Llama(model_path=path, n_ctx=2048, verbose=False)
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
        else:
            print(f"Model {filename} not found!")

async def stream_mock_response(response, agent_id, delay=0.02):
    """Simulate a streaming LLM response."""
    # Prefix to show it's mock
    text = f"[MOCK {agent_id.upper()}] " + response
    tokens = text.split(' ')
    for token in tokens:
        yield token + " "
        await asyncio.sleep(delay)

async def handle_inference(request):
    ip = request.remote or "unknown"
    if is_rate_limited(ip):
        return web.json_response({"error": "Rate limit exceeded"}, status=429)

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    
    agent_id = data.get("agent_id")
    prompt = data.get("prompt")
    
    if not agent_id or not prompt:
        return web.json_response({"error": "Missing agent_id or prompt"}, status=400)
    
    if len(prompt) > 4000:
        return web.json_response({"error": "Prompt too long (max 4000 chars)"}, status=400)

    if agent_id not in COUNCIL_MODELS:
        return web.json_response({"error": f"Unknown agent {agent_id}"}, status=400)

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache'}
    )
    await response.prepare(request)

    if MOCK_MODE:
        # Generate a sophisticated mock response based on persona
        mock_text = f"I am analyzing the prompt: '{prompt[:50]}...'. As {agent_id.title()}, I conclude that this requires deep consideration. My locally inferred parameters suggest an optimal path forward."
        if agent_id == "judge":
            mock_text += "\n\nCONFIDENCE: HIGH\nRERUN: NO"
        
        async for token in stream_mock_response(mock_text, agent_id):
            await response.write(f"data: {json.dumps({'token': token})}\n\n".encode('utf-8'))
    else:
        if agent_id not in loaded_models:
            await response.write(f"data: {json.dumps({'error': 'Model not loaded'})}\n\n".encode('utf-8'))
        else:
            llm = loaded_models[agent_id]
            # Use Llama-cpp stream
            stream = llm(prompt, max_tokens=300, stream=True)
            for chunk in stream:
                token = chunk["choices"][0]["text"]
                if token:
                    await response.write(f"data: {json.dumps({'token': token})}\n\n".encode('utf-8'))
                    await asyncio.sleep(0.01) # Yield control

    await response.write(b"data: [DONE]\n\n")
    await response.write_eof()
    return response

async def handle_health(request):
    return web.json_response({
        "status": "online",
        "mock_mode": MOCK_MODE,
        "models_loaded": list(loaded_models.keys()) if not MOCK_MODE else []
    })

app = web.Application()

# Add CORS
import aiohttp_cors
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

cors.add(app.router.add_post('/api/infer', handle_inference))
cors.add(app.router.add_get('/api/health', handle_health))

if __name__ == '__main__':
    load_models()
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting ML Engine on port {port}...")
    web.run_app(app, host='0.0.0.0', port=port)
