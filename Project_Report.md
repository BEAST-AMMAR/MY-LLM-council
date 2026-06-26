# Project Report
## Project Name: LLM Council

### 1. Executive Summary
LLM Council successfully bridges the gap between single-model querying and comprehensive multi-model reasoning. The release of version 3.0 has significantly enhanced the system architecture, migrating from a basic Python script to an enterprise-grade FastAPI/Next.js application capable of real-time WebSocket communication and complex graph-based AI orchestration.

### 2. Objectives Achieved
- **Multi-Agent Orchestration**: Successfully implemented a 5-agent debate system using LangGraph. Agents (Sage, Analyst, Strategist, Skeptic, and Judge) effectively pass context, maintain individual personalities, and synthesize final verdicts.
- **Multimodal Context**: Integrated HTML5 canvas and Web Speech API into the Next.js frontend, allowing the backend to receive image attachments, live video frames, and transcribed audio as debate context.
- **Hybrid Execution**: Built the `hybrid_adapter.py` layer, which dynamically routes requests either to OpenRouter's cloud APIs or to local `.gguf` weights, providing users with the choice between high-speed cloud execution and absolute local privacy.
- **Real-Time Streaming**: Resolved previous latency issues by utilizing FastAPI WebSockets and LangGraph's streaming capabilities, ensuring the user interface updates instantly as tokens are generated.

### 3. Technical Challenges & Solutions
#### 3.1 Synchronous vs Asynchronous Graph Execution
**Challenge**: LangChain and LangGraph default to synchronous execution which blocks the FastAPI event loop, causing the WebSocket to drop connection or fail to receive intermediate tokens.
**Solution**: Migrated the graph invocation to use `ainvoke` and wrapped the execution in `asyncio.create_task()`. Implemented custom async stream callbacks to push tokens to the active WebSocket session seamlessly.

#### 3.2 Handling Large Multimodal Payloads via WebSockets
**Challenge**: Sending base64 video frames repeatedly via WebSockets caused buffer bloat and server lag.
**Solution**: Optimized the frontend to only capture and send keyframes when the user explicitly triggers a "capture" event, rather than streaming raw 30fps video into the LLM context.

#### 3.3 Free Tier API Rate Limiting
**Challenge**: Hitting OpenRouter's free tier endpoints simultaneously for 4 agents resulted in 429 Too Many Requests errors.
**Solution**: Staggered the initial agent analysis using `asyncio.sleep` delays and implemented a robust fallback mechanism that automatically switches to a secondary model if the primary model is rate-limited.

### 4. Future Roadmap
- **Custom Agent Builder**: Allow users to dynamically define agent names, prompts, and assigned models directly from the frontend UI.
- **Persistent Database Analytics**: Expand the SQLite implementation to store and query historical debate metrics, allowing users to review past verdicts.
- **Mobile Responsiveness**: Enhance the Tailwind CSS styling to ensure the UI is fully functional and aesthetic on iOS and Android devices.
- **Export to PDF Integration**: Improve the `generate_pdf.py` script to allow users to download a beautifully formatted report of their specific debate sessions.
