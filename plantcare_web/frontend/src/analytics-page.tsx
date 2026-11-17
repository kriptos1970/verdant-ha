import React, { Suspense, useState } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import {
  ChartDataTable,
  ChartPanel,
  ChartSkeleton,
  DeferredSection,
  HEALTH_COLORS,
  type HealthBucket,
} from "./chart-kit";
import {
  HEALTH_LABEL_KEYS,
  HealthRing,
  healthyShare,
} from "./health-ring";
import { useAnalytics } from "./analytics";
import type { AnalyticsPeriod } from "./analytics";
import { useI18n } from "./i18n";

const AnalyticsCharts = React.lazy(() => import("./charts"));

const HEALTH_ORDER: HealthBucket[] = [
  "excellent",
  "good",
  "struggling",
  "sick",
  "unrated",
];

function ChartsFallback() {
  return (
    <div className="analytics-charts" aria-busy="true">
      <div className="panel chart-panel">
        <ChartSkeleton />
      </div>
      <div className="panel chart-panel">
        <ChartSkeleton />
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { t, plural, formatDate, formatNumber } = useI18n();
  const [period, setPeriod] = useState<AnalyticsPeriod>(30);
  const { data, loading, error, reload } = useAnalytics(period);

  const share = data ? healthyShare(data.health) : null;
  const shownPeriod: AnalyticsPeriod = data?.days ?? period;

  return (
    <div className="analytics-page" aria-busy={loading || undefined}>
      <div className="page-heading">
        <div>
          <div className="eyebrow">{t("analytics.eyebrow")}</div>
          <h1>{t("analytics.title")}</h1>
          <p>{t("analytics.subtitle")}</p>
        </div>
      </div>
      <div className="analytics-meta">
        <div
          className="analytics-periods"
          role="group"
          aria-label={t("analytics.period")}
        >
          {([30, 90, 365] as const).map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={period === value}
              onClick={() => setPeriod(value)}
            >
              {t(
                value === 30
                  ? "analytics.period.30"
                  : value === 90
                    ? "analytics.period.90"
                    : "analytics.period.365",
              )}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="alert error analytics-error" role="alert">
          <AlertCircle size={18} />
          <span>{t("analytics.error")}</span>
          <button className="button secondary compact" onClick={reload}>
            <RefreshCw size={15} />
            {t("common.retry")}
          </button>
        </div>
      ) : null}

      {!data && loading ? (
        <div className="analytics-loading">
          <div className="analytics-charts" aria-busy="true">
            <div className="panel chart-panel">
              <ChartSkeleton />
            </div>
            <div className="panel chart-panel">
              <ChartSkeleton />
            </div>
          </div>
        </div>
      ) : null}

      {data ? (
        <>
          <div className="stats analytics-stats">
            <div>
              <span>{t("analytics.stats.plants")}</span>
              <strong>{formatNumber(data.plantCount)}</strong>
            </div>
            <div>
              <span>{t("analytics.stats.care")}</span>
              <strong>{formatNumber(data.completedEvents)}</strong>
            </div>
            <div>
              <span>{t("analytics.stats.activeDays")}</span>
              <strong>{formatNumber(data.activeDays)}</strong>
            </div>
            <div>
              <span>{t("analytics.stats.timeliness")}</span>
              <strong>
                {data.timelinessPercent === null
                  ? "—"
                  : `${formatNumber(data.timelinessPercent)}%`}
              </strong>
            </div>
          </div>

          {data.plantCount === 0 ? (
            <ChartPanel
              title={t("charts.emptyTitle")}
              empty
              emptyText={t("analytics.emptyText")}
            >
              {null}
            </ChartPanel>
          ) : (
            <>
              <section className="panel chart-panel health-panel">
                <header className="chart-head">
                  <div>
                    <h2>{t("charts.health.title")}</h2>
                    <p>{t("charts.health.description")}</p>
                  </div>
                </header>
                {share ? (
                  <div className="health-summary">
                    <HealthRing
                      value={share.percent}
                      bucket={share.bucket}
                      label={t("charts.health.healthyShare")}
                      caption={
                        share.rated
                          ? plural("charts.health.ratedCount", share.rated)
                          : t("charts.health.none")
                      }
                    />
                    <ul className="health-legend">
                      {HEALTH_ORDER.map((bucket) => (
                        <li key={bucket}>
                          <span
                            className="chart-swatch"
                            style={{ background: HEALTH_COLORS[bucket] }}
                            aria-hidden="true"
                          />
                          <span>{t(HEALTH_LABEL_KEYS[bucket])}</span>
                          <b>{formatNumber(data.health[bucket])}</b>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                <ChartDataTable
                  caption={t("charts.table.health")}
                  columns={[
                    { key: "state", label: t("charts.column.state") },
                    {
                      key: "value",
                      label: t("charts.column.plants"),
                      numeric: true,
                    },
                  ]}
                  rows={HEALTH_ORDER.map((bucket) => ({
                    id: bucket,
                    state: t(HEALTH_LABEL_KEYS[bucket]),
                    value: data.health[bucket],
                  }))}
                />
                <p className="analytics-note">
                  {t("analytics.updated", {
                    date: formatDate(data.generatedAt, {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    }),
                  })}
                </p>
              </section>

              <DeferredSection fallback={<ChartsFallback />}>
                <Suspense fallback={<ChartsFallback />}>
                  <AnalyticsCharts
                    activity={data.dailyActivity}
                    careMix={data.careMix}
                    rooms={data.rooms}
                    period={shownPeriod}
                  />
                </Suspense>
              </DeferredSection>
            </>
          )}
        </>
      ) : null}
    </div>
  );
}
