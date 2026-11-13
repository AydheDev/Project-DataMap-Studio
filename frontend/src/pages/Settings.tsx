import { Save, HardDrive, ShieldCheck } from 'lucide-react';
import type { Config } from '../types';
import { Button, SectionHeading } from '../components/ui';
import { RuleConfig } from '../features/account-role-mapping/RuleConfig';
export function Settings({
  config,
  setConfig,
  onSave,
  busy,
}: {
  config: Config;
  setConfig: (value: Config) => void;
  onSave: () => void;
  busy: boolean;
}) {
  return (
    <>
      <SectionHeading
        eyebrow="YOUR WORKSPACE PREFERENCES"
        title="Settings"
        description="Set the defaults used for new processing workflows."
        action={
          <Button onClick={onSave} busy={busy}>
            <Save size={16} />
            Save defaults
          </Button>
        }
      />
      <div className="settings-grid">
        <section className="panel">
          <h3>Processing defaults</h3>
          <p className="muted">
            Current workflows and saved templates keep their own settings. Start a new workflow to
            use updated defaults.
          </p>
          <RuleConfig config={config} setConfig={setConfig} showRules={false} />
        </section>
        <div>
          <section className="panel storage-panel">
            <HardDrive size={23} />
            <h3>Local storage</h3>
            <p>
              Original workbooks, reports, templates, and processing history are stored on this
              computer.
            </p>
            <dl>
              <dt>Workbook types</dt>
              <dd>.xlsx, .xls</dd>
              <dt>Upload limit</dt>
              <dd>30 MB per workbook</dd>
              <dt>Sheet limit</dt>
              <dd>200,000 rows / 256 columns</dd>
              <dt>Cell limit</dt>
              <dd>2,000,000 per sheet</dd>
              <dt>Concurrent jobs</dt>
              <dd>2 running / 2 queued</dd>
            </dl>
          </section>
          <section className="privacy-note">
            <ShieldCheck size={20} />
            <div>
              <strong>Keep reports private</strong>
              <p>
                Unique Mapping contains full account email addresses. Audit emails are redacted by
                default. Store and share workbooks appropriately.
              </p>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
