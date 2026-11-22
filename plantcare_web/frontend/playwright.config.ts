import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../..", import.meta.url));
const python = existsSync(`${root}/.venv/bin/python`) ? ".venv/bin/python" : "python3";
const baseURL = "http://127.0.0.1:8771";

export default defineConfig({
  testDir: "./tests",
  workers: 1, // The preview server holds one isolated demo archive.
  forbidOnly: Boolean(process.env.CI),
  use: { baseURL, locale: "en-US", trace: "retain-on-failure" },
  webServer: {
    cwd: root,
    command: `${python} scripts/preview_ios.py --port 8771 --paired-care`,
    url: baseURL,
    reuseExistingServer: false, // Never send test mutations to an existing server.
  },
});
