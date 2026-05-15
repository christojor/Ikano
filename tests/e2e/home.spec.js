const { test, expect } = require("@playwright/test");

test("home page renders healthy status", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Ikano Python Developer Work Sample" })).toBeVisible();
  await expect(page.getByText("Service status: ok")).toBeVisible();
});
