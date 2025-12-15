import { test, expect } from "@playwright/test";

test("Login flow smoke test", async ({ page }) => {
    // 1. Navigate to home
    await page.goto("/");

    // Expect Landing Page content (since we are not logged in)
    await expect(page.getByText("Get Better Answers Through")).toBeVisible();

    // 2. Open Login Modal
    // First "Login" button is in the header nav
    await page.getByRole("button", { name: "Login" }).first().click();

    // 3. Switch to Registration
    // Expect Login form first
    await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
    // Click "Register here" to switch mode
    await page.getByRole("button", { name: "Register here" }).click();

    // Expect Create Account form
    await expect(page.getByRole("heading", { name: "Create Account" })).toBeVisible();

    // 4. Perform Registration
    const timestamp = Date.now();
    const username = `smoke_${timestamp}`;
    const password = "password123";
    const orgName = `Smoke Org ${timestamp}`;
    const email = `smoke_${timestamp}@example.com`;

    await page.getByLabel("Username").fill(username);
    await page.getByLabel("Password").fill(password);
    await page.getByLabel("Organization Name").fill(orgName);
    await page.getByLabel("Owner Email").fill(email);

    // Submit
    await page.getByRole("button", { name: "Register & Continue" }).click();

    // 5. Verify landing on Dashboard/Chat
    // The app should now render the Dashboard layout (Sidebar + Chat)

    // Wait for the main app container
    await expect(page.locator(".app")).toBeVisible();

    // Since this is a new user, no conversation is selected initially.
    // Expect empty state message
    await expect(page.getByRole("heading", { name: "Welcome to LLM Council" })).toBeVisible();
});
