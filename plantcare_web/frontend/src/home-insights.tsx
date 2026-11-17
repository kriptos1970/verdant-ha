import React from "react";
import {
  ArrowUpRight,
  ChevronRight,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import {
  ChartDataTable,
  ChartSkeleton,
  DeferredSection,
  HEALTH_COLORS,
} from "./chart-kit";
import {
  HEALTH_LABEL_KEYS,
  HealthRing,
  healthyShare,
} from "./health-ring";
import { useAnalytics, type PlantAtRisk } from "./analytics";
import { useI18n } from "./i18n";

type HomeInsightsProps = {
  onOpenAnalytics: () => void;
  onOpenPlant: (id: string) => void;
};

function HomeInsightsSkeleton() {
  return (
    <div className="home-insights" aria-busy="true">
      <div className="home-insight-grid">
        <div className="panel home-insight">
          <ChartSkeleton />
        </div>
        <div className="panel home-insight">
          <ChartSkeleton />
        </div>
      </div>
    </div>
  );
}

function healthRisks(plants: PlantAtRisk[]) {
  return plants
    .filter((plant) => plant.reason.code === "health")
    .slice(0, 3);
}

function HomeInsightsContent({
  onOpenAnalytics,
  onOpenPlant,
}: HomeInsightsProps) {
  const { t, plural, formatDate } = useI18n();
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

  const share = healthyShare(data.health);
  const healthy = data.health.excellent + data.health.good;
  const watch = data.health.struggling + data.health.sick;
  const activity = data.dailyActivity.slice(-14);
  const totalCare = activity.reduce((sum, day) => sum + day.count, 0);
  const activeDays = activity.filter((day) => day.count > 0).length;
  const peak = Math.max(1, ...activity.map((day) => day.count));
  const risks = healthRisks(data.plantsAtRisk);

  return (
    <div className="home-insights">
      <div className="section-heading home-insights-heading">
        <h2>{t("home.insights.title")}</h2>
        <button className="text-button" onClick={onOpenAnalytics}>
          {t("home.insights.openAnalytics")} <ArrowUpRight size={16} />
        </button>
      </div>

      <div className="home-insight-grid">
        <section className="panel home-insight">
          <header className="home-insight-head">
            <span className="home-insight-icon" aria-hidden="true">
              <ShieldCheck size={17} />
            </span>
            <h3>{t("home.insights.health")}</h3>
          </header>
          {share.rated ? (
            <div className="home-insight-health">
              <HealthRing
                value={share.percent}
                bucket={share.bucket}
                size={104}
                label={t("home.insights.healthAria", {
                  percent: share.percent,
                })}
                caption={plural("charts.health.ratedCount", share.rated)}
              />
              <ul className="health-legend">
                <li>
                  <span
                    className="chart-swatch"
                    style={{ background: HEALTH_COLORS.good }}
                    aria-hidden="true"
                  />
                  <span>{t("home.insights.healthy")}</span>
                  <b>{healthy}</b>
                </li>
                <li>
                  <span
                    className="chart-swatch"
                    style={{ background: HEALTH_COLORS.struggling }}
                    aria-hidden="true"
                  />
                  <span>{t("home.insights.watch")}</span>
                  <b>{watch}</b>
                </li>
                <li>
                  <span
                    className="chart-swatch"
                    style={{ background: HEALTH_COLORS.unrated }}
                    aria-hidden="true"
                  />
                  <span>{t("home.insights.unrated")}</span>
                  <b>{data.health.unrated}</b>
                </li>
              </ul>
            </div>
          ) : (
            <div className="home-insight-empty">
              <ShieldCheck size={22} aria-hidden="true" />
              <p>{t("home.insights.healthEmpty")}</p>
            </div>
          )}
        </section>

        <section className="panel home-insight">
          <header className="home-insight-head">
            <span className="home-insight-icon" aria-hidden="true">
              <TrendingUp size={17} />
            </span>
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

      {risks.length > 0 ? (
        <section className="panel home-risk">
          <div className="section-heading">
            <h2>
              {t("home.insights.risk")} <span>{risks.length}</span>
            </h2>
          </div>
          {risks.map((plant) => {
            const reason =
              plant.reason.code === "health" ? plant.reason.health : null;
            return (
              <button
                key={plant.id}
                className="home-risk-row"
                onClick={() => onOpenPlant(plant.id)}
                aria-label={t("home.insights.riskAria", {
                  name: plant.name,
                })}
              >
                <span
                  className="home-risk-dot"
                  style={{
                    background: HEALTH_COLORS[reason ?? "unrated"],
                  }}
                  aria-hidden="true"
                />
                <span className="home-risk-name">
                  <strong>{plant.name}</strong>
                  <small>
                    {plant.room || t("charts.roomUnassigned")}
                  </small>
                </span>
                <span className="home-risk-state">
                  {reason
                    ? t(HEALTH_LABEL_KEYS[reason])
                    : t("health.state.unrated")}
                </span>
                <ChevronRight size={16} aria-hidden="true" />
              </button>
            );
          })}
        </section>
      ) : null}
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
