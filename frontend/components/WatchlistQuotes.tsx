"use client";

import { useEffect, useState, useCallback } from "react";
import { watchlistApi } from "@/lib/api";
import { TrendingUp, TrendingDown, ArrowUpRight, Star, RefreshCw, Tag } from "lucide-react";
import Link from "next/link";

interface Quote {
  code: string;
  name: string;
  price: number;
  change_pct: number;
  change_amt: number;
  volume: number;
  amount: number;
  turnover: number;
  amplitude: number;
  sparkline: number[];
  tags: string[];
  high: number;
  low: number;
  error?: string;
}

interface Summary {
  total_stocks: number;
  gainers: number;
  losers: number;
  flat: number;
  avg_change_pct: number;
  best_stock: { code: string; name: string; change_pct: number } | null;
  worst_stock: { code: string; name: string; change_pct: number } | null;
  total_amount: number;
}

const TAG_COLORS: Record<string, string> = {
  "底仓": "bg-blue-500/15 text-blue-400 border-blue-500/30",
  "观望": "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  "做T": "bg-purple-500/15 text-purple-400 border-purple-500/30",
  "加仓": "bg-green-500/15 text-green-400 border-green-500/30",
  "减仓": "bg-orange-500/15 text-orange-400 border-orange-500/30",
  "止损": "bg-red-500/15 text-red-400 border-red-500/30",
};

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 80;
  const h = 28;

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg width={w} height={h} className="opacity-60">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function WatchlistQuotes() {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadQuotes = useCallback(async () => {
    setRefreshing(true);
    try {
      const res = await watchlistApi.getQuotes();
      setQuotes(res.quotes || []);
      setSummary(res.summary || null);
    } catch (e) {
      console.error("Failed to load quotes", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadQuotes();
    const interval = setInterval(loadQuotes, 30000);
    return () => clearInterval(interval);
  }, [loadQuotes]);

  if (loading) {
    return (
      <div className="bg-neutral-900/50 rounded-xl p-5 border border-neutral-800 animate-pulse">
        <div className="h-4 bg-neutral-800 rounded w-1/3 mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-28 bg-neutral-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (quotes.length === 0) return null; // Hide section if no watchlist

  return (
    <div className="bg-neutral-900/50 rounded-xl p-5 border border-neutral-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">自选行情 · My Portfolio</h3>
          <span className="text-[10px] text-gray-600 bg-neutral-800 px-2 py-0.5 rounded-full">
            {quotes.length} 只
          </span>
        </div>
        <button
          onClick={loadQuotes}
          disabled={refreshing}
          className="p-1 rounded hover:bg-neutral-800 transition-colors disabled:opacity-30"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Portfolio Summary Bar */}
      {summary && (
        <div className="flex items-center gap-4 mb-4 p-3 bg-neutral-800/40 rounded-lg border border-neutral-800">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-gray-500">平均涨幅</span>
            <span className={`text-sm font-bold font-mono ${summary.avg_change_pct >= 0 ? "text-red-400" : "text-green-400"}`}>
              {summary.avg_change_pct >= 0 ? "+" : ""}{summary.avg_change_pct}%
            </span>
          </div>
          <div className="w-px h-4 bg-neutral-700" />
          <div className="flex items-center gap-2 text-[10px]">
            <span className="text-red-400">↑ {summary.gainers}</span>
            <span className="text-gray-500">— {summary.flat}</span>
            <span className="text-green-400">↓ {summary.losers}</span>
          </div>
          <div className="w-px h-4 bg-neutral-700" />
          {summary.best_stock && (
            <div className="text-[10px] text-gray-500">
              最强 <span className="text-red-400 font-medium">{summary.best_stock.name}</span>
              <span className="text-red-400 font-mono ml-1">+{summary.best_stock.change_pct}%</span>
            </div>
          )}
          {summary.worst_stock && summary.worst_stock.code !== summary.best_stock?.code && (
            <>
              <div className="w-px h-4 bg-neutral-700" />
              <div className="text-[10px] text-gray-500">
                最弱 <span className="text-green-400 font-medium">{summary.worst_stock.name}</span>
                <span className="text-green-400 font-mono ml-1">{summary.worst_stock.change_pct}%</span>
              </div>
            </>
          )}
        </div>
      )}

      {/* Quote Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {quotes.map((q) => {
          const isUp = q.change_pct >= 0;
          const accentColor = isUp ? "#ef4444" : "#22c55e";
          const textColor = isUp ? "text-red-400" : "text-green-400";
          const bgColor = isUp ? "bg-red-500/3" : "bg-green-500/3";
          const borderColor = isUp ? "border-red-900/20" : "border-green-900/20";

          return (
            <div
              key={q.code}
              className={`relative p-3 rounded-lg ${bgColor} border ${borderColor} hover:brightness-125 transition-all group`}
            >
              {/* Top: Name + Code */}
              <div className="flex items-start justify-between mb-2">
                <div>
                  <span className="text-sm font-semibold text-gray-200">{q.name}</span>
                  <span className="text-[10px] text-gray-500 font-mono ml-1.5">{q.code}</span>
                </div>
                <Link
                  href={`/diagnose/${q.code}`}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-neutral-700/50 transition-all"
                  title="AI 诊断"
                >
                  <ArrowUpRight className="w-3.5 h-3.5 text-blue-400" />
                </Link>
              </div>

              {/* Middle: Price + Change */}
              <div className="flex items-end justify-between mb-2">
                <div>
                  <span className={`text-lg font-bold font-mono ${textColor}`}>
                    ¥{q.price?.toFixed(2)}
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    {isUp ? (
                      <TrendingUp className={`w-3 h-3 ${textColor}`} />
                    ) : (
                      <TrendingDown className={`w-3 h-3 ${textColor}`} />
                    )}
                    <span className={`text-xs font-mono font-bold ${textColor}`}>
                      {isUp ? "+" : ""}{q.change_pct}%
                    </span>
                    <span className={`text-[10px] font-mono ${textColor}`}>
                      {isUp ? "+" : ""}{q.change_amt?.toFixed(2)}
                    </span>
                  </div>
                </div>
                <MiniSparkline data={q.sparkline} color={accentColor} />
              </div>

              {/* Bottom: Volume stats */}
              <div className="flex items-center gap-3 text-[10px] text-gray-600">
                <span>量: {q.volume ? (q.volume / 10000).toFixed(0) + "万" : "-"}</span>
                <span>换手: {q.turnover}%</span>
                <span>振幅: {q.amplitude}%</span>
              </div>

              {/* Tags */}
              {q.tags && q.tags.length > 0 && (
                <div className="flex items-center gap-1 mt-2">
                  <Tag className="w-2.5 h-2.5 text-gray-600" />
                  {q.tags.map(tag => (
                    <span
                      key={tag}
                      className={`text-[9px] px-1.5 py-0.5 rounded border ${TAG_COLORS[tag] || "bg-neutral-700/30 text-gray-400 border-neutral-600"}`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
