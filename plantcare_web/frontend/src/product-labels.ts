import { useI18n, type MessageKey } from "./i18n";

const CATEGORY_KEYS: Record<string, MessageKey> = {
  Fertilizzante: "products.category.fertilizer",
  Radicante: "products.category.rooting",
  Antiparassitario: "products.category.pest",
  Fungicida: "products.category.fungicide",
  Biostimolante: "products.category.biostimulant",
  Ammendante: "products.category.amendment",
  "Altro trattamento": "products.category.other",
};

const FORM_KEYS: Record<string, MessageKey> = {
  Liquido: "products.form.liquid",
  Granulare: "products.form.granular",
  Bastoncini: "products.form.sticks",
  Polvere: "products.form.powder",
  Organico: "products.form.organic",
  Altro: "products.form.other",
};

export function useProductLabels() {
  const { t } = useI18n();
  return {
    categoryLabel: (value?: string | null) =>
      value && CATEGORY_KEYS[value] ? t(CATEGORY_KEYS[value]) : value || "",
    formLabel: (value?: string | null) =>
      value && FORM_KEYS[value] ? t(FORM_KEYS[value]) : value || "",
  };
}
