export const TEXT_SIZE_STORAGE_KEY = "verdant.textSize.v1";

export const TEXT_SIZE_SCALES = {
  small: 0.9,
  normal: 1,
  large: 1.15,
  "extra-large": 1.3,
  maximum: 1.5,
} as const;

export type TextSizePreference = keyof typeof TEXT_SIZE_SCALES;

export function isTextSizePreference(value: unknown): value is TextSizePreference {
  return typeof value === "string" && Object.hasOwn(TEXT_SIZE_SCALES, value);
}

export function readTextSizePreference(
  storage?: Pick<Storage, "getItem">,
): TextSizePreference {
  try {
    const value = (storage ?? localStorage).getItem(TEXT_SIZE_STORAGE_KEY);
    return isTextSizePreference(value) ? value : "normal";
  } catch {
    // Storage may be blocked or unavailable; preserve the default appearance.
    return "normal";
  }
}

export function saveTextSizePreference(
  preference: TextSizePreference,
  storage?: Pick<Storage, "setItem">,
): void {
  try {
    (storage ?? localStorage).setItem(TEXT_SIZE_STORAGE_KEY, preference);
  } catch {
    // The provider keeps the choice in memory for the current session.
  }
}
