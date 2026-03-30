import { chromium } from 'playwright';

(async () => {
  console.log('正在启动 Chromium 浏览器...');
  const browser = await chromium.launch({ headless: true });
  console.log('浏览器启动成功！');

  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('正在访问测试页面...');
  await page.goto('https://www.example.com');
  const title = await page.title();

  console.log(`页面标题: ${title}`);
  console.log('测试成功！浏览器工作正常。');

  await browser.close();
  console.log('浏览器已关闭。');
})();
