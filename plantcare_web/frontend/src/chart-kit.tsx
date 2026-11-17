import React, {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Leaf } from "lucide-react";
import { useI18n } from "./i18n";

/**
 * Shared, Recharts-free chart shell.
 *
 * Everything here stays in the main bundle: palette, reduced-motion helper,
 * deferred mount, empty/loading states and the accessible data table. The
 * Recharts components live in charts.tsx and are loaded on demand.
 */

export const CHART_COLORS = {
  forest: "#194330",
  moss: "#406e4d",
  sage: "#7fa88a",
  pale: "#c9d8c6",
  clay: "#a9554b",
  sand: "#b0893f",
  sky: "#3d7ea6",
  violet: "#6d5aa8",
} as const;

/** Care colours keep the same hue in every chart and legend. */
export const CARE_COLORS: Record<string, string> = {
  Annaffia: "#3d7ea6",
  Concima: "#b07d38",
  Ruota: "#4f8a72",
  Rinvasa: "#a15c47",
  Pota: "#6d5aa8",
  "Controlla salute": "#7a8b5a",
  "Aggiorna progressi": "#607d8b",
  Trattamento: "#9a5b7d",
  Spostamento: "#8a7a5c",
  "Aggiornamento piano": "#9aa79c",
};

export function careColor(kind: string) {
  return CARE_COLORS[kind] ?? CHART_COLORS.sage;
}

export type HealthBucket =
  | "excellent"
  | "good"
  | "struggling"
  | "sick"
  | "unrated";

export const HEALTH_COLORS: Record<HealthBucket, string> = {
  excellent: "#3f7d5a",
  good: "#6f9d64",
  struggling: "#b0893f",
  sick: "#a9554b",
  unrated: "#9aa79c",
};

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

/** True when the user asked the system to reduce motion. */
export function useReducedMotion() {
  const [reduced, setReduced] = useState(
    () =>
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia(REDUCED_MOTION_QUERY).matches,
  );

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const query = window.matchMedia(REDUCED_MOTION_QUERY);
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener?.("change", update);
    return () => query.removeEventListener?.("change", update);
  }, []);

  return reduced;
}

/**
 * Mounts its children only when the placeholder gets close to the viewport.
 * It keeps the Recharts chunk out of the initial plant-list load.
 */
export function DeferredSection({
  children,
  fallback,
  className = "",
  rootMargin = "360px 0px",
}: {
  children: ReactNode;
  fallback?: ReactNode;
  className?: string;
  rootMargin?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (visible) return;
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [visible, rootMargin]);

  return (
    <div ref={ref} className={`chart-deferred ${className}`.trim()}>
      {visible ? children : fallback}
    </div>
  );
}

export function ChartSkeleton({ label }: { label?: string }) {
  const { t } = useI18n();
  return (
    <div
      className="chart-skeleton"
      role="status"
      aria-label={label ?? t("common.loading")}
    />
  );
}

export function ChartEmpty({
  title,
  text,
}: {
  title?: string;
  text?: string;
}) {
  const { t } = useI18n();
  return (
    <div className="chart-empty">
      <Leaf size={22} aria-hidden="true" />
      <strong>{title ?? t("charts.emptyTitle")}</strong>
      <p>{text ?? t("charts.emptyText")}</p>
    </div>
  );
}

export type ChartColumn = {
  key: string;
  label: string;
  numeric?: boolean;
};

export type ChartRow = Record<string, string | number>;

export function ChartDataTable({
  caption,
  columns,
  rows,
}: {
  caption: string;
  columns: ChartColumn[];
  rows: ChartRow[];
}) {
  const { t } = useI18n();
  return (
    <details className="chart-table">
      <summary>{t("charts.dataTable")}</summary>
      <div className="chart-table-scroll">
        <table>
          <caption>{caption}</caption>
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={column.numeric ? "num" : undefined}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={String(row.id ?? index)}>
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={column.numeric ? "num" : undefined}
                  >
                    {row[column.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

export function ChartPanel({
  title,
  description,
  empty,
  emptyText,
  table,
  className = "",
  children,
}: {
  title: string;
  description?: string;
  empty?: boolean;
  emptyText?: string;
  table?: {
    caption: string;
    columns: ChartColumn[];
    rows: ChartRow[];
  };
  className?: string;
  children: ReactNode;
}) {
  return (
    <section className={`panel chart-panel ${className}`.trim()}>
      <header className="chart-head">
        <div>
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
      </header>
      {empty ? (
        <ChartEmpty text={emptyText} />
      ) : (
        <>
          <div className="chart-body">{children}</div>
          {table && table.rows.length > 0 ? (
            <ChartDataTable
              caption={table.caption}
              columns={table.columns}
              rows={table.rows}
            />
          ) : null}
        </>
      )}
    </section>
  );
}

export function ChartLegend({
  items,
}: {
  items: Array<{ label: string; color: string; value?: string | number }>;
}) {
  return (
    <ul className="chart-legend">
      {items.map((item) => (
        <li key={item.label}>
          <span
            className="chart-swatch"
            style={{ background: item.color }}
            aria-hidden="true"
          />
          <span>{item.label}</span>
          {item.value !== undefined ? <b>{item.value}</b> : null}
        </li>
      ))}
    </ul>
  );
}
