const { test, expect } = require("@playwright/test");

async function startApplication(page, countryCode, partyTypeCode) {
  await page.goto("/onboarding");
  await page.selectOption("#country_code", countryCode);
  await page.locator(`input[name='party_type_code'][value='${partyTypeCode}']`).check();

  const startResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/onboarding/start") &&
      response.request().method() === "POST" &&
      response.status() === 201,
  );

  await page.getByRole("button", { name: /Start Application/ }).click();

  await startResponsePromise;
  await page.waitForURL(/\/onboarding\/\d+\/step$/);
  await expect(page.getByText("Step 1 / 4")).toBeVisible();

  const idMatch = page.url().match(/\/onboarding\/(\d+)\/step$/);
  if (!idMatch) {
    throw new Error("Failed to parse application id from onboarding step URL");
  }

  return Number(idMatch[1]);
}

async function continueStep(page, scenario = "PASS") {
  const scenarioOption = page.locator(`input[name='scenario'][value='${scenario}']`);
  if (await scenarioOption.isVisible()) {
    await scenarioOption.check();
  }

  const advanceResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/onboarding/") &&
      response.url().includes("/advance") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );

  await page.getByRole("button", { name: /Continue/ }).click();
  await advanceResponsePromise;
  await page.waitForLoadState("domcontentloaded");
}

async function completeFlow(page, countryCode, partyTypeCode, scenario) {
  await startApplication(page, countryCode, partyTypeCode);

  for (let i = 0; i < 5; i += 1) {
    if (page.url().includes("/result")) {
      break;
    }
    await continueStep(page, scenario);
  }

  await expect(page).toHaveURL(/\/onboarding\/\d+\/result$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    /Application Approved|Application Rejected|Under Manual Review/,
  );
}

test("Sweden Private Individual happy path", async ({ page }) => {
  await completeFlow(page, "SE", "PRIVATE", "PASS");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
  await expect(page.getByText("APP-")).toBeVisible();
  await expect(page.getByRole("cell", { name: "SE" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "PRIVATE" })).toBeVisible();
});

test("Sweden Business happy path", async ({ page }) => {
  await completeFlow(page, "SE", "BUSINESS", "PASS");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
  await expect(page.getByRole("cell", { name: "SE" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS" })).toBeVisible();
});

test("Spain Private Individual happy path", async ({ page }) => {
  await completeFlow(page, "ES", "PRIVATE", "PASS");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
  await expect(page.getByRole("cell", { name: "ES" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "PRIVATE" })).toBeVisible();
});

test("Spain Business happy path", async ({ page }) => {
  await completeFlow(page, "ES", "BUSINESS", "PASS");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
  await expect(page.getByRole("cell", { name: "ES" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS" })).toBeVisible();
});

test("Poland Private Individual happy path", async ({ page }) => {
  await completeFlow(page, "PL", "PRIVATE", "PASS");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
  await expect(page.getByRole("cell", { name: "PL" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "PRIVATE" })).toBeVisible();
});

test("Poland Business happy path", async ({ page }) => {
  await completeFlow(page, "PL", "BUSINESS", "PASS");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
  await expect(page.getByRole("cell", { name: "PL" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS" })).toBeVisible();
});

test("Manual review path - choose manual review scenario", async ({ page }) => {
  await completeFlow(page, "SE", "PRIVATE", "MANUAL_REVIEW");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Under Manual Review");
});

test("Rejection path - choose fail scenario", async ({ page }) => {
  await completeFlow(page, "ES", "BUSINESS", "FAIL");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Rejected");
});

test("Start form validation - cannot submit without country", async ({ page }) => {
  await page.goto("/onboarding");

  await page.locator("input[name='party_type_code'][value='PRIVATE']").check();
  await page.getByRole("button", { name: /Start Application/ }).click();

  await expect(page).toHaveURL(/\/onboarding$/);
});

test("Start form validation - cannot submit without party type", async ({ page }) => {
  await page.goto("/onboarding");

  await page.selectOption("#country_code", "PL");
  await page.getByRole("button", { name: /Start Application/ }).click();

  await expect(page.locator("#form-error")).toContainText("Please select an account type.");
});

test("Navigation - back to home from start page", async ({ page }) => {
  await page.goto("/onboarding");

  await Promise.all([
    page.waitForURL(/\/$/),
    page.getByRole("link", { name: /Back to home/ }).click(),
  ]);

  await expect(page.getByRole("heading", { name: "Welcome to Ikano Bank" })).toBeVisible();
});

test("Navigation - header logo returns to home", async ({ page }) => {
  await page.goto("/onboarding");

  await Promise.all([
    page.waitForURL(/\/$/),
    page.getByRole("link", { name: /IKANO BANK/ }).click(),
  ]);

  await expect(page.getByRole("heading", { name: "Welcome to Ikano Bank" })).toBeVisible();
});

test("Navigation - new application from result page", async ({ page }) => {
  await completeFlow(page, "SE", "PRIVATE", "PASS");

  await Promise.all([
    page.waitForURL(/\/onboarding$/),
    page.getByRole("link", { name: /New Application/ }).click(),
  ]);

  await expect(page.getByRole("heading", { name: "Start Your Application" })).toBeVisible();
});

test("Progress tracking - progress badge updates", async ({ page }) => {
  await startApplication(page, "SE", "PRIVATE");
  await expect(page.getByText("Step 1 / 4")).toBeVisible();

  await continueStep(page, "PASS");

  await expect(page).toHaveURL(/\/onboarding\/\d+\/step$/);
  await expect(page.getByText("Step 2 / 4")).toBeVisible();
});



