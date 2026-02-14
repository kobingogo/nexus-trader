"use client";

import { useState } from "react";
import { SectorHeatmap } from "@/components/SectorHeatmap";
import { LeaderList } from "@/components/LeaderList";
import { SignalFeed } from "@/components/SignalFeed";
import { MarketBreadth } from "@/components/MarketBreadth";
import { LogicChain } from "@/components/LogicChain";
import { SentimentRadar } from "@/components/SentimentRadar";
import { AnomalyStream } from "@/components/AnomalyStream";
import { DailyReview } from "@/components/DailyReview";
import { WatchlistManager } from "@/components/WatchlistManager";
import { WatchlistQuotes } from "@/components/WatchlistQuotes";
import { LLMSettings } from "@/components/LLMSettings";
import { Star, Bot } from "lucide-react";

export default function Home() {
  const [watchlistOpen, setWatchlistOpen] = useState(false);
  const [llmSettingsOpen, setLLMSettingsOpen] = useState(false);

  return (
    <main className="min-h-screen bg-black text-gray-100">
      {/* Gradient top bar */}
      <div className="h-[2px] bg-linear-to-r from-blue-600 via-purple-600 to-pink-600" />

      <div className="max-w-[1440px] mx-auto px-4 md:px-8 py-6 space-y-6">
        
        {/* Header */}
        <header className="flex justify-between items-center pb-4 border-b border-neutral-800/50">
            <div>
                <h1 className="text-2xl font-bold bg-linear-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
                    NEXUS TRADER
                </h1>
                <p className="text-xs text-gray-600 mt-0.5 tracking-widest uppercase">A-Share Rational Co-pilot · 理性副驾驶</p>
            </div>
            <div className="flex items-center gap-4">
                {/* AI Model Button */}
                <button
                  onClick={() => setLLMSettingsOpen(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-lg hover:bg-purple-500/20 transition-colors text-sm"
                >
                  <Bot className="w-4 h-4" />
                  AI 模型
                </button>
                {/* Watchlist Button */}
                <button
                  onClick={() => setWatchlistOpen(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-lg hover:bg-yellow-500/20 transition-colors text-sm"
                >
                  <Star className="w-4 h-4 fill-yellow-400" />
                  我的关注
                </button>
                <div className="text-right">
                    <div className="text-[10px] text-gray-600 uppercase tracking-wider">Market Status</div>
                    <div className="text-green-400 font-mono text-xs flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                        Trading
                    </div>
                </div>
            </div>
        </header>

        {/* Row 1: Market Mood + Macro Events */}
        {/* Row 1: Market Breadth + Logic Chain (replace Macro) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <MarketBreadth />
          <LogicChain />
          <div className="md:col-span-2 lg:col-span-1">
             <SignalFeed />
          </div>
        </div>

        {/* Added SentimentRadar below Market Mood/Macro Events, as MarketOverview is not present */}
        <SentimentRadar />

        {/* Row 2: Watchlist Quotes (full width) */}
        <WatchlistQuotes />

        {/* Row 3: Heatmap (wide) + Leader List (narrow) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
                <SectorHeatmap />
            </div>
            <div className="lg:col-span-1">
                <LeaderList />
            </div>
        </div>

        {/* Row 4: Anomaly Stream */}
        <AnomalyStream />

        {/* Row 5: Daily Review */}
        <DailyReview />

        {/* Footer */}
        <footer className="text-center py-6 border-t border-neutral-800/30">
          <p className="text-[10px] text-gray-700 tracking-wider">
            NEXUS TRADER v1.0 · Data powered by AkShare · Not financial advice
          </p>
        </footer>
      </div>

      {/* Slide-out Panels */}
      <WatchlistManager open={watchlistOpen} onClose={() => setWatchlistOpen(false)} />
      <LLMSettings open={llmSettingsOpen} onClose={() => setLLMSettingsOpen(false)} />
    </main>
  );
}
