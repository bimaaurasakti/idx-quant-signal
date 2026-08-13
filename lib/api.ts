/**
 * lib/api.ts
 * ===========
 * SATU-SATUNYA titik komunikasi frontend ke luar untuk data aplikasi.
 * Frontend TIDAK PERNAH mengimpor @supabase/* atau menyimpan kredensial
 * Supabase apa pun -- hanya kenal NEXT_PUBLIC_API_BASE_URL (lihat §0 &
 * §5.5 implementation plan). Ini bagian paling penting untuk audit
 * keamanan: cek file ini + grep seluruh repo untuk "supabase" harus
 * NOL hasil di luar sini.
 */
import type {
  BacktestRunRequest,
  BacktestRunResponse,
  IndicatorsMetaResponse,
  LastUpdateResponse,
  PortfolioResponse,
  ScreenerResponse,
  TickerDetailResponse,
  TickersMetaResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // respons bukan JSON, pakai statusText apa adanya
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  screener: () => request<ScreenerResponse>("/api/screener"),
  tickerDetail: (ticker: string) => request<TickerDetailResponse>(`/api/tickers/${ticker}`),
  portfolio: () => request<PortfolioResponse>("/api/portfolio"),
  metaIndicators: () => request<IndicatorsMetaResponse>("/api/meta/indicators"),
  metaTickers: () => request<TickersMetaResponse>("/api/meta/tickers"),
  metaLastUpdate: () => request<LastUpdateResponse>("/api/meta/last-update"),
  runBacktest: (body: BacktestRunRequest) =>
    request<BacktestRunResponse>("/api/backtest/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
