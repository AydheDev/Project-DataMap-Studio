import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  FileUp,
  LoaderCircle,
  Play,
  RotateCcw,
  Save,
  X,
  AlertCircle,
} from 'lucide-react';
import Shell from './layouts/Shell';
import { Dashboard } from './pages/Dashboard';
import { Reports } from './pages/Reports';
import { History } from './pages/History';
import { Modules } from './pages/Modules';
import { Settings } from './pages/Settings';
import { InputCard, mappingComplete } from './features/account-role-mapping/InputCard';
import { RuleConfig, DEFAULT_CONFIG } from './features/account-role-mapping/RuleConfig';
import { Badge, Button, SectionHeading } from './components/ui';
import { api } from './services/api';
import type {
  Config,
  Dashboard as DashboardData,
  InputId,
  Inputs,
  Job,
  Module,
  Page,
  Preview,
  Selection,
  Template,
  Upload,
} from './types';

const emptySelection = (): Selection => ({ upload_id: '', sheet: '', header_row: 1, mapping: {} });
const emptyInputs = (): Inputs => ({
  source: { selection: emptySelection(), loading: false },
  roles: { selection: emptySelection(), loading: false },
});
const validPages: Page[] = [
  'dashboard',
  'import',
  'mapping',
  'quality',
  'reports',
  'history',
  'modules',
  'settings',
];
const currentPage = (): Page =>
  validPages.includes(location.hash.slice(1) as Page)
    ? (location.hash.slice(1) as Page)
    : 'dashboard';

