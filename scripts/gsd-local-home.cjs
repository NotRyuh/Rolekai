// Confine installer-only os.homedir() writes (defaults/cache) to this project.
// Loaded only in the installer child; no runtime/global security setting changes.
require('node:os').homedir = () => require('node:path').resolve(__dirname, '../.tools/home');
