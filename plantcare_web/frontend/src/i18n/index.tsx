import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import it, { type MessageKey } from "./it";
import en from "./en";
import { api } from "../api";

export type { MessageKey } from "./it";

export type Locale = "it" | "en";
export type LanguagePreference = "auto" | Locale;

const STORAGE_KEY = "plantcare.language";
const catalogs: Record<Locale, Record<MessageKey, string>> = { it, en };

function detectLocale(): Locale {
  if (typeof document === "undefined") return "en";
  const browserLanguage =
    typeof navigator === "undefined" ? "" : navigator.language;
  const documentLanguage = document.documentElement.lang;
  return (browserLanguage || documentLanguage || "")
    .toLowerCase()
    .startsWith("it")
    ? "it"
    : "en";
}

function readPreference(): LanguagePreference {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "it" || value === "en" || value === "auto") return value;
  } catch {
    // localStorage can be unavailable in private mode; keep the default.
  }
  return "auto";
}

function interpolate(
  message: string,
  params?: Record<string, string | number>,
) {
  if (!params) return message;
  return message.replace(/\{(\w+)\}/g, (match, key) =>
    key in params ? String(params[key]) : match,
  );
}

type I18nValue = {
  locale: Locale;
  preference: LanguagePreference;
  setPreference: (value: LanguagePreference) => void;
  t: (key: MessageKey, params?: Record<string, string | number>) => string;
  plural: (
    key: string,
    count: number,
    params?: Record<string, string | number>,
  ) => string;
  formatDate: (
    value: Date | string | number,
    options?: Intl.DateTimeFormatOptions,
  ) => string;
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string;
};

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] =
    useState<LanguagePreference>(readPreference);
  const locale: Locale = preference === "auto" ? detectLocale() : preference;

  useEffect(() => {
    document.documentElement.lang = locale;
    void api("preferences", {
      method: "PUT",
      body: JSON.stringify({ language: locale }),
    }).catch(() => {
      // Older servers may not expose the preference endpoint.
    });
  }, [locale]);

  const setPreference = useCallback((value: LanguagePreference) => {
    setPreferenceState(value);
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch {
      // The UI still switches for this session.
    }
  }, []);

  const value = useMemo<I18nValue>(() => {
    const t = (key: MessageKey, params?: Record<string, string | number>) => {
      const message = catalogs[locale][key] ?? it[key] ?? key;
      return interpolate(message, params);
    };
    return {
      locale,
      preference,
      setPreference,
      t,
      plural: (key, count, params) => {
        const category = new Intl.PluralRules(locale).select(count);
        return t(`${key}.${category}` as MessageKey, { count, ...params });
      },
      formatDate: (value, options) =>
        new Intl.DateTimeFormat(locale, options).format(new Date(value)),
      formatNumber: (value, options) =>
        new Intl.NumberFormat(locale, options).format(value),
    };
  }, [locale, preference, setPreference]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside I18nProvider");
  return value;
}
