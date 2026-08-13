"use client";

import * as React from "react";
import { Play, Pause, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { formatDateId } from "@/lib/format";

interface ReplayScrubberProps {
  dates: string[]; // tanggal seluruh bar (setelah warm-up dibuang), terurut naik
  onDateChange: (date: string | null) => void;
}

const WARMUP_START = 29; // window minimum sebelum replay mulai terasa berarti
const TICK_MS = 90;

/**
 * Padanan langsung "▶️ Play" chart_animation.py lama -- tapi di sini
 * scrubbing HANYA mengubah index lokal (state React murni, lihat §6),
 * tidak pernah memicu network call ulang. Histori pendek (< 30 bar)
 * disembunyikan, sama seperti estimate_frame_count()==0 di versi lama.
 */
export function ReplayScrubber({ dates, onDateChange }: ReplayScrubberProps) {
  const [index, setIndex] = React.useState(dates.length - 1);
  const [playing, setPlaying] = React.useState(false);
  const [active, setActive] = React.useState(false);

  React.useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setIndex((prev) => {
        if (prev >= dates.length - 1) {
          setPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, TICK_MS);
    return () => clearInterval(id);
  }, [playing, dates.length]);

  React.useEffect(() => {
    onDateChange(active ? (dates[index] ?? null) : null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, active]);

  if (dates.length <= WARMUP_START + 1) return null;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-border bg-surface-1 px-4 py-3">
      <Button
        type="button"
        variant="outline"
        size="icon"
        onClick={() => {
          if (!active) {
            setActive(true);
            setIndex(WARMUP_START);
          }
          setPlaying((p) => !p);
        }}
        aria-label={playing ? "Jeda replay" : "Putar replay"}
      >
        {playing ? <Pause className="size-4" /> : <Play className="size-4" />}
      </Button>

      <div className="flex-1">
        <Slider
          value={[active ? index : dates.length - 1]}
          onValueChange={([v]) => {
            setActive(true);
            setPlaying(false);
            setIndex(v);
          }}
          min={WARMUP_START}
          max={dates.length - 1}
          step={1}
        />
      </div>

      <span className="w-24 shrink-0 text-right font-mono text-[12px] text-text-secondary">
        {active ? formatDateId(dates[index]) : "Statis"}
      </span>

      {active && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => {
            setActive(false);
            setPlaying(false);
          }}
          aria-label="Reset ke tampilan statis"
        >
          <RotateCcw className="size-4" />
        </Button>
      )}
    </div>
  );
}
