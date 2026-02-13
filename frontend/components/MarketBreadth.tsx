"use client";

import { useEffect, useState, useCallback } from "react";
import { marketApi } from "@/lib/api";
import { Thermometer, TrendingUp, TrendingDown, Activity } from "lucide-react";

interface SentimentData {
  temperature: number;
  up_count: number;
  down_count: number;
  flat_count: number;
  limit_up_count: number;
  limit_down_count: number;
  activity: number;
  ts: string;
}

function getTemperatureZone(temp: number) {
  if (temp <= 20) return { label: "极寒 · 冰点期", color: "from-blue-500 to-cyan-400", textColor: "text-blue-400", bg: "bg-blue-500/10", strategy: "空仓/试错" };
  if (temp <= 50) return { label: "回暖 · 修复期", color: "from-yellow-500 to-amber-400", textColor: "text-yellow-400", bg: "bg-yellow-500/10", strategy: "低吸核心" };
  if (temp <= 80) return { label: "活跃 · 进攻期", color: "from-orange-500 to-red-400", textColor: "text-orange-400", bg: "bg-orange-500/10", strategy: "加仓跟进" };
  return { label: "沸点 · 高潮期", color: "from-red-500 to-pink-500", textColor: "text-red-400", bg: "bg-red-500/10", strategy: "加速/兑现" };
}

export function MarketBreadth() {
  const [data, setData] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const res = await marketApi.getSentiment();
      setData(res.data);
    } catch (e) {
      console.error("Failed to load sentiment", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading || !data) {
    return (
      <div className="h-full bg-neutral-900/50 rounded-xl p-5 border border-neutral-800 flex items-center justify-center">
        <Activity className="w-5 h-5 text-gray-600 animate-pulse mr-2" />
        <span className="text-gray-600 text-sm">Loading Sentiment...</span>
      </div>
    );
  }

  const zone = getTemperatureZone(data.temperature);
  const total = data.up_count + data.down_count + data.flat_count || 1;
  const upPct = ((data.up_count / total) * 100).toFixed(1);
  const downPct = ((data.down_count / total) * 100).toFixed(1);
  const flatPct = ((data.flat_count / total) * 100).toFixed(1);

  return (
    <div className="h-full bg-neutral-900/50 rounded-xl p-5 border border-neutral-800 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Thermometer className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">市场温度</h3>
        </div>
        <span className="text-[10px] text-gray-600 font-mono">{data.ts || "LIVE"}</span>
      </div>

      {/* Temperature Gauge */}
      <div className="flex items-center gap-4">
        <div className="relative w-20 h-20 flex-shrink-0">
          {/* Background circle */}
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle cx="50" cy="50" r="42" stroke="currentColor" strokeWidth="8" fill="none" className="text-neutral-800" />
            <circle
              cx="50" cy="50" r="42"
              stroke="url(#tempGrad)"
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={`${(data.temperature / 100) * 264} 264`}
              className="transition-all duration-1000 ease-out"
            />
            <defs>
              <linearGradient id="tempGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#3b82f6" />
                <stop offset="50%" stopColor="#f59e0b" />
                <stop offset="100%" stopColor="#ef4444" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-xl font-bold font-mono ${zone.textColor}`}>
              {data.temperature.toFixed(0)}
            </span>
          </div>
        </div>
        <div className="flex-1 space-y-1">
          <div className={`text-base font-bold ${zone.textColor}`}>{zone.label}</div>
          <div className="text-xs text-gray-500">策略建议: {zone.strategy}</div>
          <div className="text-xs text-gray-600 font-mono">活跃度: {data.activity}%</div>
        </div>
      </div>

      {/* Up/Down Distribution Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-[10px] text-gray-500 font-mono">
          <span className="text-red-400">↑ {data.up_count} ({upPct}%)</span>
          <span className="text-gray-500">— {data.flat_count} ({flatPct}%)</span>
          <span className="text-green-400">↓ {data.down_count} ({downPct}%)</span>
        </div>
        <div className="relative h-2 bg-neutral-800 rounded-full overflow-hidden flex shrink-0">
          <div className="bg-red-500/80 transition-all duration-700" style={{ width: `${upPct}%` }} />
          <div className="bg-gray-600/50 transition-all duration-700" style={{ width: `${flatPct}%` }} />
          <div className="bg-green-500/80 transition-all duration-700" style={{ width: `${downPct}%` }} />
        </div>
      </div>

      {/* Limit Up/Down Cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-red-500/5 rounded-lg p-3 border border-red-900/30">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-red-400" />
            <span className="text-[10px] text-gray-500">涨停</span>
          </div>
          <div className="text-2xl font-bold text-red-400 font-mono mt-1">{data.limit_up_count}</div>
        </div>
        <div className="bg-green-500/5 rounded-lg p-3 border border-green-900/30">
          <div className="flex items-center gap-1.5">
            <TrendingDown className="w-3.5 h-3.5 text-green-400" />
            <span className="text-[10px] text-gray-500">跌停</span>
          </div>
          <div className="text-2xl font-bold text-green-400 font-mono mt-1">{data.limit_down_count}</div>
        </div>
      </div>
    </div>
  );
}
