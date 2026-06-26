"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';

export default function AuthPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        
        try {
            if (isLogin) {
                // Next.js proxy or direct API
                const response = await fetch("http://localhost:8001/api/auth/token", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: new URLSearchParams({
                        username: username,
                        password: password
                    })
                });
                
                if (!response.ok) {
                    throw new Error("Invalid credentials");
                }
                
                const data = await response.json();
                localStorage.setItem("access_token", data.access_token);
                // Redirect to main page
                window.location.href = "/";
            } else {
                const response = await fetch("http://localhost:8001/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });
                
                if (!response.ok) {
                    throw new Error("Registration failed");
                }
                
                setIsLogin(true);
                setError("Registration successful! Please log in.");
            }
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className="min-h-screen bg-black text-cyan-400 flex flex-col items-center justify-center font-mono p-4" style={{ 
            backgroundImage: "radial-gradient(circle at center, rgba(0, 150, 255, 0.1) 0%, rgba(0,0,0,1) 70%)" 
        }}>
            <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md p-8 rounded-xl border border-cyan-500/30 bg-black/40 backdrop-blur-md shadow-[0_0_40px_rgba(0,255,255,0.1)] relative overflow-hidden"
            >
                {/* Holographic scanning line */}
                <motion.div 
                    animate={{ top: ["-10%", "110%"] }}
                    transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                    className="absolute left-0 right-0 h-1 bg-cyan-400/50 shadow-[0_0_10px_#0ff] z-0"
                />

                <div className="relative z-10">
                    <div className="flex justify-center mb-8">
                        <div className="w-16 h-16 rounded-full border-2 border-cyan-500 flex items-center justify-center animate-[spin_10s_linear_infinite]">
                            <div className="w-12 h-12 rounded-full border-t-2 border-cyan-300 animate-[spin_5s_linear_infinite_reverse]"></div>
                        </div>
                    </div>

                    <h1 className="text-3xl text-center mb-2 tracking-widest font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">
                        LLM COUNCIL
                    </h1>
                    <p className="text-center text-sm text-cyan-600/80 mb-8 uppercase tracking-widest">
                        {isLogin ? "System Access Protocol" : "New User Registration"}
                    </p>

                    <form onSubmit={handleAuth} className="space-y-6">
                        <div>
                            <input 
                                type="text" 
                                placeholder="USERNAME"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-black/50 border-b border-cyan-500/50 p-3 text-cyan-300 focus:outline-none focus:border-cyan-400 focus:shadow-[0_4px_10px_rgba(0,255,255,0.2)] transition-all placeholder-cyan-800 tracking-wider"
                                required
                            />
                        </div>
                        <div>
                            <input 
                                type="password" 
                                placeholder="PASSPHRASE"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-black/50 border-b border-cyan-500/50 p-3 text-cyan-300 focus:outline-none focus:border-cyan-400 focus:shadow-[0_4px_10px_rgba(0,255,255,0.2)] transition-all placeholder-cyan-800 tracking-wider"
                                required
                            />
                        </div>

                        {error && (
                            <p className={`text-sm text-center ${error.includes('successful') ? 'text-green-400' : 'text-red-500'}`}>
                                {error}
                            </p>
                        )}

                        <button 
                            type="submit"
                            className="w-full py-3 mt-4 border border-cyan-500 text-cyan-400 hover:bg-cyan-500/20 hover:shadow-[0_0_20px_rgba(0,255,255,0.4)] transition-all uppercase tracking-[0.3em] text-sm font-bold"
                        >
                            {isLogin ? "Authenticate" : "Initialize"}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <button 
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-xs text-cyan-600 hover:text-cyan-400 transition-colors uppercase tracking-widest"
                        >
                            {isLogin ? "Request Access (Register)" : "Return to Login"}
                        </button>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
