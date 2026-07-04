# Project Details
## Project Name: LLM Council (v4.0 Enterprise Edition)

### Overview
LLM Council is a highly experimental, sophisticated multi-agent system designed to bring the power of diverse LLM perspectives to the end-user. Instead of relying on a single AI model to answer a prompt, LLM Council orchestrates a debate between four distinct AI personalities, followed by a final verdict from a "Judge" agent. The system now supports Custom Agents defined by the user to tailor debates to highly specific use-cases.

### Motivation
As LLMs become more capable, their biases, limitations, and "hallucinations" remain a challenge. By having multiple state-of-the-art models (Llama, Qwen, Gemini, Mistral, DeepSeek) debate each other, the system forces rigorous fact-checking, strategic planning, and philosophical grounding. The result is a much more robust, well-rounded answer than any single model could provide. 

With version 4.0, the motivation expanded to include creating a secure, enterprise-grade architecture capable of defending against malicious inputs, credential stuffing, and resource exhaustion.

### Team
- **Creator/Lead Developer**: AMMAR (BEAST-AMMAR)
- **AI Assistant**: Google DeepMind Agent (Antigravity)

### Timeline & Milestones
- **v1.0**: Initial command-line prototype of multi-agent debate.
- **v2.0**: Introduction of the JARVIS-style frontend UI with basic WebSocket streaming.
- **v3.0**: 
  - Complete migration to FastAPI backend and Next.js frontend.
  - Implementation of Hybrid Model Adapter (Cloud OpenRouter + Local GGUF execution).
  - Advanced multimodal capabilities (Voice API, WebCam capture, Image uploading).
- **v4.0 (Enterprise Edition - Current)**:
  - Total security overhaul: implemented `slowapi` rate limiting, WebSocket payload bounds, and strict Pydantic input validation.
  - Hardened JWT lifecycle with secure fallback runtime secrets.
  - Complete folder structure reorganization (moved tests, scripts, and docs into dedicated directories).
  - UI-driven Custom Agent creation with database persistence.
  - Robust search fallback layer (DuckDuckGo -> Tavily API) for agent fact-checking.

### Technological Highlights
- **LangGraph Integration**: State-of-the-art graph-based AI orchestration allows complex routing of context between agents without messy imperative code.
- **Real-Time Streaming**: The integration of Python `asyncio` and FastAPI WebSockets ensures that the user doesn't wait minutes for the debate to finish; they read the debate in real-time token-by-token.
- **Cost Efficiency & Privacy**: Utilizing OpenRouter's free tier models ensures that the application is accessible and completely free to run in the cloud, while local `.gguf` fallback ensures absolute privacy and offline capability.
- **Enterprise Security**: Built to withstand brute-force login attempts, massive file drop payloads, and SQL injection via strict ORM usage.
