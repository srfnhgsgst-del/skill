const fs = require('fs');
const path = require('path');

const MEMORY_FILE = path.resolve('.opencode/MEMORY.md');

function read() {
  if (!fs.existsSync(MEMORY_FILE)) return null;
  return fs.readFileSync(MEMORY_FILE, 'utf-8');
}

function append(text) {
  const ts = new Date().toISOString().slice(0, 10);
  const entry = `\n## ${ts}\n${text.trim()}\n`;
  fs.appendFileSync(MEMORY_FILE, entry);
}

function snapshot({ objective, done, decisions, activeFile, blockers, next }) {
  const block = `
### Session Snapshot
**Objective:** ${objective || '—'}
**Done:** ${(done || []).map(d => `\n- ${d}`).join('')}
**Decisions:** ${(decisions || []).map(d => `\n- ${d}`).join('')}
**Active File:** ${activeFile || '—'}
**Blockers:** ${blockers || '—'}
**Next:** ${next || '—'}
`;
  append(block);
}

const cmd = process.argv[2];
const args = process.argv.slice(3);

switch (cmd) {
  case 'read':
    console.log(read() || 'No MEMORY.md found');
    break;
  case 'snapshot':
    snapshot({
      objective: args[0],
      done: args[1] ? args[1].split('|') : [],
      decisions: args[2] ? args[2].split('|') : [],
      activeFile: args[3],
      blockers: args[4],
      next: args[5],
    });
    console.log('Snapshot appended.');
    break;
  case 'init':
    if (!fs.existsSync(path.dirname(MEMORY_FILE))) {
      fs.mkdirSync(path.dirname(MEMORY_FILE), { recursive: true });
    }
    if (!fs.existsSync(MEMORY_FILE)) {
      fs.writeFileSync(MEMORY_FILE, `# MEMORY\n\n## Active Objective\n\n## Key Decisions\n\n## Pending Tasks\n`);
    }
    console.log('MEMORY.md initialized.');
    break;
  default:
    console.log(`Usage: node memory-mgr.js <read|snapshot|init> [args...]`);
    console.log(`  snapshot <objective> <done|sep> <decisions|sep> <activeFile> <blockers> <next>`);
}
