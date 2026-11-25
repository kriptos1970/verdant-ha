import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CHART_COLORS,
  ChartLegend,
  ChartPanel,
  careColor,
  useReducedMotion,
} from "./chart-kit";
import { useI18n } from "./i18n";
import { useCareLabels } from "./care-labels";
import type {
  ActivityPoint,
  AnalyticsPeriod,
  CareMixSlice,
  RoomSummary,
} from "./analytics";

type TooltipEntry = {
  value?: number | string;
  name?: string;
  dataKey?: string | number;
  payload?: Record<string, unknown>;
};

function ChartTooltip({
  active,
  payload,
  label,
  mode,
  unit,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string | number;
  mode: "activity" | "donut" | "rooms";
  unit: (value: number) => string;
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload ?? {};
  const heading =
    mode === "activity"
      ? String(point.full ?? label ?? "")
      : String(point.label ?? label ?? "");
  return (
    <div className="chart-tooltip">
      <strong>{heading}</strong>
      {payload.map((entry, index) => (
        <span key={`${String(entry.dataKey ?? entry.name ?? index)}`}>
          {mode === "rooms" && entry.name ? `${entry.name}: ` : ""}
          {mode === "activity" || mode === "donut"
            ? unit(Number(entry.value ?? 0))
            : Number(entry.value ?? 0)}
        </span>
      ))}
    </div>
  );
}

type BucketMode = "day" | "week" | "month";

function parseDay(date: string) {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function isoDay(date: Date) {
  return date.toISOString().slice(0, 10);
}

function bucketFor(period: AnalyticsPeriod): BucketMode {
  return period === 30 ? "day" : period === 90 ? "week" : "month";
}

/** Folds the daily series so a 90- or 365-day window stays readable. */
export function bucketize(activity: ActivityPoint[], mode: BucketMode) {
  if (mode === "day") return activity;
  const totals = new Map<string, number>();
  for (const point of activity) {
    let key = point.date;
    if (mode === "week") {
      const date = parseDay(point.date);
      const offset = (date.getUTCDay() + 6) % 7;
      date.setUTCDate(date.getUTCDate() - offset);
      key = isoDay(date);
    } else {
      key = point.date.slice(0, 7);
    }
    totals.set(key, (totals.get(key) ?? 0) + point.count);
  }
  return [...totals.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, count]) => ({ date, count }));
}

