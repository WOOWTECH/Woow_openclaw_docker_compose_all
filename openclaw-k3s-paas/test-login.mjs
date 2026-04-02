import { chromium } from 'playwright';

const URL = 'https://cindytech1-openclaw.woowtech.io/#token=woowtech';

(async () => {
  console.log('=== OpenClaw Token Auth Login Test ===');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('websocket', ws => {
    console.log(`  [WS] opened: ${ws.url()}`);
    ws.on('close', () => console.log('  [WS] closed'));
  });

  console.log(`\n[1] Opening ${URL}`);
  await page.goto(URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000);

  await page.screenshot({ path: '/tmp/openclaw-token-1.png', fullPage: true });

  const body = await page.textContent('body');
  const inputs = await page.$$('input');
  for (let i = 0; i < inputs.length; i++) {
    const val = await inputs[i].inputValue();
    const ph = await inputs[i].getAttribute('placeholder');
    console.log(`  Input ${i}: value="${val}" ph="${ph}"`);
  }

  if (body.includes('pairing')) {
    console.log('\n  RESULT: pairing required');
  } else if (body.includes('unauthorized') || body.includes('password')) {
    console.log('\n  RESULT: unauthorized/password error');
  } else if (body.includes('Connect') || body.includes('連接')) {
    console.log('\n  RESULT: still on login page (no error yet)');
  } else {
    console.log('\n  RESULT: SUCCESS!');
  }

  await browser.close();
})();
