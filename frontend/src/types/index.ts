export type Config = {
  include_zero_counts: boolean;
  exclude_invalid_emails: boolean;
  include_full_audit_emails: boolean;
  login_day_first: boolean;
};
export type InputId = 'source' | 'roles';
export type CellValue =
  string | number | boolean | null | { error: string; original: string | null };
export type Upload = {
  id: string;
  name: string;
  size: number;
  sheets: string[];
  created_at: string;
};
export type Column = {
  key: string;
  label: string;
  aliases: string[];
  forbidden_aliases?: string[];
};
export type Module = {
  id: string;
  name: string;
  description: string;
  version: string;
  enabled: boolean;
  ui_route: string;
  inputs: { id: string; label: string; columns: Column[] }[];
  configuration_schema: Record<string, unknown>;
};
export type Preview = {
  sheet: string;
  header_row: number;
  columns: string[];
  row_count: number;
  column_count: number;
  rows: { source_row: number; values: CellValue[] }[];
  suggested_mapping: Record<string, string>;
  missing_fields: string[];
};
export type Selection = {
  upload_id: string;
  sheet: string;
  header_row: number;
  mapping: Record<string, string>;
};
export type InputState = {
  selection: Selection;
  preview?: Preview;
  loading: boolean;
  error?: string;
};
export type Inputs = Record<InputId, InputState>;
export type Job = {
  id: string;
  module_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  created_at: string;
  finished_at?: string;
  error?: string;
  metrics: Record<string, number>;
  tables?: { name: string; row_count: number; columns: string[] }[];
  notes?: string[];
  request: { module_id: string; inputs: Record<string, Selection>; config: Config };
};
export type Dashboard = {
  processed_files: number;
  uploaded_files: number;
  completed_jobs: number;
  latest_processing_date: string | null;
  latest_metrics: Record<string, number>;
  module_count: number;
  recent_jobs: Job[];
};
export type Template = {
  id: string;
  name: string;
  module_id: string;
  config: Config;
  inputs: Record<InputId, Omit<Selection, 'upload_id'>>;
};
export type TableData = {
  columns: string[];
  rows: CellValue[][];
  total: number;
  markets: string[];
  roles: string[];
  offset: number;
};
export type Page =
  'dashboard' | 'import' | 'mapping' | 'quality' | 'reports' | 'history' | 'modules' | 'settings';
