"use client";

import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { Check, ChevronDown, Search } from "lucide-react";

import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: string;
  sublabel?: string;
}

export interface SelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  searchable?: boolean;
  searchPlaceholder?: string;
  className?: string;
  triggerClassName?: string;
  disabled?: boolean;
}

export function Select({
  value,
  onValueChange,
  options,
  placeholder = "Pilih opsi...",
  searchable = false,
  searchPlaceholder = "Cari...",
  className,
  triggerClassName,
  disabled = false,
}: SelectProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");

  const selectedOption = React.useMemo(
    () => options.find((opt) => opt.value === value),
    [options, value],
  );

  const filteredOptions = React.useMemo(() => {
    if (!search.trim()) return options;
    const q = search.toLowerCase();
    return options.filter(
      (opt) =>
        opt.label.toLowerCase().includes(q) ||
        opt.value.toLowerCase().includes(q) ||
        (opt.sublabel && opt.sublabel.toLowerCase().includes(q)),
    );
  }, [options, search]);

  const handleSelect = (val: string) => {
    onValueChange(val);
    setOpen(false);
    setSearch("");
  };

  return (
    <PopoverPrimitive.Root open={open} onOpenChange={setOpen}>
      <PopoverPrimitive.Trigger
        disabled={disabled}
        className={cn(
          "inline-flex h-8 items-center justify-between gap-2 rounded-md border border-border bg-surface-1 px-2.5 py-1 text-[12.5px] font-medium text-text-primary transition-all duration-100 outline-none",
          "hover:border-border-strong hover:bg-surface-2/60",
          "focus-visible:border-brand focus-visible:ring-[3px] focus-visible:ring-brand/25",
          "disabled:cursor-not-allowed disabled:opacity-50",
          triggerClassName,
          className,
        )}
      >
        <span className="truncate">
          {selectedOption ? selectedOption.label : <span className="text-text-muted">{placeholder}</span>}
        </span>
        <ChevronDown className={cn("size-3.5 shrink-0 text-text-muted transition-transform duration-120", open && "rotate-180 text-brand")} />
      </PopoverPrimitive.Trigger>

      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Content
          align="start"
          sideOffset={4}
          className="z-50 min-w-[180px] max-w-[280px] overflow-hidden rounded-md border border-border bg-surface-1 p-1 text-text-primary shadow-lg outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-1 duration-100"
        >
          {searchable && (
            <div className="flex items-center gap-1.5 border-b border-border px-2 pb-1.5 pt-1">
              <Search className="size-3.5 text-text-muted shrink-0" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-transparent text-[11.5px] text-text-primary placeholder:text-text-muted outline-none"
                autoFocus
              />
            </div>
          )}

          <div className="max-h-[220px] overflow-y-auto py-1">
            {filteredOptions.length === 0 ? (
              <div className="px-2 py-3 text-center text-[11.5px] text-text-muted">
                Tidak ada hasil ditemukan
              </div>
            ) : (
              filteredOptions.map((opt) => {
                const isSelected = opt.value === value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleSelect(opt.value)}
                    className={cn(
                      "flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-[12px] transition-colors duration-80 outline-none cursor-pointer",
                      isSelected
                        ? "bg-brand/15 text-brand font-medium"
                        : "hover:bg-surface-2 text-text-primary",
                    )}
                  >
                    <div className="flex flex-col truncate pr-2">
                      <span className="truncate">{opt.label}</span>
                      {opt.sublabel && (
                        <span className="text-[10px] text-text-muted">{opt.sublabel}</span>
                      )}
                    </div>
                    {isSelected && <Check className="size-3.5 shrink-0 text-brand" />}
                  </button>
                );
              })
            )}
          </div>
        </PopoverPrimitive.Content>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  );
}
