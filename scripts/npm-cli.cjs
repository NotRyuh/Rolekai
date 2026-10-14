'use strict';
const fs = require('node:fs');
const path = require('node:path');

function resolveNpmCli({ execPath = process.execPath, npmExecPath = process.env.npm_execpath } = {}) {
  const nodeDir = path.dirname(execPath);
  const candidates = [
    npmExecPath,
    path.join(nodeDir, 'node_modules/npm/bin/npm-cli.js'),
    path.resolve(nodeDir, '../lib/node_modules/npm/bin/npm-cli.js'),
  ];
  const found = candidates.find(file => file && fs.existsSync(file) && fs.statSync(file).isFile());
  if (!found) throw new Error('npm CLI not found; check the selected Node installation');
  return found;
}

module.exports = { resolveNpmCli };
