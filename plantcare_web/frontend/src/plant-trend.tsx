import React from "react";
import {
  CARE_COLORS,
  CHART_COLORS,
  ChartDataTable,
  ChartEmpty,
  ChartLegend,
} from "./chart-kit";
import { useI18n } from "./i18n";
import { dateFormatter } from "./intl-cache";
import type { CareEvent } from "./types";

const WATER_KIND = "Annaffia";
const MONTHS = 12;

type MonthKey = { key: string; short: string; long: string; water: number; other: number };

function zoneMonth(date: Date, zone: string) {
  const parts = dateFormatter("en-CA", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
  }).formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value ?? "";
  const month = parts.find((part) => part.type === "month")?.value ?? "";
  return `${year}-${month}`;
}

function monthKeys(zone: string, now: Date) {
  const parts = dateFormatter("en-CA", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
  }).formatToParts(now);
  let year = Number(parts.find((part) => part.type === "year")?.value ?? 0);
  let month = Number(parts.find((part) => part.type === "month")?.value ?? 1);
  const keys: string[] = [];
  for (let index = 0; index < MONTHS; index += 1) {
    keys.unshift(`${year}-${String(month).padStart(2, "0")}`);
    month -= 1;
    if (month < 1) {
      month += 12;
      year -= 1;
    }
  }
  return keys;
}

function monthLabel(key: string, locale: string, zone: string) {
  const [year, month] = key.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, 1));
  const short = dateFormatter(locale, {
    timeZone: zone,
    month: "short",
  }).format(date);
  const long = dateFormatter(locale, {
    timeZone: zone,
    month: "long",
    year: "numeric",
  }).format(date);
  return { short: short.replace(/\.$/, ""), long };
}

/**
 * Twelve months of recorded care for one plant: watering against the other
 * care kinds, built from the history already present in the plant payload.
 * Pure CSS bars, so it stays in the main bundle and never loads a chart chunk.
 */
export function PlantTrend({
  history,
  zone = "Europe/Rome",
}: {
  history: CareEvent[];
  zone?: string;
}) {
  const { t, locale, plural } = useI18n();
  const now = new Date();
  const keys = monthKeys(zone, now);
  const counts = new Map<string, { water: number; other: number }>(
    keys.map((key) => [key, { water: 0, other: 0 }]),
  );

  for (const event of history) {
    if (event.deletedAt || event.status === "postponed") continue;
    const bucket = counts.get(zoneMonth(new Date(event.date), zone));
    if (!bucket) continue;
    if (event.kind === WATER_KIND) bucket.water += 1;
    else bucket.other += 1;
  }

  const months: MonthKey[] = keys.map((key) => ({
    key,
    ...monthLabel(key, locale, zone),
    ...counts.get(key)!,
  }));
  const total = months.reduce(
    (sum, month) => sum + month.water + month.other,
    0,
  );
  const activeMonths = months.filter((month) => month.water + month.other > 0).length;
  const peak = Math.max(1, ...months.map((month) => month.water + month.other));
  const waterColor = CARE_COLORS[WATER_KIND] ?? CHART_COLORS.sky;
  const otherColor = CHART_COLORS.sage;

  return (
    <div className="detail-section plant-trend">
      <h3>{t("detail.trendTitle")}</h3>
      {total === 0 ? (
        <ChartEmpty text={t("detail.trendEmpty")} />
      ) : (
        <>
          <div
            className="trend-chart"
            role="img"
            aria-label={t("detail.trendAria", { count: total, months: activeMonths })}
          >
            {months.map((month) => {
              const monthTotal = month.water + month.other;
              const waterHeight = month.water
                ? `${Math.max(7, (month.water / peak) * 100)}%`
                : "0";
              const otherHeight = month.other
                ? `${Math.max(7, (month.other / peak) * 100)}%`
                : "0";
              return (
                <div className="trend-col" key={month.key}>
                  <div
                    className="trend-bar"
                    title={`${month.long}: ${monthTotal}`}
                  >
                    {month.water > 0 ? (
                      <span
                        className="trend-water"
                        style={{ height: waterHeight }}
                        aria-hidden="true"
                      />
                    ) : null}
                    {month.other > 0 ? (
                      <span
                        className="trend-other"
                        style={{ height: otherHeight }}
                        aria-hidden="true"
                      />
                    ) : null}
                  </div>
                  <small aria-hidden="true">{month.short}</small>
                </div>
              );
            })}
          </div>
          <ChartLegend
            items={[
              { label: t("detail.trendWater"), color: waterColor, value: months.reduce((sum, month) => sum + month.water, 0) },
              { label: t("detail.trendOther"), color: otherColor, value: months.reduce((sum, month) => sum + month.other, 0) },
            ]}
          />
          <p className="trend-meta">
            <strong>{total}</strong> {plural("detail.trendCareCount", total)}
            <span aria-hidden="true"> · </span>
            {plural("detail.trendActiveMonths", activeMonths)}
          </p>
          <ChartDataTable
            caption={t("detail.trendTable")}
            columns={[
              { key: "month", label: t("detail.trendColumnMonth") },
              { key: "water", label: t("detail.trendColumnWater"), numeric: true },
              { key: "other", label: t("detail.trendColumnOther"), numeric: true },
              { key: "total", label: t("detail.trendColumnTotal"), numeric: true },
            ]}
            rows={months.map((month) => ({
              id: month.key,
              month: month.long,
              water: month.water,
              other: month.other,
              total: month.water + month.other,
            }))}
          />
        </>
      )}
    </div>
  );
}
