// Usage: node scripts/check_syntax.js <file.js>...  Parses each Workflow script without running it.
const fs = require('fs')
const AF = Object.getPrototypeOf(async function () {}).constructor
for (const f of process.argv.slice(2)) {
  const s = fs.readFileSync(f, 'utf8').replace(/^export const meta = /m, 'const meta = ')
  try {
    new AF('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', 'workflow', s)
    console.log('ok', f)
  } catch (e) {
    console.error('FAIL', f, e.message)
    process.exitCode = 1
  }
}
