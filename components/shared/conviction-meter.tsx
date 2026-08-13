"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import { directionFromSignal, type SignalDirection, type SignalType } from "@/lib/constants";

const DIRECTION_COLOR: Record<SignalDirection, string> = {
  bullish: "var(--bullish)",
  bearish: "var(--bearish)",
  neutral: "var(--signal-hold)",
};

interface ConvictionMeterProps {
  filled: number;
  total: number;
  signal?: SignalType;
  direction?: SignalDirection;
  size?: "sm" | "md";
  className?: string;
}

/**
 * Signature element #1 (§5.3) -- evolusi "Meteran Konfirmasi" yang di
 * components.py lama sendiri sudah disebut "elemen signature dashboard
 * ini". Di sini: glow tipis pada segmen terisi + animasi mengisi
 * kiri-ke-kanan bertahap saat pertama render.
 */
export function ConvictionMeter({
  filled,
  total,
  signal,
  direction,
  size = "md",
  className,
}: ConvictionMeterProps) {
  const dir = direction ?? directionFromSignal(signal);
  const color = DIRECTION_COLOR[dir];
  const clampedTotal = Math.max(total, 1);
  const clampedFilled = Math.max(0, Math.min(filled, clampedTotal));

  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const barHeight = size === "sm" ? "h-2.5" : "h-3.5";
  const barWidth = size === "sm" ? "w-[3px]" : "w-1.5";

  return (
    <span
      className={cn("inline-flex items-center gap-[3px]", className)}
      title={`Konfirmasi ${clampedFilled} dari ${clampedTotal}`}
    >
      {Array.from({ length: clampedTotal }).map((_, i) => {
        const isFilled = i < clampedFilled;
        return (
          <span
            key={i}
            className={cn(barWidth, barHeight, "rounded-sm transition-all duration-300 ease-out")}
            style={{
              backgroundColor: isFilled ? color : "var(--border-strong)",
              boxShadow: isFilled && mounted ? `0 0 6px 0 ${color}66` : "none",
              transitionDelay: `${i * 60}ms`,
              opacity: mounted ? 1 : 0,
              transform: mounted ? "scaleY(1)" : "scaleY(0.4)",
            }}
          />
        );
      })}
    </span>
  );
}
