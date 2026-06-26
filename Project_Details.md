# Project Details
## Project Name: LLM Council

### Overview
LLM Council is a highly experimental, sophisticated multi-agent system designed to bring the power of diverse LLM perspectives to the end-user. Instead of relying on a single AI model to answer a prompt, LLM Council orchestrates a debate between four distinct AI personalities, followed by a final verdict from a "Judge" agent.

### Motivation
As LLMs become more capable, their biases, limitations, and "hallucinations" remain a challenge. By having multiple state-of-the-art models (Llama, Qwen, Gemini, Mistral, DeepSeek) debate each other, the system forces rigorous fact-checking, strategic planning, and philosophical grounding. The result is a much more robust, well-rounded answer than any single model could provide.

### Team
- **Creator/Lead Developer**: AMMAR (BEAST-AMMAR)
- **AI Assistant**: Google DeepMind Agent (Antigravity)

### Timeline & Milestones
- **v1.0**: Initial command-line prototype of multi-agent debate.
- **v2.0**: Introduction of the JARVIS-style frontend UI with basic WebSocket streaming.
- **v3.0 (Current)**: 
  - Complete migration to FastAPI backend and Next.js frontend.
  - Implementation of Hybrid Model Adapter (Cloud OpenRouter + Local GGUF execution).
  - Advanced multimodal capabilities (Voice API, WebCam capture, Image uploading).
  - Implementation of SQLite Database for user management.
  - Support for "Branching Timelines" during debate.

### Technological Highlights
- **LangGraph Integration**: State-of-the-art graph-based AI orchestration allows complex routing of context between agents without messy imperative code.
- **Real-Time Streaming**: The integration of Python `asyncio` and FastAPI WebSockets ensures that the user doesn't wait minutes for the debate to finish; they read the debate in real-time token-by-token.
- **Cost Efficiency**: Utilizing OpenRouter's free tier models ensures that the application is accessible and completely free to run in the cloud, while local `.gguf` fallback ensures absolute privacy and offline capability.
