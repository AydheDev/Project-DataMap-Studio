import { LockKeyhole, ShieldCheck } from 'lucide-react';
import type { Config } from '../../types';
import { Toggle } from '../../components/ui';
export const DEFAULT_CONFIG: Config = {
  include_zero_counts: true,
  exclude_invalid_emails: true,
  include_full_audit_emails: false,
  login_day_first: true,
};
export function RuleConfig({
  config,
  setConfig,
  showRules = true,
}: {
  config: Config;
  setConfig: (config: Config) => void;
  showRules?: boolean;
}) {
  return (
    <>
      {showRules && (
        <div className="locked-rules">
          <div className="rules-title">
            <ShieldCheck size={19} />
            <strong>Business rules</strong>
            <span>
              <LockKeyhole size={12} />
              Protected
            </span>
          </div>
          <ol>
            <li>
              <strong>Eligibility</strong>
              <span>
                Valid Salesforce Last login. Blank values and Excel errors are excluded. Fed ID is
                never used.
              </span>
            </li>
            <li>
              <strong>Approved roles</strong>
              <span>Match the uploaded role list, ignoring case and repeated whitespace.</span>
            </li>
            <li>
              <strong>Account email</strong>
              <span>
                FDS Email first, EIP Email when missing. Trim spaces and convert to lowercase.
              </span>
            </li>
            <li>
              <strong>Deduplication & counting</strong>
              <span>
                One mapping per Market + Role + Email. Keep different roles and markets; count
                unique accounts.
              </span>
            </li>
          </ol>
        </div>
      )}
      <div className="configuration">
        <Toggle
          title="Include zero-count roles"
          description="Show every approved role in each market that has eligible mappings."
          checked={config.include_zero_counts}
          onChange={(v) => setConfig({ ...config, include_zero_counts: v })}
        />
        <Toggle
          title="Exclude invalid email formats"
          description="Flag invalid addresses in Data Quality and exclude them from the mapping."
          checked={config.exclude_invalid_emails}
          onChange={(v) => setConfig({ ...config, exclude_invalid_emails: v })}
        />
        <Toggle
          title="Day-first login dates"
          description="Read ambiguous dates such as 03/04/2026 as 3 April. ISO dates remain unchanged."
          checked={config.login_day_first}
          onChange={(v) => setConfig({ ...config, login_day_first: v })}
        />
        <Toggle
          title="Full emails in excluded-record audit"
          description="Off by default. Unique Mapping always includes full account emails."
          checked={config.include_full_audit_emails}
          onChange={(v) => setConfig({ ...config, include_full_audit_emails: v })}
          sensitive
        />
      </div>
    </>
  );
}
