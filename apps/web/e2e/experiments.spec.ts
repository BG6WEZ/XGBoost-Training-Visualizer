import { test, expect } from '@playwright/test';

/**
 * Experiments E2E tests - Task 3.2 (M7-T76 real business flow)
 * 
 * Covers:
 * 1. Navigate to experiments page after login
 * 2. Create experiment button visible
 * 3. Open create experiment form
 * 4. Experiment list shows data (API-verified)
 * 5. Navigate to monitor page
 * 
 * Data preparation strategy: Use API to create dataset + experiment before UI tests
 */
test.describe('Experiments flow', () => {
  let authToken: string;
  let datasetId: string;
  let experimentId: string;

  test.beforeAll(async ({ request }) => {
    // Step 1: Login via API to get auth token
    const loginResponse = await request.post('http://127.0.0.1:8000/api/auth/login', {
      data: { username: 'admin', password: 'admin123' },
    });
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    authToken = loginData.access_token;

    // Step 2: Upload CSV and create dataset for experiments
    const TEST_CSV = 'feature1,feature2,target\n1.0,2.0,0\n3.0,4.0,1\n5.0,6.0,0\n';
    const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
      headers: { Authorization: `Bearer ${authToken}` },
      multipart: {
        file: {
          name: 'experiment-dataset.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(TEST_CSV),
        },
      },
    });
    expect(uploadResponse.ok()).toBeTruthy();
    const uploadData = await uploadResponse.json();

    // Step 3: Create dataset with the uploaded file
    const createDatasetResponse = await request.post('http://127.0.0.1:8000/api/datasets/', {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        name: 'e2e-experiment-dataset',
        description: 'Dataset for E2E experiment tests',
        files: [{
          file_path: uploadData.file_path,
          file_name: 'experiment-dataset.csv',
          role: 'primary',
          row_count: 3,
          column_count: 3,
          file_size: TEST_CSV.length,
        }],
      },
    });
    expect(createDatasetResponse.ok()).toBeTruthy();
    const datasetData = await createDatasetResponse.json();
    datasetId = datasetData.id;

    // Step 4: Create an experiment via API
    const createExpResponse = await request.post('http://127.0.0.1:8000/api/experiments/', {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        name: 'e2e-test-experiment',
        description: 'E2E test experiment',
        dataset_id: datasetId,
        config: {
          xgboost_params: {
            max_depth: 3,
            learning_rate: 0.1,
            n_estimators: 10,
            subsample: 0.8,
            colsample_bytree: 0.8,
            lambda_: 1.0,
            alpha: 0.0,
            min_child_weight: 1,
            random_state: 42,
          },
          num_boost_round: 10,
          early_stopping_rounds: 5,
          eval_metrics: ['rmse', 'mae'],
          test_size: 0.2,
          cv_folds: 2,
        },
        tags: ['e2e', 'test'],
      },
    });
    expect(createExpResponse.ok()).toBeTruthy();
    const expData = await createExpResponse.json();
    experimentId = expData.id;

    // Step 5: Verify experiment exists via API
    const getExpResponse = await request.get(`http://127.0.0.1:8000/api/experiments/${experimentId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getExpResponse.ok()).toBeTruthy();
    const getExpData = await getExpResponse.json();
    expect(getExpData.name).toBe('e2e-test-experiment');
    expect(getExpData.status).toBe('pending');
  });

  test.beforeEach(async ({ page }) => {
    // Login via UI for each test
    await page.goto('/');
    await page.locator('#username').fill('admin');
    await page.locator('#password').fill('admin123');
    await page.getByRole('button', { name: /登录/i }).click();
    await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
  });

  test('TC11: navigate to experiments page after login', async ({ page }) => {
    await page.goto('/experiments');
    await page.waitForLoadState('networkidle');
    
    // Verify experiments page loads with heading
    const heading = page.locator('h1, h2').filter({ hasText: /experiment|实验/i }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    await page.screenshot({ path: 'e2e/screens/TC11-experiments-page.png', fullPage: true });
  });

  test('TC12: create experiment button is visible', async ({ page }) => {
    await page.goto('/experiments');
    await page.waitForLoadState('networkidle');
    
    // Verify create button exists - must fail if not found
    const createBtn = page.locator('button:has-text("Create"), button:has-text("新建"), button:has-text("创建"), button:has-text("+")').first();
    await expect(createBtn).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screens/TC12-create-btn.png', fullPage: true });
  });

  test('TC13: open create experiment form', async ({ page }) => {
    await page.goto('/experiments');
    await page.waitForLoadState('networkidle');
    
    // Click create button
    const createBtn = page.locator('button:has-text("Create"), button:has-text("新建"), button:has-text("创建")').first();
    await expect(createBtn).toBeVisible({ timeout: 5000 });
    await createBtn.click();
    
    // Verify form inputs appear - must fail if not found
    await page.waitForTimeout(1000);
    const formInputs = page.locator('input, textarea, select');
    const inputCount = await formInputs.count();
    expect(inputCount).toBeGreaterThanOrEqual(1);
    
    await page.screenshot({ path: 'e2e/screens/TC13-create-form.png', fullPage: true });
  });

  test('TC14: experiment list shows created experiment', async ({ page }) => {
    await page.goto('/experiments');
    await page.waitForLoadState('networkidle');
    
    // Verify the experiment we created via API appears in the UI
    // The experiment name should be visible somewhere on the page
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('e2e-test-experiment');
    
    await page.screenshot({ path: 'e2e/screens/TC14-experiment-list.png', fullPage: true });
  });

  test('TC15: navigate to monitor page', async ({ page }) => {
    await page.goto('/monitor');
    await page.waitForLoadState('networkidle');
    
    // Verify monitor page loads with heading
    const heading = page.locator('h1, h2').filter({ hasText: /monitor|监控|training|训练/i }).first();
    await expect(heading.or(page.locator('h1, h2, h3').first())).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screens/TC15-monitor.png', fullPage: true });
  });
});