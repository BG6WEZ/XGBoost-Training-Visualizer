# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Protected route access >> TC6: unauthenticated access redirects to login
- Location: e2e\auth.spec.ts:106:3

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/login/
Received string:  "http://localhost:3000/assets/"
Timeout: 10000ms

Call log:
  - Expect "toHaveURL" with timeout 10000ms
    14 × unexpected value "http://localhost:3000/assets/"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - heading "403 Forbidden" [level=1] [ref=e3]
  - separator [ref=e4]
  - generic [ref=e5]: nginx/1.29.8
```

# Test source

```ts
  21  |     await expect(page.locator('#username')).toBeVisible();
  22  |     await expect(page.locator('#password')).toBeVisible();
  23  |     await expect(page.getByRole('button', { name: /登录/i })).toBeVisible();
  24  |     // Use first() to avoid strict mode violation (text appears in both h1 and h2)
  25  |     await expect(page.getByText('XGBoost Training Visualizer').first()).toBeVisible();
  26  |     await expect(page.getByText('请登录以继续使用')).toBeVisible();
  27  |     
  28  |     await page.screenshot({ path: 'e2e/screens/TC1-login-page.png', fullPage: true });
  29  |   });
  30  | 
  31  |   test('TC2: valid credentials login succeeds and navigates to home', async ({ page }) => {
  32  |     await page.goto('/');
  33  |     await page.locator('#username').fill('admin');
  34  |     await page.locator('#password').fill('admin123');
  35  |     await page.getByRole('button', { name: /登录/i }).click();
  36  |     
  37  |     // Wait for successful login redirect
  38  |     await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
  39  |     await expect(page).toHaveURL(/\/$/, { timeout: 10000 });
  40  |     
  41  |     // Verify we are on home page after login
  42  |     await expect(page.locator('h1, h2, h3').first()).toBeVisible({ timeout: 5000 });
  43  |     
  44  |     await page.screenshot({ path: 'e2e/screens/TC2-login-success.png', fullPage: true });
  45  |   });
  46  | 
  47  |   test('TC3: invalid credentials shows explicit error message', async ({ page }) => {
  48  |     await page.goto('/');
  49  |     await page.locator('#username').fill('admin');
  50  |     await page.locator('#password').fill('wrong_password_12345');
  51  |     await page.getByRole('button', { name: /登录/i }).click();
  52  |     
  53  |     // Verify error message appears within the error container
  54  |     const errorEl = page.locator('.bg-red-50');
  55  |     await expect(errorEl).toBeVisible({ timeout: 10000 });
  56  |     
  57  |     // Verify error text is meaningful
  58  |     const errorText = await errorEl.textContent();
  59  |     expect(errorText).toBeTruthy();
  60  |     expect(errorText.length).toBeGreaterThan(0);
  61  |     
  62  |     await page.screenshot({ path: 'e2e/screens/TC3-login-error.png', fullPage: true });
  63  |   });
  64  | 
  65  |   test('TC4: empty form submission triggers validation', async ({ page }) => {
  66  |     await page.goto('/');
  67  |     
  68  |     // Verify both inputs have required attribute
  69  |     await expect(page.locator('#username')).toHaveAttribute('required');
  70  |     await expect(page.locator('#password')).toHaveAttribute('required');
  71  |     
  72  |     // Try clicking submit without filling anything
  73  |     // Browser native validation should prevent submission
  74  |     await page.getByRole('button', { name: /登录/i }).click();
  75  |     await page.waitForTimeout(500);
  76  |     
  77  |     // Should still be on login page
  78  |     await expect(page).toHaveURL(/\/login/);
  79  |   });
  80  | });
  81  | 
  82  | test.describe('Logout flow', () => {
  83  |   test('TC5: logout redirects to login page', async ({ page }) => {
  84  |     // First login
  85  |     await page.goto('/');
  86  |     await page.locator('#username').fill('admin');
  87  |     await page.locator('#password').fill('admin123');
  88  |     await page.getByRole('button', { name: /登录/i }).click();
  89  |     await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
  90  |     
  91  |     // Find and click logout button
  92  |     // Try multiple selectors to find logout
  93  |     const logoutBtn = page.locator('button:has-text("退出"), button:has-text("Logout"), button:has-text("登出"), [data-testid="logout"]').first();
  94  |     await expect(logoutBtn).toBeVisible({ timeout: 5000 });
  95  |     await logoutBtn.click();
  96  |     
  97  |     // Verify redirect to login page
  98  |     await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  99  |     await expect(page.locator('#username')).toBeVisible({ timeout: 5000 });
  100 |     
  101 |     await page.screenshot({ path: 'e2e/screens/TC5-logout.png', fullPage: true });
  102 |   });
  103 | });
  104 | 
  105 | test.describe('Protected route access', () => {
  106 |   test('TC6: unauthenticated access redirects to login', async ({ page }) => {
  107 |     // Ensure we are logged out
  108 |     await page.goto('/');
  109 |     if (!await page.url().includes('/login')) {
  110 |       const logoutBtn = page.locator('button:has-text("退出"), button:has-text("Logout"), button:has-text("登出")').first();
  111 |       if (await logoutBtn.isVisible({ timeout: 3000 })) {
  112 |         await logoutBtn.click();
  113 |         await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  114 |       }
  115 |     }
  116 |     
  117 |     // Try accessing protected routes - should redirect to login
  118 |     const protectedRoutes = ['/', '/experiments', '/monitor', '/compare', '/assets'];
  119 |     for (const route of protectedRoutes) {
  120 |       await page.goto(route);
> 121 |       await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
      |                          ^ Error: expect(page).toHaveURL(expected) failed
  122 |     }
  123 |     
  124 |     await page.screenshot({ path: 'e2e/screens/TC6-protected-routes.png', fullPage: true });
  125 |   });
  126 | });
```