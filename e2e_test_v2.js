const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  const errors = [];
  const networkErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push({ type: msg.type(), text: msg.text() });
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
    { name: 'review', path: '/review' },
    { name: 'settings', path: '/settings' },
  ];

  for (const p of pages) {
    console.log(`Testing: ${p.name}`);
    try {
      await page.goto(`http://localhost:5175${p.path}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2500);
      await page.screenshot({ path: `K:/Hackthon/Playbook/PlaybookRepo/e2e_v2_${p.name}.png`, fullPage: true });
    } catch (e) {
      errors.push({ type: 'navigation', text: `${p.name}: ${e.message}` });
    }
  }

  // Interactions
  console.log('Testing: incidents filter');
  try {
    await page.goto('http://localhost:5175/incidents', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    // Use label-based selector for severity filter
    const severitySelect = await page.locator('label:has-text("Severity") + select, select:has(~ option[value="critical"])').first();
    if (await severitySelect.isVisible().catch(() => false)) {
      await severitySelect.selectOption('critical');
      await page.waitForTimeout(1500);
      await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/e2e_v2_incidents_filter.png', fullPage: false });
    }
  } catch (e) {
    errors.push({ type: 'interaction', text: `incidents filter: ${e.message}` });
  }

  console.log('Testing: agent health click');
  try {
    await page.goto('http://localhost:5175/agents', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const viewBtn = await page.locator('text=View').first();
    if (await viewBtn.isVisible().catch(() => false)) {
      await viewBtn.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/e2e_v2_agent_click.png', fullPage: false });
    }
  } catch (e) {
    errors.push({ type: 'interaction', text: `agent health click: ${e.message}` });
  }

  console.log('Testing: simulator select');
  try {
    await page.goto('http://localhost:5175/swarm', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const card = await page.locator('text=FX Swap Unauthorized Trade').first();
    if (await card.isVisible().catch(() => false)) {
      await card.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'K:/Hackthon/Playbook/PlaybookRepo/e2e_v2_swarm_select.png', fullPage: false });
    }
  } catch (e) {
    errors.push({ type: 'interaction', text: `simulator click: ${e.message}` });
  }

  await browser.close();

  fs.writeFileSync('K:/Hackthon/Playbook/PlaybookRepo/e2e_v2_errors.json', JSON.stringify({ errors, networkErrors }, null, 2));
  console.log('Test complete. Errors written to e2e_v2_errors.json');
})();
