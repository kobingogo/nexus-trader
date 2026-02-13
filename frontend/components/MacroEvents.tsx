"use client";

import { useEffect, useState } from "react";
import { marketApi } from "@/lib/api";
import { Globe, Star, Clock } from "lucide-react";

interface MacroEvent {
  time: string;
  country: string;
  event: string;
  actual: number | string;
  forecast: number | string;
  previous: number | string;
  importance: number;
}

const COUNTRY_FLAG: Record<string, string> = {
  "美国": "🇺🇸",
  "中国": "🇨🇳",
  "日本": "🇯🇵",
  "欧元区": "🇪🇺",
  "英国": "🇬🇧",
  "德国": "🇩🇪",
  "法国": "🇫🇷",
  "澳大利亚": "🇦🇺",
  "加拿大": "🇨🇦",
  "韩国": "🇰🇷",
  "印度": "🇮🇳",
  "巴西": "🇧🇷",
  "俄罗斯": "🇷🇺",
  "意大利": "🇮🇹",
  "南非": "🇿🇦",
  "墨西哥": "🇲🇽",
  "瑞士": "🇨🇭",
  "新西兰": "🇳🇿",
};

function ImportanceDots({ level }: { level: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3].map((i) => (
        <Star
          key={i}
          className={`w-2.5 h-2.5 ${
            i <= level ? "text-yellow-400 fill-yellow-400" : "text-neutral-700"
          }`}
        />
      ))}
    </div>
  );
}

export function MacroEvents() {
  const [events, setEvents] = useState<MacroEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all"); // "all" | "cn" | "us" | "high"

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await marketApi.getMacroEvents();
        setEvents(res.data || []);
      } catch {
        setEvents([]);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const filtered = events.filter((e) => {
    if (filter === "cn") return e.country === "中国";
    if (filter === "us") return e.country === "美国";
    if (filter === "high") return e.importance >= 2;
    return true;
  });

  if (loading) {
    return (
      <div className="bg-neutral-900/50 rounded-xl p-5 border border-neutral-800 animate-pulse h-full">
        <div className="h-4 bg-neutral-800 rounded w-1/3 mb-4" />
        <div className="space-y-2">
          <div className="h-8 bg-neutral-800 rounded" />
          <div className="h-8 bg-neutral-800 rounded" />
          <div className="h-8 bg-neutral-800 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-neutral-900/50 rounded-xl p-5 border border-neutral-800 h-full flex flex-col">
      {/* Title */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-400 flex items-center gap-2">
          <Globe className="w-4 h-4 text-blue-500" />
          宏观日历 (Macro)
        </h3>
        <span className="text-xs text-gray-600">{events.length} 条</span>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1 mb-3">
        {[
          { key: "all", label: "全部" },
          { key: "cn", label: "🇨🇳 中国" },
          { key: "us", label: "🇺🇸 美国" },
          { key: "high", label: "⭐ 重要" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              filter === tab.key
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                : "bg-neutral-800/50 text-gray-500 border border-transparent hover:text-gray-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto max-h-[280px] space-y-1 pr-1 scrollbar-thin">
        {filtered.length === 0 ? (
          <div className="text-center text-gray-600 text-xs py-4">暂无数据</div>
        ) : (
          filtered.map((event, i) => (
            <div
              key={i}
              className={`flex items-start gap-2 p-2 rounded-lg text-xs transition-colors hover:bg-neutral-800/50 ${
                event.importance >= 2 ? "border-l-2 border-yellow-500/50" : "border-l-2 border-transparent"
              }`}
            >
              {/* Time */}
              <div className="flex items-center gap-1 text-gray-500 whitespace-nowrap min-w-[42px]">
                <Clock className="w-3 h-3" />
                {event.time}
              </div>

              {/* Country Flag */}
              <span className="text-sm leading-tight">{COUNTRY_FLAG[event.country] || "🌐"}</span>

              {/* Event Info */}
              <div className="flex-1 min-w-0">
                <div className="text-gray-300 truncate leading-tight" title={event.event}>
                  {event.event}
                </div>
                <div className="flex gap-3 mt-0.5 text-gray-500">
                  {event.actual !== "" && event.actual !== null && (
                    <span>
                      公布: <span className="text-white font-mono">{event.actual}</span>
                    </span>
                  )}
                  {event.forecast !== "" && event.forecast !== null && (
                    <span>
                      预期: <span className="text-yellow-400/70 font-mono">{event.forecast}</span>
                    </span>
                  )}
                  {event.previous !== "" && event.previous !== null && (
                    <span>
                      前值: <span className="text-gray-400 font-mono">{event.previous}</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Importance */}
              <ImportanceDots level={event.importance} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
