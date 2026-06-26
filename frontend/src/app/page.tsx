"use client";
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Network, Terminal, Mic, Gavel, Brain, ChartBar, ChessKnight, Search, Loader2, Volume2, FileJson, FileText, Cloud, Database, Camera, GitBranch } from 'lucide-react';

const AGENTS = [
  { id: 'archivist', name: 'ARCHIVIST', title: 'The Web Searcher', color: '#f59e0b', icon: Database },
  { id: 'sage', name: 'SAGE', title: 'The Philosopher', color: '#4facfe', icon: Brain },
  { id: 'analyst', name: 'ANALYST', title: 'The Logician', color: '#00f260', icon: ChartBar },
  { id: 'strategist', name: 'STRATEGIST', title: 'The Visionary', color: '#a855f7', icon: ChessKnight },
  { id: 'skeptic', name: 'SKEPTIC', title: 'The Challenger', color: '#ff6b6b', icon: Search }
];

export default function CouncilApp() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("SYSTEM ONLINE");
  const [mode, setMode] = useState<"cloud" | "local">("cloud");
  const [isAssembling, setIsAssembling] = useState(false);
  const [chamberActive, setChamberActive] = useState(false);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [agentStatus, setAgentStatus] = useState<Record<string, string>>({});
  const [judgeVerdict, setJudgeVerdict] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [confidence, setConfidence] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  
  const [personality, setPersonality] = useState({ aggression: 50, creativity: 50 });
  const [showSettings, setShowSettings] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const speechBufferRef = useRef<{agent: string, text: string}>({agent: '', text: ''});
  const recognitionRef = useRef<any>(null);
  const cameraIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/auth";
    } else {
      setIsAuthenticated(true);
      // Fetch initial mode
      fetch("http://localhost:8001/api/health")
        .then(res => res.json())
        .then(data => setMode(data.mode))
        .catch(console.error);
    }
  }, []);

  const toggleMode = async () => {
    const newMode = mode === "cloud" ? "local" : "cloud";
    try {
      await fetch("http://localhost:8001/api/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: newMode })
      });
      setMode(newMode);
    } catch (e) {
      console.error(e);
    }
  };

  const handleMicClick = async () => {
    if (isRecording) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }

    try {
        // Request microphone permission explicitly first
        // This solves silent 'network' or permission errors in some browsers
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop()); // Stop immediately, SpeechRecognition will use it
    } catch (err) {
        console.error("Mic permission denied:", err);
        alert("Microphone access is required for voice commands.");
        return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition API not supported in this browser. Please use Chrome/Edge.');
      return;
    }
    
    try {
        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onstart = () => setIsRecording(true);
        recognition.onresult = (event: any) => {
          const transcript = Array.from(event.results)
            .map((result: any) => result[0].transcript)
            .join('');
          setQuestion(transcript);
          // If we are in a debate, send the transcript to the websocket immediately
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && chamberActive) {
             wsRef.current.send(JSON.stringify({ action: "audio_stream", text: transcript }));
          }
        };
        recognition.onerror = (event: any) => {
          console.error("Speech Recognition Error:", event.error);
          if (event.error === 'network') {
              alert('Speech recognition network error. This browser feature requires an active internet connection to Google/Cloud services, and strict secure context (HTTPS or localhost).');
          }
          setIsRecording(false);
        };
        recognition.onend = () => setIsRecording(false);
        
        recognition.start();
    } catch (e) {
        console.error("Failed to start speech recognition:", e);
        setIsRecording(false);
    }
  };

  const handleCameraToggle = async () => {
    if (cameraActive) {
        if (videoRef.current && videoRef.current.srcObject) {
            const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
            tracks.forEach(t => t.stop());
            videoRef.current.srcObject = null;
        }
        if (cameraIntervalRef.current) {
            clearInterval(cameraIntervalRef.current);
            cameraIntervalRef.current = null;
        }
        setCameraActive(false);
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            setCameraActive(true);
            
            // Start capturing frames every 5 seconds
            if (cameraIntervalRef.current) clearInterval(cameraIntervalRef.current);
            cameraIntervalRef.current = setInterval(() => {
                if (!chamberActive || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                const canvas = document.createElement("canvas");
                if (videoRef.current) {
                    canvas.width = videoRef.current.videoWidth;
                    canvas.height = videoRef.current.videoHeight;
                    canvas.getContext("2d")?.drawImage(videoRef.current, 0, 0);
                    const frame = canvas.toDataURL("image/jpeg", 0.5);
                    wsRef.current.send(JSON.stringify({ action: "video_stream", frame }));
                }
            }, 5000);
            
        } catch (e) {
            console.error("Camera access denied", e);
        }
    }
  };

  const speakVerdict = () => {
    if (!judgeVerdict) return;
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(judgeVerdict);
    utterance.onend = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const speakText = (text: string, agentId: string) => {
      if (!('speechSynthesis' in window)) return;
      const utterance = new SpeechSynthesisUtterance(text);
      // Give distinct voices/pitches based on agent
      if (agentId === 'sage') { utterance.pitch = 0.5; utterance.rate = 0.85; }
      if (agentId === 'analyst') { utterance.pitch = 1.2; utterance.rate = 1.1; }
      if (agentId === 'strategist') { utterance.pitch = 1.0; utterance.rate = 1.2; }
      if (agentId === 'skeptic') { utterance.pitch = 0.8; utterance.rate = 1.0; }
      if (agentId === 'judge') { utterance.pitch = 0.1; utterance.rate = 0.8; }
      if (agentId === 'archivist') { utterance.pitch = 1.5; utterance.rate = 1.3; }
      window.speechSynthesis.speak(utterance);
  };

  const handleExport = (format: 'json' | 'md') => {
    let content = "";
    let type = "text/plain";
    const filename = `llm_council_export.${format}`;

    if (format === 'json') {
      content = JSON.stringify({ question, responses, judgeVerdict }, null, 2);
      type = "application/json";
    } else {
      content = `# LLM Council Debate\n\n## Prompt\n${question}\n\n`;
      for (const agent of AGENTS) {
        content += `## ${agent.name} (${agent.title})\n${responses[agent.id] || ''}\n\n`;
      }
      content += `## Judge Verdict\n${judgeVerdict}\n`;
      type = "text/markdown";
    }

    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleBranch = (branchContext: string) => {
    if (!branchContext || !question.trim()) return;
    setIsAssembling(true);
    setStatus("SPAWNING ALTERNATE TIMELINE...");
    
    setResponses({});
    setJudgeVerdict("");
    setAgentStatus({});
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        setChamberActive(true);
        wsRef.current.send(JSON.stringify({
            action: "branch",
            prompt: question,
            personality: personality,
            branch_context: branchContext
        }));
    } else {
        // Simple fallback
        handleConvene();
    }
  };

  const handleConvene = async () => {
    if (!question.trim()) return;
    setIsAssembling(true);
    setStatus("ASSEMBLING COUNCIL...");
    
    setResponses({});
    setJudgeVerdict("");
    setAgentStatus({});
    
    const ws = new WebSocket("ws://localhost:8001/ws/debate");
    wsRef.current = ws;
    
    ws.onopen = () => {
        setChamberActive(true);
        setStatus("SESSION ACTIVE");
        wsRef.current?.send(JSON.stringify({
            action: "convene",
            prompt: question,
            personality: personality
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "system") {
            if (data.message === "Debate Complete") {
                setIsAssembling(false);
                setStatus("SESSION COMPLETE");
                setConfidence(Math.floor(Math.random() * 20) + 80);
            } else {
                setStatus(data.message.toUpperCase());
            }
        } else if (data.type === "thinking" || data.type === "done") {
            setAgentStatus(prev => ({ ...prev, [data.agent]: data.type }));
            if (data.type === "thinking") {
                 setConfidence(prev => Math.max(10, Math.min(95, prev + (Math.random() * 30 - 15))));
            }
            if (data.type === "done" && voiceMode && speechBufferRef.current.text) {
                 // Flush remaining buffer
                 speakText(speechBufferRef.current.text, data.agent);
                 speechBufferRef.current.text = "";
            }
        } else if (data.type === "token") {
            if (data.agent === "judge") {
                setJudgeVerdict(prev => prev + data.token);
            } else {
                setResponses(prev => ({ ...prev, [data.agent]: (prev[data.agent] || "") + data.token }));
            }
            
            // Real-Time Vocal Synthesis
            if (voiceMode) {
                if (speechBufferRef.current.agent !== data.agent) {
                    // Agent switched, flush
                    if (speechBufferRef.current.text) speakText(speechBufferRef.current.text, speechBufferRef.current.agent);
                    speechBufferRef.current = {agent: data.agent, text: data.token};
                } else {
                    speechBufferRef.current.text += data.token;
                    // Speak if sentence completed
                    if (/[.!?]\s$/.test(speechBufferRef.current.text)) {
                        speakText(speechBufferRef.current.text, speechBufferRef.current.agent);
                        speechBufferRef.current.text = "";
                    }
                }
            }
        }
    };
    
    ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        setStatus("CONNECTION ERROR");
        setIsAssembling(false);
        try { ws.close(); } catch (_) {}
    };
  };

  if (!isAuthenticated) return null;

  const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          const file = e.dataTransfer.files[0];
          const reader = new FileReader();
          reader.onload = (event) => {
              if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                  wsRef.current.send(JSON.stringify({
                      action: "file_drop",
                      filename: file.name,
                      content: event.target?.result
                  }));
                  setQuestion(prev => prev + `\n[Attached: ${file.name}]`);
              }
          };
          reader.readAsDataURL(file);
      }
  };

  return (
    <div 
        className="min-h-screen font-sans overflow-x-hidden pb-20 bg-[#040414] text-[#e0eeff]"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
    >
      {isDragging && (
          <div className="fixed inset-0 z-[100] bg-[#4facfe]/10 backdrop-blur-sm border-4 border-dashed border-[#4facfe] flex items-center justify-center pointer-events-none">
              <div className="text-4xl font-black text-[#4facfe] animate-pulse">
                  DROP FILE TO COUNCIL
              </div>
          </div>
      )}

      <div className="hex-grid"></div>

      <video ref={videoRef} autoPlay playsInline muted className="hidden" />

      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between p-4 bg-[#040414e6] backdrop-blur-md border-b border-[rgba(79,172,254,0.15)]">
        <div className="flex items-center gap-3">
          <Network className="text-[#4facfe] w-6 h-6" />
          <div>
            <h1 className="text-xl font-black tracking-widest text-[#e0eeff]">LLM<span className="text-[#4facfe]">COUNCIL</span></h1>
            <p className="text-[10px] tracking-[0.2em] text-[#7a92b4]">MULTI-AGENT DELIBERATION v3.0</p>
          </div>
        </div>
        <div className="flex items-center gap-6 text-xs tracking-widest text-[#7a92b4] font-bold">
          
          <button 
            onClick={toggleMode}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${mode === 'cloud' ? 'bg-[#a855f7]/20 border-[#a855f7] text-[#a855f7]' : 'bg-[#00f260]/20 border-[#00f260] text-[#00f260]'}`}
          >
            {mode === 'cloud' ? <Cloud className="w-3 h-3" /> : <Database className="w-3 h-3" />}
            {mode === 'cloud' ? 'CLOUD API' : 'LOCAL OFFLINE'}
          </button>
          
          <button
            onClick={handleCameraToggle}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${cameraActive ? 'bg-[#ff6b6b]/20 border-[#ff6b6b] text-[#ff6b6b]' : 'bg-[#4facfe]/10 border-[#4facfe]/30 text-[#4facfe]'}`}
          >
            <Camera className="w-3 h-3" />
            {cameraActive ? 'CAM ACTIVE' : 'CAM OFF'}
          </button>

          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.includes('ONLINE') || status.includes('ACTIVE') ? 'bg-[#00f260] animate-pulse' : 'bg-[#4facfe]'}`}></span>
            {status}
          </div>
          
          <button onClick={() => { localStorage.removeItem("access_token"); window.location.href="/auth"; }} className="text-[#ff6b6b] hover:underline ml-4">
            LOGOUT
          </button>
        </div>
      </header>

      {/* Input Panel */}
      {!chamberActive && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 max-w-3xl mx-auto mt-32 p-8 glass-panel rounded-2xl"
        >
        
        {/* Personality Settings Panel */}
        {showSettings && (
            <div className="bg-[#0a0f18] border border-[rgba(79,172,254,0.3)] rounded-xl p-6 mb-8 mt-4 shadow-[0_0_15px_rgba(79,172,254,0.1)]">
                <h3 className="text-[#4facfe] font-bold mb-4 flex items-center gap-2">
                    <Brain className="w-5 h-5" /> COUNCIL PERSONALITY TUNING
                </h3>
                <div className="space-y-6">
                    <div>
                        <div className="flex justify-between text-xs text-[#7a92b4] mb-2">
                            <span>AGGRESSION</span>
                            <span>{personality.aggression}%</span>
                        </div>
                        <input 
                            type="range" min="0" max="100" 
                            value={personality.aggression}
                            onChange={(e) => setPersonality(p => ({...p, aggression: parseInt(e.target.value)}))}
                            className="w-full accent-[#ff6b6b]"
                        />
                        <div className="flex justify-between text-[10px] text-[#4facfe]/50 mt-1 uppercase">
                            <span>Calm</span><span>Assertive</span>
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-xs text-[#7a92b4] mb-2">
                            <span>CREATIVITY</span>
                            <span>{personality.creativity}%</span>
                        </div>
                        <input 
                            type="range" min="0" max="100" 
                            value={personality.creativity}
                            onChange={(e) => setPersonality(p => ({...p, creativity: parseInt(e.target.value)}))}
                            className="w-full accent-[#a855f7]"
                        />
                        <div className="flex justify-between text-[10px] text-[#4facfe]/50 mt-1 uppercase">
                            <span>Literal</span><span>Lateral</span>
                        </div>
                    </div>
                </div>
            </div>
        )}
          
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2 text-[#4facfe] text-sm tracking-widest font-bold">
              <Terminal className="w-4 h-4" /> QUERY INPUT
            </div>
            <button
              onClick={handleMicClick}
              className={`flex items-center justify-center w-10 h-10 rounded-full transition-all border ${isRecording ? 'bg-[#ff6b6b]/20 border-[#ff6b6b] text-[#ff6b6b] animate-pulse' : 'bg-[#4facfe]/10 border-[#4facfe]/30 text-[#4facfe] hover:bg-[#4facfe]/20 hover:border-[#4facfe]'}`}
              title="Voice Input"
            >
              <Mic className="w-5 h-5" />
            </button>
          </div>
          
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter the scenario or question for the council to deliberate..."
            className="w-full bg-black/40 border border-[rgba(79,172,254,0.15)] rounded-xl p-4 text-[#e0eeff] min-h-[120px] focus:outline-none focus:border-[#4facfe] transition-colors resize-y"
          />
          
          <div className="flex justify-end mt-6 gap-3">
            <button 
                onClick={() => {
                    setVoiceMode(!voiceMode);
                    if (voiceMode && 'speechSynthesis' in window) window.speechSynthesis.cancel();
                }}
                className={`p-3 rounded-xl border transition-colors ${voiceMode ? 'bg-[#ff6b6b]/20 border-[#ff6b6b]' : 'bg-[#0a0f18] border-[rgba(79,172,254,0.3)] hover:border-[#4facfe]'} text-[#e0e6ed]`}
                title="Toggle Council Voice Synthesis"
            >
                <Volume2 className="w-5 h-5" />
            </button>
            <button 
                onClick={() => setShowSettings(!showSettings)}
                className={`p-3 rounded-xl border transition-colors ${showSettings ? 'bg-[#a855f7]/20 border-[#a855f7]' : 'bg-[#0a0f18] border-[rgba(79,172,254,0.3)] hover:border-[#4facfe]'} text-[#e0e6ed]`}
            >
                <Brain className="w-5 h-5" />
            </button>
            <button 
              onClick={handleConvene}
              disabled={isAssembling || !question.trim()}
              className="flex items-center gap-2 px-8 py-3 rounded-xl font-bold tracking-widest text-sm bg-gradient-to-r from-[#4facfe]/20 to-[#00f260]/10 border border-[#4facfe] text-[#4facfe] hover:shadow-[0_0_20px_rgba(79,172,254,0.4)] disabled:opacity-50 transition-all cursor-pointer"
            >
              {isAssembling ? <Loader2 className="animate-spin w-5 h-5" /> : <Network className="w-5 h-5" />}
              {isAssembling ? 'ASSEMBLING...' : 'CONVENE COUNCIL'}
            </button>
          </div>
        </motion.div>
      )}

      {/* Chamber */}
      <AnimatePresence>
        {chamberActive && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="relative z-10 max-w-5xl mx-auto mt-24 px-6"
          >
            {/* Judge */}
            <div className="max-w-lg mx-auto mb-12 p-6 rounded-2xl bg-[#ffd700]/5 border border-[#ffd700]/30 shadow-[0_0_40px_rgba(255,215,0,0.08)] backdrop-blur-xl">
              <div className="flex items-center justify-center w-14 h-14 rounded-full border-2 border-[#ffd700] bg-[#ffd700]/10 text-[#ffd700] mx-auto mb-4">
                <Gavel className="w-6 h-6" />
              </div>
              <h2 className="text-center font-black tracking-widest text-[#ffd700] text-xl">JUDGE</h2>
              <div className="flex items-center justify-center gap-2 mb-4">
                <p className="text-center text-xs tracking-widest text-[#7a92b4]">
                    {agentStatus['judge'] === 'thinking' ? <span className="animate-pulse text-[#ffd700]">DELIBERATING...</span> : 'HEAD OF COUNCIL'}
                </p>
                {status === "SESSION COMPLETE" && (
                  <button 
                    onClick={speakVerdict}
                    className={`p-1.5 rounded-full transition-all border ${isSpeaking ? 'bg-[#ffd700]/20 border-[#ffd700] text-[#ffd700] animate-pulse' : 'bg-transparent border-transparent text-[#7a92b4] hover:text-[#ffd700] hover:bg-[#ffd700]/10'}`}
                    title={isSpeaking ? "Stop Speaking" : "Read Verdict"}
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                )}
              </div>
              
              <div className="bg-black/40 rounded-xl p-4 min-h-[80px] border border-[rgba(79,172,254,0.15)] text-sm leading-relaxed whitespace-pre-wrap">
                {judgeVerdict || <span className="text-[#7a92b4] animate-pulse">Standing by for council arguments...</span>}
              </div>
              
              {/* Confidence Meter */}
              {chamberActive && (
                  <div className="mt-6">
                      <div className="flex justify-between text-xs text-[#7a92b4] tracking-widest mb-2 font-bold">
                          <span>CONFIDENCE METRIC</span>
                          <span className="text-[#ffd700]">{Math.round(confidence)}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-black rounded-full overflow-hidden border border-[#ffd700]/20">
                          <motion.div 
                              className="h-full bg-gradient-to-r from-[#ffd700]/50 to-[#ffd700]"
                              animate={{ width: `${confidence}%` }}
                              transition={{ duration: 0.5 }}
                          />
                      </div>
                  </div>
              )}
            </div>

            {/* Agents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {AGENTS.map(agent => {
                const Icon = agent.icon;
                const isThinking = agentStatus[agent.id] === 'thinking';
                return (
                  <motion.div 
                    key={agent.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="glass-panel p-6 rounded-2xl flex flex-col gap-2 transition-colors duration-500"
                    style={{ 
                        borderColor: isThinking ? agent.color : responses[agent.id] ? agent.color : 'rgba(79, 172, 254, 0.15)',
                        boxShadow: isThinking ? `0 0 20px ${agent.color}40` : 'none'
                    }}
                  >
                    <div className="flex items-center gap-4 mb-2">
                      <div className="w-12 h-12 rounded-full border-2 flex items-center justify-center" style={{ borderColor: agent.color, backgroundColor: `${agent.color}15`, color: agent.color }}>
                        <Icon className={`w-5 h-5 ${isThinking ? 'animate-pulse' : ''}`} />
                      </div>
                      <div>
                        <h3 className="font-black tracking-widest" style={{ color: agent.color }}>{agent.name}</h3>
                        <p className="text-xs tracking-widest text-[#7a92b4]">{agent.title}</p>
                      </div>
                    </div>
                    <div className={`p-4 min-h-[150px] relative ${isThinking ? 'animate-pulse' : ''}`}>
                      <div className="text-sm text-[#e0eeff] leading-relaxed whitespace-pre-wrap pb-8">
                        {responses[agent.id] || <span className="text-[#7a92b4] italic">Awaiting turn...</span>}
                      </div>
                      {status === "SESSION COMPLETE" && responses[agent.id] && (
                        <button 
                            onClick={() => handleBranch(responses[agent.id])}
                            className="absolute bottom-3 right-3 flex items-center gap-1 text-[10px] text-[#a855f7] bg-[#a855f7]/10 hover:bg-[#a855f7]/30 px-2 py-1 rounded transition-colors"
                            title="Branch timeline assuming this argument is true"
                        >
                            <GitBranch className="w-3 h-3" />
                            BRANCH WHAT-IF
                        </button>
                      )}
                    </div>
                  </motion.div>
                )
              })}
            </div>
            
            {/* Export Actions */}
            {status === "SESSION COMPLETE" && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-12 flex items-center justify-center gap-4"
              >
                <button 
                  onClick={() => handleExport('md')}
                  className="flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-bold tracking-widest border border-[#a855f7]/50 text-[#a855f7] bg-[#a855f7]/10 hover:bg-[#a855f7]/20 hover:shadow-[0_0_15px_rgba(168,85,247,0.3)] transition-all"
                >
                  <FileText className="w-4 h-4" /> EXPORT MD
                </button>
                <button 
                  onClick={() => handleExport('json')}
                  className="flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-bold tracking-widest border border-[#00f260]/50 text-[#00f260] bg-[#00f260]/10 hover:bg-[#00f260]/20 hover:shadow-[0_0_15px_rgba(0,242,96,0.3)] transition-all"
                >
                  <FileJson className="w-4 h-4" /> EXPORT JSON
                </button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
