'use strict';
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const script = process.argv.includes('--export') ? 'export-openapi.py' : 'check-openapi.py';
const result = spawnSync(python, [path.join(root, 'scripts', script)], { cwd: root, stdio: 'inherit', windowsHide: true });
process.exitCode = result.status === 0 ? 0 : 1;
