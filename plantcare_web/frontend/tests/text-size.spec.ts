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

for (const width of [1280, 390]) {
  test(`shared typography scales text once without resizing icons or photos at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    const navigation = page.getByRole("navigation", { name: "Main navigation" });
    await navigation.getByRole("button", { name: "Plants", exact: true }).click();
    const card = page.locator(".plant-card").first();
    await expect(card).toBeVisible();
    const readSizes = () => page.evaluate(() => {
      const fontSize = (selector: string) =>
        parseFloat(getComputedStyle(document.querySelector(selector)!).fontSize);
      const size = (selector: string) => {
        const { width, height } = document.querySelector(selector)!.getBoundingClientRect();
        return { width, height };
      };
      return {
        heading: fontSize(".plant-card-body h3"),
        caption: fontSize(".plant-card-body > small"),
        inherited: fontSize("body"),
        input: fontSize(".search input"),
        icon: size(".topbar-right .button > svg"),
        photo: size(".card-image .plant-cover"),
      };
    });
    const baseline = await readSizes();
    for (const [preference, scale] of Object.entries(TEXT_SIZE_SCALES)) {
      // The settings control will use the provider in the next step.
      // Updating its CSS output here isolates the typography contract.
      await page.evaluate(({ scale }) => {
        document.documentElement.style.setProperty("--vc-text-scale", String(scale));
      }, { scale });
      const actual = await readSizes();
      expect(actual.heading, preference).toBeCloseTo(baseline.heading * scale);
      expect(actual.caption, preference).toBeCloseTo(baseline.caption * scale);
      expect(actual.inherited, preference).toBeCloseTo(baseline.inherited * scale);
      expect(actual.input, preference).toBeCloseTo(
        width <= 760 ? Math.max(16, baseline.input * scale) : baseline.input * scale,
      );
      expect(actual.icon, preference).toEqual(baseline.icon);
      expect(actual.photo, preference).toEqual(baseline.photo);
    }
  });
}

test("printing ignores the reading scale and restores it on screen", async ({ page }) => {
  await page.addInitScript(({ key }) => localStorage.setItem(key, "maximum"), {
    key: TEXT_SIZE_STORAGE_KEY,
  });
  await page.goto("/");
  const scale = () => page.locator("html").evaluate(
    root => getComputedStyle(root).getPropertyValue("--vc-text-scale").trim(),
  );
  await expect.poll(scale).toBe("1.5");
  await page.emulateMedia({ media: "print" });
  await expect.poll(scale).toBe("1");
  await expect(page.locator("html")).toHaveCSS("font-size", "16px");
  await page.emulateMedia({ media: "screen" });
  await expect.poll(scale).toBe("1.5");
  await expect(page.locator("html")).toHaveCSS("font-size", "24px");
});
