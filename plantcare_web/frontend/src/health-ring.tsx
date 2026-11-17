import React from "react";
import { HEALTH_COLORS, type HealthBucket } from "./chart-kit";
import { useI18n } from "./i18n";

/**
 * Pure SVG health ring: no Recharts, no chart bundle, no animation, so it is
 * safe to render eagerly and kind to prefers-reduced-motion.
 */
export function HealthRing({
  value,
  bucket,
  label,
  caption,
  size = 132,
}: {
  value: number;
  bucket: HealthBucket;
  label: string;
  caption?: string;
  size?: number;
}) {
  const { t } = useI18n();
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const dash = (clamped / 100) * circumference;
  const color = HEALTH_COLORS[bucket];

  return (
    <svg
      className="health-ring"
      width={size}
      height={size}
      viewBox="0 0 120 120"
      role="img"
      aria-label={`${label}: ${clamped}%${caption ? ` · ${caption}` : ""}`}
    >
      <circle
        className="health-ring-track"
        cx="60"
        cy="60"
        r={radius}
        fill="none"
        stroke="#e8ede4"
        strokeWidth="9"
      />
      <circle
        cx="60"
        cy="60"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="9"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${circumference - dash}`}
        transform="rotate(-90 60 60)"
      />
      <text
        x="60"
        y="60"
        textAnchor="middle"
        dominantBaseline="central"
        className="health-ring-value"
        fill="var(--forest)"
      >
        {clamped}%
      </text>
      <text
        x="60"
        y="80"
        textAnchor="middle"
        className="health-ring-label"
        fill="#5f6d62"
      >
        {caption ?? t("charts.health.rated")}
      </text>
    </svg>
  );
}

/** Ring-text-friendly aggregate: share of rated plants that are healthy. */
export function healthyShare(counts: {
  excellent: number;
  good: number;
  struggling: number;
  sick: number;
  unrated: number;
}) {
  const rated =
    counts.excellent + counts.good + counts.struggling + counts.sick;
  const healthy = counts.excellent + counts.good;
  return {
    rated,
    healthy,
    percent: rated ? Math.round((healthy / rated) * 100) : 0,
    bucket: healthBucket(rated ? (healthy / rated) * 100 : null),
  };
}

export function healthBucket(percent: number | null): HealthBucket {
  if (percent === null) return "unrated";
  if (percent >= 80) return "excellent";
  if (percent >= 60) return "good";
  if (percent >= 35) return "struggling";
  return "sick";
}
