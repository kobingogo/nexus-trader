"use client";

import { useEffect, useRef } from "react";
import { FileText, Sparkles, StopCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useStreamFetcher } from "@/hooks/useStreamFetcher";
import { API_BASE_URL } from "@/lib/api";

export function DailyReview() {
  const { data: report, loading, error, fetchStream, abort } = useStreamFetcher();
  const bottomRef = useRef<HTMLDivElement>(null);

  const generateReport = () => {
    fetchStream(`${API_BASE_URL}/review/daily`);
  };

  // Auto-scroll to bottom as content streams in
  useEffect(() => {
    if (loading && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [report, loading]);

  return (
    <div className="bg-neutral-900/50 rounded-xl p-5 border border-neutral-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">复盘助手 · Daily Review</h3>
        </div>
        {(loading || report) && (
          <span className="text-[10px] text-gray-600 bg-neutral-800 px-2 py-0.5 rounded-full flex items-center gap-1">
            {loading && <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"/>}
            {loading ? "Generate Streaming..." : "Completed"}
          </span>
        )}
      </div>

      {/* Content */}
      {!report && !loading && !error && (
        <div className="flex flex-col items-center py-8 space-y-4">
          <div className="relative">
            <FileText className="w-12 h-12 text-neutral-700" />
            <Sparkles className="w-5 h-5 text-purple-400 absolute -top-1 -right-1" />
          </div>
          <p className="text-gray-600 text-xs text-center">
            收盘后点击生成，NEXUS AI 将为您总结今日行情
          </p>
          <button
            onClick={generateReport}
            className="px-4 py-2 bg-purple-600/20 text-purple-400 rounded-lg border border-purple-600/30 hover:bg-purple-600/30 transition-colors text-sm font-medium flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            生成复盘报告
          </button>
        </div>
      )}
      
      {error && (
         <div className="p-4 bg-red-900/20 border border-red-900/50 rounded-lg mb-4 text-red-200 text-sm">
            ❌ {error}
            <button onClick={generateReport} className="ml-2 underline">Retry</button>
         </div>
      )}

      {(report || loading) && (
        <div className="space-y-3">
          <div className="prose prose-invert prose-sm max-w-none max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({...props}) => <h1 className="text-xl font-bold text-transparent bg-clip-text bg-linear-to-r from-purple-400 to-pink-600 mb-4" {...props} />,
                h2: ({...props}) => <h2 className="text-lg font-semibold text-purple-300 mt-6 mb-3 border-l-4 border-purple-500 pl-3" {...props} />,
                h3: ({...props}) => <h3 className="text-md font-medium text-gray-200 mt-4 mb-2" {...props} />,
                p: ({...props}) => <p className="text-gray-300 leading-relaxed mb-3" {...props} />,
                ul: ({...props}) => <ul className="list-disc list-inside space-y-1 text-gray-300 mb-4" {...props} />,
                li: ({...props}) => <li className="pl-1 marker:text-purple-500" {...props} />,
                strong: ({...props}) => <strong className="text-purple-200 font-bold" {...props} />,
                blockquote: ({...props}) => <blockquote className="border-l-4 border-gray-700 pl-4 py-1 my-4 italic text-gray-400 bg-gray-800/30 rounded-r" {...props} />,
              }}
            >
              {report}
            </ReactMarkdown>
            
            {/* Typewriter Cursor */}
            {loading && (
              <span className="inline-block w-2 h-4 bg-purple-500 ml-1 animate-pulse align-middle" />
            )}
            
            <div ref={bottomRef} />
          </div>
          
          <div className="flex justify-end pt-2 border-t border-neutral-800">
            {loading ? (
                <button
                  onClick={abort}
                  className="px-3 py-1.5 text-[10px] text-red-400 hover:text-red-300 transition-colors flex items-center gap-1"
                >
                  <StopCircle className="w-3 h-3" /> Stop
                </button>
            ) : (
                <button
                  onClick={generateReport}
                  className="px-3 py-1.5 text-[10px] text-gray-500 hover:text-purple-400 transition-colors flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3" /> 重新生成
                </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
