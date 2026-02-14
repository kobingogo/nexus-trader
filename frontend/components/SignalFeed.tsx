"use client";

import { useEffect, useState } from "react";
import { agentApi } from "@/lib/api";
import { BrainCircuit, AlertTriangle, Zap, Info, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import ReactMarkdown from 'react-markdown';

interface Signal {
  id: number;
  timestamp: string;
  type: string;
  level: "info" | "warning" | "critical";
  message: string;
  analysis_content?: string;
  metadata_json: string;
}

export function SignalFeed() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchSignals = async () => {
    try {
      const res = await agentApi.getSignals(20);
      if (res.data) {
        setSignals(res.data);
      }
    } catch (e) {
      console.error("Failed to fetch signals", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getIcon = (type: string, level: string) => {
    if (level === "critical") return <AlertTriangle className="w-4 h-4 text-red-500 animate-pulse" />;
    if (level === "warning") return <Zap className="w-4 h-4 text-yellow-500" />;
    return <Info className="w-4 h-4 text-blue-400" />;
  };

  const getBorderColor = (level: string) => {
    if (level === "critical") return "border-red-500/50 bg-red-500/5";
    if (level === "warning") return "border-yellow-500/30 bg-yellow-500/5";
    return "border-blue-500/20 bg-blue-500/5";
  };

  return (
    <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-4 h-[400px] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-purple-400" />
          <h2 className="font-semibold text-gray-200">NEXUS Brain Signals</h2>
        </div>
        <div className="text-xs text-gray-500 flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
          </span>
          Live
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
        {loading && signals.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Connecting to Cortex...
          </div>
        ) : (
          signals.map((signal) => (
            <div
              key={signal.id}
              className={`p-3 rounded-lg border ${getBorderColor(
                signal.level
              )} flex flex-col gap-2 transition-all hover:bg-neutral-800/30 cursor-pointer`}
              onClick={() => signal.analysis_content && toggleExpand(signal.id)}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">{getIcon(signal.type, signal.level)}</div>
                <div className="flex-1">
                  <p className="text-sm text-gray-200 font-medium leading-snug">
                    {signal.message}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <span className="text-[10px] text-gray-500 uppercase tracking-wider font-mono">
                      {new Date(signal.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-neutral-800 text-gray-400 border border-neutral-700">
                      {signal.type}
                    </span>
                    {signal.analysis_content && (
                        <div className="flex items-center gap-1">
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1">
                                <BrainCircuit className="w-3 h-3" />
                                AI Analysis
                            </span>
                            {expandedId === signal.id ? 
                                <ChevronUp className="w-3 h-3 text-gray-500"/> : 
                                <ChevronDown className="w-3 h-3 text-gray-500"/>
                            }
                        </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Expandable Analysis Content */}
              {expandedId === signal.id && signal.analysis_content && (
                <div className="mt-2 pl-8 text-xs text-gray-300 border-t border-dashed border-gray-700/50 pt-2">
                    <div className="prose prose-invert prose-p:my-1 prose-headings:my-2 prose-ul:my-1 max-w-none">
                        <ReactMarkdown>{signal.analysis_content}</ReactMarkdown>
                    </div>
                </div>
              )}
            </div>
          ))
        )}
        
        {!loading && signals.length === 0 && (
            <div className="text-center text-gray-600 text-sm py-10">
                No signals detected yet. Brain is calm. 🧠
            </div>
        )}
      </div>
    </div>
  );
}
