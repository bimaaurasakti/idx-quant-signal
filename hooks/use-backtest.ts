"use client";

import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { BacktestRunRequest } from "@/lib/types";

export function useRunBacktest() {
  return useMutation({
    mutationFn: (body: BacktestRunRequest) => api.runBacktest(body),
  });
}