function ActivityBars({
  activity,
  period,
}: {
  activity: ActivityPoint[];
  period: AnalyticsPeriod;
}) {
  const { formatDate, t, plural } = useI18n();
  const reduced = useReducedMotion();
  const mode = bucketFor(period);
  const series = bucketize(activity, mode);
  const data = series.map((point) => {
    if (mode === "week") {
      return {
        label: formatDate(point.date, { day: "numeric", month: "short" }),
        full: t("charts.weekOf", {
          date: formatDate(point.date, { day: "numeric", month: "long" }),
        }),
        count: point.count,
      };
    }
    if (mode === "month") {
      const first = `${point.date}-01`;
      return {
        label: formatDate(first, { month: "short" }),
        full: formatDate(first, { month: "long", year: "numeric" }),
        count: point.count,
      };
    }
    return {
      label: formatDate(point.date, { day: "numeric", month: "short" }),
      full: formatDate(point.date, {
        weekday: "long",
        day: "numeric",
        month: "long",
      }),
      count: point.count,
    };
  });
  const total = series.reduce((sum, point) => sum + point.count, 0);
  const description = t(`charts.activity.description.${mode}`);
  const caption =
    mode === "week"
      ? t("charts.table.activityWeek")
      : mode === "month"
        ? t("charts.table.activityMonth")
        : t("charts.table.activity");
  const periodColumn =
    mode === "week"
      ? t("charts.column.week")
      : mode === "month"
        ? t("charts.column.month")
        : t("charts.column.date");

  return (
    <ChartPanel
      title={t("charts.activity.title")}
      description={description}
      empty={!data.length || total === 0}
      table={{
        caption,
        columns: [
          { key: "day", label: periodColumn },
          { key: "count", label: t("charts.column.count"), numeric: true },
        ],
        rows: data.map((point) => ({
          id: point.full,
          day: point.full,
          count: point.count,
        })),
      }}
    >
      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height={224}>
          <BarChart
            data={data}
            margin={{ top: 8, right: 4, left: -20, bottom: 0 }}
            barCategoryGap="18%"
            accessibilityLayer
            title={t("charts.activity.title")}
            desc={description}
          >
            <CartesianGrid
              vertical={false}
              stroke="#e5e9df"
              strokeDasharray="3 4"
            />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              minTickGap={18}
              tick={{ fontSize: "var(--vc-text-11)", fill: "#7c877e" }}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              width={34}
              tick={{ fontSize: "var(--vc-text-11)", fill: "#7c877e" }}
            />
            <Tooltip
              cursor={{ fill: "rgba(64,110,77,0.07)" }}
              content={
                <ChartTooltip
                  mode="activity"
                  unit={(value) => plural("charts.events", value)}
                />
              }
            />
            <Bar
              dataKey="count"
              name={t("charts.column.count")}
              fill={CHART_COLORS.moss}
              radius={[4, 4, 0, 0]}
              maxBarSize={mode === "day" ? 16 : 40}
              isAnimationActive={!reduced}
              animationDuration={420}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}

function CareMixDonut({ careMix }: { careMix: CareMixSlice[] }) {
  const { t, formatNumber, plural } = useI18n();
  const { kindLabel } = useCareLabels();
  const reduced = useReducedMotion();
  const slices = careMix.map((slice) => ({
    ...slice,
    label: kindLabel(slice.kind),
  }));
  const total = slices.reduce((sum, slice) => sum + slice.count, 0);

  return (
    <ChartPanel
      title={t("charts.careMix.title")}
      description={t("charts.careMix.description")}
      empty={!slices.length || total === 0}
      table={{
        caption: t("charts.table.careMix"),
        columns: [
          { key: "kind", label: t("charts.column.kind") },
          { key: "count", label: t("charts.column.count"), numeric: true },
          { key: "share", label: t("charts.column.share"), numeric: true },
        ],
        rows: slices.map((slice) => ({
          id: slice.kind,
          kind: slice.label,
          count: slice.count,
          share: formatNumber(slice.count / total, {
            style: "percent",
            maximumFractionDigits: 0,
          }),
        })),
      }}
    >
      <div className="donut-layout">
        <div className="donut-wrap">
          <ResponsiveContainer width="100%" height={214}>
            <PieChart
              accessibilityLayer
              title={t("charts.careMix.title")}
              desc={t("charts.careMix.description")}
            >
              <Pie
                data={slices}
                dataKey="count"
                nameKey="label"
                innerRadius="58%"
                outerRadius="84%"
                paddingAngle={2}
                stroke="#fff"
                strokeWidth={2}
                isAnimationActive={!reduced}
                animationDuration={420}
              >
                {slices.map((slice) => (
                  <Cell
                    key={slice.kind}
                    fill={careColor(slice.kind)}
                  />
                ))}
              </Pie>
              <Tooltip
                content={
                  <ChartTooltip
                    mode="donut"
                    unit={(value) => plural("charts.events", value)}
                  />
                }
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="donut-center" aria-hidden="true">
            <strong>{total}</strong>
            <span>{t("charts.careMix.center")}</span>
          </div>
        </div>
        <ChartLegend
          items={slices.map((slice) => ({
            label: slice.label,
            color: careColor(slice.kind),
            value: slice.count,
          }))}
        />
      </div>
    </ChartPanel>
  );
}

function RoomBars({ rooms }: { rooms: RoomSummary[] }) {
  const { t, formatNumber } = useI18n();
  const reduced = useReducedMotion();
  const data = rooms.map((room) => ({
    label: room.room || t("charts.roomUnassigned"),
    room: room.room,
    plants: room.plants,
    overdue: room.overdue,
    ok: Math.max(0, room.plants - room.overdue),
  }));

  return (
    <ChartPanel
      title={t("charts.rooms.title")}
      description={t("charts.rooms.description")}
      empty={!data.length}
      table={{
        caption: t("charts.table.rooms"),
        columns: [
          { key: "room", label: t("charts.column.room") },
          { key: "plants", label: t("charts.column.plants"), numeric: true },
          { key: "overdue", label: t("charts.column.overdue"), numeric: true },
        ],
        rows: data.map((room) => ({
          id: room.label,
          room: room.label,
          plants: room.plants,
          overdue: room.overdue,
        })),
      }}
    >
      <div className="chart-canvas chart-canvas-rooms">
        <ResponsiveContainer
          width="100%"
          height={Math.max(160, data.length * 34 + 24)}
        >
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 16, left: 0, bottom: 0 }}
            accessibilityLayer
            title={t("charts.rooms.title")}
            desc={t("charts.rooms.description")}
          >
            <CartesianGrid
              horizontal={false}
              stroke="#e5e9df"
              strokeDasharray="3 4"
            />
            <XAxis
              type="number"
              hide
              allowDecimals={false}
            />
            <YAxis
              type="category"
              dataKey="label"
              width={92}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: "var(--vc-text-12)", fill: "#4c5a50" }}
            />
            <Tooltip
              cursor={{ fill: "rgba(64,110,77,0.07)" }}
              content={<ChartTooltip mode="rooms" unit={formatNumber} />}
            />
            <Bar
              dataKey="ok"
              name={t("charts.rooms.ok")}
              stackId="plants"
              fill={CHART_COLORS.moss}
              isAnimationActive={!reduced}
              animationDuration={420}
            />
            <Bar
              dataKey="overdue"
              name={t("charts.rooms.overdue")}
              stackId="plants"
              fill={CHART_COLORS.clay}
              radius={[0, 4, 4, 0]}
              isAnimationActive={!reduced}
              animationDuration={420}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ChartLegend
        items={[
          { label: t("charts.rooms.ok"), color: CHART_COLORS.moss },
          { label: t("charts.rooms.overdue"), color: CHART_COLORS.clay },
        ]}
      />
    </ChartPanel>
  );
}

export default function AnalyticsCharts({
  activity,
  careMix,
  rooms,
  period,
}: {
  activity: ActivityPoint[];
  careMix: CareMixSlice[];
  rooms: RoomSummary[];
  period: AnalyticsPeriod;
}) {
  return (
    <div className="analytics-charts">
      <ActivityBars activity={activity} period={period} />
      <CareMixDonut careMix={careMix} />
      <RoomBars rooms={rooms} />
    </div>
  );
}
