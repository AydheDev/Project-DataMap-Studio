export async function api<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch('/api' + url, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const payload = await response
      .json()
      .catch(() => ({ detail: 'The server could not complete this request.' }));
    const detail = payload.detail;
    throw new Error(
      Array.isArray(detail)
        ? detail.map((v: { msg: string }) => v.msg).join('; ')
        : detail || 'Request failed.'
    );
  }
  return response.json();
}
export function display(value: unknown): string {
  if (value == null) return '—';
  if (typeof value === 'object' && 'error' in value)
    return String((value as { error: string }).error);
  return String(value);
}
export function formatDate(value?: string | null) {
  return value
    ? new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    : 'No runs yet';
}
export const number = (value: number | undefined) => (value ?? 0).toLocaleString();
