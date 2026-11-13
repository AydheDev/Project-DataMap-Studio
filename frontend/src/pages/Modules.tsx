import { GitBranch, Blocks, Code2 } from 'lucide-react';
import type { Module, Page } from '../types';
import { Badge, Button, SectionHeading } from '../components/ui';
export function Modules({
  modules,
  navigate,
}: {
  modules: Module[];
  navigate: (page: Page) => void;
}) {
  return (
    <>
      <SectionHeading
        eyebrow="ONE WORKSPACE, ROOM TO GROW"
        title="Module management"
        description="Independent features, connected through a shared processing platform."
      />
      <div className="module-grid">
        {modules.map((module) => (
          <section className="panel module-card" key={module.id}>
            <span className="module-icon">
              {module.enabled ? <GitBranch size={28} /> : <Blocks size={28} />}
            </span>
            <Badge status={module.enabled ? 'succeeded' : undefined}>
              {module.enabled ? 'Active' : 'Developer example'}
            </Badge>
            <h3>{module.name}</h3>
            <p>{module.description}</p>
            <dl>
              <dt>Version</dt>
              <dd>{module.version}</dd>
              <dt>Inputs</dt>
              <dd>{module.inputs.length} workbooks</dd>
              <dt>Entry point</dt>
              <dd>
                <code>{module.ui_route}</code>
              </dd>
            </dl>
            <Button
              variant={module.enabled ? 'primary' : 'secondary'}
              disabled={!module.enabled}
              onClick={() => navigate('mapping')}
            >
              {module.enabled ? 'Open module' : 'Not enabled'}
            </Button>
          </section>
        ))}
      </div>
      <div className="info-banner">
        <Code2 size={21} />
        <div>
          <strong>Designed for independent extensions</strong>
          <p>
            Modules declare their inputs, configuration, validation, processor, and exporter. Only
            trusted modules installed with the application can run. See docs/MODULES.md to add a
            feature.
          </p>
        </div>
      </div>
    </>
  );
}
