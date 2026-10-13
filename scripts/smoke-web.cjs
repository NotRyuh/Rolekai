'use strict';
const path = require('node:path');
const http = require('node:http');
const { spawn } = require('node:child_process');
async function main() {
  const reservation = http.createServer();
  await new Promise(resolve => reservation.listen(0, '127.0.0.1', resolve));
  const port = reservation.address().port;
  await new Promise(resolve => reservation.close(resolve));
  const child = spawn(process.execPath, [path.resolve('node_modules/next/dist/bin/next'), 'start', '--hostname', '127.0.0.1', '--port', String(port)], { cwd: path.resolve('apps/web'), windowsHide: true, stdio: 'ignore', env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1' } });
  let ended = false;
  child.on('exit', () => { ended = true; });
  try {
    const deadline = Date.now() + 15000;
    while (Date.now() < deadline && !ended) {
      try {
        const response = await fetch('http://127.0.0.1:' + port, { signal: AbortSignal.timeout(1000) });
        const html = await response.text();
        if (response.status !== 200 || !html.includes('<h1>Rolekai</h1>')) throw new Error('Unexpected shell response');
        console.log('Production web smoke: HTTP 200 and Rolekai shell verified.');
        return;
      } catch { await new Promise(resolve => setTimeout(resolve, 200)); }
    }
    throw new Error('Production web smoke failed to become ready.');
  } finally {
    child.kill();
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
