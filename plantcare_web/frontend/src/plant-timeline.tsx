import React, { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "./api";
import {
  CHART_COLORS,
  ChartEmpty,
  ChartSkeleton,
  careColor,
  type HealthBucket,
} from "./chart-kit";
import { HEALTH_LABEL_KEYS } from "./health-ring";
import { useCareLabels } from "./care-labels";
import { useI18n, type MessageKey } from "./i18n";

type TimelineItem = {
  id: string;
  type: "event" | "measurement";
  date: string;
  kind: string;
  status?: string;
  note?: string;
  health?: string | null;
  value?: number;
  unit?: string;
};

const MEASURE_KEYS: Record<string, MessageKey> = {
  moisture: "detail.timeline.moisture",
  humidity: "detail.timeline.humidity",
  temperature: "detail.timeline.temperature",
  illuminance: "detail.timeline.illuminance",
  conductivity: "detail.timeline.conductivity",
};

function isHealth(value?: string | null): value is HealthBucket {
  return !!value && value in HEALTH_LABEL_KEYS;
}

function TimelineContent({ plantId }: { plantId: string }) {
  const { t, formatDate, formatNumber } = useI18n();
  const { kindLabel } = useCareLabels();
  const [items, setItems] = useState<TimelineItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api<{ items: TimelineItem[] }>(`plants/${plantId}/timeline?limit=12`, {
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) {
          setItems(data.items ?? []);
          setLoading(false);
        }
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        setItems([]);
        setLoading(false);
        setError(
          reason instanceof Error && reason.message
            ? reason.message
            : t("detail.timelineError"),
        );
      });
    return () => controller.abort();
  }, [plantId, attempt, t]);

  return (
    <div className="detail-section plant-timeline-section">
      <h3>{t("detail.timelineTitle")}</h3>
      {loading ? (
        <ChartSkeleton />
      ) : error ? (
        <div className="timeline-error">
          <span>{t("detail.timelineError")}</span>
          <button
            type="button"
            className="text-button"
            onClick={() => setAttempt((value) => value + 1)}
          >
            <RefreshCw size={15} /> {t("common.retry")}
          </button>
        </div>
      ) : items.length === 0 ? (
        <ChartEmpty text={t("detail.timelineEmpty")} />
      ) : (
        <ol className="plant-timeline">
          {items.map((item) => {
            const date = formatDate(item.date, {
              day: "numeric",
              month: "short",
            });
            const measurement = item.type === "measurement";
            const health = isHealth(item.health) ? item.health : null;
            return (
              <li key={`${item.type}-${item.id}`}>
                <span
                  className="plant-timeline-dot"
                  style={{
                    background: measurement
                      ? CHART_COLORS.sage
                      : careColor(item.kind),
                  }}
                  aria-hidden="true"
                />
                <time dateTime={item.date}>{date}</time>
                <strong>
                  {measurement
                    ? t(MEASURE_KEYS[item.kind] ?? "detail.timeline.measure")
                    : kindLabel(item.kind)}
                  {item.status === "postponed"
                    ? ` · ${t("calendar.postponed")}`
                    : ""}
                  {health ? ` · ${t(HEALTH_LABEL_KEYS[health])}` : ""}
                </strong>
                {measurement ? (
                  <p className="plant-timeline-value">
                    {formatNumber(item.value ?? 0)} {item.unit}
                  </p>
                ) : item.note ? (
                  <p>{item.note}</p>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

/**
 * Care events and measurements merged newest first, from the timeline
 * endpoint. It mounts with the plant diary tab, so the request is small and
 * no chart runtime is loaded.
 */
export function PlantTimeline({ plantId }: { plantId: string }) {
  return <TimelineContent plantId={plantId} />;
}
