/**
 * lib/derive.ts
 * ==============
 * Fungsi turunan (derived) murni -- tidak melakukan fetch apa pun, hanya
 * menghitung dari data yang sudah ada. Dipakai oleh lib/supabase/mappers.ts
 * untuk field yang TIDAK tersimpan langsung di tabel Supabase (mis.
 * hold_days & return_pct_now untuk ongoing_positions, change/change_pct
 * untuk price_history) -- lihat §6.1 & §9.3 di
 * IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md untuk penjelasan trade-off
 * tiap fungsi.
 */
import type { MarketRegimeInfo, PriceBar } from "@/lib/types";

/**
 * Aproksimasi CEPAT hari kerja (Senin-Jumat) antara dua tanggal ISO
 * ("2026-01-15"). TIDAK memperhitungkan libur nasional/bursa Indonesia --
 * cocok untuk tampilan list (Portfolio, Screener) di mana fetch
 * price_history penuh per baris terlalu mahal. Untuk presisi penuh di
 * halaman Detail (yang sudah punya price_history ter-fetch), pakai
 * `barsBetween` di bawah.
 */
export function businessDaysBetween(startDate: string, endDate: string): number {
  const start = new Date(startDate);
  const end = new Date(endDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;

  let count = 0;
  const cur = new Date(start);
  while (cur < end) {
    cur.setDate(cur.getDate() + 1);
    const day = cur.getDay();
    if (day !== 0 && day !== 6) count++;
  }
  return count;
}

/**
 * Presisi -- hitung jumlah bar price_history di antara 2 tanggal untuk 1
 * ticker. Karena price_history hanya berisi hari bursa ASLI (tidak ada
 * baris untuk weekend/libur), ini otomatis benar tanpa perlu kalender
 * libur terpisah. Pakai HANYA kalau `bars` sudah ter-fetch di context yang
 * sama (mis. halaman Detail) -- jangan fetch khusus untuk ini di list.
 */
export function barsBetween(
  bars: Pick<PriceBar, "date">[],
  startDate: string,
  endDate: string,
): number {
  const dates = bars.map((b) => b.date).sort();
  const startIdx = dates.indexOf(startDate);
  const endIdx = dates.indexOf(endDate);
  if (startIdx === -1 || endIdx === -1) return businessDaysBetween(startDate, endDate);
  return endIdx - startIdx;
}

export function computeReturnPctNow(
  entryPrice: number | null,
  lastClose: number | null,
): number | null {
  if (entryPrice == null || lastClose == null || entryPrice === 0) return null;
  return ((lastClose - entryPrice) / entryPrice) * 100;
}

export function computeChangeAndChangePct(
  bars: Pick<PriceBar, "close">[],
): { change: number | null; change_pct: number | null } {
  if (bars.length < 2) return { change: null, change_pct: null };
  const prev = bars[bars.length - 2];
  const curr = bars[bars.length - 1];
  if (prev.close == null || curr.close == null || prev.close === 0) {
    return { change: null, change_pct: null };
  }
  const change = curr.close - prev.close;
  return { change, change_pct: (change / prev.close) * 100 };
}

export function sum(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0);
}

/**
  * Parse catatan sinkronisasi update_log menjadi structured MarketRegimeInfo
  * untuk visualisasi widget Market Regime di header Screener.
  */
export function parseMarketRegime(notes: string | null | undefined): MarketRegimeInfo {
  if (!notes) {
    return {
      tier: "HIGH_ALPHA",
      macro_bull: true,
      momentum_green: true,
      sizing_pct: 100,
      max_positions: 7,
      description: "Rezim default High Alpha. Full deployment.",
    };
  }

  const isTactical = notes.includes("TIER=TACTICAL_SWING");
  const isHighAlpha = notes.includes("TIER=HIGH_ALPHA") || notes.includes("IHSG=BULL");
  const isDefensive = notes.includes("TIER=DEFENSIVE") || notes.includes("IHSG=BEAR");

  if (isTactical) {
    return {
      tier: "TACTICAL_SWING",
      macro_bull: false,
      momentum_green: true,
      sizing_pct: 50,
      max_positions: 3,
      description: "IHSG Bearish namun Momentum Hijau/Rebound. Alokasi taktis 50% lot untuk leading stocks.",
    };
  }

  if (isHighAlpha) {
    return {
      tier: "HIGH_ALPHA",
      macro_bull: true,
      momentum_green: true,
      sizing_pct: 100,
      max_positions: 7,
      description: "IHSG Bullish & Momentum Kuat. Full deployment 100% standard lot.",
    };
  }

  if (isDefensive) {
    return {
      tier: "DEFENSIVE",
      macro_bull: false,
      momentum_green: false,
      sizing_pct: 0,
      max_positions: 0,
      description: "IHSG Risk-Off / Momentum Melemah. Menahan entri baru (0% sizing) untuk mengamankan modal.",
    };
  }

  return {
    tier: "HIGH_ALPHA",
    macro_bull: true,
    momentum_green: true,
    sizing_pct: 100,
    max_positions: 7,
    description: "Rezim pasar aktif.",
  };
}
