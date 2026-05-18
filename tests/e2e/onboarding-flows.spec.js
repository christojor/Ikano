const { test, expect } = require("@playwright/test");

async function submitCurrentStep(page) {
  const currentHeading = await page.getByRole('heading', { level: 1 }).textContent();
  await page.evaluate(() => {
    const form = document.getElementById("advance-form");
    if (!form) {
      throw new Error("advance-form not found");
    }

    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
      return;
    }

    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await page.waitForFunction((previousHeading) => {
    const heading = document.querySelector("h1");
    return heading && heading.textContent && heading.textContent.trim() !== previousHeading;
  }, currentHeading);
}

// Helper to complete a flow
async function completeFlow(page, country, partyType) {
  // Start page
  await page.goto("/onboarding");
  
  // Select country
  await page.selectOption('select[name="country_code"]', country);
  
  // Select party type
  await page.check(`input[value="${partyType}"]`);
  
  // Submit start form
  await page.evaluate(() => {
    const form = document.getElementById("start-form");
    if (!form) {
      throw new Error("start-form not found");
    }

    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
      return;
    }

    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await page.waitForFunction(() => {
    return window.location.pathname.includes("/step") || window.location.pathname.includes("/result");
  });
  
  // Complete steps until final decision page
  for (let i = 0; i < 12; i++) {
    if ((await page.locator('button[type="submit"]').count()) === 0) {
      break;
    }
    await submitCurrentStep(page);
  }
  
  // Verify result page
  await expect(page.getByRole('heading', { level: 1 })).toContainText(/Approved|Rejected|Review/);
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
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");

  // Verify Decision Date is displayed as date + time (YYYY-MM-DD HH:MM:SS)
  const decisionDateCell = page.locator("tr", { hasText: "Decision Date" }).locator("td");
  const decisionDateTime = (await decisionDateCell.textContent()).trim();
  expect(decisionDateTime).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
});

test("Sweden Business happy path", async ({ page }) => {
  const url = await completeFlow(page, "SE", "BUSINESS");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "SE", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
});

test("Spain Private Individual happy path", async ({ page }) => {
  const url = await completeFlow(page, "ES", "PRIVATE");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "ES", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "PRIVATE", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
});

test("Spain Business happy path", async ({ page }) => {
  const url = await completeFlow(page, "ES", "BUSINESS");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "ES", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
});

test("Poland Private Individual happy path", async ({ page }) => {
  const url = await completeFlow(page, "PL", "PRIVATE");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "PL", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "PRIVATE", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
});

test("Poland Business happy path", async ({ page }) => {
  const url = await completeFlow(page, "PL", "BUSINESS");
  expect(url).toContain("/result");
  
  await expect(page.getByRole("cell", { name: "PL", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "BUSINESS", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Application Approved");
});

// Test alternative decision paths

test("Manual review path - choose manual review scenario", async ({ page }) => {
  await page.goto("/onboarding");
  
  // Start with SE/PRIVATE
  await page.selectOption('select[name="country_code"]', "SE");
  await page.check('input[value="PRIVATE"]');
  await page.evaluate(() => {
    const form = document.getElementById("start-form");
    if (!form) {
      throw new Error("start-form not found");
    }

    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
      return;
    }

    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await page.waitForFunction(() => {
    return window.location.pathname.includes("/step") || window.location.pathname.includes("/result");
  });
  
  // Go through first step
  await submitCurrentStep(page);

  // At check step, choose MANUAL_REVIEW
  await expect(page.locator('input[value="MANUAL_REVIEW"]')).toBeVisible();
  await page.check('input[value="MANUAL_REVIEW"]');
  await page.evaluate(() => {
    const form = document.getElementById("advance-form");
    if (!form) {
      throw new Error("advance-form not found");
    }

    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
      return;
    }

    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await page.waitForFunction(() => {
    return window.location.pathname.includes("/step") || window.location.pathname.includes("/result");
  });

  // Continue with PASS for remaining steps until the final decision page.
  for (let i = 0; i < 10; i++) {
    if ((await page.locator('button[type="submit"]').count()) === 0) {
      break;
    }
    await submitCurrentStep(page);
  }
  
  // Should end in UNDER_REVIEW
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Under Manual Review");
});

test("Rejection path - choose fail scenario", async ({ page }) => {
  await page.goto("/onboarding");
  
  // Start with ES/BUSINESS
  await page.selectOption('select[name="country_code"]', "ES");
  await page.check('input[value="BUSINESS"]');
  await page.evaluate(() => {
    const form = document.getElementById("start-form");
    if (!form) {
      throw new Error("start-form not found");
    }

    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
      return;
    }

    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await page.waitForFunction(() => {
    return window.location.pathname.includes("/step") || window.location.pathname.includes("/result");
  });
  
  // Go through steps, choose FAIL at a check step
  await submitCurrentStep(page);

  await expect(page.locator('input[value="FAIL"]')).toBeVisible();
  await page.check('input[value="FAIL"]');
  await page.evaluate(() => {
    const form = document.getElementById("advance-form");
    if (!form) {
      throw new Error("advance-form not found");
    }

    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
      return;
    }

    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await page.waitForFunction(() => {
    return window.location.pathname.includes("/step") || window.location.pathname.includes("/result");
  });

  // Continue until the final decision page.
  for (let i = 0; i < 10; i++) {
    if ((await page.locator('button[type="submit"]').count()) === 0) {
      break;
    }
    await submitCurrentStep(page);
  }

  // Should end in REJECTED
  await expect(page).toHaveURL(/\/result$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Rejected");
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

test("Navigation - browser history resets loading state on start page", async ({ page }) => {
  await page.goto("/onboarding");
  await page.selectOption('select[name="country_code"]', "SE");
  await page.check('input[value="PRIVATE"]');

  await page.evaluate(() => {
    const form = document.getElementById("start-form");
    if (!form) {
      throw new Error("start-form not found");
    }
    form.requestSubmit();
  });

  await expect(page).toHaveURL(/\/onboarding\/\d+\/step$/);

  await page.goBack();
  await expect(page).toHaveURL(/\/onboarding$/);
  await expect(page.locator("#submit-btn")).toBeEnabled();
  await expect(page.locator("#submit-btn")).toContainText("Start Application");

  await page.goForward();
  await expect(page).toHaveURL(/\/onboarding\/\d+\/step$/);
  await expect(page.locator("#advance-btn")).toBeEnabled();
  await expect(page.locator("#advance-btn")).toContainText("Continue");
});

test("Navigation - browser history resets loading state on step page", async ({ page }) => {
  await page.goto("/onboarding");
  await page.selectOption('select[name="country_code"]', "SE");
  await page.check('input[value="PRIVATE"]');

  await page.evaluate(() => {
    const form = document.getElementById("start-form");
    if (!form) {
      throw new Error("start-form not found");
    }
    form.requestSubmit();
  });

  await expect(page).toHaveURL(/\/onboarding\/\d+\/step$/);

  const headingBeforeAdvance = await page.getByRole("heading", { level: 1 }).textContent();
  await page.evaluate(() => {
    const form = document.getElementById("advance-form");
    if (!form) {
      throw new Error("advance-form not found");
    }
    form.requestSubmit();
  });

  await page.waitForFunction((previousHeading) => {
    const heading = document.querySelector("h1");
    return heading && heading.textContent && heading.textContent.trim() !== previousHeading;
  }, headingBeforeAdvance);

  await page.goBack();
  if (page.url().match(/\/onboarding$/)) {
    await expect(page.locator("#submit-btn")).toBeEnabled();
    await expect(page.locator("#submit-btn")).toContainText("Start Application");
  } else {
    await expect(page).toHaveURL(/\/onboarding\/\d+\/step$/);
    await expect(page.locator("#advance-btn")).toBeEnabled();
    await expect(page.locator("#advance-btn")).toContainText("Continue");
  }
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
