export default {
  testDir: '.',
  timeout: 60000,
  retries: 1,
  use: {
    headless: true,
    browserName: 'chromium',
    baseURL: 'https://cindytech1-openclaw.woowtech.io',
    ignoreHTTPSErrors: true,
  },
};
