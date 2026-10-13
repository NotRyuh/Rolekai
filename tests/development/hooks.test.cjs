const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const project = process.cwd();
test('D,E: native Claude thresholds, warning debounce and PreCompact reset', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'Rolekai threshold '));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, '.planning'));
  fs.writeFileSync(path.join(root, '.planning/config.json'), JSON.stringify({ hooks: { context_warning_threshold: 25, context_critical_threshold: 15 } }));
  // No STATE in this fixture: test advisories without native asynchronous breadcrumb writes.
  const session = crypto.randomUUID();
  const files = ['', '-warned', '-compacted'].map(suffix => path.join(os.tmpdir(), `claude-ctx-${session}${suffix}.json`));
  t.after(() => files.forEach(file => { try { fs.unlinkSync(file); } catch {} }));
  const line = path.join(project, '.claude/hooks/gsd-statusline.js');
  const monitor = path.join(project, '.claude/hooks/gsd-context-monitor.js');
  const invoke = (file, data) => spawnSync(process.execPath, [file], { cwd: root, input: JSON.stringify(data), encoding: 'utf8', timeout: 4000 });
  const status = remaining => invoke(line, { session_id: session, workspace: { current_dir: root }, context_window: { remaining_percentage: remaining, total_tokens: 200000 } });
  const input = { session_id: session, cwd: root, hook_event_name: 'PostToolUse' };
  status(26); assert.equal(invoke(monitor, input).stdout, '');
  status(25); assert.match(invoke(monitor, input).stdout, /CONTEXT WARNING/);
  assert.equal(invoke(monitor, input).stdout, '');
  status(15); assert.match(invoke(monitor, input).stdout, /CONTEXT CRITICAL/);
  assert.equal(invoke(monitor, { ...input, hook_event_name: 'PreCompact' }).status, 0);
  assert.ok(!fs.existsSync(files[0]));
  assert.equal(invoke(monitor, input).stdout, '');
});
test('configured Claude exec hooks launch without Bash and preserve privacy', () => {
  const cfg = JSON.parse(fs.readFileSync('.claude/settings.json'));
  assert.ok(!cfg.permissions);
  for (const event of ['SessionStart', 'PreCompact', 'PostCompact', 'Stop', 'SessionEnd']) {
    const h = cfg.hooks[event].flatMap(g => g.hooks).find(h => h.args?.some(a => a.includes('agent-continuity')));
    const argv = h.args.map(a => a.replace('${CLAUDE_PROJECT_DIR}', project));
    const r = spawnSync(process.execPath, argv, { cwd: project, input: JSON.stringify({ session_id: 'contract-claude', cwd: project, hook_event_name: event, prompt: 'private prompt' }), encoding: 'utf8', timeout: 5000 });
    assert.equal(r.status, 0, r.stderr);
    assert.ok(!r.stdout.includes('private prompt'));
    if (event === 'SessionStart') assert.equal(JSON.parse(r.stdout).hookSpecificOutput.hookEventName, event);
  }
});
test('configured Codex Windows hook command works from a subdirectory', { skip: process.platform !== 'win32' }, () => {
  const cfg = JSON.parse(fs.readFileSync('.codex/hooks.json'));
  const command = cfg.hooks.SessionStart[0].hooks[0].commandWindows;
  const r = spawnSync('powershell.exe', ['-NoProfile', '-Command', command], { cwd: path.join(project, 'docs'), input: JSON.stringify({ session_id: 'contract-codex', cwd: project, hook_event_name: 'SessionStart' }), encoding: 'utf8', timeout: 6000 });
  assert.equal(r.status, 0, r.stderr);
  assert.equal(JSON.parse(r.stdout).hookSpecificOutput.hookEventName, 'SessionStart');
});
test('D: Claude native warning produces one auxiliary technical checkpoint', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'Rolekai warning '));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  spawnSync('git', ['init', '--quiet', root]);
  fs.mkdirSync(path.join(root, '.planning'));
  fs.writeFileSync(path.join(root, '.planning/config.json'), JSON.stringify({ hooks: { context_warning_threshold: 25, context_critical_threshold: 15 } }));
  const session = crypto.randomUUID();
  const bridge = path.join(os.tmpdir(), `claude-ctx-${session}.json`);
  const warned = path.join(os.tmpdir(), `claude-ctx-${session}-warned.json`);
  t.after(() => [bridge, warned].forEach(file => { try { fs.unlinkSync(file); } catch {} }));
  fs.writeFileSync(bridge, JSON.stringify({ session_id: session, remaining_percentage: 25, used_pct: 75, timestamp: Math.floor(Date.now() / 1000) }));
  const argv = [path.join(project, 'scripts/claude-context.cjs')];
  const input = JSON.stringify({ session_id: session, cwd: root, hook_event_name: 'PostToolUse' });
  const first = spawnSync(process.execPath, argv, { cwd: root, input, encoding: 'utf8' });
  assert.equal(first.status, 0); assert.match(first.stdout, /CONTEXT WARNING/);
  const dirs = fs.readdirSync(path.join(root, '.planning/.continuity/sessions'));
  const checkpoints = fs.readdirSync(path.join(root, '.planning/.continuity/sessions', dirs[0])).filter(f => f.startsWith('checkpoint-'));
  assert.equal(checkpoints.length, 1);
  const cp = JSON.parse(fs.readFileSync(path.join(root, '.planning/.continuity/sessions', dirs[0], checkpoints[0])));
  assert.equal(cp.event, 'context-warning');
  assert.equal(cp.runtime, 'claude');
  const second = spawnSync(process.execPath, argv, { cwd: root, input, encoding: 'utf8' });
  assert.equal(second.stdout, '');
  assert.equal(fs.readdirSync(path.join(root, '.planning/.continuity/sessions', dirs[0])).filter(f => f.startsWith('checkpoint-')).length, 1);
});
