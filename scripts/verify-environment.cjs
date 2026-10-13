'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const tool = '.codex/gsd-core/bin/gsd-tools.cjs';
const checks = [];
function native(name, argv, accept) {
  const r = spawnSync(process.execPath, [tool, ...argv], { cwd: root, encoding: 'utf8', timeout: 15000, windowsHide: true });
  let value;
  try { value = JSON.parse(r.stdout); } catch { value = null; }
  const ok = r.status === 0 && value && accept(value);
  checks.push({ name, ok: !!ok, result: value });
  return value;
}
const suite = spawnSync(process.execPath, ['--test', 'tests/development/continuity.test.cjs', 'tests/development/hooks.test.cjs'], { cwd: root, encoding: 'utf8', timeout: 60000, windowsHide: true });
process.stdout.write(suite.stdout); process.stderr.write(suite.stderr);
checks.push({ name: 'development suite', ok: suite.status === 0, exit_code: suite.status, test_count: Number(suite.stdout.match(/tests (\d+)/)?.[1] || 0), passed: Number(suite.stdout.match(/pass (\d+)/)?.[1] || 0), failed: Number(suite.stdout.match(/fail (\d+)/)?.[1] || 0) });
for (const dir of fs.readdirSync(path.join(root, '.planning/phases'))) {
  const files = fs.readdirSync(path.join(root, '.planning/phases', dir)).filter(file => file.endsWith('-PLAN.md'));
  for (const file of files) {
    const plan = '.planning/phases/' + dir + '/' + file;
    native('structure ' + file, ['verify', 'plan-structure', plan], v => v.valid && !v.errors.length && !v.warnings.length && v.task_count === 3);
    native('frontmatter ' + file, ['frontmatter', 'validate', plan, '--schema', 'plan'], v => v.valid);
  }
}
native('roadmap phase IDs', ['roadmap', 'validate'], v => !v.warnings.length);
native('planning consistency', ['validate', 'consistency'], v => v.passed && !v.warnings.length);
native('native snapshot', ['planning', 'inspect'], v => !!v.schema_version);
const health = native('health errors (known upstream advisories retained)', ['validate', 'health'], v => !v.errors.length);
const sources = JSON.parse(fs.readFileSync(path.join(root, '.planning/intel/sources.json')));
const sourceOK = sources.sources.length === 9 && sources.sources.every(source => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, source.path))).digest('hex') === source.sha256);
checks.push({ name: 'nine authoritative source hashes preserved', ok: sourceOK });
checks.push({ name: 'no product implementation', ok: !['apps', 'packages', 'compose.yaml'].some(p => fs.existsSync(path.join(root, p))) });
for (const file of ['.claude/settings.json', '.codex/hooks.json']) {
  const config = JSON.parse(fs.readFileSync(path.join(root, file)));
  const signatures = Object.entries(config.hooks).flatMap(([event, groups]) => groups.flatMap(g => g.hooks.map(h => event + ':' + (g.matcher || '') + ':' + JSON.stringify(h))));
  checks.push({ name: file + ' hook idempotence', ok: new Set(signatures).size === signatures.length });
}
const report = { observed_at: new Date().toISOString(), checks, passed: checks.every(check => check.ok), limitations: ['Native Codex project/hook trust review still required; no bypass.', 'Live compaction and LLM-assisted execution were not forced; lifecycle/threshold tests are simulations.', 'GSD standard profile triggers W010 for optional full-profile roles; official ingest report triggers upstream W019.'] };
fs.writeFileSync(path.join(root, 'docs/development/VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
const record = spawnSync(process.execPath, ['scripts/agent-continuity.cjs', 'test-result', '--session', 'environment-verification', '--runtime', 'codex', '--label', 'development-suite-and-native-planning-validation', '--exit-code', report.passed ? '0' : '1'], { cwd: root, encoding: 'utf8', windowsHide: true });
console.log(JSON.stringify({ passed: report.passed, checks: checks.length, failed: checks.filter(c => !c.ok).map(c => c.name), health_warnings: health?.warnings?.map(w => w.code), report: 'docs/development/VERIFICATION.json' }, null, 2));
if (!report.passed || record.status !== 0) process.exitCode = 1;
