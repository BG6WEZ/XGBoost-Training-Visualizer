import { test, expect } from '@playwright/test';

/**
 * Login flow E2E tests - Task 3.2 (M7-T74 hardened)
 * 
 * Covers:
 * 1. Login page renders correctly
 * 2. Valid credentials login succeeds
 * 3. Invalid credentials shows explicit error
 * 4. Logout redirects to login
 * 5. Protected routes require authentication
 */
test.describe('Login flow', () => {
  test('TC1: login page renders with all required elements', async ({ page }) => {
    await page.goto('/');
    
    // Verify page redirects to login when not authenticated
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    
    // Verify all required login page elements
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.getByRole('button', { name: /登录/i })).toBeVisible();
    // Use first() to avoid strict mode violation (text appears in both h1 and h2)
    await expect(page.getByText('XGBoost Training Visualizer').first()).toBeVisible();
    await expect(page.getByText('请登录以继续使用')).toBeVisible();
    
    await page.screenshot({ path: 'e2e/screens/TC1-login-page.png', fullPage: true });
  });

  test('TC2: valid credentials login succeeds and navigates to home', async ({ page }) => {
    await page.goto('/');
    await page.locator('#username').fill('admin');
    await page.locator('#password').fill('admin123');
    await page.getByRole('button', { name: /登录/i }).click();
    
    // Wait for successful login redirect
    await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
    await expect(page).toHaveURL(/\/$/, { timeout: 10000 });
    
    // Verify we are on home page after login
    await expect(page.locator('h1, h2, h3').first()).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screens/TC2-login-success.png', fullPage: true });
  });

  test('TC3: invalid credentials shows explicit error message', async ({ page }) => {
    await page.goto('/');
    await page.locator('#username').fill('admin');
    await page.locator('#password').fill('wrong_password_12345');
    await page.getByRole('button', { name: /登录/i }).click();
    
    // Verify error message appears within the error container
    const errorEl = page.locator('.bg-red-50');
    await expect(errorEl).toBeVisible({ timeout: 10000 });
    
    // Verify error text is meaningful
    const errorText = await errorEl.textContent();
    expect(errorText).toBeTruthy();
    expect(errorText.length).toBeGreaterThan(0);
    
    await page.screenshot({ path: 'e2e/screens/TC3-login-error.png', fullPage: true });
  });

  test('TC4: empty form submission triggers validation', async ({ page }) => {
    await page.goto('/');
    
    // Verify both inputs have required attribute
    await expect(page.locator('#username')).toHaveAttribute('required');
    await expect(page.locator('#password')).toHaveAttribute('required');
    
    // Try clicking submit without filling anything
    // Browser native validation should prevent submission
    await page.getByRole('button', { name: /登录/i }).click();
    await page.waitForTimeout(500);
    
    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Logout flow', () => {
  test('TC5: logout redirects to login page', async ({ page }) => {
    // First login
    await page.goto('/');
    await page.locator('#username').fill('admin');
    await page.locator('#password').fill('admin123');
    await page.getByRole('button', { name: /登录/i }).click();
    await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
    
    // Find and click logout button
    // Try multiple selectors to find logout
    const logoutBtn = page.locator('button:has-text("退出"), button:has-text("Logout"), button:has-text("登出"), [data-testid="logout"]').first();
    await expect(logoutBtn).toBeVisible({ timeout: 5000 });
    await logoutBtn.click();
    
    // Verify redirect to login page
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    await expect(page.locator('#username')).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screens/TC5-logout.png', fullPage: true });
  });
});

test.describe('Protected route access', () => {
  test('TC6: unauthenticated access redirects to login', async ({ page }) => {
    // Ensure we are logged out
    await page.goto('/');
    if (!await page.url().includes('/login')) {
      const logoutBtn = page.locator('button:has-text("退出"), button:has-text("Logout"), button:has-text("登出")').first();
      if (await logoutBtn.isVisible({ timeout: 3000 })) {
        await logoutBtn.click();
        await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
      }
    }
    
    // Try accessing protected routes - should redirect to login
    const protectedRoutes = ['/', '/experiments', '/monitor', '/compare', '/assets'];
    for (const route of protectedRoutes) {
      await page.goto(route);
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    }
    
    await page.screenshot({ path: 'e2e/screens/TC6-protected-routes.png', fullPage: true });
  });
});