"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { anomalyApi } from "@/lib/api";
import { Zap, Rocket, AlertTriangle, DollarSign, ArrowDownCircle, RefreshCw, Globe, Star, Crown, Bell, BellOff } from "lucide-react";

interface AnomalyAlert {
  type: "rocket" | "dive" | "big_order_buy" | "big_order_sell" | "error";
  change_type?: string;
  code?: string;
  name?: string;
  price?: number;
  change_pct?: number;
  amount?: number;
  message: string;
  severity: "high" | "medium" | "low";
  time?: string;
  ts: number;
}

type FilterMode = "all" | "watchlist" | "leaders";

const TYPE_CONFIG: Record<string, { icon: typeof Rocket; color: string; bg: string; border: string }> = {
  rocket: { icon: Rocket, color: "text-red-400", bg: "bg-red-500/5", border: "border-red-900/30" },
  dive: { icon: AlertTriangle, color: "text-green-400", bg: "bg-green-500/5", border: "border-green-900/30" },
  big_order_buy: { icon: DollarSign, color: "text-yellow-400", bg: "bg-yellow-500/5", border: "border-yellow-900/30" },
  big_order_sell: { icon: ArrowDownCircle, color: "text-orange-400", bg: "bg-orange-500/5", border: "border-orange-900/30" },
  error: { icon: AlertTriangle, color: "text-gray-400", bg: "bg-neutral-800/30", border: "border-neutral-700" },
};

const FILTER_TABS: { key: FilterMode; label: string; icon: typeof Globe }[] = [
  { key: "all", label: "全市场", icon: Globe },
  { key: "watchlist", label: "我的关注", icon: Star },
  { key: "leaders", label: "核心龙头", icon: Crown },
];

// Request browser notification permission
async function requestNotificationPermission(): Promise<boolean> {
  if (!("Notification" in window)) return false;
  if (Notification.permission === "granted") return true;
  const result = await Notification.requestPermission();
  return result === "granted";
}

function sendBrowserNotification(alert: AnomalyAlert) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;

  const EMOJI: Record<string, string> = {
    rocket: "🚀", dive: "☢️", big_order_buy: "💰", big_order_sell: "💸",
  };

  const icon = EMOJI[alert.type] || "⚡";
  const title = `${icon} ${alert.change_type || "异动提醒"}`;
  const body = `${alert.name}(${alert.code}) ${alert.change_pct !== undefined ? (alert.change_pct > 0 ? "+" : "") + alert.change_pct + "%" : ""}`;

  try {
    new Notification(title, {
      body,
      tag: `nexus-${alert.code}-${alert.time}`,
      silent: false,
    });
  } catch {
    // Notification API not available in this context
  }
}

