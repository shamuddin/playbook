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

  // Navigate to Incidents using sidebar link
  await page.getByRole('link', { name: /Incidents/i }).first().click();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_incidents.png', fullPage: true });

  // Navigate to Analytics
  await page.getByRole('link', { name: /Analytics/i }).first().click();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_analytics.png', fullPage: true });

  // Navigate to Agent Health
  await page.getByRole('link', { name: /Agent Health/i }).first().click();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_agenthealth.png', fullPage: true });

  // Navigate to Agent Swarm
  await page.getByRole('link', { name: /Agent Swarm/i }).first().click();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_agentswarm.png', fullPage: true });

  // Navigate to Compliance
  await page.getByRole('link', { name: /Compliance/i }).first().click();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/screenshot_compliance.png', fullPage: true });

  await browser.close();
  console.log('All screenshots saved');
})();
