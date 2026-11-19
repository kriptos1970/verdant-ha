import React from "react";
import { ArrowUpRight, RefreshCw } from "lucide-react";
import {
  ChartDataTable,
  ChartSkeleton,
  DeferredSection,
} from "./chart-kit";
import { useAnalytics } from "./analytics";
import { useI18n } from "./i18n";
import { IOSIcon } from "./ios-icons";

type HomeInsightsProps = {
  onOpenAnalytics: () => void;
};

function HomeInsightsSkeleton() {
  return (
    <div className="home-insights" aria-busy="true">
      <div className="panel home-insight">
        <ChartSkeleton />
      </div>
    </div>
  );
}

function HomeInsightsContent({
  onOpenAnalytics,
}: HomeInsightsProps) {
  const { t, plural, formatDate, formatNumber } = useI18n();
  const { data, loading, error, reload } = useAnalytics(30);

  if (!data) {
    if (loading) return <HomeInsightsSkeleton />;
    return (
      <div className="home-insights">
        <div className="panel home-insight home-insight-error">
          <span>{t("home.insights.error")}</span>
          <button className="text-button" onClick={reload}>
            <RefreshCw size={15} />
            {t("common.retry")}
          </button>
        </div>
      </div>
    );
  }

  if (data.plantCount === 0) return null;

  const activity = data.dailyActivity.slice(-14);
  const totalCare = activity.reduce((sum, day) => sum + day.count, 0);
  const activeDays = activity.filter((day) => day.count > 0).length;
  const peak = Math.max(1, ...activity.map((day) => day.count));

  return (
    <div className="home-insights">
      <div className="section-heading home-insights-heading">
        <div>
          <h2>{t("home.insights.title")}</h2>
          <p>{t("home.insights.subtitle")}</p>
        </div>
        <button className="text-button" onClick={onOpenAnalytics}>
          {t("home.insights.openAnalytics")} <ArrowUpRight size={16} />
        </button>
      </div>

      <div className="home-metrics">
        <div className="home-metric">
          <span className="home-metric-icon metric-care">
            <IOSIcon name="checkCircle" size={24} />
          </span>
          <strong>{formatNumber(data.completedEvents)}</strong>
          <small>{t("home.metrics.care")}</small>
        </div>
        <div className="home-metric">
          <span className="home-metric-icon metric-days">
            <IOSIcon name="calendar" size={24} />
            <span className="metric-check" aria-hidden="true">✓</span>
          </span>
          <strong>{formatNumber(data.activeDays)}</strong>
          <small>{t("home.metrics.activeDays")}</small>
        </div>
        <div className="home-metric">
          <span className="home-metric-icon metric-regularity">
            <IOSIcon name="clock" size={24} />
            <span className="metric-check" aria-hidden="true">✓</span>
          </span>
          <strong>
            {data.timelinessPercent === null
              ? "—"
              : `${formatNumber(data.timelinessPercent)}%`}
          </strong>
          <small>{t("home.metrics.timeliness")}</small>
        </div>
        <div className="home-metric">
          <span className="home-metric-icon metric-watch">
            <IOSIcon name="warning" size={24} />
          </span>
          <strong>{formatNumber(data.plantsAtRisk.length)}</strong>
          <small>{t("home.metrics.watch")}</small>
        </div>
      </div>

      <section className="panel home-insight home-activity">
        <header className="home-insight-head">
          <h3>{t("home.insights.activity")}</h3>
        </header>
        <div
          className="home-spark"
          role="img"
          aria-label={t("home.insights.activityAria", {
            count: totalCare,
            days: activeDays,
          })}
        >
          {activity.map((day) => (
            <span
              key={day.date}
              className={day.count ? "" : "zero"}
              style={{
                height: day.count
                  ? `${Math.max(8, (day.count / peak) * 100)}%`
                  : "3px",
              }}
              aria-hidden="true"
            />
          ))}
        </div>
        <div className="home-insight-meta">
          <strong>{totalCare}</strong>
          <span>{plural("home.insights.careCount", totalCare)}</span>
          <span aria-hidden="true">·</span>
          <span>{plural("home.insights.activeDays", activeDays)}</span>
        </div>
        <ChartDataTable
          caption={t("charts.table.activity")}
          columns={[
            { key: "day", label: t("charts.column.date") },
            { key: "count", label: t("charts.column.count"), numeric: true },
          ]}
          rows={activity.map((day) => ({
            id: day.date,
            day: formatDate(day.date, { day: "numeric", month: "short" }),
            count: day.count,
          }))}
        />
      </section>
    </div>
  );
}

/**
 * Home summary of the collection health and of the last two weeks of care.
 * It uses the shared SVG/CSS pieces only: the Recharts chunk never loads on
 * the initial page. The analytics request starts only when the block nears
 * the viewport.
 */
export function HomeInsights(props: HomeInsightsProps) {
  return (
    <DeferredSection
      className="home-insights-deferred"
      rootMargin="320px 0px"
      fallback={<HomeInsightsSkeleton />}
    >
      <HomeInsightsContent {...props} />
    </DeferredSection>
  );
}
