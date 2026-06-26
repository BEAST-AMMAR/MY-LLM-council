import os
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from auth import auth_router, get_current_user_from_token
from adapter import hybrid_adapter
import debate_graph
from langchain_core.messages import HumanMessage

# Ensure tables are created
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load local models
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    hybrid_adapter.load_local_models(models_dir)
    yield
    # Shutdown: nothing to clean up

app = FastAPI(title="LLM Council API v3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://172.19.48.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/api/health")
def health_check():
    return {"status": "online", "mode": hybrid_adapter.mode}

@app.post("/api/mode")
def set_mode(mode: dict):
    new_mode = mode.get("mode")
    if new_mode in ["local", "cloud"]:
        hybrid_adapter.set_mode(new_mode)
        return {"status": "success", "mode": new_mode}
    raise HTTPException(status_code=400, detail="Invalid mode")

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/debate")
async def debate_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    session_id = str(id(websocket))
    debate_graph.live_media_context[session_id] = {"audio": [], "video": None, "files": []}
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")
            
            if action == "convene" or action == "branch":
                prompt = payload.get("prompt")
                personality = payload.get("personality", {"aggression": 50, "creativity": 50})
                branch_context = payload.get("branch_context")
                
                async def ws_stream_callback(agent, msg_type, token):
                    await websocket.send_text(json.dumps({
                        "type": msg_type, 
                        "agent": agent, 
                        "token": token,
                        "status": "thinking" if msg_type == "thinking" else "done" if msg_type == "done" else None
                    }))
                
                debate_graph.stream_callback = ws_stream_callback
                
                # If branching, inject the branch context into the topic
                topic = prompt
                if action == "branch" and branch_context:
                    topic = f"{prompt}\n\n[TIMELINE DIVERGENCE: The Council MUST assume the following statement is absolute truth for this debate run]:\n\"{branch_context}\""
                
                initial_state = {
                    "messages": [HumanMessage(content=topic)],
                    "round_count": 0,
                    "max_rounds": 2, 
                    "current_topic": topic,
                    "session_id": session_id,
                    "personality": personality
                }
                
                await websocket.send_text(json.dumps({"type": "system", "message": "Starting LangGraph Debate..." if action == "convene" else "Spawning Alternate Timeline..."}))
                
                # Run graph in background task so we can keep listening for media
                async def run_graph():
                    try:
                        await debate_graph.debate_app.ainvoke(initial_state)
                        await websocket.send_text(json.dumps({"type": "system", "message": "Debate Complete"}))
                    except Exception as e:
                        print(f"Graph execution failed: {e}")
                        try:
                            await websocket.send_text(json.dumps({"type": "system", "message": f"Council Error: {str(e)}"}))
                        except:
                            pass
                
                asyncio.create_task(run_graph())
                
            elif action == "audio_stream":
                text = payload.get("text")
                if text:
                    debate_graph.live_media_context[session_id]["audio"].append(text)
            elif action == "video_stream":
                frame = payload.get("frame")
                if frame:
                    debate_graph.live_media_context[session_id]["video"] = frame
            elif action == "file_drop":
                filename = payload.get("filename")
                content = payload.get("content") # Base64 or text
                if filename and content:
                    debate_graph.live_media_context[session_id]["files"].append((filename, content))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if session_id in debate_graph.live_media_context:
            del debate_graph.live_media_context[session_id]
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(websocket)
        if session_id in debate_graph.live_media_context:
            del debate_graph.live_media_context[session_id]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting FastAPI server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
