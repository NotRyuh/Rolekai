'use strict';
// Invoke GSD's existing monitor. Only its actual warning output triggers a
// technical checkpoint; this adapter does not compute or monitor percentages.
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
try {
  const input = fs.readFileSync(0, 'utf8');
  if (input.length > 128 * 1024) process.exit(0);
  const data = JSON.parse(input);
  if (data.cwd && fs.realpathSync(data.cwd) !== fs.realpathSync(process.cwd())) process.exit(0);
  const root = path.resolve(__dirname, '..');
  const native = spawnSync(process.execPath, [path.join(root, '.claude/hooks/gsd-context-monitor.js')], { input, encoding: 'utf8', cwd: process.cwd(), timeout: 2000, windowsHide: true });
  if (native.stdout) process.stdout.write(native.stdout);
  if (/CONTEXT (WARNING|CRITICAL)/.test(native.stdout || '')) {
    spawnSync(process.execPath, [path.join(__dirname, 'agent-continuity.cjs'), 'checkpoint', '--runtime', 'claude', '--session', data.session_id, '--event', /CONTEXT CRITICAL/.test(native.stdout) ? 'context-critical' : 'context-warning'], { cwd: data.cwd || process.cwd(), timeout: 2000, windowsHide: true, stdio: 'ignore' });
    // No checkpoint output is injected after tool calls.
  }
} catch {} // advisory adapter never blocks normal operations
