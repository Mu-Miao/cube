import { expect, test } from '@playwright/test'

const fakeAccessToken = [
  Buffer.from(JSON.stringify({ alg: 'none' })).toString('base64url'),
  Buffer.from(JSON.stringify({ username: 'e2e-user', role: 'user' })).toString('base64url'),
  'signature',
].join('.')

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/auth/refresh', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"expired"}' }),
  )
})

test('protected route redirects to the standalone login view', async ({ page }) => {
  await page.goto('/teen/dashboard')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: '智能桌面魔方' })).toBeVisible()
  await expect(page.getByRole('link', { name: '立即注册' })).toBeVisible()
})

test('public auth screen switches between login and registration', async ({ page }) => {
  await page.goto('/public')
  await expect(page.getByRole('heading', { name: '登录控制台' })).toBeVisible()
  await page.getByRole('button', { name: '没有账号？注册' }).click()
  await expect(page.getByRole('heading', { name: '创建账号' })).toBeVisible()
})

test('login stores access only in memory and enters dashboard', async ({ page }) => {
  await page.route('**/api/v1/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '{"code":0,"message":"ok","data":[]}',
    }),
  )
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 0,
        message: 'ok',
        data: {
          access_token: fakeAccessToken,
          token_type: 'bearer',
          expires_in: 900,
        },
      }),
    }),
  )

  await page.goto('/login')
  await page.locator('input[placeholder="请输入用户名"]').fill('e2e-user')
  await page.locator('input[placeholder="请输入密码"]').fill('password123')
  await page.locator('button.login-btn').click()
  await expect(page).toHaveURL(/\/teen\/dashboard/)
  await expect(page.evaluate(() => localStorage.getItem('token'))).resolves.toBeNull()
})
