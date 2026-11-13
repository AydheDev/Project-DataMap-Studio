import { useRef, useState } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle2, ChevronDown, RefreshCw } from 'lucide-react';
import type { Column, InputId, InputState, Upload } from '../../types';
import { Badge, Button } from '../../components/ui';
import { display, number } from '../../services/api';
export function mappingComplete(state: InputState, columns: Column[]) {
  const mapped = columns.map((c) => state.selection.mapping[c.key]);
  return (
    !!state.preview &&
    !state.loading &&
    !state.error &&
    mapped.every((v) => !!v && state.preview!.columns.includes(v)) &&
    new Set(mapped).size === mapped.length
  );
}
export function InputCard({
  id,
  title,
  subtitle,
  columns,
  state,
  uploads,
  onUpload,
  onSelect,
  onSheet,
  onHeader,
  onMapping,
  onRetry,
}: {
  id: InputId;
  title: string;
  subtitle: string;
  columns: Column[];
  state: InputState;
  uploads: Upload[];
  onUpload: (file: File) => void;
  onSelect: (id: string) => void;
  onSheet: (sheet: string) => void;
  onHeader: (row: number) => void;
  onMapping: (key: string, value: string) => void;
  onRetry: () => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [header, setHeader] = useState('');
  const selected = uploads.find((u) => u.id === state.selection.upload_id);
  const complete = mappingComplete(state, columns);
  return (
    <section className="panel input-card">
      <div className="input-heading">
        <span className="input-number">{id === 'source' ? '01' : '02'}</span>
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
        <Badge status={complete ? 'succeeded' : state.loading ? 'running' : undefined}>
          {complete ? 'Mapped' : state.loading ? 'Loading' : 'Required'}
        </Badge>
      </div>
      <input
        ref={fileRef}
        type="file"
        className="sr-only"
        accept=".xlsx,.xls"
        aria-label={'Upload ' + title}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUpload(file);
          e.target.value = '';
        }}
      />
      <button
        className={'dropzone ' + (dragging ? 'dragging' : '')}
        disabled={state.loading}
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!state.loading && e.dataTransfer.files[0]) onUpload(e.dataTransfer.files[0]);
        }}
      >
        {selected ? <FileSpreadsheet size={25} /> : <UploadCloud size={27} />}
        <strong>{selected ? selected.name : 'Drop an Excel workbook here'}</strong>
        <small>
          {selected
            ? (selected.size / 1024).toFixed(1) + ' KB · Click to replace'
            : 'or click to browse · XLSX / XLS · up to 30 MB'}
        </small>
      </button>
      {uploads.length > 0 && (
        <label className="field">
          <span>Use a previous upload</span>
          <select
            value={state.selection.upload_id}
            disabled={state.loading}
            onChange={(e) => onSelect(e.target.value)}
            aria-label={title + ' uploaded file'}
          >
            <option value="">Select a workbook</option>
            {uploads.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name} · {u.id.slice(0, 6)}
              </option>
            ))}
          </select>
        </label>
      )}
      {selected && (
        <>
          <div className="sheet-controls">
            <label className="field">
              <span>Worksheet</span>
              <select
                value={state.selection.sheet}
                disabled={state.loading}
                onChange={(e) => onSheet(e.target.value)}
                aria-label={title + ' worksheet'}
              >
                {selected.sheets.map((sheet) => (
                  <option key={sheet}>{sheet}</option>
                ))}
              </select>
            </label>
            <label className="field header-field">
              <span>Header row</span>
              <input
                type="number"
                min="1"
                max="100"
                value={header || state.selection.header_row}
                onChange={(e) => setHeader(e.target.value)}
                aria-label={title + ' header row'}
              />
            </label>
            <Button
              variant="secondary"
              disabled={state.loading}
              onClick={() => {
                onHeader(Number(header || state.selection.header_row));
                setHeader('');
              }}
            >
              Apply
            </Button>
          </div>
          {state.error && (
            <div role="alert" className="inline-error">
              {state.error}
              <Button variant="ghost" onClick={onRetry}>
                <RefreshCw size={14} />
                Retry preview
              </Button>
            </div>
          )}
          {state.preview && !state.loading && (
            <>
              <div className="preview-meta">
                <CheckCircle2 size={15} />
                {number(state.preview.row_count)} rows<span>·</span>
                {state.preview.column_count} columns<span>·</span>Header at row{' '}
                {state.preview.header_row}
              </div>
              <div className="mapping-label">
                <strong>Column mapping</strong>
                <small>Match your headers to required fields</small>
              </div>
              <div className="column-mapping">
                {columns.map((column) => (
                  <label className="mapping-row" key={column.key}>
                    <span>
                      {column.label}
                      <span className="required-mark">*</span>
                    </span>
                    <select
                      aria-label={title + ' ' + column.label}
                      value={state.selection.mapping[column.key] || ''}
                      className={!state.selection.mapping[column.key] ? 'unmapped' : ''}
                      onChange={(e) => onMapping(column.key, e.target.value)}
                    >
                      <option value="">Select source column</option>
                      {state.preview!.columns.map((name) => (
                        <option
                          key={name}
                          disabled={column.forbidden_aliases?.some(
                            (v) =>
                              v.toLowerCase().replace(/\s+/g, ' ').trim() ===
                              name.toLowerCase().replace(/\s+/g, ' ').trim()
                          )}
                        >
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
              {new Set(Object.values(state.selection.mapping).filter(Boolean)).size !==
                Object.values(state.selection.mapping).filter(Boolean).length && (
                <p className="inline-error">Each field must use a different source column.</p>
              )}
              <details className="preview-details">
                <summary>
                  Preview source data <span>First {state.preview.rows.length} rows</span>
                  <ChevronDown size={15} />
                </summary>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Row</th>
                        {state.preview.columns.map((c) => (
                          <th key={c}>{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {state.preview.rows.map((row) => (
                        <tr key={row.source_row}>
                          <td>{row.source_row}</td>
                          {row.values.map((v, i) => (
                            <td key={i}>{display(v)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </>
          )}
        </>
      )}
    </section>
  );
}
