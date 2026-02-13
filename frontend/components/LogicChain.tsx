
"use client";

import { useState } from "react";
import { logicApi } from "@/lib/api";
import { Search, Zap, ArrowRight, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

interface LeaderStock {
  code: string;
  name: string;
  price: number;
  change_pct: number;
  turnover: number;
}

interface LogicResult {
  query: string;
  found_concepts: string[];
  best_match: string;
  reasoning: string;
  leaders: LeaderStock[];
}

export function LogicChain() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<LogicResult | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await logicApi.analyze(query);
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-4 h-4 text-purple-400" />
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">逻辑链 (Logic Chain)</h3>
      </div>

      <form onSubmit={handleSearch} className="relative mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入概念/新闻关键词..."
          className="w-full bg-neutral-900 border border-neutral-700 rounded-lg py-2 pl-10 pr-4 text-gray-200 text-sm focus:outline-none focus:border-purple-500 transition-colors"
        />
        <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="absolute right-2 top-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs px-3 py-1 rounded transition-colors disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : "推演"}
        </button>
      </form>

      {result ? (
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="mb-4">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <span>匹配:</span>
              <span className="text-purple-400 font-bold bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                {result.best_match}
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto pr-2 space-y-2 custom-scrollbar">
            {result.leaders.slice(0, 5).map((stock) => (
              <div
                key={stock.code}
                onClick={() => router.push(`/diagnose/${stock.code}`)}
                className="flex items-center justify-between p-3 bg-neutral-800/30 hover:bg-neutral-800/60 rounded-lg cursor-pointer transition-colors group"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-200 font-medium">{stock.name}</span>
                    <span className="text-xs text-gray-500 font-mono">{stock.code}</span>
                  </div>
                </div>
                <div className="text-right flex items-center gap-2">
                  <div className={`font-mono font-bold ${stock.change_pct >= 0 ? "text-red-400" : "text-green-400"}`}>
                    {stock.change_pct > 0 ? "+" : ""}{stock.change_pct.toFixed(2)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-600 text-sm">
          <Zap className="w-8 h-8 opacity-20 mb-2" />
          <p>寻找最强逻辑</p>
        </div>
      )}
    </div>
  );
}
