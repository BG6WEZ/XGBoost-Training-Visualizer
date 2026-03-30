const { chromium } = require('playwright');
const fs = require('fs');

async function main() {
  const browser = await chromium.launch({
    headless: false,
    channel: 'msedge'
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  const results = {
    steps: [],
    verifiedPages: [],
    unverifiedPages: [],
    apiCalls: []
  };

  // 监听网络请求
  page.on('response', async (response) => {
    if (response.url().includes('localhost:8000')) {
      try {
        const request = response.request();
        let body = null;
        try {
          body = await response.json();
        } catch (e) {
          // 不是 JSON 响应
        }
        results.apiCalls.push({
          url: response.url(),
          method: request.method(),
          status: response.status(),
          body: body
        });
      } catch (e) {
        // 忽略错误
      }
    }
  });

  try {
    // 步骤 1: 扫描资产
    console.log('\n=== 步骤 1: 扫描资产 ===');
    await page.goto('http://localhost:3000/assets', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'screenshot-1-assets-page.png', fullPage: true });
    console.log('已导航到 /assets 页面');

    // 查找扫描按钮
    const scanButton = await page.locator('button:has-text("扫描 dataset")').first();
    if (await scanButton.isVisible()) {
      await scanButton.click();
      console.log('已点击扫描按钮');
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'screenshot-2-after-scan.png', fullPage: true });
      results.steps.push({ step: 1, status: 'success', description: '扫描资产完成' });
    } else {
      console.log('未找到扫描按钮');
      results.steps.push({ step: 1, status: 'warning', description: '未找到扫描按钮' });
    }

    // 步骤 2: 登记数据集
    console.log('\n=== 步骤 2: 登记数据集 ===');
    await page.waitForTimeout(1000);

    // 查找未登记的资产
    const registerButton = await page.locator('button:has-text("登记"):not(:has-text("已登记"))').first();
    if (await registerButton.isVisible()) {
      await registerButton.click();
      console.log('已点击登记按钮');
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'screenshot-3-after-register.png', fullPage: true });
      results.steps.push({ step: 2, status: 'success', description: '登记数据集完成' });
    } else {
      console.log('未找到登记按钮');
      results.steps.push({ step: 2, status: 'warning', description: '未找到登记按钮' });
    }

    // 步骤 3: 发起切分
    console.log('\n=== 步骤 3: 发起切分 ===');
    // 切换到已登记数据集标签
    const registeredTab = await page.locator('button:has-text("已登记数据集")').first();
    if (await registeredTab.isVisible()) {
      await registeredTab.click();
      console.log('已切换到已登记数据集标签');
      await page.waitForTimeout(1000);
    }

    // 查找数据集详情链接
    const datasetLink = await page.locator('a[href^="/assets/"]').first();
    if (await datasetLink.isVisible()) {
      await datasetLink.click();
      console.log('已进入数据集详情页');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshot-4-dataset-detail.png', fullPage: true });

      // 查找切分按钮
      const splitButton = await page.locator('button:has-text("切分")').first();
      if (await splitButton.isVisible()) {
        await splitButton.click();
        console.log('已点击切分按钮');
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'screenshot-5-after-split.png', fullPage: true });
        results.steps.push({ step: 3, status: 'success', description: '数据切分完成' });
      } else {
        console.log('未找到切分按钮');
        results.steps.push({ step: 3, status: 'warning', description: '未找到切分按钮' });
      }
    } else {
      console.log('未找到数据集详情链接');
      results.steps.push({ step: 3, status: 'warning', description: '未找到数据集详情链接' });
    }

    // 步骤 4: 创建实验
    console.log('\n=== 步骤 4: 创建实验 ===');
    await page.goto('http://localhost:3000/experiments', { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'screenshot-6-experiments-page.png', fullPage: true });
    console.log('已导航到 /experiments 页面');

    const createExpButton = await page.locator('button:has-text("创建"), button:has-text("新建")').first();
    if (await createExpButton.isVisible()) {
      await createExpButton.click();
      console.log('已点击创建实验按钮');
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'screenshot-7-create-experiment.png', fullPage: true });

      // 填写实验表单（如果有）
      const nameInput = await page.locator('input[name="name"], input[placeholder*="名称"], input[placeholder*="name"]').first();
      if (await nameInput.isVisible()) {
        await nameInput.fill('Test Experiment ' + Date.now());
        console.log('已填写实验名称');
      }

      // 提交表单
      const submitButton = await page.locator('button[type="submit"], button:has-text("确定"), button:has-text("提交"), button:has-text("创建")').first();
      if (await submitButton.isVisible()) {
        await submitButton.click();
        console.log('已提交实验表单');
        await page.waitForTimeout(2000);
      }

      results.steps.push({ step: 4, status: 'success', description: '创建实验完成' });
    } else {
      console.log('未找到创建实验按钮');
      results.steps.push({ step: 4, status: 'warning', description: '未找到创建实验按钮' });
    }

    // 步骤 5: 启动实验
    console.log('\n=== 步骤 5: 启动实验 ===');
    await page.waitForTimeout(1000);
    const startButton = await page.locator('button:has-text("启动"), button:has-text("Start"), button:has-text("训练")').first();
    if (await startButton.isVisible()) {
      await startButton.click();
      console.log('已点击启动训练按钮');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshot-8-start-experiment.png', fullPage: true });
      results.steps.push({ step: 5, status: 'success', description: '启动实验完成' });
    } else {
      console.log('未找到启动按钮');
      results.steps.push({ step: 5, status: 'warning', description: '未找到启动按钮' });
    }

    // 步骤 6: 查看训练状态与结果
    console.log('\n=== 步骤 6: 查看训练状态与结果 ===');

    // 查看监控页
    await page.goto('http://localhost:3000/monitor', { waitUntil: 'networkidle' });
    console.log('已导航到监控页');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshot-9-monitor-page.png', fullPage: true });
    results.verifiedPages.push('/monitor');

    // 查看实验详情页
    await page.goto('http://localhost:3000/experiments', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    const expDetailLink = await page.locator('a[href^="/experiments/"]').first();
    if (await expDetailLink.isVisible()) {
      await expDetailLink.click();
      console.log('已进入实验详情页');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshot-10-experiment-detail.png', fullPage: true });
      results.verifiedPages.push('/experiments/[id]');
      results.steps.push({ step: 6, status: 'success', description: '查看训练状态与结果完成' });
    } else {
      results.steps.push({ step: 6, status: 'warning', description: '未找到实验详情链接' });
    }

  } catch (error) {
    console.error('执行过程中出错:', error);
    results.error = error.message;
  } finally {
    await browser.close();
  }

  // 保存结果
  fs.writeFileSync('test-results.json', JSON.stringify(results, null, 2));
  console.log('\n=== 测试结果 ===');
  console.log(JSON.stringify(results, null, 2));

  return results;
}

main().catch(console.error);
