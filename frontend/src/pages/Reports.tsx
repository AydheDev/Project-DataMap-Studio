import { useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { Download, ShieldCheck, FileSpreadsheet, ArrowRight, Info } from 'lucide-react';
import type { Job } from '../types';
import { Button, Empty, SectionHeading, Stat, Badge } from '../components/ui';
import { ReportTable } from '../components/ReportTable';
import { formatDate, number } from '../services/api';
export function Reports({
  jobs,
  selected,
  select,
  quality,
  onStart,
}: {
  jobs: Job[];
  selected?: Job;
  select: (job: Job) => void;
  quality?: boolean;
  onStart: () => void;
}) {
  const [activeTable, setActiveTable] = useState(quality ? 'Data Quality' : 'Market Summary');
  const succeeded = jobs.filter((j) => j.status === 'succeeded');
  const job = selected?.status === 'succeeded' ? selected : succeeded[0];
  const tables = quality
    ? ['Data Quality', 'Unmatched Roles', 'Excluded Records', 'Duplicate Audit']
    : [
        'Market Summary',
        'Role Counts',
        'Unique Mapping',
        'Duplicate Audit',
        'Data Quality',
        'Unmatched Roles',
        'Excluded Records',
      ];
  return (
    <>
      <SectionHeading
        eyebrow={quality ? 'TRUST, WITH A PAPER TRAIL' : 'THE COMPLETE PICTURE'}
        title={quality ? 'Data quality' : 'Reports & insights'}
        description={
          quality
            ? 'Understand exclusions, unmatched roles, and duplicate records.'
            : 'Explore market summaries and download the complete Excel report.'
        }
        action={
          job && (
            <a className="button primary" href={'/api/jobs/' + job.id + '/download'}>
              <Download size={17} />
              Download Excel
            </a>
          )
        }
      />
      {!job ? (
        <section className="panel">
          <Empty
            title="No completed reports yet"
            action={
              <Button onClick={onStart}>
                Start a workflow
                <ArrowRight size={16} />
              </Button>
            }
          >
            Complete an Account Role Mapping run to explore its results here.
          </Empty>
        </section>
      ) : (
        <>
          <div className="report-selector">
            <FileSpreadsheet size={20} />
            <label>
              Processing run
              <select
                aria-label="Processing run"
                value={job.id}
                onChange={(e) => {
                  const selectedJob = jobs.find((j) => j.id === e.target.value);
                  if (selectedJob) select(selectedJob);
                }}
              >
                {succeeded.map((j) => (
                  <option key={j.id} value={j.id}>
                    {formatDate(j.created_at)} · {j.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            <Badge status="succeeded">Complete</Badge>
          </div>
          <div className="stats-grid">
            <Stat
              label={quality ? 'Source records' : 'Unique accounts'}
              value={number(job.metrics[quality ? 'source_rows' : 'unique_accounts'])}
              detail={quality ? 'Original non-empty data rows' : 'Across all markets'}
            />
            <Stat
              label={quality ? 'Excluded records' : 'Role assignments'}
              value={number(job.metrics[quality ? 'excluded_rows' : 'unique_mappings'])}
              detail={quality ? 'Before deduplication' : 'Unique market · role · account mappings'}
            />
            <Stat
              label="Eligible records"
              value={number(job.metrics.eligible_rows)}
              detail="Passed all configured filters"
            />
            <Stat
              label="Duplicates removed"
              value={number(job.metrics.duplicates_removed)}
              detail="Repeated composite keys"
              accent
            />
          </div>
          <section className="panel report-panel">
            <Tabs.Root value={activeTable} onValueChange={setActiveTable}>
              <Tabs.List className="tabs" aria-label="Report worksheets">
                {tables.map((t) => (
                  <Tabs.Trigger value={t} key={t}>
                    {t}
                  </Tabs.Trigger>
                ))}
              </Tabs.List>
              {tables.map((t) => (
                <Tabs.Content value={t} key={t}>
                  <ReportTable key={job.id + t} jobId={job.id} table={t} />
                </Tabs.Content>
              ))}
            </Tabs.Root>
          </section>
          <section className="report-notes">
            <Info size={18} />
            <div>
              <strong>How to read this report</strong>
              {job.notes?.map((note) => (
                <p key={note}>{note}</p>
              ))}
              {job.request.config.include_full_audit_emails && (
                <p className="privacy-warning">
                  Full email addresses are enabled in this run’s excluded-record audit.
                </p>
              )}
            </div>
          </section>
          <div className="report-provenance">
            <ShieldCheck size={16} />
            Original uploads preserved · Job {job.id.slice(0, 8)} · Completed{' '}
            {formatDate(job.finished_at)}
          </div>
        </>
      )}
    </>
  );
}
