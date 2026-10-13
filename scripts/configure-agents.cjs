'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const write = (file, value) => fs.writeFileSync(path.join(root, file), JSON.stringify(value, null, 2) + '\n');
const localGenerated = JSON.parse(fs.readFileSync(path.join(root, '.claude/settings.local.json')));
const projectFile = path.join(root, '.claude/settings.json');
const project = fs.existsSync(projectFile) ? JSON.parse(fs.readFileSync(projectFile)) : {};
const generated = structuredClone(localGenerated.hooks ? localGenerated : project);
// Keep unrelated user entries. Normalize only installer-owned GSD and our hooks.
for (const [event, groups] of Object.entries(project.hooks || {})) {
  for (const group of groups) group.hooks = group.hooks.filter(h => !JSON.stringify(h).includes('gsd-') && !JSON.stringify(h).includes('agent-continuity') && !JSON.stringify(h).includes('claude-context'));
  project.hooks[event] = groups.filter(g => g.hooks.length);
}
project.hooks ||= {};
for (const [event, groups] of Object.entries(generated.hooks)) {
  for (const group of groups) {
    const hooks = [];
    for (const h of group.hooks) {
      const name = h.command.match(/(gsd-[\w-]+\.js)/)?.[1];
      if (!name || name === 'gsd-check-update.js') continue; // offline; .sh hooks are inactive optional features
      hooks.push({ type: 'command', command: 'node', args: [name === 'gsd-context-monitor.js' ? '${CLAUDE_PROJECT_DIR}/scripts/claude-context.cjs' : '${CLAUDE_PROJECT_DIR}/.claude/hooks/' + name], timeout: Math.min(h.timeout || 5, 10) });
    }
    if (hooks.length) (project.hooks[event] ||= []).push({ ...(group.matcher ? { matcher: group.matcher.replace(/Bash/g, 'Bash|PowerShell') } : {}), hooks });
  }
}
for (const event of ['SessionStart', 'PreCompact', 'PostCompact', 'Stop', 'SessionEnd']) {
  (project.hooks[event] ||= []).push({ hooks: [{ type: 'command', command: 'node', args: ['${CLAUDE_PROJECT_DIR}/scripts/agent-continuity.cjs', 'hook', '--runtime', 'claude'], timeout: 5 }] });
}
project.statusLine = { type: 'command', command: 'node .claude/hooks/gsd-statusline.js' };
if (project.permissions?.allow) {
  const added = new Set(['Bash(npx gsd-core *)', 'Read(.planning/*)', 'Edit(.planning/*)', 'Read(STATE.md)', 'Edit(STATE.md)']);
  project.permissions.allow = project.permissions.allow.filter(rule => !added.has(rule));
  if (!project.permissions.allow.length) delete project.permissions.allow;
  if (!Object.keys(project.permissions).length) delete project.permissions;
}
// No permissions grants, global settings or LLM hooks added by our integration.
write('.claude/settings.json', project);
write('.claude/settings.local.json', {}); // installer-generated grants/hooks would otherwise duplicate project hooks
const codexFile = path.join(root, '.codex/hooks.json');
const codex = JSON.parse(fs.readFileSync(codexFile));
for (const event of Object.keys(codex.hooks || {})) {
  codex.hooks[event] = codex.hooks[event].map(g => ({ ...g, hooks: g.hooks.filter(h => !JSON.stringify(h).includes('gsd-check-update') && !JSON.stringify(h).includes('agent-continuity')) })).filter(g => g.hooks.length);
}
for (const event of ['SessionStart', 'PreCompact', 'PostCompact', 'Stop', 'SessionEnd', 'Interrupt']) {
  (codex.hooks[event] ||= []).push({ hooks: [{ type: 'command', command: 'node "$(git rev-parse --show-toplevel)/scripts/agent-continuity.cjs" hook --runtime codex', commandWindows: 'powershell.exe -NoProfile -Command "node ((git rev-parse --show-toplevel) + \'/scripts/agent-continuity.cjs\') hook --runtime codex"', timeout: 5 }] });
}
write('.codex/hooks.json', codex);
console.log('Configured local Node hooks; GSD guards retained; no permission grants or online update hooks.');
