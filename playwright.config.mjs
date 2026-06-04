import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60000,
  retries: 1,
  use: {
    headless: true,
    baseURL: 'https://markstudio-odoo.woowtech.io',
    ignoreHTTPSErrors: true,
  },
});
