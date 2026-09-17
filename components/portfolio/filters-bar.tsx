"use client";

import * as React from "react";
import { Calendar, Search, RotateCcw } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
  const hasActiveFilters =
    selectedSectors.length > 0 || dateFrom !== "" || dateTo !== "" || tickerSearch !== "";

  const handleResetFilters = () => {
    selectedSectors.forEach((s) => onToggleSector(s));
    onDateFromChange("");
    onDateToChange("");
    onTickerSearchChange("");
  };

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface-1 p-3.5">
      {/* Sektor Filter Chips */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-xs font-medium text-text-muted">Sektor:</span>
        {sectors.map((s) => {
          const active = selectedSectors.includes(s);
          return (
            <button
              key={s}
              type="button"
              onClick={() => onToggleSector(s)}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[11.5px] font-medium transition-colors cursor-pointer",
                active
                  ? "border-brand bg-brand/15 text-brand-emphasis shadow-xs"
                  : "border-border bg-surface-2/50 text-text-secondary hover:border-border-strong hover:text-text-primary",
              )}
            >
              {s.replaceAll("_", " ")}
            </button>
          );
        })}
      </div>

      {/* Date Range & Search Input Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-border-subtle">
        <div className="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
          <span className="text-text-muted">Exit:</span>
          <div className="w-[145px]">
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => onDateFromChange(e.target.value)}
              prefix={<Calendar className="size-3.5 text-text-muted shrink-0" />}
              className="h-8 text-xs bg-surface-2"
            />
          </div>
          <span className="text-text-muted">s/d</span>
          <div className="w-[145px]">
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => onDateToChange(e.target.value)}
              prefix={<Calendar className="size-3.5 text-text-muted shrink-0" />}
              className="h-8 text-xs bg-surface-2"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-[180px] sm:w-[220px]">
            <Input
              type="text"
              placeholder="Cari emiten..."
              value={tickerSearch}
              onChange={(e) => onTickerSearchChange(e.target.value)}
              onClear={() => onTickerSearchChange("")}
              prefix={<Search className="size-3.5 text-text-muted shrink-0" />}
              className="h-8 text-xs bg-surface-2 font-mono"
            />
          </div>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetFilters}
              className="h-8 px-2 text-xs text-text-muted hover:text-text-primary gap-1"
              title="Reset semua filter"
            >
              <RotateCcw className="size-3 text-text-muted" />
              <span className="hidden sm:inline">Reset</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
