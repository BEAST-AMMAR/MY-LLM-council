"use client";
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Network, Terminal, Keyboard, Camera, Mic, Image as ImageIcon, Gavel, Brain, ChartBar, ChessKnight, Search, Loader2 } from 'lucide-react';

const AGENTS = [
  { id: 'sage', name: 'SAGE', title: 'The Philosopher', color: '#4facfe', icon: Brain },
  { id: 'analyst', name: 'ANALYST', title: 'The Logician', color: '#00f260', icon: ChartBar },
  { id: 'strategist', name: 'STRATEGIST', title: 'The Visionary', color: '#a855f7', icon: ChessKnight },
  { id: 'skeptic', name: 'SKEPTIC', title: 'The Challenger', color: '#ff6b6b', icon: Search }
];

export default function CouncilApp() {
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("SYSTEM ONLINE");
  const [isAssembling, setIsAssembling] = useState(false);
  const [chamberActive, setChamberActive] = useState(false);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [judgeVerdict, setJudgeVerdict] = useState("");

  const handleConvene = async () => {
    if (!question.trim()) return;
    setIsAssembling(true);
    setStatus("ASSEMBLING COUNCIL...");
    
    // Simulate delay for assembly
    await new Promise(r => setTimeout(r, 1500));
    setChamberActive(true);
    setStatus("SESSION ACTIVE");

    // Start inference (mocked for now, points to local ML engine)
    for (const agent of AGENTS) {
        await fetchInference(agent.id, question);
    }
    
    // Judge synthesis
    await fetchInference('judge', question);
    setIsAssembling(false);
    setStatus("SESSION COMPLETE");
  };

  const fetchInference = async (agentId: string, prompt: string) => {
    try {
      const mlUrl = process.env.NEXT_PUBLIC_ML_ENGINE_URL || 'http://localhost:8001';
      const res = await fetch(`${mlUrl}/api/infer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId, prompt })
      });
      
      if (!res.body) return;
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                fullText += data.token;
                if (agentId === 'judge') {
                  setJudgeVerdict(prev => prev + data.token);
                } else {
                  setResponses(prev => ({...prev, [agentId]: fullText}));
                }
              }
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      console.error(err);
      if (agentId === 'judge') setJudgeVerdict("[Error communicating with local ML engine]");
      else setResponses(prev => ({...prev, [agentId]: "[Error communicating with local ML engine]"}));
    }
  };

  return (
    <main className="min-h-screen font-sans overflow-x-hidden pb-20">
      <div className="hex-grid"></div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between p-4 bg-[#040414e6] backdrop-blur-md border-b border-[rgba(79,172,254,0.15)]">
        <div className="flex items-center gap-3">
          <Network className="text-[#4facfe] w-6 h-6" />
          <div>
            <h1 className="text-xl font-black tracking-widest text-[#e0eeff]">LLM<span className="text-[#4facfe]">COUNCIL</span></h1>
            <p className="text-[10px] tracking-[0.2em] text-[#7a92b4]">MULTI-AGENT DELIBERATION v3.0 OFFLINE</p>
          </div>
        </div>
        <div className="flex items-center gap-6 text-xs tracking-widest text-[#7a92b4] font-bold">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.includes('ONLINE') ? 'bg-[#00f260] animate-pulse' : 'bg-[#4facfe]'}`}></span>
            {status}
          </div>
        </div>
      </header>

      {/* Input Panel */}
      {!chamberActive && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 max-w-3xl mx-auto mt-32 p-8 glass-panel rounded-2xl"
        >
          <div className="flex items-center gap-2 text-[#4facfe] text-sm tracking-widest mb-6 font-bold">
            <Terminal className="w-4 h-4" /> QUERY INPUT
          </div>
          
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter the scenario or question for the council to deliberate offline..."
            className="w-full bg-black/40 border border-[rgba(79,172,254,0.15)] rounded-xl p-4 text-[#e0eeff] min-h-[120px] focus:outline-none focus:border-[#4facfe] transition-colors resize-y"
          />
          
          <div className="flex justify-end mt-6">
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
              <p className="text-center text-xs tracking-widest text-[#7a92b4] mb-4">HEAD OF COUNCIL</p>
              
              <div className="bg-black/40 rounded-xl p-4 min-h-[80px] border border-[rgba(79,172,254,0.15)] text-sm leading-relaxed whitespace-pre-wrap">
                {judgeVerdict || <span className="text-[#7a92b4] animate-pulse">Standing by for council arguments...</span>}
              </div>
            </div>

            {/* Agents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {AGENTS.map(agent => {
                const Icon = agent.icon;
                return (
                  <motion.div 
                    key={agent.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="glass-panel p-6 rounded-2xl flex flex-col gap-2 transition-colors duration-500"
                    style={{ borderColor: responses[agent.id] ? agent.color : 'rgba(79, 172, 254, 0.15)' }}
                  >
                    <div className="flex items-center gap-4 mb-2">
                      <div className="w-12 h-12 rounded-full border-2 flex items-center justify-center" style={{ borderColor: agent.color, backgroundColor: `${agent.color}15`, color: agent.color }}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-black tracking-widest" style={{ color: agent.color }}>{agent.name}</h3>
                        <p className="text-xs tracking-widest text-[#7a92b4]">{agent.title}</p>
                      </div>
                    </div>
                    <div className="bg-black/30 rounded-xl p-4 min-h-[100px] border border-[rgba(79,172,254,0.15)] text-sm leading-relaxed">
                      {responses[agent.id] || <span className="text-[#7a92b4] animate-pulse">Computing inference locally...</span>}
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
