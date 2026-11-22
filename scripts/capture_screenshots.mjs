// Capture README screenshots from a running Verdant instance with headless Chrome.
//
// Development helper, not part of the add-on. Start the backend with a throwaway
// data directory, then run:
//
//     node scripts/capture_screenshots.mjs
//
// Writes PNG files to docs/screenshots/readme/.

import { spawn } from "node:child_process";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.env.VERDANT_URL || "http://127.0.0.1:8099";
const OUT = "docs/screenshots/readme";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9333;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function launch() {
  const profile = await mkdtemp(join(tmpdir(), "verdant-chrome-"));
  const child = spawn(CHROME, [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--lang=en-US",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${profile}`,
    "about:blank",
  ], { stdio: "ignore" });
  for (let i = 0; i < 60; i += 1) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (res.ok) return { child, profile };
    } catch {
      /* not ready yet */
    }
    await sleep(200);
  }
  throw new Error("Chrome did not expose the debugging port");
}

async function pageTarget() {
  const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
  const targets = await res.json();
  const page = targets.find((t) => t.type === "page");
  if (!page) throw new Error("No page target");
  return page.webSocketDebuggerUrl;
}

function client(url) {
  const ws = new WebSocket(url);
  let id = 0;
  const pending = new Map();
  const events = [];
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    } else if (msg.method) {
      events.push(msg.method);
    }
  });
  const ready = new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve);
    ws.addEventListener("error", reject);
  });
  return {
    ready,
    events,
    send(method, params = {}) {
      id += 1;
      const current = id;
      ws.send(JSON.stringify({ id: current, method, params }));
      return new Promise((resolve, reject) => pending.set(current, { resolve, reject }));
    },
    close: () => ws.close(),
  };
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const { child, profile } = await launch();
  const cdp = client(await pageTarget());
  await cdp.ready;
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Emulation.setLocaleOverride", { locale: "en-US" });
  await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
    source: "try { localStorage.setItem('plantcare.language', 'en'); } catch (e) {}",
  });

  const viewport = async (width, height) => {
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width, height, deviceScaleFactor: 2, mobile: width < 600,
    });
  };

  const open = async (path) => {
    await cdp.send("Page.navigate", { url: BASE + path });
    await sleep(2200);
  };

  const clickText = async (text) => {
    await cdp.send("Runtime.evaluate", {
      expression: `(() => {
        const button = [...document.querySelectorAll('button')]
          .find((b) => b.textContent.trim().startsWith(${JSON.stringify(text)}));
        if (!button) return 'missing';
        button.click();
        return 'clicked';
      })()`,
      returnByValue: true,
    });
    await sleep(1200);
  };

  const shot = async (name) => {
    const { data } = await cdp.send("Page.captureScreenshot", { format: "png" });
    await writeFile(join(OUT, `${name}.png`), Buffer.from(data, "base64"));
    console.log("captured", name);
  };

  const plants = await (await fetch(`${BASE}/api/plants`)).json();
  const avocado = plants.find((p) => p.name === "Avocado") || plants[0];

  await viewport(390, 844);
  await open("/");
  await shot("home-phone");

  await clickText("Plants");
  await shot("plants-phone");

  await clickText("Care");
  await shot("care-phone");

  await open(`/#plant=${avocado.id}`);
  await shot("plant-phone");

  await viewport(1440, 900);
  await open(`/#plant=${avocado.id}`);
  await shot("home-desktop");

  cdp.close();
  child.kill();
  await rm(profile, { recursive: true, force: true });
}

main().catch(async (error) => {
  console.error(error);
  process.exitCode = 1;
});
