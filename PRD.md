# Product Requirements Document (PRD)
## Project Name: LLM Council

### 1. Introduction
LLM Council is a multi-agent AI debate system where four specialized LLM agents discuss and debate a user-provided prompt or topic, while a fifth "Judge" agent oversees the debate, synthesizes arguments, and delivers a final verdict. The product allows users to gain diverse perspectives on complex problems before arriving at a well-reasoned conclusion.

### 2. Objectives
- Provide users with highly nuanced, well-debated answers to complex queries.
- Support multimodal inputs (Text, Voice, Image, and live Webcam Video) to make the council accessible and versatile.
- Deliver an interactive "JARVIS-like" user interface where users can watch the AI agents deliberate in real-time.
- Offer local and cloud model execution capabilities.

### 3. Target Audience
- Researchers and professionals looking for deep analysis of complex topics.
- Developers and tech enthusiasts interested in multi-agent LangGraph architectures.
- General users seeking an advanced alternative to single-model chatbots.

### 4. Key Features
#### 4.1. The Council (Multi-Agent System)
- **Sage (Philosopher)**: Focuses on ethical, philosophical, and long-term implications.
- **Analyst (Logician)**: Focuses on data, logic, factual correctness, and structural breakdown.
- **Strategist (Visionary)**: Focuses on actionable plans, future trends, and out-of-the-box thinking.
- **Skeptic (Challenger)**: Acts as the devil's advocate, finding flaws in the other agents' reasoning.
- **Judge**: Synthesizes the debate, issues a final verdict, provides a confidence score, and determines if a rerun is necessary.

#### 4.2. Multimodal Inputs
- **Text**: Standard keyboard input.
- **Voice**: Speech-to-text integration via browser Web Speech API.
- **Image Upload**: Users can drop files into the context.
- **Live Video Stream**: Captures webcam frames to pass vision context to the council.

#### 4.3. Real-Time Streaming & Interaction
- The UI streams the agents' internal thoughts ("thinking") and final tokens in real-time via WebSockets.
- **Branching Timelines**: Users can branch off the debate with a hypothetical scenario ("what if X was true?") to see how the council reacts.

#### 4.4. Audio Output
- **Text-to-Speech (TTS)**: The final verdict from the Judge is read aloud.

#### 4.5. Hybrid Model Support
- Users can toggle between **Cloud Mode** (OpenRouter APIs for Llama 3, Qwen, Gemini, DeepSeek, Mistral) and **Local Mode** (using locally downloaded weights for privacy).

### 5. Non-Functional Requirements
- **Performance**: Real-time WebSocket streaming with minimal latency.
- **Reliability**: Fallback systems for API timeouts. The Judge has a safe low-confidence fallback if all models fail.
- **Scalability**: Stateless WebSocket design allowing for multiple concurrent debate sessions.
- **Security**: Local SQLite database for session and user authentication. Token-based auth for secure access.

### 6. Future Enhancements
- Integration of custom user-defined agents.
- Saving debate transcripts and exporting to PDF.
- Persistent user history across devices.
