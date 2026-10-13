'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const file = path.resolve(__dirname, '../.env');
if (fs.existsSync(file)) {
  console.log('Existing .env preserved.');
} else {
  const password = crypto.randomBytes(32).toString('base64url');
  const token = crypto.randomBytes(32).toString('base64url');
  fs.writeFileSync(file, `POSTGRES_PASSWORD=${password}\nPOSTGRES_PORT=15432\nDATABASE_URL=postgresql://rolekai:${password}@127.0.0.1:15432/rolekai\nTEST_DATABASE_URL=postgresql://rolekai:${password}@127.0.0.1:15432/rolekai_foundation_test\nDATABASE_CONNECT_TIMEOUT_SECONDS=2\nCURRENT_OWNER_ID=00000000-0000-0000-0000-000000000001\nAPI_ACCESS_TOKEN=${token}\n`, { flag: 'wx', mode: 0o600 });
  console.log('Created ignored local .env with random development password.');
}
