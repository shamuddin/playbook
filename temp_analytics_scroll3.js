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

  // Scroll to the "Incidents by Agent" heading
  await page.locator('h3:has-text("Incidents by Agent")').scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);

  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_analytics_agent_swarm.png', fullPage: false });

  await browser.close();
  console.log('Done');
})();
