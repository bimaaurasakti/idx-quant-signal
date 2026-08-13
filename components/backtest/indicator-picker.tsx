"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import type { IndicatorSpec } from "@/lib/types";

interface IndicatorPickerProps {
  categories: string[];
  indicatorsByCategory: Record<string, IndicatorSpec[]>;
  selected: string[];
  onToggle: (key: string) => void;
  maxSelected: number;
}

/** Accordion per kategori + toggle-chip multi-select -- padanan
 * st.expander + st.multiselect di views/backtest.py lama, dgn badge
 * jumlah terpilih di judul (fitur yg sudah ada, dipertahankan). */
export function IndicatorPicker({
  categories,
  indicatorsByCategory,
  selected,
  onToggle,
  maxSelected,
}: IndicatorPickerProps) {
  const [openCategory, setOpenCategory] = React.useState<string | null>(categories[0] ?? null);

  return (
    <div className="flex flex-col gap-2">
      {categories.map((cat) => {
        const items = indicatorsByCategory[cat] ?? [];
        const countSelected = items.filter((i) => selected.includes(i.key)).length;
        const isOpen = openCategory === cat;
        return (
          <div key={cat} className="rounded-lg border border-border bg-surface-1">
            <button
              type="button"
              onClick={() => setOpenCategory(isOpen ? null : cat)}
              className="flex w-full items-center justify-between px-3.5 py-2.5 text-left"
            >
              <span className="flex items-center gap-2 text-[13.5px] font-medium text-text-primary">
                📂 {cat}
                {countSelected > 0 && (
                  <span className="rounded-full bg-brand/20 px-2 py-0.5 text-[11px] font-semibold text-brand-emphasis">
                    {countSelected} dipilih
                  </span>
                )}
              </span>
              <ChevronDown
                className={cn("size-4 text-text-muted transition-transform", isOpen && "rotate-180")}
              />
            </button>
            {isOpen && (
              <div className="flex flex-wrap gap-1.5 border-t border-border px-3.5 py-3">
                {items.map((item) => {
                  const active = selected.includes(item.key);
                  const disabled = !active && selected.length >= maxSelected;
                  return (
                    <button
                      key={item.key}
                      type="button"
                      disabled={disabled}
                      onClick={() => onToggle(item.key)}
                      className={cn(
                        "rounded-full border px-2.5 py-1 text-[12px] font-medium transition-colors",
                        active
                          ? "border-brand bg-brand/15 text-brand-emphasis"
                          : "border-border text-text-secondary hover:border-border-strong hover:text-text-primary",
                        disabled && "cursor-not-allowed opacity-40",
                      )}
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