export function AnomalyStream() {
  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [filter, setFilter] = useState<FilterMode>("all");
  const [notifyEnabled, setNotifyEnabled] = useState(false);
  const prevWatchlistAlertsRef = useRef<Set<string>>(new Set());
  const listRef = useRef<HTMLDivElement>(null);

  // Toggle notification
  const toggleNotify = async () => {
    if (notifyEnabled) {
      setNotifyEnabled(false);
      return;
    }
    const granted = await requestNotificationPermission();
    setNotifyEnabled(granted);
    if (!granted) {
      alert("请在浏览器设置中允许通知权限");
    }
  };

  const loadAlerts = useCallback(async (filterMode?: FilterMode) => {
    setScanning(true);
    try {
      const res = await anomalyApi.scan(filterMode || filter);
      const newAlerts: AnomalyAlert[] = res.data || [];
      setAlerts(newAlerts);
      setLastUpdate(new Date());

      // Browser notification for watchlist alerts
      if (notifyEnabled) {
        // Always check watchlist alerts for notifications
        let watchlistAlerts: AnomalyAlert[];
        if ((filterMode || filter) === "watchlist") {
          watchlistAlerts = newAlerts;
        } else {
          // Also fetch watchlist in background to notify
          try {
            const watchRes = await anomalyApi.scan("watchlist");
            watchlistAlerts = watchRes.data || [];
          } catch {
            watchlistAlerts = [];
          }
        }

        const currentKeys = new Set(
          watchlistAlerts.map(a => `${a.code}-${a.time}`)
        );

        // Find new alerts (not in previous set)
        watchlistAlerts.forEach(alert => {
          const key = `${alert.code}-${alert.time}`;
          if (!prevWatchlistAlertsRef.current.has(key)) {
            sendBrowserNotification(alert);
          }
        });

        prevWatchlistAlertsRef.current = currentKeys;
      }
    } catch (e) {
      console.error("Failed to scan anomalies", e);
    } finally {
      setLoading(false);
      setScanning(false);
    }
  }, [filter, notifyEnabled]);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(() => loadAlerts(), 30000);
    return () => clearInterval(interval);
  }, [loadAlerts]);

  const handleFilterChange = (newFilter: FilterMode) => {
    setFilter(newFilter);
    setLoading(true);
    loadAlerts(newFilter);
  };

  if (loading) {
    return (
      <div className="bg-neutral-900/50 rounded-xl p-5 border border-neutral-800 animate-pulse">
        <div className="h-4 bg-neutral-800 rounded w-1/3 mb-4" />
        <div className="space-y-2">
          <div className="h-12 bg-neutral-800 rounded" />
          <div className="h-12 bg-neutral-800 rounded" />
          <div className="h-12 bg-neutral-800 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-neutral-900/50 rounded-xl p-5 border border-neutral-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Zap className="w-4 h-4 text-yellow-400" />
            {alerts.length > 0 && (
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
            )}
          </div>
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">异动精灵 · NEXUS Eyes</h3>
        </div>
        <div className="flex items-center gap-2">
          {/* Notification Toggle */}
          <button
            onClick={toggleNotify}
            className={`p-1.5 rounded-md transition-all ${
              notifyEnabled
                ? "bg-yellow-500/10 text-yellow-400"
                : "text-gray-600 hover:text-gray-400 hover:bg-neutral-800"
            }`}
            title={notifyEnabled ? "已开启异动通知" : "开启异动通知"}
          >
            {notifyEnabled ? (
              <Bell className="w-3.5 h-3.5" />
            ) : (
              <BellOff className="w-3.5 h-3.5" />
            )}
          </button>
          <span className="text-[10px] text-gray-600 font-mono">
            {lastUpdate ? lastUpdate.toLocaleTimeString() : "—"}
          </span>
          <button
            onClick={() => loadAlerts()}
            disabled={scanning}
            className="p-1 rounded hover:bg-neutral-800 transition-colors disabled:opacity-30"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${scanning ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Notification hint */}
      {notifyEnabled && (
        <div className="flex items-center gap-2 mb-3 px-3 py-1.5 bg-yellow-500/5 border border-yellow-900/20 rounded-lg">
          <Bell className="w-3 h-3 text-yellow-400" />
          <span className="text-[10px] text-yellow-400/70">异动通知已开启 · 关注个股出现异动时将推送浏览器通知</span>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-1 mb-3 p-1 bg-neutral-800/50 rounded-lg">
        {FILTER_TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => handleFilterChange(key)}
            className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
              filter === key
                ? "bg-neutral-700 text-gray-100 shadow-sm"
                : "text-gray-500 hover:text-gray-300 hover:bg-neutral-800"
            }`}
          >
            <Icon className={`w-3 h-3 ${filter === key && key === "watchlist" ? "fill-yellow-400 text-yellow-400" : ""}`} />
            {label}
          </button>
        ))}
      </div>

      {/* Alert Count Summary */}
      <div className="flex gap-3 mb-3">
        {[
          { type: "rocket", label: "拉升", count: alerts.filter(a => a.type === "rocket").length },
          { type: "dive", label: "跳水", count: alerts.filter(a => a.type === "dive").length },
          { type: "big_order_buy", label: "大买", count: alerts.filter(a => a.type === "big_order_buy").length },
          { type: "big_order_sell", label: "大卖", count: alerts.filter(a => a.type === "big_order_sell").length },
        ].map(({ type, label, count }) => {
          const cfg = TYPE_CONFIG[type];
          return (
            <div key={type} className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] ${cfg.bg} border ${cfg.border}`}>
              <cfg.icon className={`w-3 h-3 ${cfg.color}`} />
              <span className={cfg.color}>{label}</span>
              <span className={`${cfg.color} font-mono font-bold`}>{count}</span>
            </div>
          );
        })}
      </div>

      {/* Alert List */}
      <div ref={listRef} className="space-y-1.5 max-h-[400px] overflow-y-auto pr-1">
        {alerts.length === 0 ? (
          <div className="text-center py-8">
            <Zap className="w-8 h-8 text-neutral-700 mx-auto mb-2" />
            <p className="text-gray-600 text-xs">
              {filter === "watchlist"
                ? "关注列表中暂无异动"
                : filter === "leaders"
                ? "龙头股暂无异动"
                : "暂无异动信号"}
            </p>
            <p className="text-gray-700 text-[10px] mt-1">
              {filter === "watchlist" ? "请先添加关注个股" : "系统每30秒自动扫描"}
            </p>
          </div>
        ) : (
          alerts.map((alert, i) => {
            const cfg = TYPE_CONFIG[alert.type] || TYPE_CONFIG.error;
            const Icon = cfg.icon;
            return (
              <div
                key={i}
                className={`flex items-start gap-2.5 p-3 rounded-lg ${cfg.bg} border ${cfg.border} transition-all duration-300 hover:brightness-110`}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${cfg.color}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-200 leading-relaxed">{alert.message}</p>
                  {alert.code && (
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className="text-[10px] font-mono text-gray-500">{alert.code}</span>
                      {alert.price !== undefined && alert.price > 0 && <span className="text-[10px] font-mono text-gray-500">¥{alert.price}</span>}
                      <span className="text-[10px] text-gray-600 ml-auto font-mono">
                        {alert.time || new Date(alert.ts * 1000).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
