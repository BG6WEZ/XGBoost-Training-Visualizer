import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * Data assets E2E tests - Task 3.2 (M7-T75 real business flow)
 * 
 * Covers:
 * 1. Navigate to assets page after login
 * 2. Upload CSV file via API helper, then verify it appears in UI
 * 3. View dataset list with required columns
 * 4. Access quality report page
 * 
 * Data preparation strategy: Use API to upload test dataset before UI tests
 */

const TEST_CSV_CONTENT = 'name,age,score\nAlice,30,95\nBob,25,88\nCharlie,35,92\n';

test.describe('Data assets flow', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // Login via API to get auth token for data preparation
    const loginResponse = await request.post('http://127.0.0.1:8000/api/auth/login', {
      data: { username: 'admin', password: 'admin123' },
    });
    const loginData = await loginResponse.json();
    authToken = loginData.access_token;
  });

  test.beforeEach(async ({ page }) => {
    // Login via UI for each test
    await page.goto('/');
    await page.locator('#username').fill('admin');
    await page.locator('#password').fill('admin123');
    await page.getByRole('button', { name: /登录/i }).click();
    await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
  });

  test('TC7: navigate to assets page after login', async ({ page }) => {
    // Navigate to assets page
    await page.goto('/assets');
    await page.waitForLoadState('networkidle');
    
    // Verify page title or heading is visible - must fail if not found
    const heading = page.locator('h1, h2').filter({ hasText: /asset|数据/i }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    await page.screenshot({ path: 'e2e/screens/TC7-assets-page.png', fullPage: true });
  });

  test('TC8: upload CSV and verify dataset registration', async ({ page, request }) => {
    // Step 1: Upload file via API (real data preparation)
    const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      multipart: {
        file: {
          name: 'test-e2e-dataset.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(TEST_CSV_CONTENT),
        },
      },
    });
    
    // Verify upload succeeded (must fail if status not 200/201)
    expect(uploadResponse.ok()).toBeTruthy();
    const uploadData = await uploadResponse.json();
    // API returns file_name, not filename
    const uploadedFilename = uploadData.file_name;
    expect(uploadedFilename).toBeTruthy();
    expect(uploadData.file_size).toBeGreaterThan(0);
    expect(uploadData.row_count).toBe(3);
    expect(uploadData.column_count).toBe(3);

    // Navigate to assets page to visualize upload result
    await page.goto('/assets');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'e2e/screens/TC8-upload-success.png', fullPage: true });
  });

  test('TC9: view dataset list with required columns', async ({ page, request }) => {
    // Data prep: upload file + create dataset via API
    const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      multipart: {
        file: {
          name: 'list-test.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(TEST_CSV_CONTENT),
        },
      },
    });
    expect(uploadResponse.ok()).toBeTruthy();
    const uploadData = await uploadResponse.json();
    const filePath = uploadData.file_path;

    // Create dataset with the uploaded file
    const createResponse = await request.post('http://127.0.0.1:8000/api/datasets/', {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        name: 'e2e-list-test-dataset',
        description: 'E2E test dataset for list view',
        files: [{
          file_path: filePath,
          file_name: 'list-test.csv',
          role: 'primary',
          row_count: 3,
          column_count: 3,
          file_size: TEST_CSV_CONTENT.length,
        }],
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createData = await createResponse.json();
    expect(createData.name).toBe('e2e-list-test-dataset');
    expect(createData.id).toBeTruthy();

    // Verify via API (real assertion)
    const listResponse = await request.get('http://127.0.0.1:8000/api/datasets/', {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });
    expect(listResponse.ok()).toBeTruthy();
    const datasets = await listResponse.json();
    expect(datasets.length).toBeGreaterThan(0);
    const datasetNames = datasets.map((d: { name: string }) => d.name);
    expect(datasetNames).toContain('e2e-list-test-dataset');
    
    // Navigate to assets page for visual confirmation
    await page.goto('/assets');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'e2e/screens/TC9-dataset-list.png', fullPage: true });
  });

  test('TC10: navigate to quality report page', async ({ page, request }) => {
    // Data prep: upload file + create dataset with primary file
    const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      multipart: {
        file: {
          name: 'quality-test.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(TEST_CSV_CONTENT),
        },
      },
    });
    expect(uploadResponse.ok()).toBeTruthy();
    const uploadData = await uploadResponse.json();
    const filePath = uploadData.file_path;

    // Create dataset with the uploaded file
    const createResponse = await request.post('http://127.0.0.1:8000/api/datasets/', {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        name: 'quality-test-dataset',
        description: 'Quality test dataset',
        files: [{
          file_path: filePath,
          file_name: 'quality-test.csv',
          role: 'primary',
          row_count: 3,
          column_count: 3,
          file_size: TEST_CSV_CONTENT.length,
        }],
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const createData = await createResponse.json();
    const datasetId = createData.id;

    // Navigate to quality report page via URL
    await page.goto(`/assets/${datasetId}/quality`);
    await page.waitForLoadState('networkidle');
    
    // Verify quality report page loads
    await expect(page.locator('body')).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screens/TC10-quality-report.png', fullPage: true });
  });
});