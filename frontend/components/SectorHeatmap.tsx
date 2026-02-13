"use client";

import { useEffect, useState } from "react";
import { marketApi } from "@/lib/api";
import { Treemap, Tooltip, ResponsiveContainer } from "recharts";

interface SectorData {
  name: string;
  change_pct: number;
  market_cap: number;
  leader_name: string; // Ensure this matches backend response
  value: number; // calculated for treemap size
}

export function SectorHeatmap() {
  const [data, setData] = useState<SectorData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await marketApi.getHeatmap();
        // Transform data for Recharts Treemap
        // We use market_cap as 'value' for box size
        const transform = res.data.map((item: any) => ({
          ...item,
          value: item.market_cap || 1, 
          // Recharts Treemap needs a 'value' key
        }));
        setData(transform);
      } catch (e) {
        console.error("Failed to load heatmap", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className="text-gray-400">Loading Heatmap...</div>;

  return (
    <div className="w-full h-[400px] bg-neutral-900/50 rounded-lg p-4 border border-neutral-800">
      <h2 className="text-lg font-semibold mb-4 text-white">🔥 板块热力图 (Sector Heatmap)</h2>
        {/* Note: Recharts Treemap customization is tricky. 
            For MVP, we use a simple Grid fallback if Treemap is too complex to style perfectly in one go.
            Let's try a colored grid first as it's often more readable for "Heatmap". 
        */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 max-h-[320px] overflow-y-auto">
        {data.slice(0, 24).map((sector) => (
          <div
            key={sector.name}
            className={`p-3 rounded-md flex flex-col justify-between cursor-pointer transition-colors hover:opacity-80
              ${sector.change_pct > 0 ? "bg-red-900/40 border-red-700/50" : "bg-green-900/40 border-green-700/50"}
              border`}
          >
            <span className="text-sm font-medium text-gray-200 truncate">{sector.name}</span>
            <div className="flex justify-between items-end mt-2">
                <span className={`text-lg font-bold ${sector.change_pct > 0 ? "text-red-400" : "text-green-400"}`}>
                    {sector.change_pct > 0 ? "+" : ""}{sector.change_pct.toFixed(2)}%
                </span>
            </div>
            <div className="text-xs text-gray-500 mt-1 truncate">
             领涨: {sector.leader_name}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
