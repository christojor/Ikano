const { test, expect } = require("@playwright/test");

// Helper to complete a flow
async function completeFlow(page, country, partyType) {
  // Start page
  await page.goto("/onboarding");
  
  // Select country
  await page.selectOption('select[name="country_code"]', country);
  
  // Select party type
  await page.check(`input[value="${partyType}"]`);
  
  // Submit start form
  await page.click('button[type="submit"]');
  await page.waitForNavigation();
  
  // Complete steps until final decision page
  for (let i = 0; i < 12; i++) {
    if (page.url().includes("/result")) {
      break;
    }

    const advanceButton = page.locator('button[type="submit"]');
    await expect(advanceButton).toBeVisible();
    await expect(advanceButton).toBeEnabled();
    await advanceButton.click();
    await page.waitForTimeout(300);
  }
  
  // Verify result page
  await expect(page.getByRole('heading')).toContainText(/Approved|Rejected|Review/);
  return page.url();
}

// Test all 6 flows: Sweden x2, Spain x2, Poland x2

test("Sweden Private Individual happy path", async ({ page }) => {
  const url = await completeFlow(page, "SE", "PRIVATE");
  expect(url).toContain("/result");
  
  // Verify application details
  await expect(page.getByText(/APP-/).first()).toBeVisible(); // Reference number
  await expect(page.getByRole("cell", { name: "SE", exact: true })).toBeVisible(); // Country
  await expect(page.getByRole("cell", { name: "PRIVATE", exact: true })).toBeVisible(); // Party type
  
  // Verify approved status
  await expect(page.getByRole("heading")).toContainText("Application Approved");
});

test("Sweden Business happy path", async ({ page }) => {
  const url = await completeFlow(page, "SE", "BUSINESS");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "SE", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS", exact: true })).toBeVisible();
  await expect(page.getByRole("heading")).toContainText("Application Approved");
});

test("Spain Private Individual happy path", async ({ page }) => {
  const url = await completeFlow(page, "ES", "PRIVATE");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "ES", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "PRIVATE", exact: true })).toBeVisible();
  await expect(page.getByRole("heading")).toContainText("Application Approved");
});

test("Spain Business happy path", async ({ page }) => {
  const url = await completeFlow(page, "ES", "BUSINESS");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "ES", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS", exact: true })).toBeVisible();
  await expect(page.getByRole("heading")).toContainText("Application Approved");
});

test("Poland Private Individual happy path", async ({ page }) => {
  const url = await completeFlow(page, "PL", "PRIVATE");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "PL", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "PRIVATE", exact: true })).toBeVisible();
  await expect(page.getByRole("heading")).toContainText("Application Approved");
});

test("Poland Business happy path", async ({ page }) => {
  const url = await completeFlow(page, "PL", "BUSINESS");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "PL", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS", exact: true })).toBeVisible();
  await expect(page.getByRole("heading")).toContainText("Application Approved");
});

// Test alternative decision paths

test("Manual review path - choose manual review scenario", async ({ page }) => {
  await page.goto("/onboarding");
  
  // Start with SE/PRIVATE
  await page.selectOption('select[name="country_code"]', "SE");
  await page.check('input[value="PRIVATE"]');
  await page.click('button[type="submit"]');
  await page.waitForNavigation();
  
  // Go through first step
  await page.click('button[type="submit"]');
  await page.waitForTimeout(300);
  
  // At check step, choose MANUAL_REVIEW
  if (page.locator('input[value="MANUAL_REVIEW"]').isVisible()) {
    await page.check('input[value="MANUAL_REVIEW"]');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(300);
  }
  
  // Continue with PASS for remaining steps
  for (let i = 0; i < 10; i++) {
    await page.click('button[type="submit"]');
    await page.waitForTimeout(300);
    if (page.url().includes("/result")) {
      break;
    }
  }
  
  // Should end in UNDER_REVIEW
  await expect(page.getByRole("heading")).toContainText("Under Manual Review");
});

test("Rejection path - choose fail scenario", async ({ page }) => {
  await page.goto("/onboarding");
  
  // Start with ES/BUSINESS
  await page.selectOption('select[name="country_code"]', "ES");
  await page.check('input[value="BUSINESS"]');
  await page.click('button[type="submit"]');
  await page.waitForNavigation();
  
  // Go through steps, choose FAIL at a check step
  await page.click('button[type="submit"]');
  await page.waitForTimeout(300);
  
  if (page.locator('input[value="FAIL"]').isVisible()) {
    await page.check('input[value="FAIL"]');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(300);
  } else {
    // Continue to next step
    await page.click('button[type="submit"]');
    await page.waitForTimeout(300);
  }
  
  // Continue until result page for final decision
  for (let i = 0; i < 6; i++) {
    if (page.url().includes("/result")) {
      break;
    }
    await page.click('button[type="submit"]');
    await page.waitForTimeout(300);
  }

  // Should end in REJECTED
  await expect(page).toHaveURL(/\/result$/);
  await expect(page.getByRole("heading")).toContainText("Rejected");
});

// Test form validation

test("Start form validation - cannot submit without country", async ({ page }) => {
  await page.goto("/onboarding");
  
  // Try without country selection
  await page.check('input[value="PRIVATE"]');
  await page.click('button[type="submit"]');
  
  // Error should appear (or form doesn't submit)
  // Wait a bit for potential error message
  await page.waitForTimeout(300);
  
  // Should still be on onboarding page
  expect(page.url()).toContain("/onboarding");
});

test("Start form validation - cannot submit without party type", async ({ page }) => {
  await page.goto("/onboarding");
  
  // Try without party type
  await page.selectOption('select[name="country_code"]', "PL");
  await page.click('button[type="submit"]');
  
  // Error should appear
  await page.waitForTimeout(300);
  
  expect(page.url()).toContain("/onboarding");
});

// Test navigation

test("Navigation - back to home from start page", async ({ page }) => {
  await page.goto("/onboarding");
  
  await page.click('a:has-text("Back to home")');
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Welcome to Ikano Bank" })).toBeVisible();
});

test("Navigation - header logo returns to home", async ({ page }) => {
  await page.goto("/onboarding");
  
  // Click header logo
  await page.click("header a[href='/']");
  await expect(page).toHaveURL(/\/$/);
});

test("Navigation - new application from result page", async ({ page }) => {
  const url = await completeFlow(page, "SE", "PRIVATE");
  
  // Click New Application
  await page.click('a:has-text("New Application")');
  await expect(page).toHaveURL(/\/onboarding$/);
  await expect(page.getByRole("heading", { name: "Start Your Application" })).toBeVisible();
});

test("Progress tracking - progress bar updates", async ({ page }) => {
  await page.goto("/onboarding");
  
  await page.selectOption('select[name="country_code"]', "SE");
  await page.check('input[value="PRIVATE"]');
  await page.click('button[type="submit"]');
  await page.waitForNavigation();
  
  // Check step counter
  const stepInfo = page.locator('text=/Step \\d+ \\/ \\d+/');
  await expect(stepInfo).toContainText("Step 1 / 7");
  
  // Proceed to step 2
  await page.click('button[type="submit"]');
  await page.waitForTimeout(300);
  
  // Should update to step 2
  if (page.url().includes("/step")) {
    const newStepInfo = page.locator('text=/Step \\d+ \\/ \\d+/');
    await expect(newStepInfo).toContainText("Step 2 / 7");
  }
});
