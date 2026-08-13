"use client";

import { cn } from "@/lib/utils";

interface FiltersBarProps {
  sectors: string[];
  selectedSectors: string[];
  onToggleSector: (s: string) => void;
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (v: string) => void;
  onDateToChange: (v: string) => void;
  tickerSearch: string;
  onTickerSearchChange: (v: string) => void;
}

export function FiltersBar({
  sectors,
  selectedSectors,
  onToggleSector,
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  tickerSearch,
  onTickerSearchChange,
}: FiltersBarProps) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface-1 p-3">
      <div className="flex flex-wrap gap-1.5">
        {sectors.map((s) => {
          const active = selectedSectors.includes(s);
          return (
            <button
              key={s}
              type="button"
              onClick={() => onToggleSector(s)}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[11.5px] font-medium transition-colors",
                active
                  ? "border-brand bg-brand/15 text-brand-emphasis"
                  : "border-border text-text-secondary hover:border-border-strong hover:text-text-primary",
              )}
            >
              {s.replaceAll("_", " ")}
            </button>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-[12.5px] text-text-secondary">
          <span>Exit dari</span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => onDateFromChange(e.target.value)}
            className="rounded-md border border-border bg-surface-2 px-2 py-1 font-mono text-[12px] text-text-primary"
          />
          <span>s/d</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => onDateToChange(e.target.value)}
            className="rounded-md border border-border bg-surface-2 px-2 py-1 font-mono text-[12px] text-text-primary"
          />
        </div>
        <input
          type="text"
          placeholder="Cari ticker..."
          value={tickerSearch}
          onChange={(e) => onTickerSearchChange(e.target.value)}
          className="rounded-md border border-border bg-surface-2 px-2.5 py-1 font-mono text-[12.5px] text-text-primary placeholder:text-text-muted"
        />
      </div>
    </div>
  );
}
