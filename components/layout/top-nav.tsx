"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  FlaskConical,
  LineChart,
  Briefcase,
  ShieldAlert,
  BookOpen,
  Settings2,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useLastUpdate } from "@/hooks/use-meta";

const NAV_ITEMS = [
  { href: "/screener", label: "Screener", icon: Compass },
  { href: "/backtest", label: "Backtest Lab", icon: FlaskConical },
  { href: "/detail", label: "Detail", icon: LineChart },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/risk", label: "Risk", icon: ShieldAlert },
  { href: "/about", label: "Metodologi", icon: BookOpen },
];

export function TopNav() {
  const pathname = usePathname();
  const { data } = useLastUpdate();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface-0/90 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-6 lg:gap-8">
          {/* Signature element #2 (§5.3): wordmark + kursor terminal berkedip */}
          <Link
            href="/screener"
            className="flex items-center gap-0.5 font-mono text-[15px] font-semibold tracking-tight text-text-primary"
          >
            <span>IDX QUANT</span>
            <span
              className="ml-0.5 inline-block h-[15px] w-[7px] animate-cursor-blink bg-brand"
              aria-hidden="true"
            />
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {NAV_ITEMS.map((item) => {
              const active = pathname?.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[12.5px] font-medium transition-all duration-150",
                    active
                      ? "bg-surface-2 text-text-primary shadow-xs"
                      : "text-text-secondary hover:bg-surface-1 hover:text-text-primary",
                  )}
                >
                  <Icon className={cn("size-3.5", active ? "text-brand" : "text-text-secondary")} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-border bg-surface-1 px-2.5 py-1 text-[11.5px] text-text-secondary sm:flex">
            <span className="relative flex size-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
            </span>
            <span aria-live="polite" className="font-mono text-[11px]">
              {data?.run_at
                ? `Sync ${new Date(data.run_at).toLocaleTimeString("id-ID", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })} WIB`
                : "Syncing..."}
            </span>
          </div>
          <button
            type="button"
            className="rounded-md p-2 text-text-secondary transition-colors hover:bg-surface-1 hover:text-text-primary"
            aria-label="Pengaturan"
          >
            <Settings2 className="size-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
