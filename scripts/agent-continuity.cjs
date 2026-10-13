#!/usr/bin/env node
'use strict';
// Auxiliary technical metadata only. GSD owns semantic state, tasks and handoff.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const args = process.argv.slice(2);
const command = args[0];
const option = (key, fallback) => { const i = args.indexOf('--' + key); return i < 0 ? fallback : args[i + 1]; };
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const read = file => { try { return fs.readFileSync(file, 'utf8'); } catch (e) { if (e.code === 'ENOENT') return ''; throw e; } };
const json = file => { const text = read(file); return text ? JSON.parse(text) : null; };
function rootAt(start) {
  let current = path.resolve(start);
  for (;;) {
    if (fs.existsSync(path.join(current, '.git')) && fs.existsSync(path.join(current, '.planning'))) return fs.realpathSync(current);
    const parent = path.dirname(current);
    if (parent === current) throw new Error('PROJECT_NOT_FOUND: Git + .planning required');
    current = parent;
  }
}
function safeText(value, limit = 240) {
  const text = String(value || '').replace(/[\r\n\x00-\x1f]/g, ' ').trim().slice(0, limit);
  if (/sk-[\w-]+|(?:api[_-]?key|token|password|secret)\s*[:=]|Bearer\s+\S+/i.test(text)) throw new Error('SENSITIVE_METADATA: use a short non-sensitive description');
  return text;
}
function atomic(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = file + '.' + crypto.randomUUID() + '.tmp';
  try { fs.writeFileSync(temp, content, { flag: 'wx', mode: 0o600 }); fs.renameSync(temp, file); }
  finally { try { fs.unlinkSync(temp); } catch {} }
}
function lock(file, fn) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  let fd;
  try { fd = fs.openSync(file, 'wx'); } catch { throw new Error('BUSY_LOCK: retry; do not delete a live lock'); }
  try { fs.writeFileSync(fd, JSON.stringify({ pid: process.pid, created_at: new Date().toISOString() })); return fn(); }
  finally { fs.closeSync(fd); fs.unlinkSync(file); }
}
function state(root) {
  const file = path.join(root, '.planning/STATE.md');
  const text = read(file);
  const field = label => text.match(new RegExp('^' + label + ':\\s*(.*)$', 'm'))?.[1] || null;
  let task = null;
  try { task = json(path.join(root, '.planning/HANDOFF.json'))?.task ?? null; } catch {}
  return { state_ref: '.planning/STATE.md', state_sha256: hash(text), position: { phase: field('Phase'), plan: field('Plan'), task, status: field('Status') } };
}
function planningHash(root) {
  const files = [];
  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.name.startsWith('.') && entry.name !== '.continue-here.md') continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile() && /\.(md|json)$/.test(entry.name)) files.push([path.relative(root, full), hash(read(full))]);
    }
  }
  walk(path.join(root, '.planning'));
  return hash(JSON.stringify(files.sort((a, b) => a[0].localeCompare(b[0]))));
}
function git(root) {
  const call = argv => spawnSync('git', ['-C', root, ...argv], { encoding: 'utf8', timeout: 2000, windowsHide: true, maxBuffer: 2 * 1024 * 1024 });
  const status = call(['status', '--porcelain=v1', '-z', '--untracked-files=all']);
  if (status.status !== 0) return { available: false, branch: null, head: null, files: [], status_sha256: null };
  const parts = status.stdout.split('\0').filter(Boolean);
  const files = [];
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    const item = { status: part.slice(0, 2), path: part.slice(3).replace(/\\/g, '/') };
    if (/[RC]/.test(item.status)) item.from = parts[++i];
    if (!item.path.startsWith('.planning/.continuity/') && !/(^|\/)(?:\.env(?:\.|$)|\.secrets|credentials|auth\.json)/i.test(item.path)) files.push(item);
  }
  return { available: true, branch: call(['symbolic-ref', '--short', 'HEAD']).stdout.trim() || null, head: call(['rev-parse', '--verify', 'HEAD']).stdout.trim() || null, status_ref: 'git status --porcelain=v1 -z --untracked-files=all (private metadata excluded)', status_sha256: hash(JSON.stringify(files)), files };
}
function native(root, argv) {
  const tool = process.env.ROLEKAI_GSD_TOOLS || path.join(root, '.codex/gsd-core/bin/gsd-tools.cjs');
  const result = spawnSync(process.execPath, [tool, ...argv], { cwd: root, encoding: 'utf8', timeout: 15000, windowsHide: true, env: { ...process.env, GSD_HOME: path.join(root, '.tools/home') } });
  if (result.status !== 0) throw new Error('GSD_FAILED: ' + safeText(result.stderr || result.stdout));
  return result.stdout.trim() ? JSON.parse(result.stdout) : {};
}
function context(root, session, runtime) {
  if (!['codex', 'claude', 'manual'].includes(runtime)) throw new Error('INVALID_RUNTIME');
  if (typeof session !== 'string' || !session || session.length > 256) throw new Error('SESSION_REQUIRED: --session <stable-id>');
  const dir = path.join(root, '.planning/.continuity/sessions', hash(runtime + ':' + session).slice(0, 24));
  fs.mkdirSync(dir, { recursive: true });
  return { root, dir, session_id: path.basename(dir), runtime };
}
function checkpoint(ctx, event) {
  return lock(path.join(ctx.dir, '.lock'), () => {
    const data = { schema_version: 1, session_id: ctx.session_id, runtime: ctx.runtime, event, ...state(ctx.root), git: git(ctx.root), tests: json(path.join(ctx.dir, 'tests.json')), handoff_ref: fs.existsSync(path.join(ctx.root, '.planning/HANDOFF.json')) ? '.planning/HANDOFF.json' : null };
    const digest = hash(JSON.stringify(data));
    const file = path.join(ctx.dir, 'checkpoint-' + digest.slice(0, 24) + '.json');
    if (fs.existsSync(file)) return { path: path.relative(ctx.root, file).replace(/\\/g, '/'), created: false };
    atomic(file, JSON.stringify({ ...data, created_at: new Date().toISOString() }, null, 2) + '\n');
    return { path: path.relative(ctx.root, file).replace(/\\/g, '/'), created: true };
  });
}
function resume(ctx) {
  const before = planningHash(ctx.root);
  const current = state(ctx.root);
  const handoff = json(path.join(ctx.root, '.planning/HANDOFF.json'));
  const after = planningHash(ctx.root);
  if (before !== after) throw new Error('STATE_CHANGED_DURING_READ: retry resume');
  atomic(path.join(ctx.dir, 'observed.json'), JSON.stringify({ planning_sha256: after, observed_at: new Date().toISOString() }));
  const sessionsDir = path.dirname(ctx.dir);
  const checkpoints = fs.readdirSync(sessionsDir).flatMap(dir => fs.readdirSync(path.join(sessionsDir, dir)).filter(f => /^checkpoint-.*\.json$/.test(f)).map(f => path.join(sessionsDir, dir, f)));
  checkpoints.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  return { ...current, handoff: handoff ? { next_action: safeText(handoff.next_action), phase: handoff.phase ?? null, task: handoff.task ?? null } : null, git: git(ctx.root), latest_checkpoint: checkpoints[0] ? path.relative(ctx.root, checkpoints[0]).replace(/\\/g, '/') : null, next: 'Verify actual files/tests; read the referenced GSD plan and handoff before editing.' };
}
function guarded(ctx, fn) {
  return lock(path.join(ctx.root, '.planning/.continuity/writer.lock'), () => {
    const observed = json(path.join(ctx.dir, 'observed.json'));
    if (!observed || observed.planning_sha256 !== planningHash(ctx.root)) throw new Error('STALE_STATE: run resume and verify current planning before writing');
    const result = fn();
    atomic(path.join(ctx.dir, 'observed.json'), JSON.stringify({ planning_sha256: planningHash(ctx.root), observed_at: new Date().toISOString() }));
    return result;
  });
}
function main() {
  let input;
  if (command === 'hook') {
    const raw = fs.readFileSync(0, 'utf8');
    if (raw.length > 128 * 1024) throw new Error('INPUT_TOO_LARGE');
    input = JSON.parse(raw);
  }
  const root = rootAt(process.cwd());
  if (input?.cwd && rootAt(input.cwd) !== root) throw new Error('FOREIGN_PROJECT');
  const runtime = option('runtime', 'manual');
  const session = option('session', input?.session_id);
  const ctx = context(root, session, runtime);
  if (command === 'hook') {
    const event = input.hook_event_name;
    if (!['SessionStart', 'PreCompact', 'PostCompact', 'Stop', 'SessionEnd', 'Interrupt'].includes(event)) return {};
    const cp = checkpoint(ctx, event);
    if (event === 'SessionStart') {
      const info = resume(ctx);
      return { hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: `Rolekai: ${JSON.stringify(info)}. Product execution requires explicit authorization. See AGENTS.md.` } };
    }
    return {}; // no decisions, no transcript reads, no numeric context claims
  }
  if (command === 'resume' || command === 'status') return resume(ctx);
  if (command === 'checkpoint') return checkpoint(ctx, safeText(option('event', 'manual'), 40));
  if (command === 'test-result') {
    const code = Number(option('exit-code'));
    if (!Number.isInteger(code)) throw new Error('EXIT_CODE_REQUIRED');
    const record = { label: safeText(option('label')), exit_code: code, evidence: 'explicit-report', observed_at: new Date().toISOString() };
    lock(path.join(ctx.dir, '.lock'), () => atomic(path.join(ctx.dir, 'tests.json'), JSON.stringify(record)));
    return record;
  }
  if (command === 'task') {
    const title = safeText(option('title'));
    const phase = safeText(option('phase'), 50), next = safeText(option('next'));
    if (!title || !phase || !next) throw new Error('TASK_REQUIRES_TITLE_PHASE_NEXT');
    // Native GSD todo format; additive capture, no independent task database.
    return lock(path.join(root, '.planning/.continuity/writer.lock'), () => {
      const name = hash(phase + ':' + title.toLowerCase()).slice(0, 16) + '.md';
      for (const bucket of ['pending', 'completed']) {
        const existing = path.join(root, '.planning/todos', bucket, name);
        if (fs.existsSync(existing)) return { path: path.relative(root, existing).replace(/\\/g, '/'), created: false };
      }
      const file = path.join(root, '.planning/todos/pending', name);
      atomic(file, `---\ncreated: ${new Date().toISOString()}\ntitle: ${JSON.stringify(title)}\narea: planning\nphase: ${JSON.stringify(phase)}\nfiles: []\n---\n\n## Problem\n\n${title}. GSD phase: ${phase}.\n\n## Solution\n\nNext action: ${next}\n`);
      return { path: path.relative(root, file).replace(/\\/g, '/'), created: true };
    });
  }
  if (command === 'gsd') {
    const argv = args.slice(args.indexOf('--') + 1);
    if (argv.some(arg => /^--(?:cwd|ws|workstream|project-root)(?:=|$)/.test(arg))) throw new Error('FOREIGN_PROJECT: scoping flags are not allowed');
    if (argv[0] === 'todo' && argv[2] && path.basename(argv[2]) !== argv[2]) throw new Error('INVALID_TODO_PATH');
    const allowed = argv[0] === 'state' && ['update', 'patch', 'add-decision', 'add-blocker', 'resolve-blocker', 'record-session'].includes(argv[1]) || argv[0] === 'todo' && argv[1] === 'complete';
    if (!allowed) throw new Error('GSD_MUTATION_NOT_ALLOWED: only state updates and todo completion; no commits/branches');
    return guarded(ctx, () => native(root, argv));
  }
  throw new Error('Usage: agent-continuity.cjs resume|status|task|checkpoint|test-result|gsd|hook --session ID [--runtime codex|claude|manual]');
}
try { const result = main(); if (Object.keys(result).length) process.stdout.write(JSON.stringify(result) + '\n'); }
catch (e) { if (command !== 'hook') { process.stderr.write(e.message + '\n'); process.exitCode = 1; } }
