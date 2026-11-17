import { useI18n, type MessageKey } from "./i18n";
import type { Action, Plant } from "./types";

const INTERVAL_FIELDS: Record<string, keyof Plant> = {
  Annaffia: "wateringInterval",
  Concima: "fertilizingInterval",
  Ruota: "rotationInterval",
  Pota: "pruningInterval",
  Rinvasa: "repottingInterval",
  "Controlla salute": "inspectionInterval",
  "Aggiorna progressi": "progressInterval",
};

const KIND_KEYS: Record<string, MessageKey> = {
  Annaffia: "care.kind.water",
  Concima: "care.kind.fertilize",
  Ruota: "care.kind.rotate",
  Rinvasa: "care.kind.repot",
  Pota: "care.kind.prune",
  "Controlla salute": "care.kind.inspect",
  "Aggiorna progressi": "care.kind.progress",
  Trattamento: "care.kind.treatment",
  Spostamento: "care.kind.move",
  "Aggiornamento piano": "care.kind.planUpdate",
};

export function useCareLabels() {
  const { t, plural, formatDate } = useI18n();

  const kindLabel = (kind: string) =>
    KIND_KEYS[kind] ? t(KIND_KEYS[kind]) : kind;

  const actionLabel = (action: Action) =>
    action.includesFertilizing
      ? t("care.waterFertilize")
      : kindLabel(action.kind);

  const dueLabel = (days: number) =>
    days < 0
      ? plural("care.due.overdue", Math.abs(days))
      : days === 0
        ? t("care.due.today")
        : days === 1
          ? t("care.due.tomorrow")
          : plural("care.due.inDays", days);

  const deadline = (days: number) =>
    days === 0
      ? t("care.due.today")
      : days > 0
        ? plural("care.due.inDays", days)
        : plural("care.deadline.overdue", Math.abs(days));

  const dateLabel = (date: string) =>
    formatDate(date, { day: "numeric", month: "short" });

  const careValue = (plant: Plant, kind: string, frequencies = false) => {
    const interval = plant[INTERVAL_FIELDS[kind]];
    if (typeof interval !== "number" || interval <= 0)
      return kind === "Annaffia" || kind === "Concima"
        ? t("care.notScheduled")
        : t("care.notPlanned");
    if (frequencies)
      return interval === 1
        ? t("care.everyDay")
        : plural("care.everyDays", interval);
    const action = plant._schedule.find((item) => item.kind === kind);
    return action ? deadline(action.daysUntil) : t("care.notScheduled");
  };

  return { kindLabel, actionLabel, dueLabel, deadline, dateLabel, careValue };
}
