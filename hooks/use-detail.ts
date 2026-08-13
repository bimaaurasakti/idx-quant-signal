"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useTickerDetail(ticker: string | null) {
  return useQuery({
    queryKey: ["detail", ticker],
    queryFn: () => api.tickerDetail(ticker as string),
    enabled: !!ticker,
  });
}
