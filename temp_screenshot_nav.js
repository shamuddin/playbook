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

  // Dashboard
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_dashboard.png', fullPage: true });

  // Incidents
  await page.goto('http://localhost:5175/incidents');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_incidents.png', fullPage: true });

  // Incident Detail (first one if exists)
  const firstRow = await page.locator('table tbody tr').first();
  if (await firstRow.isVisible().catch(() => false)) {
    await firstRow.click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_incident_detail.png', fullPage: true });
    await page.goto('http://localhost:5175/incidents');
    await page.waitForTimeout(1500);
  }

  // Analytics
  await page.goto('http://localhost:5175/analytics');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_analytics.png', fullPage: true });

  // Agent Health
  await page.goto('http://localhost:5175/agents');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_agenthealth.png', fullPage: true });

  // Agent Swarm
  await page.goto('http://localhost:5175/swarm');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_agentswarm.png', fullPage: true });

  // Compliance
  await page.goto('http://localhost:5175/compliance');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_compliance.png', fullPage: true });

  await browser.close();
  console.log('All screenshots saved');
})();
