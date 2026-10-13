'use strict';
// Temporary new files only; never overwrites user work. Both gates must reject them.
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const npmCli = process.env.npm_execpath || path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const cases = [
  ['apps/web/src/quality-negative-control.ts', 'export const broken: string = 123;\n', process.execPath, [npmCli, 'run', 'typecheck']],
  ['apps/api/tests/test_quality_negative_control.py', 'def test_negative_control():\n    assert False, "intentional quality control"\n', python, ['-m', 'pytest', 'apps/api/tests/test_quality_negative_control.py', '-q']],
];
for (const [relative, content, executable, argv] of cases) {
  const file = path.resolve(root, relative);
  if (!file.startsWith(root + path.sep)) throw new Error('Control file outside workspace');
  fs.writeFileSync(file, content, { flag: 'wx' });
  try {
    const result = spawnSync(executable, argv, { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 30000 });
    if (result.status !== 1 && result.status !== 2) throw new Error('Gate did not reject the negative control: ' + relative);
    const expected = relative.endsWith('.ts') ? /TS2322/ : /intentional quality control/;
    if (!expected.test(result.stdout + result.stderr)) throw new Error('Negative control failed for an unrelated reason');
    console.log(relative + ': intentionally invalid input rejected; file restored.');
  } finally { fs.unlinkSync(file); }
}
