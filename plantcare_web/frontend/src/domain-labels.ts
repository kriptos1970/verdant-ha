import { useI18n, type MessageKey } from "./i18n";

const CATEGORY: Record<string, MessageKey> = {
  Tropicale: "plants.category.tropical",
  Succulenta: "plants.category.succulent",
  Aromatica: "plants.category.aromatic",
  Fiorita: "plants.category.flowering",
  Altro: "plants.category.other",
};
const LIGHT: Record<string, MessageKey> = {
  "Luce bassa": "plants.light.low",
  "Luce indiretta": "plants.light.indirect",
  "Luce intensa": "plants.light.bright",
  "Sole diretto": "plants.light.direct",
};
const POT: Record<string, MessageKey> = {
  Plastica: "plants.pot.plastic",
  Terracotta: "plants.pot.terracotta",
  Ceramica: "plants.pot.ceramic",
  "Ceramica smaltata": "plants.pot.glazed",
  "Ceramica non smaltata": "plants.pot.unglazed",
  Tessuto: "plants.pot.fabric",
  "Auto-irrigante": "plants.pot.selfWatering",
  Altro: "plants.pot.other",
};
const PLACEMENT: Record<string, MessageKey> = {
  "Balcone riparato": "plants.placement.balconySheltered",
  "Pieno sole": "plants.placement.fullSun",
  Ombra: "plants.placement.shade",
  "Mezza ombra · balcone": "plants.placement.halfShadeBalcony",
  Patio: "plants.placement.patio",
  Pianerottolo: "plants.placement.landing",
  "Interno luminoso": "plants.placement.brightIndoor",
  "Interno poco luminoso": "plants.placement.lowIndoor",
};
const FREQUENCY: Record<string, MessageKey> = {
  "Molto frequente": "plants.frequency.veryFrequent",
  Frequente: "plants.frequency.frequent",
  Normale: "plants.frequency.normal",
  Diradata: "plants.frequency.sparse",
  "Molto diradata": "plants.frequency.verySparse",
};
const PLAN_MODE: Record<string, MessageKey> = {
  Manuale: "detail.planMode.manual",
  Intelligente: "detail.planMode.smart",
  AI: "detail.planMode.ai",
};

export function useDomainLabels() {
  const { t } = useI18n();
  const label = (map: Record<string, MessageKey>, value?: string | null) =>
    value && map[value] ? t(map[value]) : value || "";
  return {
    categoryLabel: (value?: string | null) => label(CATEGORY, value),
    lightLabel: (value?: string | null) => label(LIGHT, value),
    potLabel: (value?: string | null) => label(POT, value),
    placementLabel: (value?: string | null) => label(PLACEMENT, value),
    frequencyLabel: (value?: string | null) => label(FREQUENCY, value),
    planModeLabel: (value?: string | null) => label(PLAN_MODE, value),
  };
}
