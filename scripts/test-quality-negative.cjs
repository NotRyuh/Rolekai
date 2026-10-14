'use strict';
// Temporary new files only; never overwrites user work. Both gates must reject them.
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const { resolveNpmCli } = require('./npm-cli.cjs');
const npmCli = resolveNpmCli();
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const cases = [
  ['apps/web/src/quality-negative-control.ts', 'export const broken: string = 123;\n', process.execPath, [npmCli, 'run', 'typecheck'], 2, /TS2322/],
  ['apps/api/tests/test_quality_negative_control.py', 'def test_negative_control():\n    assert False, "intentional quality control"\n', python, ['-m', 'pytest', '-c', 'apps/api/pyproject.toml', 'apps/api/tests/test_quality_negative_control.py', '-q'], 1, /intentional quality control/],
];
for (const [relative, content, executable, argv, expectedExit, expected] of cases) {
  const file = path.resolve(root, relative);
  if (!file.startsWith(root + path.sep)) throw new Error('Control file outside workspace');
  fs.writeFileSync(file, content, { flag: 'wx' });
  try {
    const result = spawnSync(executable, argv, { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 30000 });
    if (result.error || result.status !== expectedExit) throw new Error('Negative control has unexpected process exit: ' + relative + ' expected=' + expectedExit + ' actual=' + result.status);
    if (!expected.test(result.stdout + result.stderr)) throw new Error('Negative control failed for an unrelated reason: ' + relative);
    console.log(relative + ': intended diagnostic detected, exit=' + result.status + '; temporary file removed in cleanup.');
  } finally { fs.unlinkSync(file); }
}
