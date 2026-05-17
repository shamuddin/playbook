const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  const errors = [];
  const networkErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      errors.push({ type: msg.type(), text: msg.text(), location: msg.location() });
    }
  });

  page.on('pageerror', (err) => {
    errors.push({ type: 'pageerror', text: err.message });
  });

  page.on('response', (response) => {
    if (response.status() >= 400) {
      networkErrors.push({ url: response.url(), status: response.status() });
    }
  });

  // Login
  await page.goto('http://localhost:5175', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.fill('input[type="email"]', 'demo@playbook.local');
  await page.fill('input[type="password"]', 'demo123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);

  const pages = [
    { name: 'dashboard', path: '/' },
    { name: 'incidents', path: '/incidents' },
    { name: 'incident_detail', path: '/incidents/INC-20260516-180658-272A6C12' },
    { name: 'judge', path: '/judge' },
    { name: 'agents', path: '/agents' },
    { name: 'swarm', path: '/swarm' },
    { name: 'compliance', path: '/compliance' },
    { name: 'analytics', path: '/analytics' },
    { name: 'policy_builder', path: '/policy-builder' },
    { name: 'review_queue', path: '/review-queue' },
    { name: 'settings', path: '/settings' },
    { name: 'forensics', path: '/forensics' },
  ];

  for (const p of pages) {
    console.log(`Testing: ${p.name}`);
    try {
      await page.goto(`http://localhost:5175${p.path}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2500);
      await page.screenshot({ path: `K:/Hackthon/Playbook/PlaybookRepo/e2e_${p.name}.png`, fullPage: true });
    } catch (e) {
      console.log(`ERROR on ${p.name}: ${e.message}`);
      errors.push({ type: 'navigation', text: `${p.name}: ${e.message}` });
    }
  }

  // Interactions on Incidents page
  console.log('Testing: incidents interactions');
  try {
    await page.goto('http://localhost:5175/incidents', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    // Try filter by severity
    await page.selectOption('select:has-text("All")', 'critical');
    await page.waitForTimeout(1500);
    await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/e2e_incidents_filter.png', fullPage: false });
  } catch (e) {
    errors.push({ type: 'interaction', text: `incidents filter: ${e.message}` });
  }

  // Interactions on Agent Health page
  console.log('Testing: agent health interactions');
  try {
    await page.goto('http://localhost:5175/agents', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const viewBtn = await page.locator('text=View').first();
    if (await viewBtn.isVisible().catch(() => false)) {
      await viewBtn.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/e2e_agent_click.png', fullPage: false });
    }
  } catch (e) {
    errors.push({ type: 'interaction', text: `agent health click: ${e.message}` });
  }

  // Test Simulator / Swarm launch
  console.log('Testing: simulator interactions');
  try {
    await page.goto('http://localhost:5175/swarm', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    // Try clicking on a scenario card
    const card = await page.locator('text=FX Swap Unauthorized Trade').first();
    if (await card.isVisible().catch(() => false)) {
      await card.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/e2e_swarm_select.png', fullPage: false });
    }
  } catch (e) {
    errors.push({ type: 'interaction', text: `simulator click: ${e.message}` });
  }

  await browser.close();

  fs.writeFileSync('K:/Hackthon/Playbook/PlaybookRepo/e2e_errors.json', JSON.stringify({ errors, networkErrors }, null, 2));
  console.log('Test complete. Errors written to e2e_errors.json');
})();
