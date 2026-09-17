import * as React from "react";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

export interface InputProps extends Omit<React.ComponentProps<"input">, "prefix"> {
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  onClear?: () => void;
}

function Input({
  className,
  type,
  prefix,
  suffix,
  onClear,
  value,
  ...props
}: InputProps) {
  const hasValue = value != null && value !== "";

  if (prefix || suffix || onClear) {
    return (
      <div
        className={cn(
          "flex h-9 w-full items-center rounded-md border border-border bg-surface-1 px-2.5 text-[13px] text-text-primary shadow-xs transition-all duration-100",
          "focus-within:border-brand focus-within:ring-[3px] focus-within:ring-brand/25",
          "has-disabled:cursor-not-allowed has-disabled:opacity-50",
          className,
        )}
      >
        {prefix && (
          <span className="mr-2 flex shrink-0 items-center text-text-muted select-none text-[12px]">
            {prefix}
          </span>
        )}
        <input
          type={type}
          value={value}
          data-slot="input"
          className="w-full min-w-0 bg-transparent font-mono text-[13px] text-text-primary outline-none placeholder:text-text-muted disabled:cursor-not-allowed"
          {...props}
        />
        {onClear && hasValue && (
          <button
            type="button"
            onClick={onClear}
            className="ml-1.5 flex size-4 shrink-0 items-center justify-center rounded-full text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors"
            tabIndex={-1}
            aria-label="Hapus input"
          >
            <X className="size-3" />
          </button>
        )}
        {suffix && (
          <span className="ml-2 flex shrink-0 items-center text-text-muted select-none text-[12px]">
            {suffix}
          </span>
        )}
      </div>
    );
  }

  return (
    <input
      type={type}
      value={value}
      data-slot="input"
      className={cn(
        "flex h-9 w-full min-w-0 rounded-md border border-border bg-surface-1 px-3 py-1 font-mono text-[13px] text-text-primary shadow-xs transition-all duration-100 outline-none",
        "placeholder:text-text-muted",
        "focus-visible:border-brand focus-visible:ring-[3px] focus-visible:ring-brand/25",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
