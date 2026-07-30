import type { Page, Route } from "@playwright/test";

const METHOD_PREFIX = "edu_quality.api.admissions_dashboard";

export const CLASSES = [
  { key: "Nursery", label: "Nursery", short: "Nur" },
  { key: "1", label: "1", short: "1" },
];

export const META = {
  academic_years: ["2026-2027", "2025-2026"],
  default_academic_year: "2026-2027",
  locations: ["Alphaville", "Betatown"],
  classes: CLASSES,
};

export const STRENGTH = {
  academic_year: "2026-2027",
  previous_academic_year: "2025-2026",
  rows: [
    {
      location: "Alphaville",
      target: null,
      balance: null,
      strength_current: 320,
      strength_previous: 300,
      new_admissions: 45,
      admission_percent: 15,
      cancelled: 25,
      cancelled_percent: 8.3,
      added_students: 20,
      added_percent: 6.7,
      enquiries: 400,
      convert_percent: 11.3,
      capacity: 500,
      full_percent: 64,
    },
    {
      location: "Betatown",
      target: 60,
      balance: 20,
      strength_current: 180,
      strength_previous: 200,
      new_admissions: 40,
      admission_percent: 20,
      cancelled: 60,
      cancelled_percent: 30,
      added_students: -20,
      added_percent: -10,
      enquiries: 250,
      convert_percent: 16,
      capacity: 400,
      full_percent: 45,
    },
    {
      location: "Total",
      is_total: true,
      target: 60,
      balance: 20,
      strength_current: 500,
      strength_previous: 500,
      new_admissions: 85,
      admission_percent: 17,
      cancelled: 85,
      cancelled_percent: 17,
      added_students: 0,
      added_percent: 0,
      enquiries: 650,
      convert_percent: 13.1,
      capacity: 900,
      full_percent: 55.6,
    },
  ],
};

export const CLASS_DISTRIBUTION = {
  academic_year: "2026-2027",
  classes: [...CLASSES, { key: "total", label: "Total", short: "Total" }],
  rows: [
    {
      location: "Alphaville",
      target: { Nursery: 30, "1": 20, total: 50 },
      admissions: { Nursery: 25, "1": 20, total: 45 },
    },
    {
      location: "Betatown",
      target: { Nursery: 40, "1": 20, total: 60 },
      admissions: { Nursery: 22, "1": 18, total: 40 },
    },
  ],
};

export const BRANCH_REPORT = {
  academic_year: "2026-2027",
  branches: [
    {
      location: "Alphaville",
      months: [
        { month: "2026-04", label: "Apr 2026", enquiries: 240, admissions: 30 },
        { month: "2026-05", label: "May 2026", enquiries: 160, admissions: 15 },
      ],
      stats: {
        total_enquiries: 400,
        total_admissions: 45,
        conversion_rate: 11.3,
        peak_month: "Apr 2026",
      },
    },
    {
      location: "Betatown",
      months: [
        { month: "2026-04", label: "Apr 2026", enquiries: 250, admissions: 40 },
      ],
      stats: {
        total_enquiries: 250,
        total_admissions: 40,
        conversion_rate: 16,
        peak_month: "Apr 2026",
      },
    },
  ],
};

export const detailFor = (location: string) => ({
  academic_year: "2026-2027",
  previous_academic_year: "2025-2026",
  location,
  locations: META.locations,
  columns: ["Nur", "1", "Total"],
  stats: [
    { name: "2026-2027 Strength", data: [120, 200, 320] },
    { name: "Capacity", data: [200, 300, 500] },
    { name: "Admissions", data: [25, 20, 45] },
  ],
  admissions: [
    { name: "Total", data: [25, 20, 45] },
    { name: "Apr 05", data: [3, 2, 5] },
  ],
  waiting_list: [
    { name: "Total", data: [8, 4, 12] },
    { name: "Apr 06", data: [1, 1, 2] },
  ],
});

type Overrides = {
  meta?: unknown;
  strength?: unknown;
  distribution?: unknown;
  branchReport?: unknown;
  detail?: (location: string) => unknown;
  status?: number;
  onRequest?: (url: URL) => void;
};

/**
 * Stub every dashboard endpoint so the specs exercise the React app alone --
 * no bench, site or database involved.
 */
export async function mockDashboardApi(page: Page, overrides: Overrides = {}) {
  const status = overrides.status ?? 200;

  // Matched with a predicate rather than a glob: the endpoints carry query
  // strings and dots, which make glob matching easy to get subtly wrong.
  await page.route(
    (url) => url.pathname.includes(METHOD_PREFIX),
    async (route: Route) => {
      const url = new URL(route.request().url());
      overrides.onRequest?.(url);

      if (status !== 200) {
        return route.fulfill({
          status,
          contentType: "application/json",
          body: JSON.stringify({ exception: "stubbed failure" }),
        });
      }

      const method = url.pathname.split(".").pop();
      const location = url.searchParams.get("location") ?? META.locations[0];

      const payloads: Record<string, unknown> = {
        get_dashboard_meta: overrides.meta ?? META,
        get_strength_analysis: overrides.strength ?? STRENGTH,
        get_class_distribution: overrides.distribution ?? CLASS_DISTRIBUTION,
        get_branch_report: overrides.branchReport ?? BRANCH_REPORT,
        get_admission_detail: (overrides.detail ?? detailFor)(location),
      };

      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ message: payloads[method ?? ""] ?? {} }),
      });
    }
  );

  // Anything else under /api must not silently fall through to the preview
  // server, which answers unknown paths with index.html and would leave the
  // app waiting forever on a response that is not JSON.
  await page.route(
    (url) => url.pathname.startsWith("/api/") && !url.pathname.includes(METHOD_PREFIX),
    (route) =>
      route.fulfill({
        status: 501,
        contentType: "application/json",
        body: JSON.stringify({ exception: `unmocked call: ${route.request().url()}` }),
      })
  );
}
