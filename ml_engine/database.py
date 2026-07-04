from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./llm_council.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    chat_histories = relationship("ChatHistory", back_populates="owner")
    custom_agents = relationship("CustomAgent", back_populates="owner")

class CustomAgent(Base):
    __tablename__ = "custom_agents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    model = Column(String, nullable=False)
    provider = Column(String, nullable=False) # 'openrouter' or 'local'
    vision_capable = Column(Integer, default=0) # SQLite doesn't have a real boolean type, use Integer 0/1
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    owner = relationship("User", back_populates="custom_agents")

class ChatHistory(Base):
    __tablename__ = "chat_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="Debate Session")
    transcript = Column(Text, default="[]") # Legacy JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    owner = relationship("User", back_populates="chat_histories")
    messages = relationship("DebateMessage", back_populates="chat_history")
    verdicts = relationship("Verdict", back_populates="chat_history")

class DebateMessage(Base):
    __tablename__ = "debate_messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_history_id = Column(Integer, ForeignKey("chat_histories.id"))
    agent_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    chat_history = relationship("ChatHistory", back_populates="messages")

class Verdict(Base):
    __tablename__ = "verdicts"
    id = Column(Integer, primary_key=True, index=True)
    chat_history_id = Column(Integer, ForeignKey("chat_histories.id"))
    verdict_text = Column(Text, nullable=False)
    confidence = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    chat_history = relationship("ChatHistory", back_populates="verdicts")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
