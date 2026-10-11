"use client";

import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Point = {
  date: string;
  close: string | number;
  volume: number;
  vwap?: string | number | null;
  anomaly?: boolean;
};

export function PriceChart({ points }: { points: Point[] }) {
  const data = points.map((point) => ({
    date: point.date.slice(5),
    close: Number(point.close),
    volume: point.volume,
    vwap: point.vwap == null ? null : Number(point.vwap),
    anomaly: point.anomaly ? Number(point.close) : null,
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis dataKey="date" tick={{ fill: "#9aa6b8", fontSize: 12 }} />
          <YAxis yAxisId="price" tick={{ fill: "#9aa6b8", fontSize: 12 }} width={64} domain={["auto", "auto"]} />
          <YAxis yAxisId="volume" orientation="right" tick={{ fill: "#9aa6b8", fontSize: 12 }} width={48} />
          <Tooltip contentStyle={{ background: "#101622", border: "1px solid rgba(255,255,255,0.1)" }} />
          <Bar yAxisId="volume" dataKey="volume" fill="rgba(61,220,151,0.22)" />
          <Line yAxisId="price" type="monotone" dataKey="vwap" stroke="#f5c16c" dot={false} strokeWidth={1.5} connectNulls />
          <Line yAxisId="price" type="monotone" dataKey="close" stroke="#5b9dff" dot={false} strokeWidth={2} />
          <Line yAxisId="price" type="monotone" dataKey="anomaly" stroke="#ff6b6b" dot={{ r: 4 }} strokeWidth={0} connectNulls={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
