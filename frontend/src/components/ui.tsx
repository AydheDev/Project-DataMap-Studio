import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { ArrowRight, LoaderCircle, Check, AlertCircle, Inbox } from 'lucide-react';
export function Button({
  children,
  variant = 'primary',
  busy,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost';
  busy?: boolean;
}) {
  return (
    <button
      {...props}
      className={['button', variant, props.className].filter(Boolean).join(' ')}
      disabled={props.disabled || busy}
    >
      {busy && <LoaderCircle size={16} className="spin" />}
      {children}
    </button>
  );
}
export function Badge({ status, children }: { status?: string; children?: ReactNode }) {
  return (
    <span className={'badge ' + (status || '')}>
      {status === 'succeeded' && <Check size={12} />}
      {status === 'failed' && <AlertCircle size={12} />}
      {(status === 'running' || status === 'queued') && <LoaderCircle size={12} className="spin" />}
      {children || status}
    </span>
  );
}
export function Empty({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Inbox size={25} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  );
}
export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {action}
    </div>
  );
}
export function Stat({
  label,
  value,
  detail,
  accent,
}: {
  label: string;
  value: string;
  detail: string;
  accent?: boolean;
}) {
  return (
    <div className={'stat ' + (accent ? 'accent' : '')}>
      <p>{label}</p>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
export function Toggle({
  checked,
  onChange,
  title,
  description,
  sensitive = false,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  title: string;
  description: string;
  sensitive?: boolean;
}) {
  return (
    <label className={'toggle-row ' + (sensitive && checked ? 'sensitive' : '')}>
      <span>
        <strong>{title}</strong>
        <small>{description}</small>
      </span>
      <input
        type="checkbox"
        role="switch"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        aria-label={title}
      />
    </label>
  );
}
export function NextButton({ children, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <Button {...props}>
      {children}
      <ArrowRight size={16} />
    </Button>
  );
}
