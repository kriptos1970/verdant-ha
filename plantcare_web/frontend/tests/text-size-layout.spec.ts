import { expect, test, type Locator, type Page } from "@playwright/test";

async function expectTextToFit(locator: Locator) {
  const overflow = await locator.evaluateAll(elements => elements.flatMap(element => {
    const bounds = element.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return [];
    return element.scrollWidth > element.clientWidth + 2
      ? [{ text: element.textContent, width: element.clientWidth, content: element.scrollWidth }]
      : [];
  }));
  expect(overflow).toEqual([]);
}

async function initialize(page: Page, width: number, language: "it" | "en") {
  await page.setViewportSize({ width, height: 900 });
  await page.addInitScript(language => {
    localStorage.setItem("verdant.textSize.v1", "maximum");
    localStorage.setItem("plantcare.language", language);
  }, language);
  await page.goto("/");
  await expect(page.locator(".native-week")).toBeVisible();
}

for (const language of ["it", "en"] as const) {
  for (const width of [320, 360, 375, 390, 1280]) {
    test(`maximum text stays readable across main pages (${language}, ${width}px)`, async ({ page }) => {
      await initialize(page, width, language);
      const navigation = page.getByRole("navigation", {
        name: language === "it" ? "Navigazione principale" : "Main navigation", exact: true,
      });
      await expectTextToFit(page.locator(".home-heading h1, .native-week .calendar-day, .bottom-tabs button"));
      if (width <= 760) {
        const wrappedLabels = await page.locator(".bottom-tab-label").evaluateAll(elements =>
          elements.filter(element => element.getBoundingClientRect().height > parseFloat(getComputedStyle(element).lineHeight) + 1)
            .map(element => element.textContent),
        );
        expect(wrappedLabels).toEqual([]);
      }
      await navigation.getByRole("button", {
        name: language === "it" ? "Piante" : "Plants", exact: true,
      }).click();
      await expect(page.locator(".plant-card").first()).toBeVisible();
      await expectTextToFit(page.locator(".plant-card-body h3, .plant-card-body > small"));
      await navigation.getByRole("button", {
        name: language === "it" ? "Prodotti" : "Products", exact: true,
      }).click();
      await expectTextToFit(page.locator(".ios-product-list strong, .ios-product-list small, .product-card h2"));
      await navigation.getByRole("button", {
        name: language === "it" ? /^Cure\b/ : /^Care\b/,
      }).click();
      await expectTextToFit(page.locator(".care-mode-toolbar .button, .care-mode-toolbar .segmented button"));
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);
    });

    test(`maximum text fits plant details and dialogs (${language}, ${width}px)`, async ({ page }) => {
      await initialize(page, width, language);
      const navigation = page.getByRole("navigation", {
        name: language === "it" ? "Navigazione principale" : "Main navigation", exact: true,
      });
      await navigation.getByRole("button", {
        name: language === "it" ? "Piante" : "Plants", exact: true,
      }).click();
      await page.locator(".plant-card-main").first().click();
      const detail = page.locator("aside.detail");
      await expect(detail.locator(".ios-plant-caption h2")).toBeVisible();
      await expectTextToFit(detail.locator(".ios-plant-actions button, .ios-summary-grid small, .ios-summary-grid strong"));
      await expectTextToFit(detail.locator(".detail-scroll"));
      const hero = detail.locator(".ios-plant-hero");
      const caption = detail.locator(".ios-plant-caption");
      const heroBounds = await hero.boundingBox();
      const captionBounds = await caption.boundingBox();
      expect(captionBounds!.y).toBeGreaterThanOrEqual(heroBounds!.y);
      expect(captionBounds!.y + captionBounds!.height).toBeLessThanOrEqual(heroBounds!.y + heroBounds!.height + 1);
      // Modal editing is checked without writing anything to the demo archive.
      await page.goto("/");
      await page.getByRole("button", {
        name: language === "it" ? "Nuova pianta" : "New plant", exact: true,
      }).first().click();
      const dialog = page.getByRole("dialog");
      await expect(dialog).toBeVisible();
      await expectTextToFit(dialog);
      await expectTextToFit(dialog.locator(".modal-top h2, .editor-actions .button, .editor-section h3, .editor-disclosure > summary > span, .editor-disclosure > summary > em"));
      await dialog.locator("details.editor-disclosure").evaluateAll(elements => {
        elements.forEach(element => { (element as HTMLDetailsElement).open = true; });
      });
      await expectTextToFit(dialog.locator("label, summary, .editor-section h3"));
      await page.keyboard.press("Escape");
      await expect(dialog).not.toBeVisible();
    });
  }
}
