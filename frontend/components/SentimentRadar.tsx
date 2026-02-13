"use client";

import { useEffect, useState } from "react";
import { marketApi } from "@/lib/api";
import { Loader2, TrendingUp, TrendingDown, Minus, AlertTriangle, Activity } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

interface SentimentData {
  timestamp: string;
  metrics: {
    limit_up_count: number;
    fried_board_count: number;
    fried_rate: number;
    premium_rate: number;
    promotion_rate: number;
    mood_index: number;
    trend: "up" | "down" | "flat";
  };
}

export function SentimentRadar() {
  const [data, setData] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await marketApi.getMarketSentiment();
        setData(res);
      } catch (e) {
        console.error("Failed to fetch sentiment:", e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    // Refresh every minute
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-6 h-64 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!data) return null;

  const { metrics } = data;
  const mood = metrics.mood_index;
  const trend = metrics.trend;

  // Gauge configuration
  const gaugeData = [{ value: mood }, { value: 100 - mood }];

  // Color & Text Scale based on mood AND trend
  let moodColor = "#3b82f6"; 
  let moodText = "未知";

  if (mood > 80) {
    if (trend === "up") { moodColor = "#ef4444"; moodText = "沸腾 (Boiling)"; }
    else if (trend === "down") { moodColor = "#f97316"; moodText = "分歧 (Diverging)"; }
    else { moodColor = "#ef4444"; moodText = "高位震荡 (Top Stable)"; }
  } else if (mood > 60) {
    if (trend === "up") { moodColor = "#ef4444"; moodText = "脉冲 (Impulse)"; }
    else if (trend === "down") { moodColor = "#f97316"; moodText = "过热 (Overheated)"; }
    else { moodColor = "#f97316"; moodText = "走强 (Strengthening)"; }
  } else if (mood > 40) {
    if (trend === "up") { moodColor = "#f97316"; moodText = "进攻 (Offending)"; }
    else if (trend === "down") { moodColor = "#eab308"; moodText = "走弱 (Weakening)"; }
    else { moodColor = "#eab308"; moodText = "活跃 (Active)"; }
  } else if (mood > 20) {
    if (trend === "up") { moodColor = "#22c55e"; moodText = "回暖 (Recovering)"; }
    else if (trend === "down") { moodColor = "#64748b"; moodText = "转冷 (Cooling)"; }
    else { moodColor = "#475569"; moodText = "磨底 (Bottoming)"; }
  } else {
    if (trend === "up") { moodColor = "#3b82f6"; moodText = "筑底 (Bottoming)"; }
    else { moodColor = "#1e293b"; moodText = "冰点 (Ice Point)"; }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* Main Mood Gauge - Takes up 1 column on mobile, 1 on desktop but visually distinct */}
      <div className="md:col-span-1 bg-neutral-900/50 border border-neutral-800 rounded-xl p-6 relative overflow-hidden group hover:border-blue-500/50 transition-all">
        <h3 className="text-gray-400 text-sm font-medium mb-4 flex items-center">
          <Activity className="w-4 h-4 mr-2 text-blue-400" />
          全市场情绪 (Market Mood)
        </h3>

        <div className="h-40 relative flex items-center justify-center">
          {/* Simple Recharts Gauge */}
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={gaugeData}
                cx="50%"
                cy="70%"
                startAngle={180}
                endAngle={0}
                innerRadius={60}
                outerRadius={80}
                dataKey="value"
                stroke="none"
              >
                <Cell fill={moodColor} />
                <Cell fill="#333" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute bottom-0 left-0 right-0 top-0 flex flex-col items-center justify-center mt-10">
            <div className="flex items-center gap-2">
              <span
                className="text-4xl font-bold text-white transition-colors duration-500"
                style={{ color: moodColor }}
              >
                {mood}
              </span>
              {trend === "up" && <TrendingUp className="w-6 h-6 text-red-500" />}
              {trend === "down" && <TrendingDown className="w-6 h-6 text-green-500" />}
              {trend === "flat" && <Minus className="w-6 h-6 text-neutral-600" />}
            </div>
            <span className="text-xs text-gray-500 mt-1">{moodText}</span>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Fried Board Rate */}
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-4 flex flex-col justify-between hover:bg-neutral-800/50 transition-colors">
          <div className="flex justify-between items-start">
            <span className="text-gray-400 text-xs">炸板率 (Fried Rate)</span>
            <AlertTriangle
              className={`w-4 h-4 ${metrics.fried_rate > 30 ? "text-red-500" : "text-green-500"}`}
            />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-white">
              {metrics.fried_rate}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {metrics.fried_board_count} /{" "}
              {metrics.fried_board_count + metrics.limit_up_count}
            </div>
          </div>
          <div className="mt-3 w-full bg-gray-800 h-1 rounded-full overflow-hidden">
            <div
              className="bg-red-500 h-full transition-all duration-500"
              style={{ width: `${Math.min(metrics.fried_rate, 100)}%` }}
            />
          </div>
        </div>

        {/* Premium Rate */}
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-4 flex flex-col justify-between hover:bg-neutral-800/50 transition-colors">
          <div className="flex justify-between items-start">
            <span className="text-gray-400 text-xs">昨涨停溢价 (Premium)</span>
            <TrendingUp className="w-4 h-4 text-yellow-500" />
          </div>
          <div className="mt-2">
            <div
              className={`text-2xl font-bold ${metrics.premium_rate > 0 ? "text-red-500" : "text-green-500"}`}
            >
              {metrics.premium_rate > 0 ? "+" : ""}
              {metrics.premium_rate}%
            </div>
            <div className="text-xs text-gray-500 mt-1">打板赚钱效应</div>
          </div>
          <div className="mt-3 w-full bg-gray-800 h-1 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${metrics.premium_rate > 3 ? "bg-red-500" : "bg-yellow-500"}`}
              style={{
                width: `${Math.min(Math.abs(metrics.premium_rate) * 10, 100)}%`,
              }}
            />
          </div>
        </div>

        {/* Promotion Rate */}
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-4 flex flex-col justify-between hover:bg-neutral-800/50 transition-colors">
          <div className="flex justify-between items-start">
            <span className="text-gray-400 text-xs">连板晋级 (Promotion)</span>
            <TrendingUp className="w-4 h-4 text-purple-500" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-white">
              {metrics.promotion_rate}%
            </div>
            <div className="text-xs text-gray-500 mt-1">接力成功率</div>
          </div>
          <div className="mt-3 w-full bg-gray-800 h-1 rounded-full overflow-hidden">
            <div
              className="bg-purple-500 h-full transition-all duration-500"
              style={{ width: `${metrics.promotion_rate}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
