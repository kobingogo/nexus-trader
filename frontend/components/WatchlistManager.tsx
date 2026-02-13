"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { watchlistApi } from "@/lib/api";
import { Star, Plus, X, Search, Loader2, Tag, ArrowUpRight } from "lucide-react";
import Link from "next/link";

interface WatchedStock {
  code: string;
  name: string;
  tags: string[];
}

interface SearchResult {
  code: string;
  name: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

const PRESET_TAGS = ["底仓", "观望", "做T", "加仓", "减仓", "止损"];

const TAG_STYLES: Record<string, string> = {
  "底仓": "bg-blue-500/15 text-blue-400 border-blue-500/30",
  "观望": "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  "做T": "bg-purple-500/15 text-purple-400 border-purple-500/30",
  "加仓": "bg-green-500/15 text-green-400 border-green-500/30",
  "减仓": "bg-orange-500/15 text-orange-400 border-orange-500/30",
  "止损": "bg-red-500/15 text-red-400 border-red-500/30",
};

export function WatchlistManager({ open, onClose }: Props) {
  const [stocks, setStocks] = useState<WatchedStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState("");
  const [editingTags, setEditingTags] = useState<string | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadWatchlist = useCallback(async () => {
    try {
      const res = await watchlistApi.list();
      setStocks((res.data || []).map((s: WatchedStock) => ({
        ...s,
        tags: s.tags || [],
      })));
    } catch (e) {
      console.error("Failed to load watchlist", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) loadWatchlist();
  }, [open, loadWatchlist]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setMessage("");

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!value.trim()) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await watchlistApi.search(value.trim());
        setSearchResults(res.results || []);
        setShowDropdown(true);
      } catch (e) {
        console.error("Search failed", e);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
  };

  const handleAddStock = async (code: string, name?: string) => {
    setAdding(true);
    setMessage("");
    try {
      const res = await watchlistApi.add(code, name);
      setMessage(res.message);
      if (res.success) {
        setSearchQuery("");
        setSearchResults([]);
        setShowDropdown(false);
        loadWatchlist();
      }
    } catch {
      setMessage("添加失败");
    } finally {
      setAdding(false);
    }
  };

  const handleSelectResult = (result: SearchResult) => {
    handleAddStock(result.code, result.name);
  };

  const handleDirectAdd = () => {
    const q = searchQuery.trim();
    if (!q) {
      setMessage("请输入股票代码或名称");
      return;
    }
    // If it looks like a stock code (all digits), add directly
    if (/^\d{6}$/.test(q)) {
      handleAddStock(q);
    } else if (searchResults.length > 0) {
      // Add the first result
      handleSelectResult(searchResults[0]);
    } else {
      setMessage("未找到匹配的股票，请输入6位股票代码");
    }
  };

  const handleRemove = async (code: string) => {
    try {
      await watchlistApi.remove(code);
      loadWatchlist();
    } catch (e) {
      console.error("Failed to remove", e);
    }
  };

  const toggleTag = async (code: string, tag: string) => {
    const stock = stocks.find(s => s.code === code);
    if (!stock) return;

    const newTags = stock.tags.includes(tag)
      ? stock.tags.filter(t => t !== tag)
      : [...stock.tags, tag];

    try {
      await watchlistApi.updateTags(code, newTags);
      setStocks(prev => prev.map(s => s.code === code ? { ...s, tags: newTags } : s));
    } catch (e) {
      console.error("Failed to update tags", e);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" onClick={onClose} />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-full max-w-md bg-neutral-900 border-l border-neutral-800 z-50 flex flex-col shadow-2xl animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
            <h2 className="text-lg font-semibold text-gray-100">我的关注</h2>
            <span className="text-xs text-gray-500 bg-neutral-800 px-2 py-0.5 rounded-full">
              {stocks.length} 只
            </span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-neutral-800 transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Search / Add Section */}
        <div className="p-4 border-b border-neutral-800" ref={searchRef}>
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  placeholder="输入代码或名称搜索，如 002340 或 格林"
                  className="w-full pl-9 pr-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-500/50"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      if (showDropdown && searchResults.length > 0) {
                        handleSelectResult(searchResults[0]);
                      } else {
                        handleDirectAdd();
                      }
                    }
                  }}
                  onFocus={() => {
                    if (searchResults.length > 0) setShowDropdown(true);
                  }}
                />
                {searching && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 animate-spin" />
                )}
              </div>

              {/* Dropdown Results */}
              {showDropdown && searchResults.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-1 bg-neutral-800 border border-neutral-700 rounded-lg shadow-xl z-10 max-h-60 overflow-y-auto">
                  {searchResults.map((result) => {
                    const isWatched = stocks.some(s => s.code === result.code);
                    return (
                      <button
                        key={result.code}
                        onClick={() => !isWatched && handleSelectResult(result)}
                        disabled={isWatched || adding}
                        className={`w-full flex items-center justify-between px-3 py-2.5 text-sm transition-colors ${
                          isWatched
                            ? "text-gray-600 cursor-not-allowed"
                            : "text-gray-200 hover:bg-neutral-700/50"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-gray-400 w-16">{result.code}</span>
                          <span>{result.name}</span>
                        </div>
                        {isWatched ? (
                          <span className="text-[10px] text-gray-600 bg-neutral-700/50 px-1.5 py-0.5 rounded">已关注</span>
                        ) : (
                          <Plus className="w-3.5 h-3.5 text-purple-400 opacity-0 group-hover:opacity-100" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            <button
              onClick={handleDirectAdd}
              disabled={adding || !searchQuery.trim()}
              className="px-3 py-2 bg-purple-600/20 text-purple-400 border border-purple-600/30 rounded-lg hover:bg-purple-600/30 transition-colors text-sm font-medium disabled:opacity-40 flex items-center gap-1 shrink-0"
            >
              {adding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              关注
            </button>
          </div>
          {message && <p className="text-xs text-gray-400 mt-2">{message}</p>}
        </div>

        {/* Stock List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-gray-600 animate-spin" />
            </div>
          ) : stocks.length === 0 ? (
            <div className="text-center py-12">
              <Search className="w-10 h-10 text-neutral-700 mx-auto mb-3" />
              <p className="text-gray-600 text-sm">暂无关注个股</p>
              <p className="text-gray-700 text-xs mt-1">输入股票代码或名称搜索添加</p>
            </div>
          ) : (
            stocks.map((stock) => (
              <div
                key={stock.code}
                className="p-3 rounded-lg bg-neutral-800/50 border border-neutral-800 hover:border-neutral-700 transition-colors"
              >
                {/* Row 1: Info + Actions */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400 shrink-0" />
                    <div>
                      <span className="text-sm font-medium text-gray-200">{stock.name}</span>
                      <span className="text-xs text-gray-500 font-mono ml-2">{stock.code}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {/* AI Diagnose */}
                    <Link
                      href={`/diagnose/${stock.code}`}
                      className="p-1.5 rounded-md hover:bg-blue-500/10 text-gray-600 hover:text-blue-400 transition-all"
                      title="AI 诊断"
                      onClick={onClose}
                    >
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </Link>
                    {/* Tag button */}
                    <button
                      onClick={() => setEditingTags(editingTags === stock.code ? null : stock.code)}
                      className={`p-1.5 rounded-md transition-all ${
                        editingTags === stock.code
                          ? "bg-purple-500/10 text-purple-400"
                          : "text-gray-600 hover:text-purple-400 hover:bg-purple-500/10"
                      }`}
                      title="管理标签"
                    >
                      <Tag className="w-3.5 h-3.5" />
                    </button>
                    {/* Remove */}
                    <button
                      onClick={() => handleRemove(stock.code)}
                      className="p-1.5 rounded-md text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                      title="取消关注"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Row 2: Current Tags */}
                {stock.tags.length > 0 && (
                  <div className="flex items-center gap-1 mt-2 ml-7">
                    {stock.tags.map(tag => (
                      <span
                        key={tag}
                        className={`text-[10px] px-1.5 py-0.5 rounded border ${TAG_STYLES[tag] || "bg-neutral-700/30 text-gray-400 border-neutral-600"}`}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Row 3: Tag Editor (expandable) */}
                {editingTags === stock.code && (
                  <div className="mt-2 ml-7 p-2 bg-neutral-800 rounded-md border border-neutral-700">
                    <p className="text-[10px] text-gray-500 mb-1.5">点击标签添加/移除:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {PRESET_TAGS.map(tag => {
                        const isActive = stock.tags.includes(tag);
                        return (
                          <button
                            key={tag}
                            onClick={() => toggleTag(stock.code, tag)}
                            className={`text-[10px] px-2 py-1 rounded border transition-all ${
                              isActive
                                ? TAG_STYLES[tag] || "bg-neutral-600 text-white border-neutral-500"
                                : "bg-neutral-800 text-gray-500 border-neutral-700 hover:border-neutral-600"
                            }`}
                          >
                            {tag}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <style jsx>{`
        @keyframes slide-in {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </>
  );
}
