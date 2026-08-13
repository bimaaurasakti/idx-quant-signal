import { cn } from "@/lib/utils";
import { signalColors, type SignalType } from "@/lib/constants";

interface SignalBadgeProps {
  signal: SignalType;
  className?: string;
}

export function SignalBadge({ signal, className }: SignalBadgeProps) {
  const { fg, bg, label } = signalColors(signal);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold",
        className,
      )}
      style={{ backgroundColor: bg, color: fg }}
    >
      <span className="size-1.5 rounded-full" style={{ backgroundColor: fg }} aria-hidden="true" />
      {label}
    </span>
  );
}
