/**
 * lib/constants.ts
 * =================
 * Single source of truth warna sinyal & exit-reason di seluruh frontend --
 * port dari theme.py::signal_colors() / direction_from_signal() dan
 * shared_ui.py::EXIT_REASON_CHART_COLORS/TOOLTIP (§5.7 implementation plan).
 * SEMUA komponen (badge, chart, meter) WAJIB mengimpor dari sini, bukan
 * menulis mapping warna sendiri-sendiri -- itulah sumber drift warna yang
 * ingin dihindari (persis semangat theme.py/shared_ui.py di versi lama).
 */

export type SignalType = string | null | undefined;
export type SignalDirection = "bullish" | "bearish" | "neutral";
export type ExitReason =
  | "TP"
  | "SL"
  | "SELL_SIGNAL"
  | "TIME_EXIT"
  | "TP1_RUNNER"
  | "TP1_BE"
  | "TP1_SIGNAL"
  | "TP1_TIME";

interface SignalColorToken {
  fg: string; // var(--bullish) dst
  bg: string; // var(--bullish-bg) dst
  label: string;
}

export function signalColors(signal: SignalType): SignalColorToken {
  const s = (signal ?? "").toUpperCase();
  if (s === "BUY") return { fg: "var(--bullish)", bg: "var(--bullish-bg)", label: "Buy" };
  if (s === "SELL") return { fg: "var(--bearish)", bg: "var(--bearish-bg)", label: "Sell" };
  if (s === "HOLD") return { fg: "var(--signal-hold)", bg: "var(--signal-hold-bg)", label: "Hold" };
  if (s === "HOLD_ACTIVE") return { fg: "var(--signal-hold)", bg: "var(--signal-hold-bg)", label: "Hold (Posisi Aktif)" };
  if (s === "WAIT" || s === "WAIT & SEE") return { fg: "var(--text-secondary)", bg: "rgba(148,163,184,0.15)", label: "Wait & See" };
  if (s === "NETRAL") return { fg: "var(--text-secondary)", bg: "rgba(148,163,184,0.15)", label: "Netral" };
  return { fg: "var(--text-muted)", bg: "rgba(148,163,184,0.12)", label: "–" };
}

export function directionFromSignal(signal: SignalType): SignalDirection {
  const s = (signal ?? "").toUpperCase();
  if (s === "BUY") return "bullish";
  if (s === "SELL") return "bearish";
  return "neutral";
}

const EXIT_REASON_LABEL: Record<ExitReason, string> = {
  TP: "Take Profit",
  SL: "Stop Loss",
  SELL_SIGNAL: "Sinyal SELL",
  TIME_EXIT: "Batas Waktu",
  TP1_RUNNER: "TP1 + Runner Trend",
  TP1_BE: "TP1 + Break-Even",
  TP1_SIGNAL: "TP1 + Sinyal SELL",
  TP1_TIME: "TP1 + Batas Waktu",
};

const EXIT_REASON_COLOR: Record<ExitReason, string> = {
  TP: "var(--bullish)",
  SL: "var(--bearish)",
  SELL_SIGNAL: "var(--info)",
  TIME_EXIT: "var(--signal-hold)",
  TP1_RUNNER: "var(--bullish)",
  TP1_BE: "var(--bullish)",
  TP1_SIGNAL: "var(--info)",
  TP1_TIME: "var(--signal-hold)",
};

export function exitReasonLabel(reason: string): string {
  return EXIT_REASON_LABEL[reason as ExitReason] ?? reason;
}

export function exitReasonColor(reason: string): string {
  return EXIT_REASON_COLOR[reason as ExitReason] ?? "var(--text-muted)";
}

/** ongoing_positions.status ("CLOSED_TP" dst) -> kode exit reason pendek
 * ("TP" dst) yang dipakai backtest_trades.reason -- disatukan di sini
 * supaya Portfolio & Detail Saham memakai warna/label exit yang sama. */
const CLOSED_STATUS_TO_REASON: Record<string, ExitReason> = {
  CLOSED_TP: "TP",
  CLOSED_SL: "SL",
  CLOSED_SIGNAL: "SELL_SIGNAL",
  CLOSED_TIME: "TIME_EXIT",
  CLOSED_RUNNER_SMA20: "TP1_RUNNER",
  CLOSED_TP1_BE: "TP1_BE",
  CLOSED_TP1_SIGNAL: "TP1_SIGNAL",
  CLOSED_TP1_TIME: "TP1_TIME",
};

export function closedStatusToReason(status: string): string {
  return CLOSED_STATUS_TO_REASON[status] ?? status;
}

export function isPositionRunner(pos: {
  status?: string | null;
  sl_price?: number | null;
  entry_price?: number | null;
}): boolean {
  return (
    pos.status === "OPEN" &&
    pos.sl_price != null &&
    pos.entry_price != null &&
    pos.sl_price >= pos.entry_price
  );
}

/** Teks tooltip metrik -- port verbatim dari shared_ui.py::TOOLTIP. */
export const METRIC_TOOLTIP = {
  winrate:
    "Persentase trade yang profit dari seluruh trade historis. Winrate tinggi TIDAK otomatis berarti profitable — selalu cek Expectancy juga.",
  expectancy:
    "Rata-rata hasil per trade (%), memperhitungkan winrate DAN besar rata-rata profit/loss: (winrate × avg profit) − (lossrate × avg loss). Metrik utama untuk menilai kualitas sebuah strategi.",
  profitFactor:
    "Total profit dibagi total loss dari seluruh trade historis. Di atas 1 berarti profit agregat lebih besar dari loss agregat.",
  maxDrawdown:
    "Penurunan terbesar dari puncak ke lembah pada equity curve hasil backtest (compounding tiap trade).",
  totalReturn:
    "Jumlah (SUM) return_pct dari SELURUH trade historis, TIDAK dikompund. Indikator kasar seberapa produktif sinyal ini secara total.",
} as const;
