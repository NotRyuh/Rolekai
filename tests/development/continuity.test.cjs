const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync, spawn } = require('node:child_process');
const script = path.resolve('scripts/agent-continuity.cjs');
const native = path.resolve('.codex/gsd-core/bin/gsd-tools.cjs');
function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'Rolekai continuity spaces '));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, '.planning'), { recursive: true });
  fs.writeFileSync(path.join(root, '.planning/STATE.md'), '# Project State\n\n## Current Position\nPhase: 1 of 6 (Foundation)\nPlan: 1 of 1\nStatus: Ready to execute\n\n## Session Continuity\nLast session: 2026-10-13\nStopped at: Planning only\nResume file: None\n');
  spawnSync('git', ['init', '--quiet', root]);
  fs.writeFileSync(path.join(root, 'café file.txt'), 'changed');
  return root;
}
function run(root, args, input) {
  const r = spawnSync(process.execPath, [script, ...args], { cwd: root, input: input ? JSON.stringify(input) : undefined, encoding: 'utf8', env: { ...process.env, ROLEKAI_GSD_TOOLS: native } });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.trim() ? JSON.parse(r.stdout) : {};
}
test('A: native todo capture is idempotent and excludes raw prompt', t => {
  const root = fixture(t);
  const args = ['task', '--session', 'a', '--title', 'Review foundation', '--phase', '1', '--next', 'Read plan'];
  const a = run(root, args), b = run(root, args);
  assert.equal(a.path, b.path);
  assert.equal(fs.readdirSync(path.join(root, '.planning/todos/pending')).length, 1);
  const todos = JSON.parse(spawnSync(process.execPath, [native, 'list-todos'], { cwd: root, encoding: 'utf8' }).stdout);
  assert.equal(todos.count, 1);
});
test('B,G: shared state and progress read identically across runtimes', t => {
  const root = fixture(t);
  const a = run(root, ['resume', '--session', 'a', '--runtime', 'codex']);
  const b = run(root, ['resume', '--session', 'b', '--runtime', 'claude']);
  assert.equal(a.state_sha256, b.state_sha256);
  assert.equal(a.position.phase, '1 of 6 (Foundation)');
  run(root, ['gsd', '--session', 'a', '--runtime', 'codex', '--', 'state', 'update', 'Status', 'In progress']);
  assert.equal(run(root, ['resume', '--session', 'b']).position.status, 'In progress');
});
test('C,F,I: checkpoint has real Git/test evidence, survives interruption, repeated event is a no-op', t => {
  const root = fixture(t);
  run(root, ['test-result', '--session', 'a', '--runtime', 'codex', '--label', 'unit-tests', '--exit-code', '0']);
  const input = { cwd: root, session_id: 'a', hook_event_name: 'PreCompact', prompt: 'SECRET PROMPT', transcript_path: 'SECRET TRANSCRIPT', tool_response: 'sk-secret' };
  run(root, ['hook', '--runtime', 'codex'], input);
  run(root, ['hook', '--runtime', 'codex'], input);
  const dir = path.join(root, '.planning/.continuity/sessions');
  const files = fs.readdirSync(dir).flatMap(d => fs.readdirSync(path.join(dir, d)).filter(f => f.startsWith('checkpoint-')).map(f => path.join(dir, d, f)));
  assert.equal(files.length, 1);
  const raw = fs.readFileSync(files[0], 'utf8');
  assert.ok(!raw.includes('SECRET')); assert.ok(!raw.includes('sk-secret'));
  const cp = JSON.parse(raw);
  assert.equal(cp.tests.exit_code, 0);
  assert.equal(cp.git.available, true);
  assert.ok(cp.git.files.some(f => f.path === 'café file.txt'));
  assert.equal(cp.git.head, null); // unborn branch is valid, no fake commit
  assert.ok(run(root, ['resume', '--session', 'b']).latest_checkpoint);
});
test('D,E: numeric Codex metrics are ignored; compaction events preserve native handoff', t => {
  const root = fixture(t);
  const handoff = '{"next_action":"Read foundation plan"}';
  fs.writeFileSync(path.join(root, '.planning/HANDOFF.json'), handoff);
  for (const event of ['PreCompact', 'PostCompact', 'SessionStart']) {
    run(root, ['hook', '--runtime', 'codex'], { session_id: 'a', cwd: root, hook_event_name: event, context_window: { used_percentage: 99 } });
  }
  assert.equal(fs.readFileSync(path.join(root, '.planning/HANDOFF.json'), 'utf8'), handoff);
  assert.equal(run(root, ['resume', '--session', 'b']).handoff.next_action, 'Read foundation plan');
});
test('H: stale session cannot overwrite newer GSD state', t => {
  const root = fixture(t);
  run(root, ['resume', '--session', 'a']); run(root, ['resume', '--session', 'b']);
  run(root, ['gsd', '--session', 'a', '--', 'state', 'update', 'Status', 'In progress']);
  const stale = spawnSync(process.execPath, [script, 'gsd', '--session', 'b', '--', 'state', 'update', 'Status', 'Old state'], { cwd: root, encoding: 'utf8', env: { ...process.env, ROLEKAI_GSD_TOOLS: native } });
  assert.notEqual(stale.status, 0); assert.match(stale.stderr, /STALE_STATE/);
  assert.match(fs.readFileSync(path.join(root, '.planning/STATE.md'), 'utf8'), /Status: In progress/);
});
test('H: parallel session checkpoints are independently atomic', async t => {
  const root = fixture(t);
  await Promise.all(['a', 'b'].map(session => new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [script, 'checkpoint', '--session', session], { cwd: root, stdio: 'ignore' });
    child.on('error', reject); child.on('exit', code => code === 0 ? resolve() : reject(new Error(String(code))));
  })));
  assert.equal(fs.readdirSync(path.join(root, '.planning/.continuity/sessions')).length, 2);
});
test('hooks fail open on malformed input and refuse foreign repositories', t => {
  const root = fixture(t);
  const bad = spawnSync(process.execPath, [script, 'hook'], { cwd: root, input: 'invalid', encoding: 'utf8' });
  assert.equal(bad.status, 0);
  const foreign = fs.mkdtempSync(path.join(os.tmpdir(), 'foreign-'));
  t.after(() => fs.rmSync(foreign, { recursive: true, force: true }));
  const result = spawnSync(process.execPath, [script, 'hook'], { cwd: root, input: JSON.stringify({ cwd: foreign, session_id: '../../escape', hook_event_name: 'Stop' }), encoding: 'utf8' });
  assert.equal(result.status, 0); assert.ok(!fs.existsSync(path.join(foreign, '.planning')));
});
test('wrapped GSD mutations cannot redirect writes to another repository', t => {
  const root = fixture(t);
  run(root, ['resume', '--session', 'a']);
  const result = spawnSync(process.execPath, [script, 'gsd', '--session', 'a', '--', 'state', 'update', 'Status', 'Bad', '--cwd', os.tmpdir()], { cwd: root, encoding: 'utf8' });
  assert.notEqual(result.status, 0); assert.match(result.stderr, /FOREIGN_PROJECT/);
});
test('native todo completion and blocked progress remain interpretable by GSD', t => {
  const root = fixture(t);
  const todo = run(root, ['task', '--session', 'a', '--title', 'Review gates', '--phase', '1', '--next', 'Run gates']);
  run(root, ['resume', '--session', 'a']);
  run(root, ['gsd', '--session', 'a', '--', 'state', 'update', 'Status', 'Blocked']);
  assert.equal(run(root, ['resume', '--session', 'a']).position.status, 'Blocked');
  run(root, ['gsd', '--session', 'a', '--', 'todo', 'complete', path.basename(todo.path)]);
  assert.ok(fs.existsSync(path.join(root, '.planning/todos/completed', path.basename(todo.path))));
  const recapture = run(root, ['task', '--session', 'a', '--title', 'Review gates', '--phase', '1', '--next', 'Run gates']);
  assert.equal(recapture.created, false); assert.match(recapture.path, /completed/);
});
