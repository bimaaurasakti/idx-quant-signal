"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useScreener() {
  return useQuery({
    queryKey: ["screener"],
    queryFn: api.screener,
  });
}
