import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const rootDir = process.cwd();
const evidenceDir = path.join(rootDir, 'docs', 'tasks', 'M7', 'evidence', 't39');
const webBaseUrl = process.env.WEB_BASE_URL || 'http://127.0.0.1:3000';
const apiBaseUrl = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
const adminUsername = process.env.ADMIN_USERNAME || 'admin';
const adminPassword = process.env.ADMIN_PASSWORD || 'admin123';

fs.mkdirSync(evidenceDir, { recursive: true });

function buildEvidencePath(fileName) {
  return path.join(evidenceDir, fileName);
}

async function takeEvidence(page, name, note, results) {
  const filePath = buildEvidencePath(name);
  await page.screenshot({ path: filePath, fullPage: true });
  results.screenshots.push({ filePath, note });
}

async function login(page, username, password) {
  await page.goto(`${webBaseUrl}/login`, { waitUntil: 'networkidle' });
  await page.locator('#username').fill(username);
  await page.locator('#password').fill(password);
  await page.getByRole('button', { name: '登录' }).click();
}

async function waitForUserRow(page, username) {
  const row = page.locator('tr', { hasText: username });
  await row.waitFor({ state: 'visible', timeout: 15000 });
  return row;
}

async function main() {
  const results = {
    webBaseUrl,
    apiBaseUrl,
    createdUser: null,
    screenshots: [],
    apiCalls: [],
    evidence: [],
  };

  const createdUsername = `t39_user_${Date.now()}`;
  const createdPassword = 'T39User123!';
  const resetPassword = 'T39Reset456!';
  results.createdUser = {
    username: createdUsername,
    initialPassword: createdPassword,
    resetPassword,
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
    await login(page, adminUsername, adminPassword);
    await page.waitForURL((url) => url.pathname === '/', { timeout: 15000 });
    await takeEvidence(page, '01-admin-home.png', '管理员登录后首页', results);

    const adminNavLink = page.getByRole('link', { name: '用户管理' });
    await adminNavLink.waitFor({ state: 'visible', timeout: 10000 });
    await adminNavLink.click();
    await page.waitForURL((url) => url.pathname === '/admin/users', { timeout: 15000 });
    await page.getByRole('heading', { name: '用户管理' }).waitFor({ state: 'visible', timeout: 15000 });
    await takeEvidence(page, '02-admin-users-page.png', '管理员通过导航进入 /admin/users 页面', results);
    results.evidence.push({
      id: 'admin-route-access',
      page: '/admin/users',
      action: '管理员登录后通过侧边栏进入用户管理页',
      result: '页面成功显示用户列表和创建按钮',
    });

    await page.getByRole('button', { name: '创建用户' }).click();
    const createModal = page.locator('div.fixed.inset-0').last();
    await createModal.waitFor({ state: 'visible', timeout: 10000 });
    const modalInputs = createModal.locator('input');
    await modalInputs.nth(0).fill(createdUsername);
    await modalInputs.nth(1).fill(createdPassword);
    await createModal.locator('select').selectOption('user');
    await takeEvidence(page, '03-create-user-modal.png', '创建用户弹窗已填写表单', results);

    const createResponsePromise = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return url.pathname === '/api/admin/users' && response.request().method() === 'POST';
    }, { timeout: 15000 });
    await createModal.getByRole('button', { name: '创建' }).click();
    const createResponse = await createResponsePromise;
    const createBody = await createResponse.json();
    const createdRow = await waitForUserRow(page, createdUsername);
    await takeEvidence(page, '04-user-created-row.png', '创建用户后列表出现新用户', results);
    results.evidence.push({
      id: 'admin-create-user',
      page: '/admin/users',
      action: `管理员创建普通用户 ${createdUsername}`,
      input: {
        username: createdUsername,
        role: 'user',
      },
      apiResult: {
        status: createResponse.status(),
        username: createBody.username,
        role: createBody.role,
        userId: createBody.id,
      },
      uiResult: '用户列表中出现新建用户行',
    });

    await page.getByRole('button', { name: '登出' }).click();
    await page.waitForURL((url) => url.pathname === '/login', { timeout: 15000 });
    await login(page, createdUsername, createdPassword);
    await page.waitForURL((url) => url.pathname === '/', { timeout: 15000 });
    await page.goto(`${webBaseUrl}/admin/users`, { waitUntil: 'networkidle' });
    await page.getByText('需要管理员权限才能访问此页面').waitFor({ state: 'visible', timeout: 10000 });
    await takeEvidence(page, '05-normal-user-blocked.png', '普通用户访问 /admin/users 被前端权限提示拦截', results);
    results.evidence.push({
      id: 'normal-user-blocked',
      page: '/admin/users',
      action: `普通用户 ${createdUsername} 直接访问管理员页面`,
      result: '页面显示需要管理员权限才能访问此页面',
    });

    await page.getByRole('button', { name: '登出' }).click();
    await page.waitForURL((url) => url.pathname === '/login', { timeout: 15000 });
    await login(page, adminUsername, adminPassword);
    await page.waitForURL((url) => url.pathname === '/', { timeout: 15000 });
    await page.goto(`${webBaseUrl}/admin/users`, { waitUntil: 'networkidle' });
    const activeUserRow = await waitForUserRow(page, createdUsername);

    const disableResponsePromise = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return url.pathname === `/api/admin/users/${createBody.id}` && response.request().method() === 'PATCH';
    }, { timeout: 15000 });
    await activeUserRow.locator('button[title="禁用用户"]').click();
    const disableResponse = await disableResponsePromise;
    const disableBody = await disableResponse.json();
    await activeUserRow.getByText('禁用').waitFor({ state: 'visible', timeout: 15000 });
    await takeEvidence(page, '06-user-disabled-row.png', '禁用用户后列表状态更新为禁用', results);
    results.evidence.push({
      id: 'admin-disable-user',
      page: '/admin/users',
      action: `管理员禁用用户 ${createdUsername}`,
      apiResult: {
        status: disableResponse.status(),
        userId: disableBody.id,
        userStatus: disableBody.status,
      },
      uiResult: '用户列表状态标签变为禁用',
    });

    const resetResponsePromise = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return url.pathname === `/api/admin/users/${createBody.id}/reset-password` && response.request().method() === 'POST';
    }, { timeout: 15000 });
    await activeUserRow.locator('button[title="重置密码"]').click();
    const resetModal = page.locator('div.fixed.inset-0').last();
    await resetModal.waitFor({ state: 'visible', timeout: 10000 });
    await resetModal.locator('input').fill(resetPassword);
    await takeEvidence(page, '07-reset-password-modal.png', '重置密码弹窗已填写新密码', results);
    await resetModal.getByRole('button', { name: '重置' }).click();
    const resetResponse = await resetResponsePromise;
    const resetBody = await resetResponse.json();
    await resetModal.waitFor({ state: 'hidden', timeout: 15000 });
    await takeEvidence(page, '08-reset-password-complete.png', '重置密码请求成功后弹窗关闭', results);
    results.evidence.push({
      id: 'admin-reset-password',
      page: '/admin/users',
      action: `管理员重置用户 ${createdUsername} 的密码`,
      apiResult: {
        status: resetResponse.status(),
        message: resetBody.message,
      },
      uiResult: '重置密码弹窗关闭，页面保持可操作',
    });
  } finally {
    await browser.close();
  }

  const reportPath = buildEvidencePath('t39-playwright-results.json');
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(JSON.stringify({ reportPath, evidenceCount: results.evidence.length }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
