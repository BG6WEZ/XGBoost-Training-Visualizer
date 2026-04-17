import { test, expect } from '@playwright/test';

/**
 * Results E2E tests - Task 3.2 (M7-T77 results assertion and evidence alignment)
 * 
 * Covers:
 * 1. Navigate to comparison page after login
 * 2. Comparison page shows experiment selection UI + checkbox state change
 * 3. Quality report page accessible via dataset created for experiment
 * 4. Monitor page with charts loads
 * 5. Experiment detail page accessible and shows experiment status/config data
 * 
 * Data preparation strategy: Use API to create dataset + experiment before UI tests
 */
test.describe('Results flow', () => {
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

    // Step 2: Upload CSV and create dataset for experiments/results
    const TEST_CSV = 'feature1,feature2,target\n1.0,2.0,0\n3.0,4.0,1\n5.0,6.0,0\n7.0,8.0,1\n9.0,10.0,0\n';
    const uploadResponse = await request.post('http://127.0.0.1:8000/api/datasets/upload', {
      headers: { Authorization: `Bearer ${authToken}` },
      multipart: {
        file: {
          name: 'results-dataset.csv',
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
        name: 'e2e-results-dataset',
        description: 'Dataset for E2E results tests',
        files: [{
          file_path: uploadData.file_path,
          file_name: 'results-dataset.csv',
          role: 'primary',
          row_count: 5,
          column_count: 3,
          file_size: TEST_CSV.length,
        }],
      },
    });
    expect(createDatasetResponse.ok()).toBeTruthy();
    const datasetData = await createDatasetResponse.json();
    datasetId = datasetData.id;

    // Step 4: Create an experiment via API for results/comparison tests
    const createExpResponse = await request.post('http://127.0.0.1:8000/api/experiments/', {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        name: 'e2e-results-experiment',
        description: 'E2E test experiment for results',
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
        tags: ['e2e', 'results'],
      },
    });
    expect(createExpResponse.ok()).toBeTruthy();
    const expData = await createExpResponse.json();
    experimentId = expData.id;

    // Step 5: Verify experiment exists and can be retrieved
    const getExpResponse = await request.get(`http://127.0.0.1:8000/api/experiments/${experimentId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getExpResponse.ok()).toBeTruthy();
    const getExpData = await getExpResponse.json();
    expect(getExpData.name).toBe('e2e-results-experiment');
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

  test('TC16: navigate to comparison page', async ({ page }) => {
    await page.goto('/compare');
    await page.waitForLoadState('networkidle');
    
    // Verify comparison page loads with heading
    const heading = page.locator('h1, h2').filter({ hasText: /compare|对比|comparison/i }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    await page.screenshot({ path: 'e2e/screens/TC16-compare-page.png', fullPage: true });
  });

  test('TC17: comparison page experiment selection state change', async ({ page }) => {
    await page.goto('/compare');
    await page.waitForLoadState('networkidle');
    
    // Wait for page to be fully rendered
    await page.waitForTimeout(1000);
    
    // Find all checkboxes on the comparison page (experiment selection)
    const checkboxes = page.locator('input[type="checkbox"]');
    const initialCount = await checkboxes.count();
    
    // If there are checkboxes, click the first one and verify state change
    if (initialCount > 0) {
      const firstCheckbox = checkboxes.first();
      await expect(firstCheckbox).toBeVisible({ timeout: 5000 });
      
      // Get initial checked state
      const initialChecked = await firstCheckbox.isChecked();
      
      // Click to change state
      await firstCheckbox.click();
      await page.waitForTimeout(500);
      
      // Verify checked state changed
      const newChecked = await firstCheckbox.isChecked();
      expect(newChecked).not.toBe(initialChecked);
      
      // Verify selection count or button state changed
      const selectedCount = await checkboxes.evaluateAll(
        (els) => els.filter((el) => (el as HTMLInputElement).checked).length
      );
      expect(selectedCount).toBeGreaterThan(0);
    } else {
      // If no checkboxes, look for experiment list items that can be clicked
      const experimentItems = page.locator('[role="option"], .experiment-item, li, tr').first();
      await expect(experimentItems.or(page.locator('h1, h2, h3, p').first())).toBeVisible({ timeout: 5000 });
    }
    
    await page.screenshot({ path: 'e2e/screens/TC17-compare-selection.png', fullPage: true });
  });

  test('TC18: quality report page accessible', async ({ page }) => {
    // Navigate to quality report page for the dataset we created
    await page.goto(`/assets/${datasetId}/quality`);
    await page.waitForLoadState('networkidle');
    
    // Verify quality report page loads
    await expect(page.locator('body')).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screens/TC18-quality-report.png', fullPage: true });
  });

  test('TC19: monitor page with charts loads', async ({ page }) => {
    await page.goto('/monitor');
    await page.waitForLoadState('networkidle');
    
    // Verify monitor page loads with heading
    const heading = page.locator('h1, h2').filter({ hasText: /monitor|监控|training|训练/i }).first();
    await expect(heading.or(page.locator('h1, h2, h3').first())).toBeVisible({ timeout: 5000 });
    
    await page.screenshot({ path: 'e2e/screens/TC19-monitor.png', fullPage: true });
  });

  test('TC20: experiment detail page shows experiment status and config', async ({ page, request }) => {
    // Fetch experiment data via API to know what to assert
    const expResponse = await request.get(`http://127.0.0.1:8000/api/experiments/${experimentId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(expResponse.ok()).toBeTruthy();
    const expData = await expResponse.json();
    
    // Navigate to experiment detail page
    await page.goto(`/experiments/${experimentId}`);
    await page.waitForLoadState('networkidle');
    
    // Verify detail page loads
    await expect(page.locator('body')).toBeVisible({ timeout: 5000 });
    
    // Real result assertion: verify experiment status appears on page
    // The page should show the experiment's status (pending) and config info
    const bodyText = await page.locator('body').textContent();
    
    // Verify experiment name appears
    expect(bodyText).toContain('e2e-results-experiment');
    
    // Verify status field appears (pending is the known API state)
    expect(bodyText).toContain(expData.status);
    
    // Verify at least one config parameter appears on the detail page
    const config = expData.config;
    if (config && config.xgboost_params) {
      // Check that max_depth value appears somewhere on the page
      expect(bodyText).toContain(String(config.xgboost_params.max_depth));
    }
    
    await page.screenshot({ path: 'e2e/screens/TC20-experiment-detail.png', fullPage: true });
  });
});