export default function App() {
  const [page, setPage] = useState<Page>(currentPage);
  const [modules, setModules] = useState<Module[]>([]),
    [uploads, setUploads] = useState<Upload[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]),
    [totalJobs, setTotalJobs] = useState(0),
    [historyLimit, setHistoryLimit] = useState(100);
  const [dashboard, setDashboard] = useState<DashboardData>(),
    [templates, setTemplates] = useState<Template[]>([]);
  const [inputs, setInputs] = useState<Inputs>(emptyInputs),
    [config, setConfig] = useState<Config>(DEFAULT_CONFIG);
  const [defaults, setDefaults] = useState<Config>(DEFAULT_CONFIG),
    [settingsDraft, setSettingsDraft] = useState<Config>(DEFAULT_CONFIG);
  const [activeJob, setActiveJob] = useState<Job>(),
    [selectedJob, setSelectedJob] = useState<Job>();
  const [connected, setConnected] = useState(false),
    [error, setError] = useState(''),
    [notice, setNotice] = useState('');
  const [starting, setStarting] = useState(false),
    [saving, setSaving] = useState(false),
    [templateName, setTemplateName] = useState('');
  const requests = useRef<Record<InputId, number>>({ source: 0, roles: 0 });
  const notifyError = (e: unknown) =>
    setError(e instanceof Error ? e.message : 'An unexpected error occurred.');
  const navigate = useCallback((next: Page) => {
    location.hash = next;
    setPage(next);
    window.scrollTo(0, 0);
  }, []);
  useEffect(() => {
    const onHash = () => setPage(currentPage());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  const refresh = useCallback(async () => {
    try {
      const [moduleList, files, history, overview, saved] = await Promise.all([
        api<Module[]>('/modules'),
        api<Upload[]>('/uploads'),
        Promise.all(
          Array.from({ length: Math.ceil(historyLimit / 100) }, (_, i) =>
            api<{ items: Job[]; total: number }>('/jobs?limit=100&offset=' + i * 100)
          )
        ).then((pages) => ({ items: pages.flatMap((p) => p.items), total: pages[0].total })),
        api<DashboardData>('/dashboard'),
        api<Template[]>('/templates'),
      ]);
      setModules(moduleList);
      setUploads(files);
      setJobs(history.items);
      setTotalJobs(history.total);
      setDashboard(overview);
      setTemplates(saved);
      setConnected(true);
    } catch (e) {
      setConnected(false);
      notifyError(e);
    }
  }, [historyLimit]);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  useEffect(() => {
    let alive = true;
    api<Config>('/settings')
      .then((value) => {
        if (alive) {
          setDefaults(value);
          setSettingsDraft(value);
          setConfig(value);
        }
      })
      .catch(notifyError);
    return () => {
      alive = false;
    };
  }, []);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(''), 6000);
    return () => clearTimeout(timer);
  }, [notice]);
  const busy = starting || activeJob?.status === 'running' || activeJob?.status === 'queued';
  useEffect(() => {
    if (!activeJob || !['running', 'queued'].includes(activeJob.status)) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const job = await api<Job>('/jobs/' + activeJob.id);
        if (cancelled) return;
        setActiveJob(job);
        setConnected(true);
        if (job.status === 'succeeded') {
          setSelectedJob(job);
          await refresh();
          navigate('reports');
          setNotice('Report ready. All seven worksheets are available.');
        } else if (job.status === 'failed') {
          await refresh();
          setError(job.error || 'Processing failed.');
        }
      } catch (e) {
        if (!cancelled) {
          setConnected(false);
          notifyError(e);
        }
      }
    };
    const timer = setInterval(() => void poll(), 1000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [activeJob?.id, activeJob?.status, refresh, navigate]);

  const loadPreview = async (
    id: InputId,
    upload: Upload,
    sheet: string,
    header?: number,
    mapping?: Record<string, string>
  ) => {
    const generation = ++requests.current[id];
    setInputs((current) => ({
      ...current,
      [id]: {
        selection: { upload_id: upload.id, sheet, header_row: header || 1, mapping: mapping || {} },
        loading: true,
      },
    }));
    try {
      const params = new URLSearchParams({ sheet, input_id: id });
      if (header) params.set('header_row', String(header));
      const preview = await api<Preview>('/uploads/' + upload.id + '/preview?' + params);
      if (generation !== requests.current[id]) return;
      const preserved = Object.fromEntries(
        Object.entries(mapping || {}).filter(([, value]) => preview.columns.includes(value))
      );
      setInputs((current) => ({
        ...current,
        [id]: {
          selection: {
            upload_id: upload.id,
            sheet,
            header_row: preview.header_row,
            mapping: { ...preview.suggested_mapping, ...preserved },
          },
          preview,
          loading: false,
        },
      }));
    } catch (e) {
      if (generation === requests.current[id])
        setInputs((current) => ({
          ...current,
          [id]: {
            ...current[id],
            loading: false,
            error: e instanceof Error ? e.message : 'Preview failed',
          },
        }));
    }
  };
  const selectUpload = (id: InputId, uploadId: string) => {
    const file = uploads.find((u) => u.id === uploadId);
    if (!file) {
      ++requests.current[id];
      setInputs((current) => ({
        ...current,
        [id]: { selection: emptySelection(), loading: false },
      }));
      return;
    }
    const old = inputs[id].selection;
    const sheet = file.sheets.includes(old.sheet) ? old.sheet : file.sheets[0];
    void loadPreview(id, file, sheet, undefined, old.mapping);
  };
  const uploadFile = async (id: InputId, file: File) => {
    if (!/\.xlsx?$/i.test(file.name)) {
      setError('Choose an Excel .xlsx or .xls workbook.');
      return;
    }
    if (file.size > 30 * 1024 * 1024) {
      setError('Workbook exceeds the 30 MB upload limit.');
      return;
    }
    setError('');
    const generation = ++requests.current[id];
    const previous = inputs[id].selection;
    setInputs((current) => ({
      ...current,
      [id]: { ...current[id], loading: true, error: undefined },
    }));
    try {
      const body = new FormData();
      body.append('file', file);
      const upload = await api<Upload>('/uploads', { method: 'POST', body });
      setUploads((current) => [upload, ...current]);
      if (generation !== requests.current[id]) return;
      const sheet = upload.sheets.includes(previous.sheet) ? previous.sheet : upload.sheets[0];
      await loadPreview(id, upload, sheet, undefined, previous.mapping);
      void refresh();
    } catch (e) {
      if (generation === requests.current[id]) {
        setInputs((current) => ({ ...current, [id]: { ...current[id], loading: false } }));
        notifyError(e);
      }
    }
  };
  const previewCurrent = (id: InputId, sheet?: string, header?: number) => {
    const state = inputs[id];
    const file = uploads.find((u) => u.id === state.selection.upload_id);
    if (!file) return;
    if (header !== undefined && (!Number.isInteger(header) || header < 1 || header > 100)) {
      setError('Header row must be between 1 and 100.');
      return;
    }
    void loadPreview(id, file, sheet || state.selection.sheet, header, state.selection.mapping);
  };
  const feature = modules.find((m) => m.id === 'account-role-mapping');
  const ready =
    !!feature &&
    feature.inputs.every((def) => mappingComplete(inputs[def.id as InputId], def.columns));
  const requestInputs = Object.fromEntries(
    Object.entries(inputs).map(([key, state]) => [key, state.selection])
  );
  const process = async () => {
    if (!ready || busy) return;
    setStarting(true);
    setError('');
    try {
      const job = await api<Job>('/jobs', {
        method: 'POST',
        body: JSON.stringify({ module_id: 'account-role-mapping', inputs: requestInputs, config }),
      });
      setActiveJob(job);
      navigate('mapping');
      void refresh();
    } catch (e) {
      notifyError(e);
    } finally {
      setStarting(false);
    }
  };
  const saveTemplate = async () => {
    if (!templateName.trim()) {
      setError('Enter a name for this template.');
      return;
    }
    setSaving(true);
    try {
      await api('/templates', {
        method: 'POST',
        body: JSON.stringify({
          name: templateName,
          module_id: 'account-role-mapping',
          config,
          inputs: requestInputs,
        }),
      });
      setTemplateName('');
      await refresh();
      setNotice('Template saved. Reuse it with your next reporting period.');
    } catch (e) {
      notifyError(e);
    } finally {
      setSaving(false);
    }
  };
  const applyTemplate = (id: string) => {
    const template = templates.find((t) => t.id === id);
    if (!template) return;
    setConfig(template.config);
    setError('');
    (['source', 'roles'] as InputId[]).forEach((input) => {
      const saved = template.inputs[input];
      const file = uploads.find((u) => u.id === inputs[input].selection.upload_id);
      if (file)
        void loadPreview(
          input,
          file,
          file.sheets.includes(saved.sheet) ? saved.sheet : file.sheets[0],
          saved.header_row,
          saved.mapping
        );
      else
        setInputs((current) => ({
          ...current,
          [input]: { selection: { upload_id: '', ...saved }, loading: false },
        }));
    });
    setNotice('Template applied. Check the worksheet and column mapping for both workbooks.');
  };
  const newWorkflow = () => {
    ++requests.current.source;
    ++requests.current.roles;
    setInputs(emptyInputs());
    setConfig(defaults);
    setActiveJob(undefined);
    setError('');
    navigate('import');
  };
  const openJob = (job: Job) => {
    if (job.status === 'succeeded') {
      setSelectedJob(job);
      navigate('reports');
    } else {
      setActiveJob(job);
      navigate('mapping');
    }
  };
  const saveSettings = async () => {
    setSaving(true);
    try {
      const saved = await api<Config>('/settings', {
        method: 'PUT',
        body: JSON.stringify(settingsDraft),
      });
      setDefaults(saved);
      setNotice('Defaults saved for new workflows.');
    } catch (e) {
      notifyError(e);
    } finally {
      setSaving(false);
    }
  };
  const inputCards = feature?.inputs.map((def) => (
    <InputCard
      key={def.id}
      id={def.id as InputId}
      title={def.label}
      subtitle={
        def.id === 'source'
          ? 'The source records you want to map'
          : 'Your list of eligible account role codes'
      }
      columns={def.columns}
      state={inputs[def.id as InputId]}
      uploads={uploads}
      onUpload={(file) => void uploadFile(def.id as InputId, file)}
      onSelect={(id) => selectUpload(def.id as InputId, id)}
      onSheet={(sheet) => previewCurrent(def.id as InputId, sheet)}
      onHeader={(row) => previewCurrent(def.id as InputId, undefined, row)}
      onRetry={() => previewCurrent(def.id as InputId)}
      onMapping={(key, value) =>
        setInputs((current) => ({
          ...current,
          [def.id]: {
            ...current[def.id as InputId],
            selection: {
              ...current[def.id as InputId].selection,
              mapping: { ...current[def.id as InputId].selection.mapping, [key]: value },
            },
          },
        }))
      }
    />
  ));
  return (
    <Shell page={page} navigate={navigate} connected={connected}>
      {error && (
        <div className="toast error" role="alert">
          <AlertCircle size={18} />
          <span>{error}</span>
          {!connected && (
            <Button variant="ghost" onClick={() => void refresh()}>
              Reconnect
            </Button>
          )}
          <button aria-label="Dismiss error" onClick={() => setError('')}>
            <X size={17} />
          </button>
        </div>
      )}
      {notice && (
        <div className="toast success" role="status">
          <CheckCircle2 size={18} />
          <span>{notice}</span>
          <button aria-label="Dismiss notification" onClick={() => setNotice('')}>
            <X size={17} />
          </button>
        </div>
      )}
      {page === 'dashboard' && <Dashboard data={dashboard} navigate={navigate} openJob={openJob} />}
      {(page === 'import' || page === 'mapping') && (
        <>
          <SectionHeading
            eyebrow="ACCOUNT ROLE MAPPING"
            title={page === 'import' ? 'Bring your data together' : 'Configure your mapping'}
            description={
              page === 'import'
                ? 'Import two workbooks, choose worksheets, and match the columns.'
                : 'Review your inputs and processing rules before creating a report.'
            }
            action={
              <Button variant="secondary" onClick={newWorkflow} disabled={busy}>
                <RotateCcw size={15} />
                New workflow
              </Button>
            }
          />
          <div className="workflow-steps">
            <button
              className={page === 'import' ? 'current' : 'complete'}
              onClick={() => navigate('import')}
            >
              <span>{page === 'mapping' ? <Check size={14} /> : 1}</span>Import & map
            </button>
            <ChevronRight size={16} />
            <button
              className={page === 'mapping' ? 'current' : ''}
              onClick={() => navigate('mapping')}
            >
              <span>2</span>Review & process
            </button>
            <ChevronRight size={16} />
            <button onClick={() => navigate('reports')}>
              <span>3</span>Explore report
            </button>
          </div>
          {activeJob && (
            <div className={'job-banner ' + activeJob.status}>
              {busy ? (
                <LoaderCircle size={20} className="spin" />
              ) : activeJob.status === 'failed' ? (
                <AlertCircle size={20} />
              ) : (
                <CheckCircle2 size={20} />
              )}
              <div>
                <strong>
                  {activeJob.status === 'running'
                    ? 'Processing your workbooks'
                    : activeJob.status === 'queued'
                      ? 'Your job is queued'
                      : activeJob.status === 'failed'
                        ? 'Processing failed'
                        : 'Report complete'}
                </strong>
                <p>
                  {activeJob.error ||
                    'Job ' +
                      activeJob.id.slice(0, 8) +
                      ' · You can continue browsing while processing runs.'}
                </p>
              </div>
              <Badge status={activeJob.status} />
              {activeJob.status === 'succeeded' && (
                <Button variant="secondary" onClick={() => openJob(activeJob)}>
                  Open report
                </Button>
              )}
            </div>
          )}
          <fieldset disabled={busy} className="workflow-fieldset">
            <div className="template-bar">
              <div>
                <Save size={17} />
                <strong>Reusable workflow</strong>
                <span>Apply a saved mapping and configuration.</span>
              </div>
              <select
                aria-label="Apply template"
                defaultValue=""
                onChange={(e) => {
                  applyTemplate(e.target.value);
                  e.target.value = '';
                }}
              >
                <option value="">Choose a template</option>
                {templates
                  .filter((t) => t.module_id === 'account-role-mapping')
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
              </select>
            </div>
            <div className="input-grid">
              {inputCards || (
                <div className="panel">
                  Connect to the local backend to load the mapping module.
                </div>
              )}
            </div>
            {page === 'mapping' && (
              <section className="panel rules-panel">
                <SectionHeading
                  title="Review processing rules"
                  description="Fixed business rules protect counting accuracy. Optional settings apply only to this run."
                />
                <RuleConfig config={config} setConfig={setConfig} />
                <div className="save-template">
                  <label className="field">
                    <span>Save these rules and mappings for next time</span>
                    <input
                      placeholder="e.g. Monthly market report"
                      maxLength={80}
                      value={templateName}
                      onChange={(e) => setTemplateName(e.target.value)}
                      aria-label="Template name"
                    />
                  </label>
                  <Button
                    variant="secondary"
                    onClick={() => void saveTemplate()}
                    disabled={!ready}
                    busy={saving}
                  >
                    <Save size={16} />
                    Save template
                  </Button>
                </div>
              </section>
            )}
          </fieldset>
          <div className="workflow-footer">
            <div>
              <span className={ready ? 'ready-dot' : 'pending-dot'} />
              <strong>
                {ready
                  ? 'Both workbooks are mapped'
                  : 'Complete both workbook mappings to continue'}
              </strong>
              <small>
                {ready
                  ? 'Review the rules before processing.'
                  : 'Choose your files, worksheets, and all required columns.'}
              </small>
            </div>
            {page === 'import' ? (
              <Button disabled={!ready || busy} onClick={() => navigate('mapping')}>
                Review & process
                <ArrowRight size={17} />
              </Button>
            ) : (
              <Button disabled={!ready || busy} busy={busy} onClick={() => void process()}>
                <Play size={16} />
                Generate report
              </Button>
            )}
          </div>
        </>
      )}
      {page === 'reports' && (
        <Reports
          key="reports"
          jobs={jobs}
          selected={selectedJob}
          select={setSelectedJob}
          onStart={() => navigate('import')}
        />
      )}
      {page === 'quality' && (
        <Reports
          key="quality"
          jobs={jobs}
          selected={selectedJob}
          select={setSelectedJob}
          quality
          onStart={() => navigate('import')}
        />
      )}
      {page === 'history' && (
        <History
          jobs={jobs}
          total={totalJobs}
          onOpen={openJob}
          onRefresh={() => void refresh()}
          onMore={() => setHistoryLimit((n) => n + 100)}
        />
      )}
      {page === 'modules' && <Modules modules={modules} navigate={navigate} />}
      {page === 'settings' && (
        <Settings
          config={settingsDraft}
          setConfig={setSettingsDraft}
          onSave={() => void saveSettings()}
          busy={saving}
        />
      )}
    </Shell>
  );
}
