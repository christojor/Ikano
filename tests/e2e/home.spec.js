const { test, expect } = require("@playwright/test");

test("home page renders welcome message and status", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Welcome to Banana Bank" })).toBeVisible();
  await expect(page.locator("header #service-status")).toContainText("Service status: ok");
  await expect(page.getByRole("link", { name: /Start Application/ })).toBeVisible();
});

test("header contains Banana logo and navigation", async ({ page }) => {
  await page.goto("/");

  // Check header is sticky
  const banner = page.locator("header");
  await expect(banner).toBeVisible();
  
  // Check logo link to home
  await expect(page.locator("header a[href='/']").first()).toBeVisible();
  
  // Check navigation links
  await expect(page.getByRole("link", { name: "Home" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Onboarding" })).toBeVisible();
});

test("navigation to onboarding works", async ({ page }) => {
  await page.goto("/");

  await Promise.all([
    page.waitForURL(/\/onboarding$/),
    page.getByRole("link", { name: /Start Application/ }).click(),
  ]);

  await expect(page.getByRole("heading", { name: "Start Your Application" })).toBeVisible();
});
