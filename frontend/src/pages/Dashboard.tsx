import { ArrowUpRight, ArrowRight, FileUp, GitBranch, FileSpreadsheet, Layers } from 'lucide-react';
import type { Dashboard as DashboardData, Job, Page } from '../types';
import { Badge, Button, Empty, SectionHeading, Stat } from '../components/ui';
import { formatDate, number } from '../services/api';
export function Dashboard({
  data,
  navigate,
  openJob,
}: {
  data?: DashboardData;
  navigate: (page: Page) => void;
  openJob: (job: Job) => void;
}) {
  const metrics = data?.latest_metrics;
  return (
    <>
      <SectionHeading
        eyebrow="YOUR DATA, CONNECTED"
        title="Workspace overview"
        description="Turn source workbooks into reliable, decision-ready reports."
        action={
          <Button onClick={() => navigate('import')}>
            <FileUp size={17} />
            New import
          </Button>
        }
      />
      <section className="hero">
        <div>
          <span className="hero-kicker">
            <span />
            ACCOUNT ROLE MAPPING
          </span>
          <h1>
            From scattered records
            <br />
            to a clearer picture.
          </h1>
          <p>
            Match approved roles. Count unique accounts.
            <br />
            Know exactly what changed along the way.
          </p>
          <Button onClick={() => navigate('import')}>
            Start a new workflow
            <ArrowRight size={17} />
          </Button>
        </div>
        <div
          className="flow-visual"
          aria-label="Workbooks flow through mapping to verified reports"
        >
          <div className="flow-source">
            <FileSpreadsheet size={22} />
            <span>FDS + SSO-EIP</span>
          </div>
          <div className="flow-source second">
            <Layers size={21} />
            <span>Approved roles</span>
          </div>
          <div className="flow-junction" />
          <div className="flow-core">
            <GitBranch size={34} />
          </div>
          <div className="flow-output">
            <span className="flow-output-icon">
              <FileSpreadsheet size={22} />
            </span>
            <strong>One trusted report</strong>
            <small>7 auditable worksheets</small>
          </div>
        </div>
      </section>
      <div className="stats-grid">
        <Stat
          label="Processed files"
          value={number(data?.processed_files)}
          detail="Distinct source workbooks"
        />
        <Stat
          label="Source records"
          value={number(metrics?.source_rows)}
          detail="Latest completed run"
        />
        <Stat
          label="Eligible records"
          value={number(metrics?.eligible_rows)}
          detail="Before deduplication"
        />
        <Stat
          label="Duplicates removed"
          value={number(metrics?.duplicates_removed)}
          detail="Latest completed run"
          accent
        />
      </div>
      <div className="dashboard-bottom">
        <section className="panel">
          <SectionHeading
            title="Recent activity"
            description={
              data?.latest_processing_date
                ? 'Latest completed run · ' + formatDate(data.latest_processing_date)
                : 'Your processing runs will appear here.'
            }
            action={
              <button className="text-button" onClick={() => navigate('history')}>
                View all
                <ArrowUpRight size={15} />
              </button>
            }
          />
          {!data?.recent_jobs.length ? (
            <Empty title="Ready for your first workbook">
              Import your source data and approved role list to begin.
            </Empty>
          ) : (
            <div className="activity-list">
              {data.recent_jobs.map((job) => (
                <button className="activity" key={job.id} onClick={() => openJob(job)}>
                  <span className="file-icon">
                    <FileSpreadsheet size={20} />
                  </span>
                  <span>
                    <strong>Account Role Mapping</strong>
                    <small>
                      {formatDate(job.created_at)} · {job.id.slice(0, 8)}
                    </small>
                  </span>
                  <Badge status={job.status} />
                  <ArrowUpRight size={16} />
                </button>
              ))}
            </div>
          )}
        </section>
        <section className="panel module-spotlight">
          <span className="eyebrow">YOUR TOOLKIT</span>
          <div className="module-icon">
            <GitBranch size={27} />
          </div>
          <h3>Account Role Mapping</h3>
          <p>
            Market-level counts with approved roles, email fallback, and a complete quality audit.
          </p>
          <div className="module-meta">
            <Badge status="succeeded">Available</Badge>
            <span>v1.0.0</span>
          </div>
          <Button variant="secondary" onClick={() => navigate('mapping')}>
            Open module
            <ArrowRight size={16} />
          </Button>
          <small className="muted">{data?.module_count ?? 1} active module · Built to grow</small>
        </section>
      </div>
    </>
  );
}
