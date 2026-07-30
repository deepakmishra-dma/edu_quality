import { expect, test } from "@playwright/test";
import { META, detailFor, mockDashboardApi } from "./fixtures";

test.describe("Admissions MIS dashboard", () => {
  test("renders the three panels from live figures", async ({ page }) => {
    await mockDashboardApi(page);
    await page.goto("/ui/dashboard");

    await expect(page.getByRole("heading", { name: "Admissions MIS" })).toBeVisible();

    // Strength Analysis: a branch row, the totals row, and the year headings.
    const strength = page.locator("table").first();
    await expect(strength).toContainText("Alphaville");
    await expect(strength).toContainText("2026-2027");
    await expect(strength).toContainText("2025-2026");
    await expect(strength.getByText("Total")).toBeVisible();
    await expect(strength).toContainText("320");

    // Targets are optional, so an unconfigured branch shows a dash.
    await expect(strength).toContainText("—");

    // Class-wise Distribution uses the class labels the API returned.
    const distribution = page.locator("table").nth(1);
    await expect(distribution).toContainText("Nursery");
    await expect(distribution).toContainText("Alphaville");

    // Branch-wise Report stat tiles.
    await expect(page.getByText("Total Enquiries").first()).toBeVisible();
    await expect(page.getByText("Conversion Rate").first()).toBeVisible();
    await expect(page.getByText("11.3%").first()).toBeVisible();
    await expect(page.getByText("Apr 2026").first()).toBeVisible();
  });

  test("opens on the running academic year and refetches when it changes", async ({ page }) => {
    const requestedYears: string[] = [];
    await mockDashboardApi(page, {
      onRequest: (url) => {
        const year = url.searchParams.get("academic_year");
        if (year) requestedYears.push(year);
      },
    });

    await page.goto("/ui/dashboard");
    await expect(page.getByRole("combobox")).toContainText(META.default_academic_year!);

    // The default is the running year, not simply the newest.
    await expect.poll(() => requestedYears).toContain("2026-2027");

    await page.getByRole("combobox").click();
    await page.getByRole("option", { name: "2025-2026" }).click();

    await expect(page.getByRole("combobox")).toContainText("2025-2026");
    await expect.poll(() => requestedYears).toContain("2025-2026");
  });

  test("shows an empty state when no branch is configured", async ({ page }) => {
    await mockDashboardApi(page, {
      meta: { ...META, locations: [], classes: [] },
      strength: { academic_year: "2026-2027", previous_academic_year: null, rows: [] },
      distribution: { academic_year: "2026-2027", classes: [], rows: [] },
      branchReport: { academic_year: "2026-2027", branches: [] },
    });
    await page.goto("/ui/dashboard");

    await expect(
      page.getByText("No branches have a location set on their School record.").first()
    ).toBeVisible();
  });

  test("surfaces an error when the API fails", async ({ page }) => {
    await mockDashboardApi(page, { status: 500 });
    await page.goto("/ui/dashboard");

    await expect(page.getByText(/Could not load/).first()).toBeVisible();
    await expect(page.getByText(/Server error/).first()).toBeVisible();
  });
});

test.describe("Detailed view", () => {
  test("is reachable from the dashboard and shows both tabs", async ({ page }) => {
    await mockDashboardApi(page);
    await page.goto("/ui/dashboard");

    await page.getByRole("link", { name: "Detailed View" }).click();
    await expect(page).toHaveURL(/\/dashboard\/detailed$/);

    // Admissions tab: the metric table plus the date-wise table.
    await expect(page.getByRole("heading", { name: "Date-wise Admissions" })).toBeVisible();
    await expect(page.getByText("2026-2027 Strength")).toBeVisible();
    await expect(page.getByText("Capacity")).toBeVisible();
    await expect(page.getByText("Apr 05")).toBeVisible();

    await page.getByRole("tab", { name: "Waiting List" }).click();
    await expect(page.getByRole("heading", { name: "Date-wise Waiting List" })).toBeVisible();
    await expect(page.getByText("Apr 06")).toBeVisible();
  });

  test("switching branch refetches for that branch", async ({ page }) => {
    const requestedLocations: string[] = [];
    await mockDashboardApi(page, {
      onRequest: (url) => {
        const location = url.searchParams.get("location");
        if (location) requestedLocations.push(location);
      },
    });

    await page.goto("/ui/dashboard/detailed");
    await expect(page.getByText("Alphaville", { exact: true }).first()).toBeVisible();

    await page.getByRole("combobox").nth(1).click();
    await page.getByRole("option", { name: "Betatown" }).click();

    await expect(page.getByText("Betatown", { exact: true }).first()).toBeVisible();
    await expect.poll(() => requestedLocations).toContain("Betatown");
  });

  test("shows an empty state when a branch has no records", async ({ page }) => {
    await mockDashboardApi(page, {
      detail: (location) => ({
        ...detailFor(location),
        stats: [],
        admissions: [],
        waiting_list: [],
      }),
    });
    await page.goto("/ui/dashboard/detailed");

    await expect(
      page.getByText("Nothing recorded for this branch and year.").first()
    ).toBeVisible();
  });
});
