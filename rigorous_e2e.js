const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  const issues = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      // Ignore expected 401 from login wrong-password test
      if (text.includes('401') && text.includes('Unauthorized') && currentPage === 'login') return;
      issues.push({ kind: 'console-error', text, page: currentPage });
    }
  });
  page.on('pageerror', (err) => {
    issues.push({ kind: 'page-error', text: err.message, page: currentPage });
  });
  page.on('response', (response) => {
    if (response.status() >= 400 && !response.url().includes('.js') && !response.url().includes('.css')) {
      // Ignore expected 401 from login wrong-password test
      if (response.url().includes('/auth/login') && response.status() === 401) return;
      issues.push({ kind: 'network-error', url: response.url(), status: response.status(), page: currentPage });
    }
  });

  let currentPage = '';
  const screenshot = async (name) => {
    try {
      await page.screenshot({ path: `K:/Hackthon/Playbook/PlaybookRepo/rigorous_${name}.png`, fullPage: true });
    } catch (e) {
      issues.push({ kind: 'screenshot-fail', text: `${name}: ${e.message}`, page: currentPage });
    }
  };
  const act = async (desc, fn) => {
    try {
      await fn();
    } catch (e) {
      issues.push({ kind: 'interaction-fail', text: `${desc}: ${e.message}`, page: currentPage });
    }
  };

  // Clear any existing auth and force login page
  await page.goto('http://localhost:5175/login', { waitUntil: 'networkidle' });
  await page.evaluate(() => localStorage.clear());
  await page.goto('http://localhost:5175/login', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // ===== 1. LOGIN =====
  currentPage = 'login';
  await screenshot('01_login');

  await act('empty submit', async () => {
    await page.fill('input[type="email"]', '');
    await page.fill('input[type="password"]', '');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(800);
    await screenshot('01_login_empty');
  });

  await act('wrong password', async () => {
    await page.goto('http://localhost:5175/login', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.fill('input[type="email"]', 'demo@playbook.local');
    await page.fill('input[type="password"]', 'wrong');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1500);
    await screenshot('01_login_wrong');
  });

  await act('correct login', async () => {
    await page.goto('http://localhost:5175/login', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.fill('input[type="email"]', 'demo@playbook.local');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2500);
    await screenshot('02_dashboard');
  });

  // ===== 2. DASHBOARD =====
  currentPage = 'dashboard';
  const dashWidgets = ['Total Incidents', 'Critical Alerts', 'Agent Health', 'Judge Decisions'];
  for (const w of dashWidgets) {
    const visible = await page.locator(`text=${w}`).first().isVisible().catch(() => false);
    if (!visible) issues.push({ kind: 'missing-widget', text: w, page: currentPage });
  }

  // ===== 3. INCIDENTS =====
  currentPage = 'incidents';
  await page.goto('http://localhost:5175/incidents', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('03_incidents');

  await act('search AGT-DEL', async () => {
    const input = await page.locator('input[type="text"]').first();
    if (await input.isVisible().catch(() => false)) {
      await input.fill('AGT-DEL');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);
      await screenshot('03_incidents_search');
      await input.fill('');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);
    }
  });

  await act('status filter', async () => {
    const selects = await page.locator('select').all();
    if (selects[0] && await selects[0].isVisible().catch(() => false)) {
      await selects[0].selectOption('detected');
      await page.waitForTimeout(1200);
      await screenshot('03_incidents_status_filter');
    }
  });

  await act('severity filter', async () => {
    const selects = await page.locator('select').all();
    if (selects[1] && await selects[1].isVisible().catch(() => false)) {
      await selects[1].selectOption('critical');
      await page.waitForTimeout(1200);
      await screenshot('03_incidents_severity_filter');
    }
  });

  await act('click first incident row', async () => {
    const row = await page.locator('table tbody tr').first();
    if (await row.isVisible().catch(() => false)) {
      await row.click();
      await page.waitForTimeout(2000);
      await screenshot('04_incident_detail');
      await page.evaluate(() => window.scrollBy(0, 600));
      await page.waitForTimeout(500);
      await screenshot('04_incident_detail_bottom');
      await page.goto('http://localhost:5175/incidents', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);
    }
  });

  // ===== 4. JUDGE LAYER =====
  currentPage = 'judge';
  await page.goto('http://localhost:5175/judge', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('05_judge');

  // ===== 5. AGENT HEALTH =====
  currentPage = 'agent-health';
  await page.goto('http://localhost:5175/agents', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('06_agent_health');

  await act('agent search', async () => {
    const input = await page.locator('input[type="text"]').first();
    if (await input.isVisible().catch(() => false)) {
      await input.fill('support');
      await page.waitForTimeout(1000);
      await screenshot('06_agent_health_search');
    }
  });

  await act('agent view click', async () => {
    const btn = await page.locator('button:has-text("View")').first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(1500);
      await screenshot('06_agent_health_view_click');
      await page.goto('http://localhost:5175/agents');
      await page.waitForTimeout(1500);
    }
  });

  // ===== 6. SIMULATOR / AGENT SWARM =====
  currentPage = 'simulator';
  await page.goto('http://localhost:5175/swarm', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('07_simulator');

  await act('select scenarios', async () => {
    const scenarios = ['FX Swap', 'Data Exfiltration', 'Prompt Injection', 'Full 3-Agent'];
    for (let i = 0; i < scenarios.length; i++) {
      const card = await page.locator(`text=${scenarios[i]}`).first();
      if (await card.isVisible().catch(() => false)) {
        await card.click();
        await page.waitForTimeout(800);
        await screenshot(`07_simulator_select_${i}`);
      }
    }
  });

  // ===== 7. COMPLIANCE =====
  currentPage = 'compliance';
  await page.goto('http://localhost:5175/compliance', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('08_compliance');

  await act('change framework', async () => {
    const select = await page.locator('select').first();
    if (await select.isVisible().catch(() => false)) {
      const options = await select.locator('option').allTextContents();
      if (options.some((o) => o.includes('NIST'))) {
        await select.selectOption({ label: options.find((o) => o.includes('NIST')) });
        await page.waitForTimeout(1500);
        await screenshot('08_compliance_nist');
      }
    }
  });

  // ===== 8. ANALYTICS =====
  currentPage = 'analytics';
  await page.goto('http://localhost:5175/analytics', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('09_analytics');

  await act('change period', async () => {
    const select = await page.locator('select').first();
    if (await select.isVisible().catch(() => false)) {
      await select.selectOption('30d');
      await page.waitForTimeout(2000);
      await screenshot('09_analytics_30d');
    }
  });

  await act('scroll analytics', async () => {
    await page.evaluate(() => window.scrollBy(0, 1200));
    await page.waitForTimeout(500);
    await screenshot('09_analytics_bottom');
  });

  // ===== 9. POLICY BUILDER =====
  currentPage = 'policy-builder';
  await page.goto('http://localhost:5175/policy-builder', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('10_policy_builder');

  await act('checkbox click', async () => {
    const cb = await page.locator('input[type="checkbox"]').first();
    if (await cb.isVisible().catch(() => false)) {
      await cb.click();
      await page.waitForTimeout(500);
      await screenshot('10_policy_builder_checkbox');
    }
  });

  await act('compare templates', async () => {
    const select = await page.locator('select').first();
    if (await select.isVisible().catch(() => false)) {
      const opts = await select.locator('option').all();
      if (opts.length > 1) {
        const secondValue = await opts[1].getAttribute('value');
        await select.selectOption(secondValue);
        const btn = await page.locator('button:has-text("Compare Templates")').first();
        if (await btn.isVisible().catch(() => false)) {
          await btn.click();
          await page.waitForTimeout(1500);
          await screenshot('10_policy_builder_compare');
        }
      }
    }
  });

  // ===== 10. REVIEW QUEUE =====
  currentPage = 'review-queue';
  await page.goto('http://localhost:5175/review', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('11_review_queue');

  await act('approve first item', async () => {
    const btn = await page.locator('button[title="Approve"]').first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(1000);
      await screenshot('11_review_queue_approve');
    }
  });

  // ===== 11. SETTINGS =====
  currentPage = 'settings';
  await page.goto('http://localhost:5175/settings', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await screenshot('12_settings');

  // ===== 12. FORENSICS (via incident detail) =====
  currentPage = 'forensics';
  await page.goto('http://localhost:5175/incidents/INC-20260516-180658-272A6C12', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  await act('scroll to forensics', async () => {
    await page.evaluate(() => window.scrollBy(0, 1200));
    await page.waitForTimeout(500);
    const forensics = await page.locator('text=Forensics Evidence Package').first();
    if (await forensics.isVisible().catch(() => false)) {
      await screenshot('13_forensics');
    } else {
      issues.push({ kind: 'missing-element', text: 'Forensics Evidence Package not found', page: currentPage });
      await screenshot('13_forensics_missing');
    }
  });

  // ===== 13. NOTIFICATIONS =====
  currentPage = 'notifications';
  await page.goto('http://localhost:5175/dashboard', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await act('open notifications', async () => {
    const bell = await page.locator('button[aria-label="Notifications"]').first();
    if (await bell.isVisible().catch(() => false)) {
      await bell.click();
      await page.waitForTimeout(1000);
      await screenshot('14_notifications');
    }
  });

  // ===== 14. LOGOUT =====
  currentPage = 'logout';
  await act('logout', async () => {
    const btn = await page.locator('button[aria-label="Logout"]').first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(2000);
      await screenshot('15_logout');
    }
  });

  await browser.close();

  fs.writeFileSync('K:/Hackthon/Playbook/PlaybookRepo/rigorous_issues.json', JSON.stringify(issues, null, 2));
  console.log('Rigorous test complete. Issues:', issues.length);
  issues.forEach((i) => console.log(`[${i.kind}] ${i.page}: ${i.text || i.url}`));
})();
