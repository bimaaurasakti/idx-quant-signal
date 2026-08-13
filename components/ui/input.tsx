import * as React from "react";

import { cn } from "@/lib/utils";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-9 w-full min-w-0 rounded-md border border-border bg-surface-1 px-3 py-1 font-mono text-[13.5px] text-text-primary shadow-xs transition-colors outline-none",
        "placeholder:text-text-muted",
        "focus-visible:border-brand focus-visible:ring-[3px] focus-visible:ring-brand/30",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
