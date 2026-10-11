"use client";

import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Point = {
  date: string;
  close: string | number;
  volume: number;
};

export function PriceChart({ points }: { points: Point[] }) {
  const data = points.map((point) => ({
    date: point.date.slice(5),
    close: Number(point.close),
    volume: point.volume,
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis dataKey="date" tick={{ fill: "#9aa6b8", fontSize: 12 }} />
          <YAxis yAxisId="price" tick={{ fill: "#9aa6b8", fontSize: 12 }} width={56} />
          <YAxis yAxisId="volume" orientation="right" tick={{ fill: "#9aa6b8", fontSize: 12 }} width={48} />
          <Tooltip contentStyle={{ background: "#101622", border: "1px solid rgba(255,255,255,0.1)" }} />
          <Bar yAxisId="volume" dataKey="volume" fill="rgba(91,157,255,0.35)" />
          <Line yAxisId="price" type="monotone" dataKey="close" stroke="#5b9dff" dot={false} strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
