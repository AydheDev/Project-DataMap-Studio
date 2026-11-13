import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { afterEach, describe, it, expect, vi } from 'vitest';
import { InputCard, mappingComplete } from '../features/account-role-mapping/InputCard';
import { RuleConfig, DEFAULT_CONFIG } from '../features/account-role-mapping/RuleConfig';
import { ReportTable } from './ReportTable';
import type { InputState } from '../types';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const columns = [
  { key: 'market', label: 'Market', aliases: ['Market'] },
  { key: 'login', label: 'Salesforce Last login', aliases: ['Salesforce Last login'] },
];
const state: InputState = {
  selection: {
    upload_id: 'a',
    sheet: 'Current',
    header_row: 2,
    mapping: { market: 'Country', login: 'Login' },
  },
  loading: false,
  preview: {
    sheet: 'Current',
    header_row: 2,
    columns: ['Country', 'Login'],
    row_count: 2,
    column_count: 2,
    rows: [{ source_row: 3, values: ['UK', '2026-10-30'] }],
    suggested_mapping: {},
    missing_fields: [],
  },
};
describe('workbook mapping', () => {
  it('requires every field and prevents duplicate column mappings', () => {
    expect(mappingComplete(state, columns)).toBe(true);
    expect(mappingComplete({ ...state, loading: true }, columns)).toBe(false);
    expect(
      mappingComplete(
        {
          ...state,
          selection: { ...state.selection, mapping: { market: 'Country', login: 'Country' } },
        },
        columns
      )
    ).toBe(false);
    expect(
      mappingComplete(
        {
          ...state,
          selection: { ...state.selection, mapping: { market: 'Country', login: 'Stale column' } },
        },
        columns
      )
    ).toBe(false);
  });
  it('supports worksheet selection, manual mapping and source preview', () => {
    const onSheet = vi.fn(),
      onMapping = vi.fn();
    render(
      <InputCard
        id="source"
        title="Source data"
        subtitle="Import"
        columns={columns}
        state={state}
        uploads={[
          {
            id: 'a',
            name: 'Current.xlsx',
            size: 123,
            sheets: ['Current', 'Archive'],
            created_at: '',
          },
        ]}
        onUpload={vi.fn()}
        onSelect={vi.fn()}
        onSheet={onSheet}
        onHeader={vi.fn()}
        onMapping={onMapping}
        onRetry={vi.fn()}
      />
    );
    fireEvent.change(screen.getByLabelText('Source data worksheet'), {
      target: { value: 'Archive' },
    });
    expect(onSheet).toHaveBeenCalledWith('Archive');
    fireEvent.change(screen.getByLabelText('Source data Market'), { target: { value: 'Login' } });
    expect(onMapping).toHaveBeenCalledWith('market', 'Login');
    expect(screen.getByText('UK')).toBeInTheDocument();
    expect(screen.getByText('Mapped')).toBeInTheDocument();
  });
  it('keeps audit emails private unless explicitly enabled', () => {
    const update = vi.fn();
    render(<RuleConfig config={DEFAULT_CONFIG} setConfig={update} />);
    const toggle = screen.getByRole('switch', { name: 'Full emails in excluded-record audit' });
    expect(toggle).not.toBeChecked();
    fireEvent.click(toggle);
    expect(update).toHaveBeenCalledWith({ ...DEFAULT_CONFIG, include_full_audit_emails: true });
    expect(screen.getByText(/Fed ID is never used/)).toBeInTheDocument();
  });
});
describe('reports', () => {
  it('requests filtered, sorted report rows from the backend', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          columns: ['Market', 'Unique Accounts'],
          rows: [['UK', 2]],
          total: 1,
          markets: ['UK', 'DE'],
          roles: [],
          offset: 0,
        }),
      });
    vi.stubGlobal('fetch', fetch);
    render(<ReportTable jobId="job" table="Market Summary" />);
    await screen.findByRole('columnheader', { name: /Unique Accounts/ });
    fireEvent.change(screen.getByLabelText('Filter market'), { target: { value: 'DE' } });
    await waitFor(() => expect(fetch.mock.calls.at(-1)?.[0]).toContain('market=DE'));
    await screen.findByRole('columnheader', { name: /Unique Accounts/ });
    fireEvent.click(screen.getByRole('button', { name: /Unique Accounts/ }));
    await waitFor(() => expect(fetch.mock.calls.at(-1)?.[0]).toContain('sort=Unique+Accounts'));
  });
  it('shows API failures and lets the user retry', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'Report unavailable' }) })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          columns: ['Market'],
          rows: [],
          total: 0,
          markets: [],
          roles: [],
          offset: 0,
        }),
      });
    vi.stubGlobal('fetch', fetch);
    render(<ReportTable jobId="job" table="Market Summary" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Report unavailable');
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('No matching records')).toBeInTheDocument();
  });
});
