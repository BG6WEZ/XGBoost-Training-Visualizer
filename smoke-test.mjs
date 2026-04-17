import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const rootDir = process.cwd();
const evidenceDir = path.join(rootDir, 'docs', 'tasks', 'M7', 'evidence', 't40');
const webBaseUrl = process.env.WEB_BASE_URL || 'http://127.0.0.1:3000';
const apiBaseUrl = process.env.API_BASE_URL || 'http://127.0.0.1:8000';

fs.mkdirSync(evidenceDir, { recursive: true });

function buildEvidencePath(fileName) {
  return path.join(evidenceDir, fileName);
}

async function main() {
  const results = {
    webBaseUrl,
    apiBaseUrl,
    screenshots: [],
    apiCalls: [],
    tests: [],
    passed: 0,
    failed: 0,
  };

  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      channel: 'msedge',
    });
  } catch {
    browser = await chromium.launch({ headless: true });
  }
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('response', async (response) => {
    const url = response.url();
    if (!url.includes('/api/')) {
      return;
    }

    const request = response.request();
    let body = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    results.apiCalls.push({
      url,
      method: request.method(),
      status: response.status(),
      body,
    });
  });

  try {
    console.log('=== T40 浏览器冒烟测试 ===');
    console.log(`Web Base URL: ${webBaseUrl}`);
    console.log(`API Base URL: ${apiBaseUrl}`);
    console.log('');

    // Test 1: 登录页面加载
    console.log('Test 1: 登录页面加载...');
    try {
      await page.goto(`${webBaseUrl}/login`, { waitUntil: 'networkidle', timeout: 30000 });
      await page.locator('#username').waitFor({ state: 'visible', timeout: 10000 });
      await page.locator('#password').waitFor({ state: 'visible', timeout: 10000 });
      await page.getByRole('button', { name: '登录' }).waitFor({ state: 'visible', timeout: 10000 });
      const screenshotPath = buildEvidencePath('01-login-page.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push({ path: screenshotPath, note: '登录页面加载成功' });
      results.tests.push({ name: '登录页面加载', status: 'passed' });
      results.passed++;
      console.log('  ✓ 通过');
    } catch (error) {
      results.tests.push({ name: '登录页面加载', status: 'failed', error: error.message });
      results.failed++;
      console.log(`  ✗ 失败: ${error.message}`);
    }

    // Test 2: 管理员登录
    console.log('Test 2: 管理员登录...');
    try {
      await page.locator('#username').fill('admin');
      await page.locator('#password').fill('admin123');
      await page.getByRole('button', { name: '登录' }).click();
      await page.waitForURL((url) => url.pathname === '/', { timeout: 15000 });
      const screenshotPath = buildEvidencePath('02-home-after-login.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push({ path: screenshotPath, note: '管理员登录后首页' });
      results.tests.push({ name: '管理员登录', status: 'passed' });
      results.passed++;
      console.log('  ✓ 通过');
    } catch (error) {
      results.tests.push({ name: '管理员登录', status: 'failed', error: error.message });
      results.failed++;
      console.log(`  ✗ 失败: ${error.message}`);
    }

    // Test 3: 用户管理页面访问
    console.log('Test 3: 用户管理页面访问...');
    try {
      const adminNavLink = page.getByRole('link', { name: '用户管理' });
      await adminNavLink.waitFor({ state: 'visible', timeout: 10000 });
      await adminNavLink.click();
      await page.waitForURL((url) => url.pathname === '/admin/users', { timeout: 15000 });
      await page.getByRole('heading', { name: '用户管理' }).waitFor({ state: 'visible', timeout: 15000 });
      const screenshotPath = buildEvidencePath('03-admin-users-page.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push({ path: screenshotPath, note: '用户管理页面' });
      results.tests.push({ name: '用户管理页面访问', status: 'passed' });
      results.passed++;
      console.log('  ✓ 通过');
    } catch (error) {
      results.tests.push({ name: '用户管理页面访问', status: 'failed', error: error.message });
      results.failed++;
      console.log(`  ✗ 失败: ${error.message}`);
    }

    // Test 4: 数据集页面访问
    console.log('Test 4: 数据集页面访问...');
    try {
      const datasetsNavLink = page.getByRole('link', { name: '数据集' });
      await datasetsNavLink.waitFor({ state: 'visible', timeout: 10000 });
      await datasetsNavLink.click();
      await page.waitForURL((url) => url.pathname === '/datasets', { timeout: 15000 });
      await page.waitForTimeout(2000);
      const screenshotPath = buildEvidencePath('04-datasets-page.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push({ path: screenshotPath, note: '数据集页面' });
      results.tests.push({ name: '数据集页面访问', status: 'passed' });
      results.passed++;
      console.log('  ✓ 通过');
    } catch (error) {
      results.tests.push({ name: '数据集页面访问', status: 'failed', error: error.message });
      results.failed++;
      console.log(`  ✗ 失败: ${error.message}`);
    }

    // Test 5: 实验页面访问
    console.log('Test 5: 实验页面访问...');
    try {
      const experimentsNavLink = page.getByRole('link', { name: '实验' });
      await experimentsNavLink.waitFor({ state: 'visible', timeout: 10000 });
      await experimentsNavLink.click();
      await page.waitForURL((url) => url.pathname === '/experiments', { timeout: 15000 });
      await page.waitForTimeout(2000);
      const screenshotPath = buildEvidencePath('05-experiments-page.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      results.screenshots.push({ path: screenshotPath, note: '实验页面' });
      results.tests.push({ name: '实验页面访问', status: 'passed' });
      results.passed++;
      console.log('  ✓ 通过');
    } catch (error) {
      results.tests.push({ name: '实验页面访问', status: 'failed', error: error.message });
      results.failed++;
      console.log(`  ✗ 失败: ${error.message}`);
    }

    console.log('');
    console.log('=== 测试结果 ===');
    console.log(`通过: ${results.passed}`);
    console.log(`失败: ${results.failed}`);
    console.log(`总计: ${results.passed + results.failed}`);

    const jsonPath = buildEvidencePath('t40-smoke-test-results.json');
    fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));
    console.log(`\n结果已保存到: ${jsonPath}`);

  } catch (error) {
    console.error('测试执行失败:', error);
    results.error = error.message;
  } finally {
    await browser.close();
  }

  process.exit(results.failed > 0 ? 1 : 0);
}

main().catch(console.error);
