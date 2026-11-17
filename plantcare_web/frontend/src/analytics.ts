import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

export type AnalyticsPeriod = 30 | 90 | 365;

export type ActivityPoint = { date: string; count: number };

export type CareMixSlice = { kind: string; count: number };

export type RoomSummary = {
  room: string;
  plants: number;
  overdue: number;
};

export type HealthCounts = {
  excellent: number;
  good: number;
  struggling: number;
  sick: number;
  unrated: number;
};

export type AttentionReason =
  | { code: "health"; health: "sick" | "struggling" }
  | { code: "watering"; days: number };

export type PlantAtRisk = {
  id: string;
  name: string;
  room: string;
  photoPath?: string | null;
  daysUntilWatering: number;
  reason: AttentionReason;
  score: number;
};

export type AnalyticsSummary = {
  days: AnalyticsPeriod;
  periodStart: string;
  generatedAt: string;
  plantCount: number;
  completedEvents: number;
  activeDays: number;
  timelinessPercent: number | null;
  dailyActivity: ActivityPoint[];
  careMix: CareMixSlice[];
  rooms: RoomSummary[];
  health: HealthCounts;
  plantsAtRisk: PlantAtRisk[];
};

type AnalyticsState = {
  data?: AnalyticsSummary;
  loading: boolean;
  error: string;
};

/**
 * Reads /api/analytics. The request is cancelled when the page unmounts or the
 * period changes, so a slow answer can never overwrite a newer one.
 */
export function useAnalytics(days: AnalyticsPeriod = 30) {
  const [state, setState] = useState<AnalyticsState>({
    loading: true,
    error: "",
  });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState((current) => ({ ...current, loading: true, error: "" }));
    api<AnalyticsSummary>(`analytics?days=${days}`, {
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted)
          setState({ data, loading: false, error: "" });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState((current) => ({
          data: current.data,
          loading: false,
          error:
            error instanceof Error && error.message
              ? error.message
              : "Analytics unavailable",
        }));
      });
    return () => controller.abort();
  }, [days, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);

  return { ...state, reload };
}
