"use client";

import { useEffect, useRef } from "react";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useStreamFetcher } from "@/hooks/useStreamFetcher";

import { API_BASE_URL } from "@/lib/api";

export default function DiagnosisPage() {
  const paramsWrapper = useParams();
  const ticker = paramsWrapper.ticker as string;
  const { data: report, loading, error, fetchStream, abort } = useStreamFetcher();
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasFetched = useRef(false);

  useEffect(() => {
    if (ticker && !hasFetched.current) {
        hasFetched.current = true;
        fetchStream(`${API_BASE_URL}/ai/diagnose/${ticker}`);
    }
  }, [ticker, fetchStream]);

  // Auto-scroll
  useEffect(() => {
    if (loading && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [report, loading]);


  return (
    <div className="min-h-screen bg-black text-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <Link href="/" className="inline-flex items-center text-gray-500 hover:text-white mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
        </Link>
        
        <header className="mb-8 border-b border-neutral-800 pb-4 flex justify-between items-center">
            <h1 className="text-3xl font-bold text-white mb-2">
                🔎 AI Deep Diagnosis: <span className="text-blue-500">{ticker}</span>
            </h1>
            {loading && (
                 <button
                  onClick={abort}
                  className="px-3 py-1.5 text-xs text-red-400 hover:text-red-300 border border-red-900/50 rounded flex items-center gap-1"
                >
                  Stop Generating
                </button>
            )}
        </header>

        <div className="bg-neutral-900/50 rounded-xl p-8 border border-neutral-800 min-h-[400px]">
            {error && (
                <div className="p-4 bg-red-900/20 border border-red-900/50 rounded-lg mb-4 text-red-200">
                    ⚠️ Error: {error}
                    <button onClick={() => fetchStream(`/api/v1/ai/diagnose/${ticker}`)} className="ml-4 underline">Retry</button>
                </div>
            )}

            {!report && loading && !error && (
                <div className="flex flex-col items-center justify-center h-64 space-y-4">
                    <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
                    <p className="text-gray-400">NEXUS AI is analyzing historical data...</p>
                </div>
            )}

            {report && (
                <article className="prose prose-invert prose-lg max-w-none">
                    <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                            h1: ({...props}) => <h1 className="text-2xl font-bold text-blue-400 mb-4 mt-6" {...props} />,
                            h2: ({...props}) => <h2 className="text-xl font-semibold text-blue-300 mt-8 mb-4 border-b border-neutral-700 pb-2" {...props} />,
                            h3: ({...props}) => <h3 className="text-lg font-medium text-blue-200 mt-6 mb-2" {...props} />,
                            strong: ({...props}) => <strong className="text-yellow-400 font-bold" {...props} />,
                            table: ({...props}) => <div className="overflow-x-auto my-6 border border-neutral-700 rounded-lg"><table className="min-w-full divide-y divide-neutral-700" {...props} /></div>,
                            thead: ({...props}) => <thead className="bg-neutral-800" {...props} />,
                            th: ({...props}) => <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider" {...props} />,
                            tbody: ({...props}) => <tbody className="bg-neutral-900/30 divide-y divide-neutral-800" {...props} />,
                            tr: ({...props}) => <tr className="hover:bg-neutral-800/50 transition-colors" {...props} />,
                            td: ({...props}) => <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300" {...props} />,
                            a: ({...props}) => <a className="text-blue-400 hover:text-blue-300 underline" {...props} />,
                            ul: ({...props}) => <ul className="list-disc pl-5 space-y-2 my-4" {...props} />,
                            li: ({...props}) => <li className="text-gray-300 leading-relaxed" {...props} />,
                            p: ({...props}) => <p className="mb-4 text-gray-300 leading-relaxed" {...props} />,
                            blockquote: ({...props}) => <blockquote className="border-l-4 border-blue-500 pl-4 py-1 my-4 bg-blue-900/20 text-blue-200 italic rounded-r" {...props} />,
                        }}
                    >
                        {report}
                    </ReactMarkdown>
                    {loading && (
                        <span className="inline-block w-2 h-5 bg-blue-500 ml-1 animate-pulse align-middle" />
                    )}
                    <div ref={bottomRef} />
                </article>
            )}
        </div>
      </div>
    </div>
  );
}
