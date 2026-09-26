"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { parseMarketRegime } from "@/lib/derive";

export function useLastUpdate() {
  return useQuery({
    queryKey: ["meta", "last-update"],
    queryFn: api.metaLastUpdate,
  });
}

export function useMarketRegime() {
  const query = useLastUpdate();
  const regime = parseMarketRegime(query.data?.notes);
  return {
    ...query,
    regime,
  };
}

export function useIndicatorsMeta() {
  return useQuery({
    queryKey: ["meta", "indicators"],
    queryFn: api.metaIndicators,
  });
}

export function useTickersMeta() {
  return useQuery({
    queryKey: ["meta", "tickers"],
    queryFn: api.metaTickers,
  });
}
