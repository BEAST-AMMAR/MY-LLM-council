"use client";
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Network, Terminal, Mic, Gavel, Brain, ChartBar, ChessKnight, Search, Loader2, Volume2, FileJson, FileText, Cloud, Database, Camera, GitBranch, History, UserPlus, X, Download } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_ML_ENGINE_URL || "http://localhost:8001";
const WS_BASE = API_BASE.replace(/^http/, 'ws');

const DEFAULT_AGENTS = [
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

  // New v4.0 States
  const [customAgents, setCustomAgents] = useState<any[]>([]);
  const [showAgentBuilder, setShowAgentBuilder] = useState(false);
  const [newAgent, setNewAgent] = useState({ name: '', role: '', system_prompt: '', model: 'google/gemma-4-31b-it:free', provider: 'openrouter' });
  
  const [history, setHistory] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [historyDetail, setHistoryDetail] = useState<any>(null);
  
  const [roomCode, setRoomCode] = useState("");
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState("");
  
  const wsRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const speechBufferRef = useRef<{agent: string, text: string}>({agent: '', text: ''});
  const recognitionRef = useRef<any>(null);
  const cameraIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAgents = async () => {
    const res = await fetch(`${API_BASE}/api/agents`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    });
    if (res.ok) {
        const data = await res.json();
        setCustomAgents(data);
    }
  };

  const fetchHistory = async () => {
    const res = await fetch(`${API_BASE}/api/history`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    });
    if (res.ok) {
        const data = await res.json();
        setHistory(data);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/auth";
    } else {
      setIsAuthenticated(true);
      fetch(`${API_BASE}/api/health`)
        .then(res => res.json())
        .then(data => setMode(data.mode))
        .catch(console.error);
        
      fetchAgents();
      fetchHistory();
    }
    
    // Cleanup on unmount: close WebSocket and stop camera
    return () => {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (_) {}
        wsRef.current = null;
      }
      if (cameraIntervalRef.current) {
        clearInterval(cameraIntervalRef.current);
        cameraIntervalRef.current = null;
      }
    };
  }, []);

  const handleCreateAgent = async () => {
      if (!newAgent.name.trim() || !newAgent.role.trim() || !newAgent.system_prompt.trim()) {
          alert("Please fill out the Name, Role, and System Prompt fields.");
          return;
      }
      await fetch(`${API_BASE}/api/agents`, {
          method: "POST",
          headers: { 
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
          },
          body: JSON.stringify(newAgent)
      });
      fetchAgents();
      setShowAgentBuilder(false);
  };
  
  const handleDeleteAgent = async (id: number) => {
      await fetch(`${API_BASE}/api/agents/${id}`, {
          method: "DELETE",
          headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      fetchAgents();
  };

  const handleViewHistory = async (id: number) => {
      const res = await fetch(`${API_BASE}/api/history/${id}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await res.json();
      setHistoryDetail(data);
  };

  const handleDownloadPDF = async (id?: number) => {
    let targetId = id;
    if (!targetId) {
        // Fetch fresh history data and use the response directly
        // instead of reading from stale React state.
        const res = await fetch(`${API_BASE}/api/history`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });
        if (res.ok) {
            const freshHistory = await res.json();
            setHistory(freshHistory);
            if (freshHistory.length > 0) targetId = freshHistory[0].id;
        }
    }
    if (targetId) {
        const res = await fetch(`${API_BASE}/api/export-pdf/${targetId}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });
        if (!res.ok) {
            console.error("PDF export failed:", res.status);
            return;
        }
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Debate_Report_${targetId}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
  };

  const toggleMode = async () => {
    const newMode = mode === "cloud" ? "local" : "cloud";
    try {
      await fetch(`${API_BASE}/api/mode`, {
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
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
    } catch (err) {
        alert("Microphone access is required for voice commands.");
        return;
    }
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition API not supported.');
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
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && chamberActive) {
             wsRef.current.send(JSON.stringify({ action: "audio_stream", text: transcript }));
          }
        };
        recognition.onerror = () => setIsRecording(false);
        recognition.onend = () => setIsRecording(false);
        recognition.start();
    } catch (e) {
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
            if (videoRef.current) videoRef.current.srcObject = stream;
            setCameraActive(true);
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
      Object.keys(responses).forEach(key => {
        content += `## ${key.toUpperCase()}\n${responses[key]}\n\n`;
      });
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
        if (wsRef.current) {
            try { wsRef.current.close(); } catch(e) {}
        }
        // Open a new WebSocket and send branch action with context
        const token = localStorage.getItem("access_token");
        const currentRoom = roomCode.trim() || `room_${Math.random().toString(36).substring(2, 9)}`;
        if (!roomCode.trim()) setRoomCode(currentRoom);
        const ws = new WebSocket(`${WS_BASE}/ws/debate/${currentRoom}?token=${token}`);
        wsRef.current = ws;
        ws.onopen = () => {
            setChamberActive(true);
            setStatus("SESSION ACTIVE");
            ws.send(JSON.stringify({
                action: "branch",
                prompt: question,
                personality: personality,
                branch_context: branchContext
            }));
        };
        // Re-use the same message handler logic
        ws.onmessage = handleWsMessage;
        ws.onerror = handleWsError;
    }
  };

  // Shared WS message handler — used by both handleConvene and handleBranch
  const handleWsMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      if (data.type === "system") {
          if (data.message === "Debate Complete") {
              setIsAssembling(false);
              setStatus("SESSION COMPLETE");
              setConfidence(Math.floor(Math.random() * 20) + 80);
              fetchHistory(); // refresh history
          } else {
              setStatus(data.message.toUpperCase());
          }
      } else if (data.type === "thinking" || data.type === "done") {
          setAgentStatus(prev => ({ ...prev, [data.agent]: data.type }));
          if (data.type === "thinking") {
               setConfidence(prev => Math.max(10, Math.min(95, prev + (Math.random() * 30 - 15))));
          }
          if (data.type === "done" && voiceMode && speechBufferRef.current.text) {
               speakText(speechBufferRef.current.text, data.agent);
               speechBufferRef.current.text = "";
          }
      } else if (data.type === "token") {
          if (data.agent === "judge") {
              setJudgeVerdict(prev => prev + data.token);
          } else {
              setResponses(prev => ({ ...prev, [data.agent]: (prev[data.agent] || "") + data.token }));
          }
          if (voiceMode) {
              if (speechBufferRef.current.agent !== data.agent) {
                  if (speechBufferRef.current.text) speakText(speechBufferRef.current.text, speechBufferRef.current.agent);
                  speechBufferRef.current = {agent: data.agent, text: data.token};
              } else {
                  speechBufferRef.current.text += data.token;
                  if (/[.!?]\s$/.test(speechBufferRef.current.text)) {
                      speakText(speechBufferRef.current.text, speechBufferRef.current.agent);
                      speechBufferRef.current.text = "";
                  }
              }
          }
      } else if (data.type === "chat") {
          setChatMessages(prev => [...prev, data]);
      }
  };

  const handleWsError = (err: Event) => {
      setStatus("CONNECTION ERROR");
      setIsAssembling(false);
      if (wsRef.current) {
          try { wsRef.current.close(); } catch (_) {}
      }
  };

  const handleConvene = async () => {
    if (!question.trim()) return;
    setIsAssembling(true);
    setStatus("ASSEMBLING COUNCIL...");
    setResponses({});
    setJudgeVerdict("");
    setAgentStatus({});
    
    if (wsRef.current) {
        try { wsRef.current.close(); } catch(e) {}
    }
    
    const token = localStorage.getItem("access_token");
    const currentRoom = roomCode.trim() || `room_${Math.random().toString(36).substring(2, 9)}`;
    if (!roomCode.trim()) setRoomCode(currentRoom); // Auto-set if empty
    const ws = new WebSocket(`${WS_BASE}/ws/debate/${currentRoom}?token=${token}`);
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
    
    ws.onmessage = handleWsMessage;
    ws.onerror = handleWsError;
  };

  if (!isAuthenticated) return null;

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

  const handleSendChat = () => {
      if (!chatInput.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      wsRef.current.send(JSON.stringify({ action: "chat_message", text: chatInput }));
      setChatInput("");
  };

  const activeAgents = customAgents.length > 0 
    ? [DEFAULT_AGENTS[0], ...customAgents.map(a => ({
        id: a.name.toLowerCase().replaceAll(' ', '_'),
        name: a.name.toUpperCase(),
        title: a.role,
        color: '#4facfe',
        icon: Brain
      }))]
    : DEFAULT_AGENTS;

  return (
    <div 
        className="min-h-screen font-sans overflow-x-hidden pb-20 bg-[#040414] text-[#e0eeff]"
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
        onDrop={handleDrop}
    >
      {isDragging && (
          <div className="fixed inset-0 z-[100] bg-[#4facfe]/10 backdrop-blur-sm border-4 border-dashed border-[#4facfe] flex items-center justify-center pointer-events-none">
              <div className="text-4xl font-black text-[#4facfe] animate-pulse">DROP FILE TO COUNCIL</div>
          </div>
      )}

      <div className="hex-grid"></div>
      <video ref={videoRef} autoPlay playsInline muted className="hidden" />

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex flex-col md:flex-row items-center justify-between p-4 bg-[#040414e6] backdrop-blur-md border-b border-[rgba(79,172,254,0.15)] gap-4">
        <div className="flex items-center gap-3 w-full md:w-auto justify-center md:justify-start">
          <Network className="text-[#4facfe] w-6 h-6" />
          <div>
            <h1 className="text-xl font-black tracking-widest text-[#e0eeff]">LLM<span className="text-[#4facfe]">COUNCIL</span></h1>
            <p className="text-[10px] tracking-[0.2em] text-[#7a92b4]">v4.0 ACTIVE</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center justify-center md:justify-end gap-4 text-xs tracking-widest text-[#7a92b4] font-bold w-full md:w-auto">
          <button onClick={() => setShowHistory(true)} className="flex items-center gap-2 hover:text-[#4facfe]"><History className="w-4 h-4"/> HISTORY</button>
          <button onClick={() => setShowAgentBuilder(true)} className="flex items-center gap-2 hover:text-[#4facfe]"><UserPlus className="w-4 h-4"/> AGENTS</button>
          
          <button onClick={toggleMode} className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${mode === 'cloud' ? 'bg-[#a855f7]/20 border-[#a855f7] text-[#a855f7]' : 'bg-[#00f260]/20 border-[#00f260] text-[#00f260]'}`}>
            {mode === 'cloud' ? <Cloud className="w-3 h-3" /> : <Database className="w-3 h-3" />}
            {mode === 'cloud' ? 'CLOUD API' : 'LOCAL OFFLINE'}
          </button>
          
          <button onClick={handleCameraToggle} className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${cameraActive ? 'bg-[#ff6b6b]/20 border-[#ff6b6b] text-[#ff6b6b]' : 'bg-[#4facfe]/10 border-[#4facfe]/30 text-[#4facfe]'}`}>
            <Camera className="w-3 h-3" />
            {cameraActive ? 'CAM ACTIVE' : 'CAM OFF'}
          </button>

          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.includes('ONLINE') || status.includes('ACTIVE') ? 'bg-[#00f260] animate-pulse' : 'bg-[#4facfe]'}`}></span>
            <span className="hidden md:inline">{status}</span>
          </div>
          
          <button onClick={() => { localStorage.removeItem("access_token"); window.location.href="/auth"; }} className="text-[#ff6b6b] hover:underline">
            LOGOUT
          </button>
        </div>
      </header>

      {/* History Modal */}
      <AnimatePresence>
          {showHistory && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                  <div className="bg-[#0a0f18] border border-[rgba(79,172,254,0.3)] rounded-2xl w-full max-w-4xl max-h-[80vh] flex flex-col overflow-hidden">
                      <div className="p-4 border-b border-[rgba(79,172,254,0.15)] flex justify-between items-center">
                          <h2 className="text-[#4facfe] font-bold text-lg flex items-center gap-2"><History/> DEBATE HISTORY</h2>
                          <button onClick={() => {setShowHistory(false); setHistoryDetail(null);}} className="text-[#7a92b4] hover:text-white"><X/></button>
                      </div>
                      <div className="flex-1 overflow-y-auto p-6 flex gap-6">
                          {/* List */}
                          <div className="w-1/3 border-r border-[rgba(79,172,254,0.15)] pr-4 space-y-2">
                              {history.map(h => (
                                  <div key={h.id} onClick={() => handleViewHistory(h.id)} className="p-3 bg-black/40 rounded-lg cursor-pointer hover:border-[#4facfe] border border-transparent transition-colors">
                                      <p className="text-sm text-white font-bold truncate">{h.title}</p>
                                      <p className="text-xs text-[#7a92b4]">{new Date(h.created_at).toLocaleString()}</p>
                                  </div>
                              ))}
                          </div>
                          {/* Detail */}
                          <div className="w-2/3 pl-2 overflow-y-auto max-h-full space-y-4">
                              {historyDetail ? (
                                  <>
                                      <div className="flex justify-between items-center">
                                          <h3 className="text-xl font-bold text-white">{historyDetail.history.title}</h3>
                                          <button onClick={() => handleDownloadPDF(historyDetail.history.id)} className="flex items-center gap-2 px-3 py-1 bg-[#4facfe]/10 text-[#4facfe] rounded-lg border border-[#4facfe] hover:bg-[#4facfe]/20"><Download className="w-4 h-4"/> PDF</button>
                                      </div>
                                      <div className="space-y-4 mt-4">
                                          {historyDetail.messages.map((m: any) => (
                                              <div key={m.id} className="bg-white/5 p-4 rounded-xl border border-white/10">
                                                  <p className="text-xs text-[#4facfe] font-bold mb-2 uppercase">{m.agent_name}</p>
                                                  <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                                              </div>
                                          ))}
                                          {historyDetail.verdicts.map((v: any) => (
                                              <div key={v.id} className="bg-[#ffd700]/5 border border-[#ffd700]/30 p-4 rounded-xl">
                                                  <p className="text-xs text-[#ffd700] font-bold mb-2 uppercase">JUDGE VERDICT - CONFIDENCE {v.confidence}</p>
                                                  <p className="text-sm whitespace-pre-wrap">{v.verdict_text}</p>
                                              </div>
                                          ))}
                                      </div>
                                  </>
                              ) : <p className="text-[#7a92b4] text-center mt-20">Select a debate to view details</p>}
                          </div>
                      </div>
                  </div>
              </motion.div>
          )}
      </AnimatePresence>

      {/* Agent Builder Modal */}
      <AnimatePresence>
          {showAgentBuilder && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                  <div className="bg-[#0a0f18] border border-[rgba(79,172,254,0.3)] rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden">
                      <div className="p-4 border-b border-[rgba(79,172,254,0.15)] flex justify-between items-center">
                          <h2 className="text-[#4facfe] font-bold text-lg flex items-center gap-2"><UserPlus/> CUSTOM AGENTS</h2>
                          <button onClick={() => setShowAgentBuilder(false)} className="text-[#7a92b4] hover:text-white"><X/></button>
                      </div>
                      <div className="p-6 overflow-y-auto">
                          <div className="grid grid-cols-2 gap-4 mb-6">
                              {customAgents.map(ag => (
                                  <div key={ag.id} className="p-4 bg-black/40 border border-[rgba(79,172,254,0.15)] rounded-xl relative group">
                                      <button onClick={() => handleDeleteAgent(ag.id)} className="absolute top-2 right-2 text-red-500 opacity-0 group-hover:opacity-100"><X className="w-4 h-4"/></button>
                                      <h3 className="font-bold text-white uppercase">{ag.name}</h3>
                                      <p className="text-xs text-[#7a92b4]">{ag.role}</p>
                                      <p className="text-xs text-[#4facfe] mt-2 truncate">{ag.model}</p>
                                  </div>
                              ))}
                          </div>
                          
                          <div className="bg-black/20 p-4 rounded-xl border border-white/5 space-y-4">
                              <h3 className="font-bold text-white">Create New Agent</h3>
                              <input placeholder="Agent Name (e.g. Einstein)" className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-sm text-white" value={newAgent.name} onChange={e => setNewAgent({...newAgent, name: e.target.value})} />
                              <input placeholder="Role (e.g. Theoretical Physicist)" className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-sm text-white" value={newAgent.role} onChange={e => setNewAgent({...newAgent, role: e.target.value})} />
                              <input placeholder="Model ID (e.g. google/gemma-4-31b-it:free)" className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-sm text-white" value={newAgent.model} onChange={e => setNewAgent({...newAgent, model: e.target.value})} />
                              <textarea placeholder="System Prompt: You are a genius..." className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-sm text-white min-h-[100px]" value={newAgent.system_prompt} onChange={e => setNewAgent({...newAgent, system_prompt: e.target.value})} />
                              <button onClick={handleCreateAgent} className="w-full bg-[#4facfe] text-black font-bold py-3 rounded-lg">CREATE AGENT</button>
                          </div>
                      </div>
                  </div>
              </motion.div>
          )}
      </AnimatePresence>

      {/* Input Panel */}
      {!chamberActive && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative z-10 w-full max-w-3xl mx-auto mt-32 px-4 md:px-8 py-8 glass-panel rounded-2xl">
        
        {showSettings && (
            <div className="bg-[#0a0f18] border border-[rgba(79,172,254,0.3)] rounded-xl p-6 mb-8 mt-4 shadow-[0_0_15px_rgba(79,172,254,0.1)]">
                <h3 className="text-[#4facfe] font-bold mb-4 flex items-center gap-2"><Brain className="w-5 h-5" /> COUNCIL PERSONALITY TUNING</h3>
                <div className="space-y-6">
                    <div>
                        <div className="flex justify-between text-xs text-[#7a92b4] mb-2"><span>AGGRESSION</span><span>{personality.aggression}%</span></div>
                        <input type="range" min="0" max="100" value={personality.aggression} onChange={(e) => setPersonality(p => ({...p, aggression: parseInt(e.target.value)}))} className="w-full accent-[#ff6b6b]"/>
                        <div className="flex justify-between text-[10px] text-[#4facfe]/50 mt-1 uppercase"><span>Calm</span><span>Assertive</span></div>
                    </div>
                    <div>
                        <div className="flex justify-between text-xs text-[#7a92b4] mb-2"><span>CREATIVITY</span><span>{personality.creativity}%</span></div>
                        <input type="range" min="0" max="100" value={personality.creativity} onChange={(e) => setPersonality(p => ({...p, creativity: parseInt(e.target.value)}))} className="w-full accent-[#a855f7]"/>
                        <div className="flex justify-between text-[10px] text-[#4facfe]/50 mt-1 uppercase"><span>Literal</span><span>Lateral</span></div>
                    </div>
                </div>
            </div>
        )}
          
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2 text-[#4facfe] text-sm tracking-widest font-bold"><Terminal className="w-4 h-4" /> QUERY INPUT</div>
            <button onClick={handleMicClick} className={`flex items-center justify-center w-10 h-10 rounded-full transition-all border ${isRecording ? 'bg-[#ff6b6b]/20 border-[#ff6b6b] text-[#ff6b6b] animate-pulse' : 'bg-[#4facfe]/10 border-[#4facfe]/30 text-[#4facfe] hover:bg-[#4facfe]/20 hover:border-[#4facfe]'}`}><Mic className="w-5 h-5" /></button>
          </div>
          
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Enter the scenario or question for the council to deliberate..." className="w-full bg-black/40 border border-[rgba(79,172,254,0.15)] rounded-xl p-4 text-[#e0eeff] min-h-[120px] focus:outline-none focus:border-[#4facfe] transition-colors resize-y"/>
          
          <div className="flex flex-wrap justify-end mt-6 gap-3">
            <input 
               type="text" 
               placeholder="Room Code (optional)" 
               value={roomCode} 
               onChange={e => setRoomCode(e.target.value)}
               className="bg-black/40 border border-[rgba(79,172,254,0.3)] rounded-xl px-4 text-sm text-[#e0eeff] focus:outline-none focus:border-[#4facfe]"
            />
            <button onClick={() => { setVoiceMode(!voiceMode); if (voiceMode && 'speechSynthesis' in window) window.speechSynthesis.cancel(); }} className={`p-3 rounded-xl border transition-colors ${voiceMode ? 'bg-[#ff6b6b]/20 border-[#ff6b6b]' : 'bg-[#0a0f18] border-[rgba(79,172,254,0.3)] hover:border-[#4facfe]'} text-[#e0e6ed]`}><Volume2 className="w-5 h-5" /></button>
            <button onClick={() => setShowSettings(!showSettings)} className={`p-3 rounded-xl border transition-colors ${showSettings ? 'bg-[#a855f7]/20 border-[#a855f7]' : 'bg-[#0a0f18] border-[rgba(79,172,254,0.3)] hover:border-[#4facfe]'} text-[#e0e6ed]`}><Brain className="w-5 h-5" /></button>
            <button onClick={handleConvene} disabled={isAssembling || !question.trim()} className="flex-1 md:flex-none flex items-center justify-center gap-2 px-8 py-3 rounded-xl font-bold tracking-widest text-sm bg-gradient-to-r from-[#4facfe]/20 to-[#00f260]/10 border border-[#4facfe] text-[#4facfe] hover:shadow-[0_0_20px_rgba(79,172,254,0.4)] disabled:opacity-50 transition-all cursor-pointer">
              {isAssembling ? <Loader2 className="animate-spin w-5 h-5" /> : <Network className="w-5 h-5" />}
              {isAssembling ? 'ASSEMBLING...' : 'CONVENE COUNCIL'}
            </button>
          </div>
        </motion.div>
      )}

      {/* Chamber */}
      <AnimatePresence>
        {chamberActive && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative z-10 w-full max-w-7xl mx-auto mt-24 px-4 md:px-6">
            
            {/* Judge */}
            <div className="max-w-lg mx-auto mb-12 p-6 rounded-2xl bg-[#ffd700]/5 border border-[#ffd700]/30 shadow-[0_0_40px_rgba(255,215,0,0.08)] backdrop-blur-xl">
              <div className="flex items-center justify-center w-14 h-14 rounded-full border-2 border-[#ffd700] bg-[#ffd700]/10 text-[#ffd700] mx-auto mb-4"><Gavel className="w-6 h-6" /></div>
              <h2 className="text-center font-black tracking-widest text-[#ffd700] text-xl">JUDGE</h2>
              <div className="flex items-center justify-center gap-2 mb-4">
                <p className="text-center text-xs tracking-widest text-[#7a92b4]">{agentStatus['judge'] === 'thinking' ? <span className="animate-pulse text-[#ffd700]">DELIBERATING...</span> : 'HEAD OF COUNCIL'}</p>
                {status === "SESSION COMPLETE" && (
                  <button onClick={speakVerdict} className={`p-1.5 rounded-full transition-all border ${isSpeaking ? 'bg-[#ffd700]/20 border-[#ffd700] text-[#ffd700] animate-pulse' : 'bg-transparent border-transparent text-[#7a92b4] hover:text-[#ffd700] hover:bg-[#ffd700]/10'}`}><Volume2 className="w-4 h-4" /></button>
                )}
              </div>
              <div className="bg-black/40 rounded-xl p-4 min-h-[80px] border border-[rgba(79,172,254,0.15)] text-sm leading-relaxed whitespace-pre-wrap">
                {judgeVerdict || <span className="text-[#7a92b4] animate-pulse">Standing by for council arguments...</span>}
              </div>
              
              {/* Confidence Meter */}
              {chamberActive && (
                  <div className="mt-6">
                      <div className="flex justify-between text-xs text-[#7a92b4] tracking-widest mb-2 font-bold"><span>CONFIDENCE METRIC</span><span className="text-[#ffd700]">{Math.round(confidence)}%</span></div>
                      <div className="h-1.5 w-full bg-black rounded-full overflow-hidden border border-[#ffd700]/20">
                          <motion.div className="h-full bg-gradient-to-r from-[#ffd700]/50 to-[#ffd700]" animate={{ width: `${confidence}%` }} transition={{ duration: 0.5 }}/>
                      </div>
                  </div>
              )}
            </div>

            {/* Agents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
              {activeAgents.map(agent => {
                const Icon = agent.icon;
                const isThinking = agentStatus[agent.id] === 'thinking';
                return (
                  <motion.div 
                    key={agent.id} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                    className="glass-panel p-4 md:p-6 rounded-2xl flex flex-col gap-2 transition-colors duration-500"
                    style={{ borderColor: isThinking ? agent.color : responses[agent.id] ? agent.color : 'rgba(79, 172, 254, 0.15)', boxShadow: isThinking ? `0 0 20px ${agent.color}40` : 'none' }}
                  >
                    <div className="flex items-center gap-4 mb-2">
                      <div className="w-10 h-10 md:w-12 md:h-12 rounded-full border-2 flex items-center justify-center shrink-0" style={{ borderColor: agent.color, backgroundColor: `${agent.color}15`, color: agent.color }}>
                        <Icon className={`w-4 h-4 md:w-5 md:h-5 ${isThinking ? 'animate-pulse' : ''}`} />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-black tracking-widest text-sm md:text-base truncate" style={{ color: agent.color }}>{agent.name}</h3>
                        <p className="text-[10px] md:text-xs tracking-widest text-[#7a92b4] truncate">{agent.title}</p>
                      </div>
                    </div>
                    <div className={`p-2 md:p-4 min-h-[120px] md:min-h-[150px] relative ${isThinking ? 'animate-pulse' : ''}`}>
                      <div className="text-xs md:text-sm text-[#e0eeff] leading-relaxed whitespace-pre-wrap pb-8">
                        {responses[agent.id] || <span className="text-[#7a92b4] italic">Awaiting turn...</span>}
                      </div>
                      {status === "SESSION COMPLETE" && responses[agent.id] && (
                        <button onClick={() => handleBranch(responses[agent.id])} className="absolute bottom-2 right-2 flex items-center gap-1 text-[10px] text-[#a855f7] bg-[#a855f7]/10 hover:bg-[#a855f7]/30 px-2 py-1 rounded transition-colors">
                            <GitBranch className="w-3 h-3" /> BRANCH
                        </button>
                      )}
                    </div>
                  </motion.div>
                )
              })}
            </div>
            
            {/* Multiplayer Chat Room */}
            <div className="mt-8 border border-[rgba(79,172,254,0.15)] bg-black/40 rounded-2xl p-4 md:p-6 backdrop-blur-md">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-[#4facfe] font-bold tracking-widest text-sm flex items-center gap-2"><Network className="w-4 h-4"/> ROOM CHAT: {roomCode}</h3>
                </div>
                <div className="h-48 overflow-y-auto mb-4 space-y-2 p-2 border border-white/5 rounded-xl bg-black/20">
                    {chatMessages.length === 0 && <p className="text-[#7a92b4] text-xs italic">No messages yet.</p>}
                    {chatMessages.map((msg, i) => (
                        <div key={i} className="text-sm">
                            <span className="font-bold text-[#4facfe]">{msg.user}: </span>
                            <span className="text-[#e0eeff]">{msg.text}</span>
                        </div>
                    ))}
                </div>
                <div className="flex gap-2">
                    <input 
                        type="text" 
                        value={chatInput} 
                        onChange={e => setChatInput(e.target.value)} 
                        onKeyDown={e => e.key === 'Enter' && handleSendChat()}
                        placeholder="Message room..." 
                        className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-[#4facfe]"
                    />
                    <button onClick={handleSendChat} className="px-6 py-2 bg-[#4facfe]/20 text-[#4facfe] border border-[#4facfe]/50 rounded-xl hover:bg-[#4facfe]/30 font-bold text-sm tracking-widest transition-colors">SEND</button>
                </div>
            </div>
            
            {/* Export Actions */}
            {status === "SESSION COMPLETE" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-12 mb-12 flex flex-wrap items-center justify-center gap-4">
                <button onClick={() => handleExport('md')} className="flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-bold tracking-widest border border-[#a855f7]/50 text-[#a855f7] bg-[#a855f7]/10 hover:bg-[#a855f7]/20 transition-all"><FileText className="w-4 h-4" /> EXPORT MD</button>
                <button onClick={() => handleExport('json')} className="flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-bold tracking-widest border border-[#00f260]/50 text-[#00f260] bg-[#00f260]/10 hover:bg-[#00f260]/20 transition-all"><FileJson className="w-4 h-4" /> EXPORT JSON</button>
                <button onClick={() => handleDownloadPDF()} className="flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-bold tracking-widest border border-[#4facfe]/50 text-[#4facfe] bg-[#4facfe]/10 hover:bg-[#4facfe]/20 transition-all"><Download className="w-4 h-4" /> EXPORT PDF</button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
