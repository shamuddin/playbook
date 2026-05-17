const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto('http://localhost:5175', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  await page.fill('input[type="email"]', 'demo@playbook.local');
  await page.fill('input[type="password"]', 'demo123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);

  await page.goto('http://localhost:5175/analytics');
  await page.waitForTimeout(3000);

  const info = await page.evaluate(() => {
    const headings = Array.from(document.querySelectorAll('h3')).map(h => h.textContent);
    const bodyHeight = document.body.scrollHeight;
    return { headings, bodyHeight };
  });

  console.log('Headings:', info.headings);
  console.log('Body height:', info.bodyHeight);

  await browser.close();
})();
