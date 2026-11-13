import { useEffect, useState } from 'react';
import { Search, ArrowDownUp, ChevronLeft, ChevronRight, LoaderCircle } from 'lucide-react';
import type { TableData } from '../types';
import { api, display, number } from '../services/api';
import { Button, Empty } from './ui';
export function ReportTable({ jobId, table }: { jobId: string; table: string }) {
  const [data, setData] = useState<TableData>();
  const [market, setMarket] = useState(''),
    [role, setRole] = useState(''),
    [search, setSearch] = useState('');
  const [sort, setSort] = useState(''),
    [descending, setDescending] = useState(false),
    [offset, setOffset] = useState(0);
  const [error, setError] = useState(''),
    [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    const timer = setTimeout(
      () => {
        const params = new URLSearchParams({
          market,
          role,
          search,
          sort,
          descending: String(descending),
          offset: String(offset),
          limit: '50',
        });
        api<TableData>('/jobs/' + jobId + '/tables/' + encodeURIComponent(table) + '?' + params, {
          signal: controller.signal,
        })
          .then((result) => {
            setData(result);
            setLoading(false);
          })
          .catch((e) => {
            if (e.name !== 'AbortError') {
              setError(e.message);
              setLoading(false);
            }
          });
      },
      search ? 180 : 0
    );
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [jobId, table, market, role, search, sort, descending, offset, retry]);
  const updateSort = (column: string) => {
    setOffset(0);
    setDescending(sort === column ? !descending : false);
    setSort(column);
  };
  return (
    <div className="report-table">
      <div className="table-toolbar">
        <label className="search-field">
          <Search size={16} />
          <input
            placeholder="Search this table…"
            aria-label="Search report"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <div className="table-filters">
          {!!data?.markets.length && (
            <select
              aria-label="Filter market"
              value={market}
              onChange={(e) => {
                setMarket(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All markets</option>
              {data.markets.map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          )}
          {!!data?.roles.length && (
            <select
              aria-label="Filter role"
              value={role}
              onChange={(e) => {
                setRole(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All roles</option>
              {data.roles.map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          )}
        </div>
      </div>
      {error ? (
        <div role="alert" className="inline-error">
          {error}
          <Button variant="secondary" onClick={() => setRetry(retry + 1)}>
            Retry
          </Button>
        </div>
      ) : loading ? (
        <div className="table-loading" role="status">
          <LoaderCircle size={20} className="spin" />
          Loading report…
        </div>
      ) : !data?.rows.length ? (
        <Empty title="No matching records">This table is empty for the current filters.</Empty>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {data.columns.map((c) => (
                  <th
                    key={c}
                    aria-sort={sort === c ? (descending ? 'descending' : 'ascending') : 'none'}
                  >
                    <button onClick={() => updateSort(c)}>
                      {c}
                      <ArrowDownUp size={12} />
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row, i) => (
                <tr key={offset + i}>
                  {row.map((v, j) => (
                    <td key={j} className={typeof v === 'number' ? 'numeric' : ''}>
                      {display(v)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="table-pagination">
        <span>
          {data ? number(data.total) + ' records' : '—'}
          {data && data.total > 0
            ? ' · Showing ' + (offset + 1) + '–' + Math.min(offset + 50, data.total)
            : ''}
        </span>
        <div>
          <Button
            variant="ghost"
            aria-label="Previous page"
            disabled={!offset || loading}
            onClick={() => setOffset(Math.max(0, offset - 50))}
          >
            <ChevronLeft size={16} />
          </Button>
          <Button
            variant="ghost"
            aria-label="Next page"
            disabled={!data || offset + 50 >= data.total || loading}
            onClick={() => setOffset(offset + 50)}
          >
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>
    </div>
  );
}
