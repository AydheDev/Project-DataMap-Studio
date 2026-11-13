import { test, expect } from '@playwright/test';
import path from 'node:path';

test('uploads real workbooks, maps data, saves a template, processes and downloads a report', async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  page.on('pageerror', (error) => consoleErrors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Workspace overview' })).toBeVisible();
  await page.getByRole('button', { name: 'New import', exact: true }).click();
  await page
    .getByLabel('Upload FDS + SSO-EIP workbook', { exact: true })
    .setInputFiles(path.resolve('../examples/sample-source.xlsx'));
  await expect(page.getByText('First 16 rows', { exact: true })).toBeVisible();
  await expect(
    page.getByLabel('FDS + SSO-EIP workbook Salesforce Last login', { exact: true })
  ).toHaveValue('Salesforce Last login');
  await page
    .getByLabel('Upload Approved account roles', { exact: true })
    .setInputFiles(path.resolve('../examples/sample-approved-roles.xlsx'));
  await expect(page.getByText('Both workbooks are mapped')).toBeVisible();
  await page.getByRole('button', { name: 'Review & process', exact: true }).last().click();
  await expect(
    page.getByText('Fixed business rules protect counting accuracy.', { exact: false })
  ).toBeVisible();
  await expect(
    page.getByRole('switch', { name: 'Full emails in excluded-record audit' })
  ).not.toBeChecked();
  await page.getByLabel('Template name').fill('Browser verified monthly mapping');
  await page.getByRole('button', { name: 'Save template', exact: true }).click();
  await expect(page.getByText('Template saved.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Generate report', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Reports & insights' })).toBeVisible({
    timeout: 20000,
  });
  await expect(page.getByRole('cell', { name: 'UK', exact: true })).toBeVisible();
  await page.getByRole('tab', { name: 'Role Counts', exact: true }).click();
  await page.getByLabel('Filter market').selectOption('UK');
  await page.getByLabel('Filter role').selectOption('Agent');
  await expect(page.getByRole('cell', { name: '2', exact: true })).toBeVisible();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download Excel' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/^DataMap-.*\.xlsx$/);
  expect(await download.failure()).toBeNull();
  await page.getByRole('button', { name: 'Data Quality', exact: true }).click();
  await page.getByRole('tab', { name: 'Excluded Records', exact: true }).click();
  await expect(page.getByRole('cell', { name: '[redacted]', exact: true }).first()).toBeVisible();
  await expect(page.getByRole('cell', { name: 'other@example.com', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Processing History', exact: true }).click();
  await expect(page.getByRole('button', { name: 'View report' }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Module Management', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Sample extension' })).toBeVisible();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('switch', { name: 'Include zero-count roles' }).uncheck();
  await page.getByRole('button', { name: 'Save defaults' }).click();
  await expect(page.getByText('Defaults saved for new workflows.')).toBeVisible();
  await page.reload();
  await expect(page.getByRole('switch', { name: 'Include zero-count roles' })).not.toBeChecked();
  // Restore the default so repeated runs have the same baseline.
  await page.getByRole('switch', { name: 'Include zero-count roles' }).check();
  await page.getByRole('button', { name: 'Save defaults' }).click();
  await expect(page.getByText('Defaults saved for new workflows.')).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test('mobile navigation and import remain usable without page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Workspace overview' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true
  );
  await page.getByRole('button', { name: 'Data Import', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bring your data together' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true
  );
});
