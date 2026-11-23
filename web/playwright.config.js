import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    fullyParallel: false,
    workers: 1,
    use: {
        baseURL: 'http://127.0.0.1:5051',
        headless: true,
        launchOptions: {
            ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}),
        },
        trace: 'retain-on-failure',
    },
    webServer: {
        command: `${process.env.SPA_TEST_PYTHON || 'python3'} ../api/tests/e2e_server.py`,
        url: 'http://127.0.0.1:5051/api/session',
        reuseExistingServer: false,
        timeout: 30000,
    },
});
