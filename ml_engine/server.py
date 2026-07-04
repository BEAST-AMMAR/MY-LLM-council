import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from database import engine, Base, get_db, SessionLocal, CustomAgent, ChatHistory, DebateMessage, Verdict, User
from auth import auth_router, get_current_user_from_token, oauth2_scheme
from limiter import limiter
from adapter import hybrid_adapter
import debate_graph
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return get_current_user_from_token(token, db)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load local models
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    hybrid_adapter.load_local_models(models_dir)
    yield
    # Shutdown: nothing to clean up

app = FastAPI(title="LLM Council API v4.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://172.19.48.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

from pydantic import Field
# Models for Agents
class AgentCreate(BaseModel):
    name: str = Field(..., max_length=100)
    role: str = Field(..., max_length=200)
    system_prompt: str = Field(..., max_length=2000)
    model: str = Field(..., max_length=100)
    provider: str = Field(..., max_length=50)
    vision_capable: int = 0

@app.post("/api/agents")
def create_agent(agent: AgentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_agent = CustomAgent(**agent.model_dump(), user_id=current_user.id)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@app.get("/api/agents")
def get_agents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CustomAgent).filter(CustomAgent.user_id == current_user.id).all()

@app.delete("/api/agents/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id, CustomAgent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"status": "success"}

from fastapi.responses import FileResponse
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

_generate_debate_report = None
try:
    from generate_pdf import generate_debate_report as _generate_debate_report
except ImportError:
    logger.warning("generate_pdf module not found. PDF export will be unavailable.")

@app.get("/api/history")
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    histories = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).order_by(ChatHistory.created_at.desc()).all()
    return histories

@app.get("/api/history/{history_id}")
def get_history_detail(history_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = db.query(ChatHistory).filter(ChatHistory.id == history_id, ChatHistory.user_id == current_user.id).first()
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    messages = db.query(DebateMessage).filter(DebateMessage.chat_history_id == history_id).order_by(DebateMessage.id.asc()).all()
    verdicts = db.query(Verdict).filter(Verdict.chat_history_id == history_id).order_by(Verdict.id.asc()).all()
    return {"history": history, "messages": messages, "verdicts": verdicts}

@app.get("/api/export-pdf/{history_id}")
def export_pdf(history_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if _generate_debate_report is None:
        raise HTTPException(status_code=501, detail="PDF export is not available. The 'fpdf2' library may not be installed.")
    history = db.query(ChatHistory).filter(ChatHistory.id == history_id, ChatHistory.user_id == current_user.id).first()
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    messages = db.query(DebateMessage).filter(DebateMessage.chat_history_id == history_id).order_by(DebateMessage.id.asc()).all()
    verdicts = db.query(Verdict).filter(Verdict.chat_history_id == history_id).order_by(Verdict.id.asc()).all()
    
    output_path = os.path.join(os.path.dirname(__file__), f"debate_report_{history_id}.pdf")
    _generate_debate_report(history, messages, verdicts, output_path)
    return FileResponse(output_path, filename=f"LLM_Council_Debate_{history_id}.pdf")

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

from rag_utils import save_precedent
import collections

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        # room_id -> list of websockets
        self.active_rooms = collections.defaultdict(list)

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        self.active_rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_rooms and websocket in self.active_rooms[room_id]:
            self.active_rooms[room_id].remove(websocket)
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

    async def broadcast_to_room(self, message: str, room_id: str):
        for connection in self.active_rooms.get(room_id, []):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.debug(f"Failed to send to WebSocket in room {room_id}: {e}")

manager = ConnectionManager()

@app.websocket("/ws/debate/{room_id}")
async def debate_websocket(websocket: WebSocket, room_id: str, token: str = Query(None), db: Session = Depends(get_db)):
    if not token:
        await websocket.close(code=1008)
        return
    try:
        current_user = get_current_user_from_token(token, db)
    except Exception as e:
        logger.warning(f"WebSocket auth failed for room {room_id}: {e}")
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, room_id)
    session_id = str(id(websocket)) # or use room_id if media is shared across the room
    
    # In multiplayer, we might want media to be room-scoped, but for now we'll scope to room_id
    if room_id not in debate_graph.live_media_context:
        debate_graph.live_media_context[room_id] = {"audio": [], "video": None, "files": []}
    
    # Max payload size set to 5MB to prevent memory exhaustion
    MAX_PAYLOAD_BYTES = 5 * 1024 * 1024
    
    try:
        while True:
            data = await websocket.receive_text()
            if len(data.encode('utf-8')) > MAX_PAYLOAD_BYTES:
                await websocket.close(code=1009, reason="Payload too large")
                return
                
            payload = json.loads(data)
            action = payload.get("action")
            
            if action == "convene" or action == "branch":
                prompt = payload.get("prompt")
                personality = payload.get("personality", {"aggression": 50, "creativity": 50})
                branch_context = payload.get("branch_context")
                
                async def ws_stream_callback(agent, msg_type, token_text):
                    # Broadcast to everyone in the room
                    await manager.broadcast_to_room(json.dumps({
                        "type": msg_type, 
                        "agent": agent, 
                        "token": token_text,
                        "status": "thinking" if msg_type == "thinking" else "done" if msg_type == "done" else None
                    }), room_id)
                
                debate_graph.stream_callbacks[room_id] = ws_stream_callback
                
                # Fetch custom agents for this user
                user_agents = db.query(CustomAgent).filter(CustomAgent.user_id == current_user.id).all()
                app_graph = debate_graph.build_graph(user_agents)
                
                topic = prompt
                if action == "branch" and branch_context:
                    topic = f"{prompt}\n\n[TIMELINE DIVERGENCE: The Council MUST assume the following statement is absolute truth for this debate run]:\n\"{branch_context}\""
                
                # Create history record
                chat_history = ChatHistory(user_id=current_user.id, title=prompt[:50] + "..." if len(prompt) > 50 else prompt)
                db.add(chat_history)
                db.commit()
                db.refresh(chat_history)
                
                # Capture values needed by the background task
                history_id = chat_history.id
                user_id = current_user.id
                
                initial_state = {
                    "messages": [HumanMessage(content=topic)],
                    "round_count": 0,
                    "max_rounds": 2, 
                    "current_topic": topic,
                    "session_id": room_id, # Link media context to room_id
                    "personality": personality
                }
                
                await manager.broadcast_to_room(json.dumps({"type": "system", "message": "Starting LangGraph Debate..." if action == "convene" else "Spawning Alternate Timeline..."}), room_id)
                
                async def run_graph():
                    # Create a dedicated DB session for this background task.
                    # The FastAPI Depends(get_db) session may be closed by the
                    # time this coroutine executes.
                    task_db = SessionLocal()
                    try:
                        result_state = await app_graph.ainvoke(initial_state)
                        await manager.broadcast_to_room(json.dumps({"type": "system", "message": "Debate Complete"}), room_id)
                        
                        judge_verdict_text = ""
                        # Save messages and verdicts
                        for msg in result_state.get("messages", []):
                            if isinstance(msg, HumanMessage):
                                continue # optionally save user prompt
                            agent_name = getattr(msg, "name", "unknown")
                            if agent_name == "judge":
                                v = Verdict(chat_history_id=history_id, verdict_text=msg.content, confidence="HIGH")
                                judge_verdict_text = msg.content
                                task_db.add(v)
                            else:
                                dm = DebateMessage(chat_history_id=history_id, agent_name=agent_name, content=msg.content)
                                task_db.add(dm)
                        task_db.commit()
                        
                        # Save to Long-Term Memory (ChromaDB)
                        if judge_verdict_text:
                            save_precedent(topic, judge_verdict_text, history_id)
                            
                    except Exception as e:
                        logger.error(f"Graph execution failed for room {room_id}: {e}", exc_info=True)
                        try:
                            await manager.broadcast_to_room(json.dumps({"type": "system", "message": f"Council Error: {str(e)}"}), room_id)
                        except Exception:
                            pass
                    finally:
                        task_db.close()
                        # Clean up per-session callback
                        debate_graph.stream_callbacks.pop(room_id, None)
                
                asyncio.create_task(run_graph())
                
            elif action == "audio_stream":
                text = payload.get("text")
                if text:
                    debate_graph.live_media_context[room_id]["audio"].append(text)
            elif action == "video_stream":
                frame = payload.get("frame")
                if frame:
                    debate_graph.live_media_context[room_id]["video"] = frame
            elif action == "file_drop":
                filename = payload.get("filename")
                content = payload.get("content")
                if filename and content:
                    debate_graph.live_media_context[room_id]["files"].append((filename, content))
            elif action == "chat_message":
                # For multiplayer chat
                msg_text = payload.get("text")
                if msg_text:
                    await manager.broadcast_to_room(json.dumps({
                        "type": "chat",
                        "user": current_user.username,
                        "text": msg_text
                    }), room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        if not manager.active_rooms.get(room_id):
            if room_id in debate_graph.live_media_context:
                del debate_graph.live_media_context[room_id]
    except Exception as e:
        logger.error(f"WS Error in room {room_id}: {e}", exc_info=True)
        manager.disconnect(websocket, room_id)
        if not manager.active_rooms.get(room_id):
            if room_id in debate_graph.live_media_context:
                del debate_graph.live_media_context[room_id]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting FastAPI server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
