const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto('http://localhost:5175', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  const html = await page.content();
  fs.writeFileSync('K:/Hackthon/Playbook/PlaybookRepo/page_content.html', html);

  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_initial.png', fullPage: true });
  console.log('Initial screenshot saved');

  await browser.close();
})();
