"use client";

import { useEffect, useState, useCallback } from "react";
import { marketApi, watchlistApi } from "@/lib/api";
import { ArrowUpRight, TrendingUp, Star, Loader2 } from "lucide-react";
import Link from "next/link";

interface Stock {
  code: string;
  name: string;
  price: number;
  change_pct: number;
  turnover: number;
}

export function LeaderList() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [watchedCodes, setWatchedCodes] = useState<Set<string>>(new Set());
  const [addingCode, setAddingCode] = useState<string | null>(null);

  const loadWatchlist = useCallback(async () => {
    try {
      const res = await watchlistApi.list();
      setWatchedCodes(new Set((res.data || []).map((s: { code: string }) => s.code)));
    } catch (e) {
      console.error("Failed to load watchlist", e);
    }
  }, []);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await marketApi.getLeaders();
        setStocks(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
    loadWatchlist();
  }, [loadWatchlist]);

  const toggleWatch = async (stock: Stock) => {
    setAddingCode(stock.code);
    try {
      if (watchedCodes.has(stock.code)) {
        await watchlistApi.remove(stock.code);
        setWatchedCodes(prev => {
          const next = new Set(prev);
          next.delete(stock.code);
          return next;
        });
      } else {
        await watchlistApi.add(stock.code, stock.name);
        setWatchedCodes(prev => new Set(prev).add(stock.code));
      }
    } catch (e) {
      console.error("Failed to toggle watch", e);
    } finally {
      setAddingCode(null);
    }
  };

  if (loading) return <div className="text-gray-400">Loading Leaders...</div>;

  return (
    <div className="bg-neutral-900/50 rounded-lg p-4 border border-neutral-800 h-full">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="text-yellow-500 w-5 h-5" />
        <h2 className="text-lg font-semibold text-white">🚀 核心龙头 (Core Leaders)</h2>
      </div>
      
      <div className="overflow-auto max-h-[500px]">
        <table className="w-full text-left text-sm text-gray-400">
          <thead className="text-xs uppercase bg-neutral-800/50 text-gray-300 sticky top-0">
            <tr>
              <th className="px-3 py-2">股票</th>
              <th className="px-3 py-2 text-right">最新价</th>
              <th className="px-3 py-2 text-right">涨幅</th>
              <th className="px-3 py-2 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => {
              const isWatched = watchedCodes.has(stock.code);
              return (
                <tr key={stock.code} className="border-b border-neutral-800 hover:bg-neutral-800/30">
                  <td className="px-3 py-3 font-medium text-white">
                    <div className="flex flex-col">
                      <span>{stock.name}</span>
                      <span className="text-xs text-gray-500">{stock.code}</span>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-right">¥{stock.price}</td>
                  <td className="px-3 py-3 text-right font-bold text-red-500">
                    +{stock.change_pct}%
                  </td>
                  <td className="px-3 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => toggleWatch(stock)}
                        disabled={addingCode === stock.code}
                        className={`p-1 rounded transition-all ${
                          isWatched
                            ? "text-yellow-400 hover:text-yellow-300"
                            : "text-gray-600 hover:text-yellow-400"
                        }`}
                        title={isWatched ? "取消关注" : "添加关注"}
                      >
                        {addingCode === stock.code ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Star className={`w-3.5 h-3.5 ${isWatched ? "fill-yellow-400" : ""}`} />
                        )}
                      </button>
                      <Link 
                        href={`/diagnose/${stock.code}`}
                        className="inline-flex items-center gap-1 text-xs bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 px-2 py-1 rounded border border-blue-600/30 transition-colors"
                      >
                        诊断 <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
