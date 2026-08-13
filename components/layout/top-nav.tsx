"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Settings2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { useLastUpdate } from "@/hooks/use-meta";

const NAV_ITEMS = [
  { href: "/screener", label: "Screener" },
  { href: "/backtest", label: "Backtest Lab" },
  { href: "/detail", label: "Detail" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/risk", label: "Risk" },
  { href: "/about", label: "Tentang" },
];

export function TopNav() {
  const pathname = usePathname();
  const { data } = useLastUpdate();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface-0/90 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-8">
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
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors",
                    active
                      ? "bg-surface-2 text-text-primary"
                      : "text-text-secondary hover:bg-surface-1 hover:text-text-primary",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-1.5 text-[12px] text-text-secondary sm:flex">
            <span
              className="size-1.5 rounded-full bg-bullish"
              style={{ backgroundColor: "var(--bullish)" }}
              aria-hidden="true"
            />
            <span aria-live="polite">
              {data?.run_at
                ? `Update ${new Date(data.run_at).toLocaleTimeString("id-ID", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })} WIB`
                : "Memuat status..."}
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
