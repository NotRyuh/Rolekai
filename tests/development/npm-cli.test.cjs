'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

function layout(t) {
  const base = path.resolve(os.tmpdir());
  const root = fs.mkdtempSync(path.join(base, 'rolekai-npmcli-'));
  t.after(() => {
    if (path.dirname(path.resolve(root)) !== base || !path.basename(root).startsWith('rolekai-npmcli-')) throw new Error('Unsafe test cleanup target');
    fs.rmSync(root, { recursive: true });
  });
  const executable = path.join(root, 'bin', 'node');
  const install = relative => {
    const file = path.join(root, relative);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, '// npm entrypoint fixture\n', { flag: 'wx' });
    return file;
  };
  return { root, executable, install };
}

test('direct node invocation resolves npm from a Linux Node distribution', t => {
  const { resolveNpmCli } = require('../../scripts/npm-cli.cjs');
  const fixture = layout(t);
  const expected = fixture.install('lib/node_modules/npm/bin/npm-cli.js');
  assert.equal(resolveNpmCli({ execPath: fixture.executable, npmExecPath: null }), expected);
});

test('direct node invocation still resolves the Windows adjacent installation', t => {
  const { resolveNpmCli } = require('../../scripts/npm-cli.cjs');
  const fixture = layout(t);
  const expected = fixture.install('bin/node_modules/npm/bin/npm-cli.js');
  assert.equal(resolveNpmCli({ execPath: fixture.executable, npmExecPath: null }), expected);
});

test('npm-run invocation uses its actual npm entrypoint', t => {
  const { resolveNpmCli } = require('../../scripts/npm-cli.cjs');
  const fixture = layout(t);
  fixture.install('lib/node_modules/npm/bin/npm-cli.js');
  const expected = fixture.install('custom/npm-cli.js');
  assert.equal(resolveNpmCli({ execPath: fixture.executable, npmExecPath: expected }), expected);
});

test('a missing npm installation fails before running a compiler control', t => {
  const { resolveNpmCli } = require('../../scripts/npm-cli.cjs');
  const fixture = layout(t);
  assert.throws(() => resolveNpmCli({ execPath: fixture.executable, npmExecPath: null }), /npm CLI not found/);
});
