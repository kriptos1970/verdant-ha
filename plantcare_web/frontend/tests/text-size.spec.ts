import { expect, test } from "@playwright/test";
import {
  isTextSizePreference,
  readTextSizePreference,
  saveTextSizePreference,
  TEXT_SIZE_SCALES,
  TEXT_SIZE_STORAGE_KEY,
} from "../src/text-size-preference";

test("text size accepts only the five supported preferences", () => {
  expect(Object.values(TEXT_SIZE_SCALES)).toEqual([0.9, 1, 1.15, 1.3, 1.5]);
  for (const value of Object.keys(TEXT_SIZE_SCALES)) {
    expect(isTextSizePreference(value)).toBe(true);
    expect(readTextSizePreference({ getItem: () => value })).toBe(value);
  }
  for (const value of [null, undefined, "", "invalid", "toString", "__proto__", 1.5]) {
    expect(isTextSizePreference(value)).toBe(false);
  }
});

test("missing, invalid and inaccessible storage use normal text size", () => {
  for (const value of [null, "", "invalid", "1.5", "constructor"]) {
    expect(readTextSizePreference({ getItem: () => value })).toBe("normal");
  }
  expect(readTextSizePreference({
    getItem: () => { throw new Error("Storage blocked"); },
  })).toBe("normal");
});

test("text size can be persisted, read back and reset to normal", () => {
  const values = new Map<string, string>();
  const storage = {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => { values.set(key, value); },
  };
  saveTextSizePreference("large", storage);
  expect(values.get(TEXT_SIZE_STORAGE_KEY)).toBe("large");
  expect(readTextSizePreference(storage)).toBe("large");
  saveTextSizePreference("normal", storage);
  expect(readTextSizePreference(storage)).toBe("normal");
  expect(() => saveTextSizePreference("maximum", {
    setItem: () => { throw new Error("Storage full"); },
  })).not.toThrow();
});

for (const [stored, preference, scale] of [
  [null, "normal", "1"],
  ["invalid", "normal", "1"],
  ["maximum", "maximum", "1.5"],
] as const) {
  test(`provider initializes text size from ${stored ?? "missing storage"} and preserves it on reload`, async ({ page }) => {
    await page.addInitScript(({ key, value }) => {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
    }, { key: TEXT_SIZE_STORAGE_KEY, value: stored });
    await page.goto("/");
    for (let attempt = 0; attempt < 2; attempt++) {
      await expect(page.locator("html")).toHaveAttribute("data-text-size", preference);
      await expect.poll(() => page.locator("html").evaluate(
        root => (root as HTMLElement).style.getPropertyValue("--vc-text-scale"),
      )).toBe(scale);
      if (attempt === 0) await page.reload();
    }
  });
}

test("provider starts normally when localStorage is blocked", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() { throw new DOMException("Storage blocked", "SecurityError"); },
    });
  });
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-text-size", "normal");
  await expect(page.getByRole("heading", { name: "Your week" })).toBeVisible();
});
