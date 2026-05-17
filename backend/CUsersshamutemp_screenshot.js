const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  // Navigate to frontend
  await page.goto('http://localhost:5175', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'C:\Users\shamu\screenshot_login.png', fullPage: false });
  
  // Try to login if login form exists
  const emailInput = await page.locator('input[type="email"]').first();
  if (await emailInput.isVisible().catch(() => false)) {
    await page.fill('input[type="email"]', 'demo@playbook.local');
    await page.fill('input[type="password"]', 'demo');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
  }
  
  // Screenshot Dashboard
  await page.screenshot({ path: 'C:\Users\shamu\screenshot_dashboard.png', fullPage: true });
  
  // Navigate to Incidents
  await page.click('text=Incidents');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'C:\Users\shamu\screenshot_incidents.png', fullPage: true });
  
  // Navigate to Analytics
  await page.click('text=Analytics');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'C:\Users\shamu\screenshot_analytics.png', fullPage: true });
  
  // Navigate to Agent Health
  await page.click('text=Agent Health');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'C:\Users\shamu\screenshot_agenthealth.png', fullPage: true });
  
  await browser.close();
  console.log('Screenshots saved');
})();
