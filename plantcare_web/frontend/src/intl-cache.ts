// Intl objects are expensive to build: one per locale and options shape is enough.
const dateFormatters = new Map<string, Intl.DateTimeFormat>();
const numberFormatters = new Map<string, Intl.NumberFormat>();
const pluralRules = new Map<string, Intl.PluralRules>();

const cacheKey = (locale: string, options?: object) =>
  options ? `${locale}|${JSON.stringify(options)}` : locale;

export function dateFormatter(locale: string, options?: Intl.DateTimeFormatOptions) {
  const key = cacheKey(locale, options);
  let formatter = dateFormatters.get(key);
  if (!formatter) {
    formatter = new Intl.DateTimeFormat(locale, options);
    dateFormatters.set(key, formatter);
  }
  return formatter;
}

export function numberFormatter(locale: string, options?: Intl.NumberFormatOptions) {
  const key = cacheKey(locale, options);
  let formatter = numberFormatters.get(key);
  if (!formatter) {
    formatter = new Intl.NumberFormat(locale, options);
    numberFormatters.set(key, formatter);
  }
  return formatter;
}

export function pluralRule(locale: string) {
  let rules = pluralRules.get(locale);
  if (!rules) {
    rules = new Intl.PluralRules(locale);
    pluralRules.set(locale, rules);
  }
  return rules;
}
