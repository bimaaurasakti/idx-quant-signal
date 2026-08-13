"use client";

import * as React from "react";
import { Info } from "lucide-react";

import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type Tone = "bullish" | "bearish" | "neutral";

const TONE_COLOR: Record<Tone, string> = {
  bullish: "var(--bullish)",
  bearish: "var(--bearish)",
  neutral: "var(--text-primary)",
};

/** Count-up singkat saat data pertama render -- menegaskan "data ini baru
 * saja dimuat", bukan hiasan (§5.3). Menghormati prefers-reduced-motion. */
function useCountUp(target: number | null, durationMs = 320): number | null {
  const [display, setDisplay] = React.useState<number | null>(target);
  // Sentinel `undefined` (bukan null) supaya animasi TETAP terpicu di mount
  // pertama walau target awal kebetulan sama dgn render berikutnya.
  const prevTargetRef = React.useRef<number | null | undefined>(undefined);

  React.useEffect(() => {
    if (target == null || target === prevTargetRef.current) {
      prevTargetRef.current = target;
      return; // tidak ada setState sinkron di sini -- nilai null diturunkan langsung di `return` bawah
    }
    prevTargetRef.current = target;

    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    let raf = 0;
    const start = performance.now();
    const safeTarget = target; // re-bind supaya TS null-narrowing tetap berlaku di closure tick()
    function tick(now: number) {
      const progress = Math.min((now - start) / durationMs, 1);
      // setState HANYA dipanggil di dalam callback rAF (async), tidak pernah
      // sinkron langsung di body effect -- menghindari cascading render.
      const eased = prefersReduced ? 1 : 1 - Math.pow(1 - progress, 3);
      setDisplay(safeTarget * eased);
      if (progress < 1 && !prefersReduced) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);

  return target == null ? null : display;
}

interface MetricCardProps {
  label: string;
  value: number | null;
  format?: (v: number) => string;
  tone?: Tone;
  helpText?: string;
  className?: string;
}

export function MetricCard({
  label,
  value,
  format = (v) => v.toLocaleString("id-ID"),
  tone = "neutral",
  helpText,
  className,
}: MetricCardProps) {
  const animated = useCountUp(value);
  const displayText = animated == null ? "N/A" : format(animated);

  return (
    <div className={cn("flex flex-col gap-0.5 rounded-md bg-surface-2 px-3.5 py-3", className)}>
      <div className="flex items-center gap-1 text-[12.5px] text-text-secondary">
        <span>{label}</span>
        {helpText && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="text-text-muted transition-colors hover:text-text-secondary"
                aria-label={`Info: ${label}`}
              >
                <Info className="size-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent>{helpText}</TooltipContent>
          </Tooltip>
        )}
      </div>
      <div
        className="font-mono-tabular font-mono text-xl font-semibold"
        style={{ color: TONE_COLOR[tone], fontFamily: "var(--font-mono)" }}
      >
        {displayText}
      </div>
    </div>
  );
}
