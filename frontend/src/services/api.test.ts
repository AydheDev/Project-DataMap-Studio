import { afterEach, expect, it, vi } from 'vitest';
import { api } from './api';

afterEach(() => vi.unstubAllGlobals());

it('keeps API requests on the local origin and refuses redirects', async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) });
  vi.stubGlobal('fetch', fetch);
  await api('/health', { mode: 'cors', redirect: 'follow' });
  expect(fetch).toHaveBeenCalledWith(
    '/api/health',
    expect.objectContaining({
      mode: 'same-origin',
      redirect: 'error',
      credentials: 'same-origin',
    })
  );
});

it('rejects absolute and protocol-relative API URLs', async () => {
  const fetch = vi.fn();
  vi.stubGlobal('fetch', fetch);
  await expect(api('https://example.com')).rejects.toThrow('local API path');
  await expect(api('//example.com')).rejects.toThrow('local API path');
  expect(fetch).not.toHaveBeenCalled();
});
