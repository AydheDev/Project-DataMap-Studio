import { RefreshCw, ArrowUpRight, Download } from 'lucide-react';
import type { Job } from '../types';
import { Badge, Button, Empty, SectionHeading } from '../components/ui';
import { formatDate, number } from '../services/api';
export function History({
  jobs,
  total,
  onOpen,
  onRefresh,
  onMore,
}: {
  jobs: Job[];
  total: number;
  onOpen: (job: Job) => void;
  onRefresh: () => void;
  onMore: () => void;
}) {
  return (
    <>
      <SectionHeading
        eyebrow="EVERY RUN, RECORDED"
        title="Processing history"
        description="Review completed reports, inspect failures, and track your work."
        action={
          <Button variant="secondary" onClick={onRefresh}>
            <RefreshCw size={16} />
            Refresh
          </Button>
        }
      />
      <section className="panel">
        {!jobs.length ? (
          <Empty title="A clean slate">
            Processing runs will appear here when you start your first workflow.
          </Empty>
        ) : (
          <>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Run / module</th>
                    <th>Started</th>
                    <th>Status</th>
                    <th>Unique mappings</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.id}>
                      <td>
                        <strong>Account Role Mapping</strong>
                        <small className="cell-sub">{job.id.slice(0, 8)}</small>
                        {job.error && <span className="failure-detail">{job.error}</span>}
                      </td>
                      <td>{formatDate(job.created_at)}</td>
                      <td>
                        <Badge status={job.status} />
                      </td>
                      <td className="numeric">
                        {job.status === 'succeeded' ? number(job.metrics.unique_mappings) : '—'}
                      </td>
                      <td>
                        <div className="row-actions">
                          <Button variant="ghost" onClick={() => onOpen(job)}>
                            {job.status === 'succeeded' ? 'View report' : 'View run'}
                            <ArrowUpRight size={14} />
                          </Button>
                          {job.status === 'succeeded' && (
                            <a
                              href={'/api/jobs/' + job.id + '/download'}
                              className="icon-button"
                              aria-label={'Download ' + job.id.slice(0, 8)}
                            >
                              <Download size={16} />
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {jobs.length < total && (
              <div className="load-more">
                <Button variant="secondary" onClick={onMore}>
                  Load more ({total - jobs.length} remaining)
                </Button>
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
}
