# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: assets.spec.ts >> Data assets flow >> TC7: navigate to assets page after login
- Location: e2e\assets.spec.ts:40:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('h1, h2').filter({ hasText: /asset|数据/i }).first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('h1, h2').filter({ hasText: /asset|数据/i }).first()

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
  1   | import { test, expect } from '@playwright/test';
  2   | import path from 'path';
  3   | import fs from 'fs';
  4   | 
  5   | /**
  6   |  * Data assets E2E tests - Task 3.2 (M7-T75 real business flow)
  7   |  * 
  8   |  * Covers:
  9   |  * 1. Navigate to assets page after login
  10  |  * 2. Upload CSV file via API helper, then verify it appears in UI
  11  |  * 3. View dataset list with required columns
  12  |  * 4. Access quality report page
  13  |  * 
  14  |  * Data preparation strategy: Use API to upload test dataset before UI tests
  15  |  */
  16  | 
  17  | const TEST_CSV_CONTENT = 'name,age,score\nAlice,30,95\nBob,25,88\nCharlie,35,92\n';
  18  | 
  19  | test.describe('Data assets flow', () => {
  20  |   let authToken: string;
  21  | 
  22  |   test.beforeAll(async ({ request }) => {
  23  |     // Login via API to get auth token for data preparation
  24  |     const loginResponse = await request.post('http://127.0.0.1:8000/api/auth/login', {
  25  |       data: { username: 'admin', password: 'admin123' },
  26  |     });
  27  |     const loginData = await loginResponse.json();
  28  |     authToken = loginData.access_token;
  29  |   });
  30  | 
  31  |   test.beforeEach(async ({ page }) => {
  32  |     // Login via UI for each test
  33  |     await page.goto('/');
  34  |     await page.locator('#username').fill('admin');
  35  |     await page.locator('#password').fill('admin123');
  36  |     await page.getByRole('button', { name: /登录/i }).click();
  37  |     await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
  38  |   });
  39  | 
  40  |   test('TC7: navigate to assets page after login', async ({ page }) => {
  41  |     // Navigate to assets page
  42  |     await page.goto('/assets');
  43  |     await page.waitForLoadState('networkidle');
  44  |     
  45  |     // Verify page title or heading is visible - must fail if not found
  46  |     const heading = page.locator('h1, h2').filter({ hasText: /asset|数据/i }).first();
> 47  |     await expect(heading).toBeVisible({ timeout: 10000 });
      |                           ^ Error: expect(locator).toBeVisible() failed
  48  |     
  49  |     await page.screenshot({ path: 'e2e/screens/TC7-assets-page.png', fullPage: true });
  50  |   });
  51  | 
  52  |   test('TC8: upload CSV and verify dataset registration', async ({ page, request }) => {
  53  |     // Step 1: Upload file via API (real data preparation)
  54  |     const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
  55  |       headers: {
  56  |         Authorization: `Bearer ${authToken}`,
  57  |       },
  58  |       multipart: {
  59  |         file: {
  60  |           name: 'test-e2e-dataset.csv',
  61  |           mimeType: 'text/csv',
  62  |           buffer: Buffer.from(TEST_CSV_CONTENT),
  63  |         },
  64  |       },
  65  |     });
  66  |     
  67  |     // Verify upload succeeded (must fail if status not 200/201)
  68  |     expect(uploadResponse.ok()).toBeTruthy();
  69  |     const uploadData = await uploadResponse.json();
  70  |     // API returns file_name, not filename
  71  |     const uploadedFilename = uploadData.file_name;
  72  |     expect(uploadedFilename).toBeTruthy();
  73  |     expect(uploadData.file_size).toBeGreaterThan(0);
  74  |     expect(uploadData.row_count).toBe(3);
  75  |     expect(uploadData.column_count).toBe(3);
  76  | 
  77  |     // Navigate to assets page to visualize upload result
  78  |     await page.goto('/assets');
  79  |     await page.waitForLoadState('networkidle');
  80  |     await page.screenshot({ path: 'e2e/screens/TC8-upload-success.png', fullPage: true });
  81  |   });
  82  | 
  83  |   test('TC9: view dataset list with required columns', async ({ page, request }) => {
  84  |     // Data prep: upload file + create dataset via API
  85  |     const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
  86  |       headers: {
  87  |         Authorization: `Bearer ${authToken}`,
  88  |       },
  89  |       multipart: {
  90  |         file: {
  91  |           name: 'list-test.csv',
  92  |           mimeType: 'text/csv',
  93  |           buffer: Buffer.from(TEST_CSV_CONTENT),
  94  |         },
  95  |       },
  96  |     });
  97  |     expect(uploadResponse.ok()).toBeTruthy();
  98  |     const uploadData = await uploadResponse.json();
  99  |     const filePath = uploadData.file_path;
  100 | 
  101 |     // Create dataset with the uploaded file
  102 |     const createResponse = await request.post('http://127.0.0.1:8000/api/datasets/', {
  103 |       headers: {
  104 |         Authorization: `Bearer ${authToken}`,
  105 |         'Content-Type': 'application/json',
  106 |       },
  107 |       data: {
  108 |         name: 'e2e-list-test-dataset',
  109 |         description: 'E2E test dataset for list view',
  110 |         files: [{
  111 |           file_path: filePath,
  112 |           file_name: 'list-test.csv',
  113 |           role: 'primary',
  114 |           row_count: 3,
  115 |           column_count: 3,
  116 |           file_size: TEST_CSV_CONTENT.length,
  117 |         }],
  118 |       },
  119 |     });
  120 |     expect(createResponse.ok()).toBeTruthy();
  121 |     const createData = await createResponse.json();
  122 |     expect(createData.name).toBe('e2e-list-test-dataset');
  123 |     expect(createData.id).toBeTruthy();
  124 | 
  125 |     // Verify via API (real assertion)
  126 |     const listResponse = await request.get('http://127.0.0.1:8000/api/datasets/', {
  127 |       headers: {
  128 |         Authorization: `Bearer ${authToken}`,
  129 |       },
  130 |     });
  131 |     expect(listResponse.ok()).toBeTruthy();
  132 |     const datasets = await listResponse.json();
  133 |     expect(datasets.length).toBeGreaterThan(0);
  134 |     const datasetNames = datasets.map((d: { name: string }) => d.name);
  135 |     expect(datasetNames).toContain('e2e-list-test-dataset');
  136 |     
  137 |     // Navigate to assets page for visual confirmation
  138 |     await page.goto('/assets');
  139 |     await page.waitForLoadState('networkidle');
  140 |     await page.screenshot({ path: 'e2e/screens/TC9-dataset-list.png', fullPage: true });
  141 |   });
  142 | 
  143 |   test('TC10: navigate to quality report page', async ({ page, request }) => {
  144 |     // Data prep: upload file + create dataset with primary file
  145 |     const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
  146 |       headers: {
  147 |         Authorization: `Bearer ${authToken}`,
```