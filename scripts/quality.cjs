'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const { resolveNpmCli } = require('./npm-cli.cjs');
const npmCli = resolveNpmCli();
const unitOnly = process.argv.includes('--unit-only');
const report = { plan: '03-01', started_at: new Date().toISOString(), mode: unitOnly ? 'unit-only' : 'full', checks: [] };
const commands = [
  ['Python 3.14 interpreter', python, ['-c', 'import sys; assert sys.version_info[:2] == (3, 14), "Foundation requires Python 3.14; select that interpreter before creating .venv"']],
  ['TypeScript', process.execPath, [npmCli, 'run', 'typecheck']],
  ['ESLint', process.execPath, [npmCli, 'run', 'lint']],
  ['Next production build', process.execPath, [npmCli, 'run', 'build']],
  ['Ruff', python, ['-m', 'ruff', 'check', '--config', 'apps/api/pyproject.toml', 'apps/api', 'scripts/export-openapi.py', 'scripts/check-openapi.py', 'scripts/openapi_artifacts.py']],
  ['OpenAPI and generated TypeScript drift', process.execPath, [npmCli, 'run', 'contracts:check']],
  ['API tests', python, ['-m', 'pytest', '-c', 'apps/api/pyproject.toml', 'apps/api/tests', '-q', ...(unitOnly ? ['-m', 'not integration'] : [])]],
  ['Python dependency consistency', python, ['-m', 'pip', 'check']],
  ['Agent Continuity tests', process.execPath, [npmCli, 'test']],
  ['Web production smoke', process.execPath, ['scripts/smoke-web.cjs']],
];
let failed = false;
for (const [label, executable, argv] of commands) {
  console.log(label);
  const start = Date.now();
  const result = spawnSync(executable, argv, { cwd: root, stdio: 'inherit', windowsHide: true, timeout: 180000, env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1' } });
  report.checks.push({ label, exit_code: result.status, duration_ms: Date.now() - start });
  if (result.status !== 0) { failed = true; break; }
}
report.completed_at = new Date().toISOString();
report.passed = !failed;
report.domain_openapi_drift = 'mandatory; checks OpenAPI and TypeScript against current DTOs';
fs.mkdirSync(path.join(root, '.planning/.continuity'), { recursive: true });
fs.writeFileSync(path.join(root, '.planning/.continuity/ingestion-03-quality.json'), JSON.stringify(report, null, 2) + '\n');
if (failed) process.exitCode = 1;
