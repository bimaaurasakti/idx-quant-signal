"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: api.portfolio,
  });
}
