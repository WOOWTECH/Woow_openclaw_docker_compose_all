export default {
  testDir: '.',
  timeout: 60000,
  retries: 1,
  reporter: [['html', { open: 'never', outputFolder: '/tmp/hermes-playwright-report' }], ['list']],
  use: {
    headless: true,
    baseURL: process.env.HERMES_TEST_URL || 'http://localhost:18787',
    ignoreHTTPSErrors: true,
    screenshot: 'on',
    video: 'retain-on-failure',
    viewport: { width: 1280, height: 720 },
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
};
