'use client';

import { useState, useEffect, useRef } from 'react';
import { RetellWebClient } from 'retell-client-js-sdk';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, PhoneOff, Loader2, Calendar as CalIcon, Sparkles } from 'lucide-react';

const retellWebClient = new RetellWebClient();

interface TranscriptMessage {
  role: string;
  content: string;
}

export default function Home() {
  const [isCalling, setIsCalling] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [agentStatus, setAgentStatus] = useState('Idle');
  
  const [callHistory, setCallHistory] = useState<TranscriptMessage[]>([]);
  const [currentTranscript, setCurrentTranscript] = useState<TranscriptMessage[]>([]);
  const [bookedDate, setBookedDate] = useState<number | null>(null);
  
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  
  // Replace with your actual Retell Agent ID
  const agentId = "agent_87e588281fb6eda14a853a06ee"; 

  const fullTranscript = [...callHistory, ...currentTranscript];

  // Auto-scroll to the latest message
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [fullTranscript]);

  // Listen for the AI booking a date in April
  useEffect(() => {
    if (currentTranscript.length > 0) {
      const latestMsg = currentTranscript[currentTranscript.length - 1];
      if (latestMsg.role === 'agent') {
        const match = latestMsg.content.match(/April (\d+)/i);
        if (match && match[1]) setBookedDate(parseInt(match[1], 10));
      }
    }
  }, [currentTranscript]);

  // Retell SDK Event Listeners
  useEffect(() => {
    retellWebClient.on('call_started', () => {
      setIsCalling(true);
      setIsConnecting(false);
      setAgentStatus('Listening...');
    });

    retellWebClient.on('call_ended', () => {
      setIsCalling(false);
      setIsConnecting(false);
      setAgentStatus('Idle');
      setCallHistory(prev => [...prev, ...currentTranscript]);
      setCurrentTranscript([]);
    });

    retellWebClient.on('agent_start_talking', () => setAgentStatus('AI Speaking'));
    retellWebClient.on('agent_stop_talking', () => setAgentStatus('Listening...'));

    retellWebClient.on('update', (update) => {
      if (update && update.transcript) setCurrentTranscript(update.transcript);
    });

    retellWebClient.on('error', (error) => {
      console.error('Call disconnected or errored:', error);
      setIsCalling(false);
      setIsConnecting(false);
      setAgentStatus('Disconnected'); 
      setCallHistory(prev => [...prev, ...currentTranscript]);
      setCurrentTranscript([]);
    });

    return () => {
      retellWebClient.off('call_started');
      retellWebClient.off('call_ended');
      retellWebClient.off('agent_start_talking');
      retellWebClient.off('agent_stop_talking');
      retellWebClient.off('update');
      retellWebClient.off('error');
    };
  }, [currentTranscript]);

  const toggleCall = async () => {
    if (isCalling) {
      retellWebClient.stopCall();
      return;
    }
    setIsConnecting(true);
    setAgentStatus('Connecting...');
    try {
      const response = await fetch('https://vikara-api.onrender.com/create-web-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
      const data = await response.json();
      await retellWebClient.startCall({ accessToken: data.access_token });
    } catch (error) {
      console.error('Call failed:', error);
      setIsConnecting(false);
      setAgentStatus('Offline');
    }
  };

  const isActive = isCalling || isConnecting;
  const isAiSpeaking = agentStatus === 'AI Speaking';

  // April 2026 Grid Logic
  const aprilDays = Array.from({ length: 30 }, (_, i) => i + 1);
  const paddingDays = Array.from({ length: 3 }, (_, i) => null);

  // Hardware-accelerated easing curve for buttery smooth animations
  const smoothEase = [0.22, 1, 0.36, 1];

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen bg-[#020203] text-white font-sans overflow-hidden">
      
      {/* 1. DEEP SPACE ENVIRONMENT */}
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_50%_50%,_#0a0a1a_0%,_#020203_100%)] opacity-80" />

      {/* 2. LOGO - QUICK MATERIALIZE */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.9, filter: 'blur(10px)' }}
        animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
        transition={{ duration: 1, ease: smoothEase as any }}
        className="absolute top-10 left-10 xl:top-12 xl:left-12 z-50 flex items-center gap-3"
      >
        <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center shadow-[0_0_30px_rgba(37,99,235,0.3)]">
            <span className="text-sm font-black text-white">V</span>
        </div>
        <span className="text-xl font-bold tracking-tighter">
          Vikara<span className="text-blue-500">.AI</span>
        </span>
      </motion.div>

      {/* 3. CENTER STAGE */}
      <div className="flex flex-col items-center z-10 w-full max-w-4xl px-6 relative mt-8">
        
        {/* HEADING - FIXED ANCHOR (Tech Reveal) */}
        <div className="overflow-hidden mb-2">
          <motion.h1 
            initial={{ opacity: 0, y: 30, letterSpacing: "0.1em" }}
            animate={{ opacity: 1, y: 0, letterSpacing: "-0.02em" }}
            transition={{ duration: 1.2, ease: smoothEase as any }}
            className="text-5xl md:text-6xl font-semibold text-white text-center whitespace-nowrap bg-clip-text text-transparent bg-gradient-to-b from-white to-zinc-500"
          >
            AI Interview Assistant
          </motion.h1>
        </div>

        {/* INTERACTION GROUP - GPU ACCELERATED GLIDE */}
        <motion.div
          animate={{ y: isActive ? -70 : 0 }} 
          transition={{ duration: 0.85, ease: smoothEase as any }}
          style={{ willChange: "transform" }}
          className="flex flex-col items-center w-full"
        >
          
          {/* FIXED HEIGHT CONTAINER FOR DESCRIPTION */}
          <div className="h-16 flex items-center justify-center mb-6 w-full">
            <AnimatePresence>
              {!isActive && (
                <motion.p 
                  key="description"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.5, filter: 'blur(0px)' }}
                  exit={{ opacity: 0, filter: 'blur(8px)', scale: 0.95 }}
                  transition={{ duration: 0.5 }}
                  className="text-zinc-400 text-sm md:text-base font-light text-center tracking-wide"
                >
                  Elevating recruitment through seamless, autonomous voice-first intelligence.
                </motion.p>
              )}
            </AnimatePresence>
          </div>

          {/* Status Pill - Brightened text for better visibility */}
          <div className="bg-zinc-900/40 border border-white/10 px-7 py-2 rounded-full backdrop-blur-3xl flex items-center gap-3 mb-10 shadow-xl">
             {isActive && (
                <div className={`w-1.5 h-1.5 rounded-full ${isAiSpeaking ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)] animate-pulse' : 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.8)] animate-pulse'}`} />
             )}
            <span className="font-mono text-[10px] text-zinc-300 tracking-[0.3em] uppercase font-medium">
              {isActive ? (isAiSpeaking ? 'AI Speaking' : 'Listening...') : 'Ready to Start'}
            </span>
          </div>

          {/* HIGH-TECH MICROPHONE ORB */}
          <motion.button
            onClick={toggleCall}
            disabled={isConnecting}
            initial={{ boxShadow: "0px 0px 0px 0px rgba(59, 130, 246, 0)" }}
            whileHover={{ 
              scale: 1.05, 
              boxShadow: "0px 0px 40px 10px rgba(59, 130, 246, 0.25)",
              borderColor: "rgba(59, 130, 246, 0.5)"
            }}
            whileTap={{ scale: 0.95 }}
            className={`relative flex items-center justify-center w-36 h-36 rounded-full transition-colors duration-500 border ${
              isActive 
                ? 'bg-blue-600/10 border-blue-500/30 text-blue-500 shadow-[0_0_80px_rgba(59,130,246,0.2)]' 
                : 'bg-zinc-900/30 border-zinc-700 text-blue-500'
            }`}
          >
            {isActive && (
              <motion.div
                animate={{ scale: [1, 1.4, 1], opacity: [0.1, 0, 0.1] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                className={`absolute inset-0 rounded-full border-2 ${isAiSpeaking ? 'border-blue-500' : 'border-green-500'}`}
              />
            )}

            {isConnecting ? (
              <Loader2 className="w-10 h-10 animate-spin text-zinc-500" />
            ) : isCalling ? (
              <PhoneOff className="w-10 h-10 text-zinc-400" />
            ) : (
              <Mic className="w-10 h-10" />
            )}
          </motion.button>

          {/* TRANSCRIPT AREA (NATIVE MASK FADE) */}
          <div className="w-full mt-8 h-48 relative bg-transparent">
            <AnimatePresence>
                {isActive && (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.3 }}
                        className="w-full h-full bg-transparent"
                    >
                        <div 
                          className="h-full overflow-y-auto [&::-webkit-scrollbar]:hidden flex flex-col space-y-6 px-4 text-center pb-12 pt-6 bg-transparent"
                          style={{ 
                            maskImage: 'linear-gradient(to bottom, transparent, black 15%, black 85%, transparent)',
                            WebkitMaskImage: 'linear-gradient(to bottom, transparent, black 15%, black 85%, transparent)' 
                          }}
                        >
                            {fullTranscript.map((msg, idx) => {
                                const cleanText = msg.content.replace(/<[^>]+>/g, '').trim();
                                if (!cleanText) return null; 
                                const isAgent = msg.role === 'agent';
                                return (
                                    <motion.div key={idx} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                        <p className={`text-[15px] leading-relaxed tracking-tight ${isAgent ? 'text-zinc-100 font-medium' : 'text-zinc-500 font-light italic'}`}>
                                            {isAgent && <Sparkles className="w-3.5 h-3.5 text-blue-500 inline mr-2" />}
                                            {cleanText}
                                        </p>
                                    </motion.div>
                                );
                            })}
                            <div ref={transcriptEndRef} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>

      {/* FIXED VIEWPORT CALENDAR */}
      <div className="fixed bottom-8 right-8 xl:bottom-12 xl:right-12 hidden lg:block z-50">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="w-64 bg-zinc-900/30 border border-white/10 backdrop-blur-3xl rounded-[2.5rem] p-7 shadow-2xl"
        >
          <div className="flex items-center justify-between mb-6 pb-2 border-b border-white/10">
            <h3 className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest flex items-center gap-2">
              <CalIcon className="w-3.5 h-3.5 text-blue-500" /> Schedule
            </h3>
            <span className="text-[10px] text-zinc-500 font-mono">APR 2026</span>
          </div>
          
          <div className="grid grid-cols-7 gap-y-3 text-center">
            {/* Brightened the Days of the week header */}
            {['S','M','T','W','T','F','S'].map((d, i) => (
              <div key={i} className="text-[10px] font-bold text-zinc-500 font-mono">{d}</div>
            ))}
            {paddingDays.map((_, i) => <div key={`p-${i}`} />)}
            {aprilDays.map((day) => {
              const isBooked = bookedDate === day;
              return (
                <div 
                  key={day}
                  // Brightened the unbooked dates to text-zinc-400
                  className={`py-1.5 text-[11px] transition-all duration-700 rounded-lg ${
                    isBooked 
                      ? 'text-blue-400 font-bold bg-blue-600/10 border border-blue-500/30 shadow-[0_0_10px_rgba(59,130,246,0.2)]' 
                      : 'text-zinc-400' 
                  }`}
                >
                  {day}
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>

    </main>
  );
}