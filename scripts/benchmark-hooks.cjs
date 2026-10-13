'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { performance } = require('node:perf_hooks');
const root = path.resolve(__dirname, '..');
const samples = 15;
const measure = (argv, input, exe = process.execPath) => {
  const values = [];
  for (let i = 0; i < samples + 1; i++) {
    const start = performance.now();
    const r = spawnSync(exe, argv, { cwd: root, input: JSON.stringify(input || {}), encoding: 'utf8', timeout: 5000, windowsHide: true });
    if (r.status !== 0) throw new Error(r.stderr);
    if (i) values.push(performance.now() - start);
  }
  values.sort((a, b) => a - b);
  return { samples, median_ms: Number(values[7].toFixed(2)), p95_ms: Number(values[14].toFixed(2)), min_ms: Number(values[0].toFixed(2)) };
};
const input = { session_id: 'benchmark', cwd: root, hook_event_name: 'Stop' };
const results = { observed_at: new Date().toISOString(), node: process.version, platform: process.platform, note: '15 sequential process launches after one warmup; local dirty Git tree; includes process startup, no LLM. No universal performance claim.', baseline_node: measure(['-e', '']), checkpoint_repeated: measure(['scripts/agent-continuity.cjs', 'hook', '--runtime', 'codex'], input), session_start: measure(['scripts/agent-continuity.cjs', 'hook', '--runtime', 'codex'], { ...input, hook_event_name: 'SessionStart' }), native_claude_monitor_no_metric: measure(['.claude/hooks/gsd-context-monitor.js'], { ...input, hook_event_name: 'PostToolUse' }) };
results.claude_adapter_no_metric = measure(['scripts/claude-context.cjs'], { ...input, hook_event_name: 'PostToolUse' });
if (process.platform === 'win32') {
  const cfg = JSON.parse(fs.readFileSync(path.join(root, '.codex/hooks.json')));
  results.baseline_powershell = measure(['-NoProfile', '-Command', ''], {}, 'powershell.exe');
  results.codex_windows_stop = measure(['-NoProfile', '-Command', cfg.hooks.Stop[0].hooks[0].commandWindows], input, 'powershell.exe');
}
fs.mkdirSync(path.join(root, 'docs/development'), { recursive: true });
fs.writeFileSync(path.join(root, 'docs/development/HOOK_BENCHMARK.json'), JSON.stringify(results, null, 2) + '\n');
console.log(JSON.stringify(results, null, 2));
