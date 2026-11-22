import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { createHash, randomUUID } from "node:crypto";

const navigation = (page: Page) =>
  page.getByRole("navigation", { name: "Main navigation" });

const plantDetail = (page: Page) => page.locator("aside.detail");
const growthNote = "Aggiornamento dimostrativo separato dalla cronologia delle cure.";

async function openPlant(page: Page, name: string) {
  const plants = navigation(page).getByRole("button", { name: "Plants", exact: true });
  if (await plants.getAttribute("aria-current") !== "page") await plants.click();
  await page.getByRole("main").getByRole("button", { name: new RegExp(`\\b${name}\\b`) }).click();
  const detail = plantDetail(page);
  await expect(detail.getByRole("heading", { name, exact: true })).toBeVisible();
  return detail;
}

async function openBackup(page: Page) {
  await navigation(page).getByRole("button", { name: "More" }).click();
  await page.getByRole("button", { name: /Archive and backup/ }).click();
}

async function audit(page: Page) {
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(violations.map(({ id, nodes }) => ({
    rule: id,
    elements: nodes.map(({ target, failureSummary }) => ({ target, failureSummary })),
  }))).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Your week" })).toBeVisible();
});

test("keyboard can skip navigation and close the named plant editor", async ({ page }) => {
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  const opener = page.getByRole("button", { name: "New plant", exact: true }).first();
  await opener.focus();
  await page.keyboard.press("Enter");
  const editor = page.getByRole("dialog", { name: "A new plant" });
  await expect(editor.getByRole("button", { name: "Close", exact: true })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(editor.locator(":focus")).toHaveCount(1);
  await editor.getByRole("button", { name: "Save plant" }).press("Enter");
  await expect(editor.getByRole("textbox", { name: "Plant name" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(editor).toBeHidden();
  await expect(opener).toBeFocused();
});

for (const name of [/^Today$/, /^Plants$/, /^Care\b/, /^Products$/]) {
  test(`desktop ${name.source} passes automated accessibility checks`, async ({ page }) => {
    const entry = navigation(page).getByRole("button", { name });
    await entry.click();
    await expect(entry).toHaveAttribute("aria-current", "page");
    await audit(page);
  });
}

test("the plant editor passes automated accessibility checks", async ({ page }) => {
  await page.getByRole("button", { name: "New plant", exact: true }).first().click();
  await expect(page.getByRole("dialog", { name: "A new plant" })).toBeVisible();
  await audit(page);
});

test("desktop plant details load the right data and reset the diary when switching plants", async ({ page }) => {
  const detail = await openPlant(page, "Olivia");
  await expect(detail.locator(".ios-plant-species")).toHaveText("Monstera deliciosa");
  const toggle = detail.getByRole("button", { name: /^Growth diary\b/ });
  const diary = detail.getByRole("region", { name: "Growth diary", exact: true });
  await toggle.click();
  await expect(diary.getByText(growthNote, { exact: true })).toBeVisible();

  await openPlant(page, "Pico");
  await expect(detail.locator(".ios-plant-species")).toHaveText("Pilea peperomioides");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(diary).toBeHidden();
  await toggle.click();
  await expect(diary).toBeVisible();
  await expect(diary.getByText(growthNote, { exact: true })).toHaveCount(0);
  await detail.getByRole("button", { name: "Close plant", exact: true }).click();
  await expect(detail.getByRole("heading", { name: "Pico", exact: true })).toHaveCount(0);
  await expect(page).not.toHaveURL(/#plant=/);
});

test.describe("mobile plant detail", () => {
  test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: "reduce" });

  test("the growth diary opens and collapses without overflowing the plant detail", async ({ page }) => {
    const detail = await openPlant(page, "Olivia");
    await expect(detail.locator(".ios-plant-species")).toHaveText("Monstera deliciosa");
    const toggle = detail.getByRole("button", { name: /^Growth diary\b/ });
    const diary = detail.getByRole("region", { name: "Growth diary", exact: true });
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await toggle.tap();
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(diary.getByText(growthNote, { exact: true })).toBeVisible();
    await expect(diary.getByRole("heading", { name: "Cronologia delle cure", exact: true })).toBeHidden();
    const overflow = await detail.locator(".detail-scroll").evaluate(el => el.scrollWidth - el.clientWidth);
    expect(overflow).toBe(0);
    await toggle.tap();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(diary).toBeHidden();
    await detail.getByRole("button", { name: "Close plant", exact: true }).tap();
    await expect(page).not.toHaveURL(/#plant=/);
  });
});

test("canceling a watering writes nothing; completing it persists in both histories", async ({ page, request }) => {
  const detail = await openPlant(page, "Pico");
  const plantId = new URLSearchParams(new URL(page.url()).hash.slice(1)).get("plant");
  expect(plantId).toBeTruthy();
  const plantPath = `/api/plants/${plantId}`;
  const beforeResponse = await request.get(plantPath);
  await expect(beforeResponse).toBeOK();
  const before = await beforeResponse.json();
  const notes = `Watered in Playwright (${randomUUID()})`;
  const water = detail.getByRole("button", { name: "Water", exact: true });
  const dialog = page.getByRole("dialog", { name: "Confirm task" });

  await water.click();
  await dialog.getByRole("textbox", { name: "Notes" }).fill(notes);
  await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(dialog).toBeHidden();
  const canceledResponse = await request.get(plantPath);
  await expect(canceledResponse).toBeOK();
  const canceled = await canceledResponse.json();
  expect(canceled._version).toBe(before._version);
  expect(canceled.history).toEqual(before.history);

  await water.click();
  await expect(dialog.getByRole("textbox", { name: "Notes" })).toBeEmpty();
  await dialog.getByRole("textbox", { name: "Notes" }).fill(notes);
  const [saved] = await Promise.all([
    page.waitForResponse(response => new URL(response.url()).pathname === `${plantPath}/events` &&
      response.request().method() === "POST"),
    dialog.getByRole("button", { name: "Complete", exact: true }).click(),
  ]);
  expect(saved.ok()).toBeTruthy();
  const updated = await saved.json();
  expect(updated.history).toHaveLength(before.history.length + 1);
  expect(updated.history).toEqual(expect.arrayContaining([
    expect.objectContaining({ kind: "Annaffia", status: "completed", note: notes }),
  ]));
  await expect(dialog).toBeHidden();

  await page.reload();
  await expect(detail.getByRole("heading", { name: "Pico", exact: true })).toBeVisible();
  await detail.getByRole("button", { name: /^Progress and history\b/ }).click();
  await expect(detail.locator(".history-event").getByText(notes, { exact: true })).toBeVisible();
  await navigation(page).getByRole("button", { name: /^Care\b/ }).click();
  await page.getByRole("button", { name: "History", exact: true }).click();
  await page.getByRole("combobox", { name: "Plant", exact: true }).selectOption({ label: "Pico" });
  const entry = page.locator(".global-history-event").filter({ hasText: notes });
  await expect(entry.getByText("Watering", { exact: true })).toBeVisible();
  await expect(entry.getByRole("button", { name: "Pico", exact: true })).toBeVisible();
});

test("Italian language persists and native backups remain blocked on a populated archive", async ({ page }) => {
  await navigation(page).getByRole("button", { name: "More" }).click();
  await page.getByRole("main").getByRole("button", { name: /Settings/ }).click();
  await page.getByRole("combobox", { name: "Language" }).selectOption("it");
  await expect(page.locator("html")).toHaveAttribute("lang", "it");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "it");
  await page.getByRole("navigation", { name: "Navigazione principale" })
    .getByRole("button", { name: "Altro" }).click();
  await page.getByRole("button", { name: /Archivio e backup/ }).click();
  const payload = Buffer.from(JSON.stringify({ plants: [{ id: randomUUID(), name: "Pothos" }], fertilizers: [], photos: {} }));
  const envelope = {
    version: 3,
    checksum: createHash("sha256").update(payload).digest("hex"),
    payload: payload.toString("base64"),
  };
  await page.getByLabel("Scegli un backup Verdant").setInputFiles({
    name: "native.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(envelope)),
  });
  await expect(page.getByRole("button", { name: /^Importa/ })).toBeDisabled();
  await expect(page.locator(".import-counts")).toContainText("1pianta");
});

for (const width of [320, 360, 375, 390]) {
  test(`phone layout fits at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 800 });
    await expect(navigation(page).getByRole("button", { name: "Today" }))
      .toHaveAttribute("aria-current", "page");
    await openBackup(page);
    await expect(page.getByLabel("Choose a Verdant backup")).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);
    if (width === 320) await audit(page);
  });
}

test("restoring a web backup needs confirmation and replaces the isolated archive", async ({ page, request }) => {
  const backup = await request.get("/api/backup");
  expect(backup.ok()).toBeTruthy();
  const file = await backup.body();
  await page.getByRole("button", { name: "New plant", exact: true }).first().click();
  const editor = page.getByRole("dialog", { name: "A new plant" });
  await editor.getByRole("textbox", { name: "Plant name" }).fill("Restore test plant");
  const [newPlant] = await Promise.all([
    page.waitForResponse(response => new URL(response.url()).pathname === "/api/plants" && response.request().method() === "POST"),
    editor.getByRole("button", { name: "Save plant" }).click(),
  ]);
  expect(newPlant.ok()).toBeTruthy();
  const { id } = await newPlant.json();
  await expect(editor).toBeHidden();
  await openBackup(page);
  const input = page.getByLabel("Choose a Verdant backup");
  await input.setInputFiles({ name: "demo.zip", mimeType: "application/zip", buffer: file });
  await expect(page.getByRole("heading", { name: "PlantCare Web" })).toBeFocused();
  await expect(page.getByText("Current archive", { exact: true })).toBeVisible();
  await audit(page);
  const restore = page.getByRole("button", { name: "Restore this backup" });
  await restore.focus();
  await page.keyboard.press("Enter");
  const confirmation = page.getByRole("dialog", { name: "Full restore" });
  await expect(confirmation.getByRole("button", { name: "Close", exact: true })).toBeFocused();
  await audit(page);
  await page.keyboard.press("Escape");
  await expect(restore).toBeFocused();
  expect((await request.get(`/api/plants/${id}`)).ok()).toBeTruthy();
  await page.keyboard.press("Enter");
  await confirmation.getByRole("button", { name: "Confirm restore" }).click();
  await expect(page.getByRole("status").getByText("Archive restored")).toBeVisible();
  await expect(input).toBeFocused();
  expect((await request.get(`/api/plants/${id}`)).status()).toBe(404);
});
