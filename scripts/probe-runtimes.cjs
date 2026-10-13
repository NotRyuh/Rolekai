'use strict';
// Read-only runtime initialization/discovery: never submits a model turn.
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
function probe(exe, argv, requests, consume) {
  return new Promise(resolve => {
    const child = spawn(exe, argv, { cwd: root, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    let buffer = '', done = false;
    const finish = result => { if (done) return; done = true; clearTimeout(timer); child.kill(); resolve(result); };
    const timer = setTimeout(() => finish({ ok: false, reason: 'initialization timeout (no model request submitted)' }), 20000);
    child.on('error', e => finish({ ok: false, reason: e.message }));
    child.on('exit', code => finish({ ok: false, reason: 'runtime exited: ' + code }));
    child.stderr.on('data', () => {}); // never persist runtime diagnostics containing private machine info
    child.stdout.on('data', bytes => {
      buffer += bytes.toString();
      let index;
      while ((index = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, index); buffer = buffer.slice(index + 1);
        try { consume(JSON.parse(line), child, finish); } catch {}
      }
    });
    for (const request of requests) child.stdin.write(JSON.stringify(request) + '\n');
  });
}
async function main() {
  const codex = await probe('codex', ['app-server', '--stdio', '--strict-config'], [{ id: 1, method: 'initialize', params: { clientInfo: { name: 'rolekai-verification', version: '1.0.0' }, capabilities: {} } }], (data, child, finish) => {
    if (data.id === 1 && data.result) {
      child.stdin.write(JSON.stringify({ method: 'initialized', params: {} }) + '\n');
      child.stdin.write(JSON.stringify({ id: 2, method: 'skills/list', params: { cwds: [root], forceReload: true } }) + '\n');
    }
    if (data.id === 2) {
      const items = data.result?.data || [];
      const names = items.flatMap(item => (item.skills || []).map(skill => skill.name)).filter(name => name.startsWith('gsd-'));
      finish({ ok: names.includes('gsd-resume-work') && names.includes('gsd-plan-phase'), commands: [...new Set(names)].sort(), error: data.error ? 'skills/list rejected' : null });
    }
  });
  const claude = await probe('claude', ['-p', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose', '--setting-sources', 'project,local'], [{ type: 'control_request', request_id: 'rolekai-init', request: { subtype: 'initialize' } }], (data, child, finish) => {
    if (data.type === 'control_response') {
      const response = data.response?.response || {};
      const commands = (response.commands || []).map(c => typeof c === 'string' ? c : c.name).filter(n => n?.startsWith('gsd-'));
      finish({ ok: commands.includes('gsd-resume-work') && commands.includes('gsd-plan-phase'), commands: commands.sort(), error: data.response?.subtype === 'error' ? 'initialize rejected' : null });
    }
  });
  const report = { observed_at: new Date().toISOString(), note: 'Real CLI startup/discovery only; no model turn or forced compaction. Hook trust is not bypassed.', codex, claude };
  fs.writeFileSync(path.join(root, 'docs/development/RUNTIME_VERIFICATION.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
}
main().catch(e => { console.error(e.message); process.exitCode = 1; });
