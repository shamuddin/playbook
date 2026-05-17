const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto('http://localhost:5175', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Login
  await page.fill('input[type="email"]', 'demo@playbook.local');
  await page.fill('input[type="password"]', 'demo123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);

  // Helper to screenshot a page by clicking sidebar
  const screenshotPage = async (name, labelRegex, path) => {
    try {
      // Try to find sidebar link by text content
      const link = await page.locator('a').filter({ hasText: labelRegex }).first();
      if (await link.isVisible().catch(() => false)) {
        await link.click();
      } else {
        // fallback: navigate via URL and inject token
        const token = await page.evaluate(() => localStorage.getItem('playbook_token'));
        await page.goto(`http://localhost:5175${path}`, { waitUntil: 'networkidle' });
        if (token) {
          await page.evaluate((t) => localStorage.setItem('playbook_token', t), token);
          await page.goto(`http://localhost:5175${path}`, { waitUntil: 'networkidle' });
        }
      }
      await page.waitForTimeout(2500);
      await page.screenshot({ path: `K:/Hackthon/Playbook/PlaybookRepo/screenshot_${name}.png`, fullPage: true });
    } catch (e) {
      console.log(`Error on ${name}:`, e.message);
    }
  };

  await screenshotPage('analytics', /Analytics/, '/analytics');
  await screenshotPage('agenthealth', /Agent Health/, '/agents');
  await screenshotPage('agentswarm', /Agent Swarm/, '/swarm');
  await screenshotPage('compliance', /Compliance/, '/compliance');

  await browser.close();
  console.log('Done');
})();
