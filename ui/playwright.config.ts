import { defineConfig, devices } from "@playwright/test";

const PORT = 5199;

/**
 * The dashboard specs stub every `/api/method/...` call, so they run against a
 * plain `vite preview` of the production build with no bench, site or database
 * involved. That keeps them runnable in CI.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  // A cold-start SPA behind a preview server needs more than the 5s default,
  // and too many parallel workers on a busy machine make that worse.
  workers: process.env.CI ? 2 : 2,
  timeout: 60 * 1000,
  expect: { timeout: 15 * 1000 },
  reporter: process.env.CI ? "list" : [["list"], ["html", { open: "never" }]],
  use: {
    // Origin only: specs navigate to "/ui/..." so the paths read the same way
    // they appear in Frappe.
    baseURL: `http://localhost:${PORT}`,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // `--base=/ui/` mirrors how Frappe serves the app, so the router's
    // basename="/ui" resolves the same way it does in production. It has to be
    // passed to `preview` as well as `build`, or the preview server mounts the
    // app at "/" instead. The separate outDir keeps this build from clobbering
    // the deploy output in edu_quality/public/ui.
    command:
      `npx vite build --base=/ui/ --outDir dist-e2e && ` +
      `npx vite preview --base=/ui/ --outDir dist-e2e --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}/ui/dashboard`,
    reuseExistingServer: !process.env.CI,
    timeout: 180 * 1000,
  },
});
