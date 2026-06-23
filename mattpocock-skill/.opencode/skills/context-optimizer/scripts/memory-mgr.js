const fs = require('fs');
const path = require('path');

const MEMORY_FILE = path.resolve('.opencode/MEMORY.md');
const HEADINGS = ['## Active Objective', '## Implementation Status', '## Key Decisions', '## Pending Tasks'];
const PRIORITY_RE = /\b(P[0-2])\b/;

function getFile() {
  return MEMORY_FILE;
}

function read() {
  if (!fs.existsSync(MEMORY_FILE)) return { raw: null, sections: {} };
  const raw = fs.readFileSync(MEMORY_FILE, 'utf-8');
  const sections = {};
  let current = null;
  for (const line of raw.split('\n')) {
    const h = HEADINGS.find(h => line.startsWith(h));
    if (h) { current = h; sections[current] = []; continue; }
    if (current) sections[current].push(line);
  }
  return { raw, sections };
}

function append(text) {
  const ts = new Date().toISOString().slice(0, 10);
  const entry = `\n## ${ts}\n${text.trim()}\n`;
  fs.appendFileSync(MEMORY_FILE, entry);
  return entry;
}

function snapshot({ objective, done, decisions, activeFile, blockers, next }) {
  const block = [
    `### Session Snapshot`,
    `**Objective:** ${objective || '—'}`,
    `**Done:**\n${(done || []).map(d => `- ${d}`).join('\n')}`,
    `**Decisions:**\n${(decisions || []).map(d => `- ${d}`).join('\n')}`,
    `**Active File:** ${activeFile || '—'}`,
    `**Blockers:** ${blockers || '—'}`,
    `**Next:** ${next || '—'}`,
  ].join('\n');
  return append(block);
}

function search(keyword) {
  const { raw } = read();
  if (!raw) return 'No MEMORY.md found';
  const lines = raw.split('\n');
  const matches = lines
    .map((l, i) => ({ line: i + 1, text: l }))
    .filter(({ text }) => text.toLowerCase().includes(keyword.toLowerCase()));
  if (matches.length === 0) return `No matches for "${keyword}"`;
  return matches.map(m => `L${m.line}: ${m.text}`).join('\n');
}

function status() {
  const { raw, sections } = read();
  if (!raw) return { exists: false, message: 'No MEMORY.md found' };
  const lines = raw.split('\n');
  const charCount = raw.length;
  const estTokens = Math.round(charCount / 4);
  const snapshots = raw.match(/### Session Snapshot/g);
  const decisions = raw.match(/- \d{4}-\d{2}-\d{2}:/g);
  const pending = raw.match(/- \[ \]/g);
  const priorities = raw.match(PRIORITY_RE);

  return {
    exists: true,
    size: { chars: charCount, lines: lines.length, estTokens },
    snapshots: snapshots ? snapshots.length : 0,
    decisions: decisions ? decisions.length : 0,
    pending: pending ? pending.length : 0,
    p0Count: priorities ? priorities.filter(p => p === 'P0').length : 0,
    p1Count: priorities ? priorities.filter(p => p === 'P1').length : 0,
    p2Count: priorities ? priorities.filter(p => p === 'P2').length : 0,
  };
}

function prune({ keepLast = 5, minPriority = 'P1' } = {}) {
  const { raw, sections } = read();
  if (!raw) return 'No MEMORY.md found';

  const lines = raw.split('\n');
  const snapshotLines = [];
  const snapshotIndices = [];
  lines.forEach((l, i) => {
    if (l.startsWith('## ') && l.match(/^\d{4}-\d{2}-\d{2}$/)) {
      snapshotIndices.push(i);
    }
  });

  if (snapshotIndices.length <= keepLast) return 'Nothing to prune (under keepLast threshold)';

  const toRemove = snapshotIndices.length - keepLast;
  const removeUpTo = snapshotIndices[toRemove];
  const kept = lines.slice(removeUpTo).join('\n');
  fs.writeFileSync(MEMORY_FILE, kept);
  return `Pruned ${toRemove} old snapshot(s), kept last ${keepLast}.`;
}

function compact() {
  const { raw } = read();
  if (!raw) return 'No MEMORY.md found';

  const lines = raw.split('\n');
  const snapshotHeaders = [];
  lines.forEach((l, i) => {
    if (l.startsWith('## ') && l.match(/^\d{4}-\d{2}-\d{2}$/)) {
      snapshotHeaders.push(i);
    }
  });

  if (snapshotHeaders.length <= 3) return 'Less than 3 snapshots, nothing to compact.';

  const keepCount = 3;
  const compactEnd = snapshotHeaders[snapshotHeaders.length - keepCount];
  const compactSection = lines.slice(0, compactEnd).join('\n');
  const recentSection = lines.slice(compactEnd).join('\n');

  const summary = [];
  const headerMatch = compactSection.match(/## \d{4}-\d{2}-\d{2}/);
  const firstDate = compactSection.match(/(\d{4}-\d{2}-\d{2})/);
  const lastDate = lines.slice(0, snapshotHeaders[snapshotHeaders.length - keepCount])
    .join('\n').match(/(\d{4}-\d{2}-\d{2})(?!.*\d{4}-\d{2}-\d{2})/s);

  summary.push(`## Archived (${firstDate ? firstDate[1] : '?'} — ${lastDate ? lastDate[1] : '?'})`);

  const decisions = compactSection.match(/- \d{4}-\d{2}-\d{2}.*/g);
  if (decisions) {
    summary.push('');
    summary.push('### Key Decisions');
    decisions.forEach(d => summary.push(d));
  }

  const objectives = compactSection.match(/\*\*Objective:\*\*.*/g);
  if (objectives) {
    summary.push('');
    summary.push('### Objectives');
    objectives.forEach(o => summary.push(`- ${o.replace('**Objective:**', '').trim()}`));
  }

  const newContent = summary.join('\n') + '\n\n---\n\n' + recentSection;
  fs.writeFileSync(MEMORY_FILE, newContent);
  return `Compacted ${snapshotHeaders.length - keepCount} old snapshots into archive summary.`;
}

function init() {
  const dir = path.dirname(MEMORY_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(MEMORY_FILE)) {
    const template = [
      '# MEMORY',
      '',
      '## Active Objective',
      '',
      '## Implementation Status',
      '| File | Purpose | Status |',
      '|------|---------|--------|',
      '',
      '## Key Decisions',
      '',
      '## Pending Tasks',
      '',
    ].join('\n');
    fs.writeFileSync(MEMORY_FILE, template);
  }
  return 'MEMORY.md initialized.';
}

const cmd = process.argv[2];
const args = process.argv.slice(3);

switch (cmd) {
  case 'read':
    console.log(read().raw || 'No MEMORY.md found');
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
  case 'search':
    console.log(search(args[0] || ''));
    break;
  case 'status':
    {
      const s = status();
      if (!s.exists) { console.log(s.message); break; }
      console.log([
        `MEMORY.md stats:`,
        `  Lines: ${s.size.lines}`,
        `  Est. tokens: ${s.size.estTokens}`,
        `  Snapshots: ${s.snapshots}`,
        `  Decisions: ${s.decisions}`,
        `  Pending tasks: ${s.pending}`,
        `  P0: ${s.p0Count} | P1: ${s.p1Count} | P2: ${s.p2Count}`,
      ].join('\n'));
    }
    break;
  case 'prune':
    console.log(prune({ keepLast: parseInt(args[0], 10) || 5 }));
    break;
  case 'compact':
    console.log(compact());
    break;
  case 'init':
    console.log(init());
    break;
  default:
    console.log([
      `Usage: node memory-mgr.js <command> [args...]`,
      ``,
      `Commands:`,
      `  init                              Create MEMORY.md with template`,
      `  read                              Print full MEMORY.md`,
      `  snapshot <obj> <done|> <dec|> <file> <blockers> <next>`,
      `                                    Append session snapshot`,
      `  search <keyword>                  Find matching lines`,
      `  status                            Show token usage and entry counts`,
      `  prune [keepLast=5]                Remove old snapshots, keep N recent`,
      `  compact                           Summarize old snapshots into archive block`,
    ].join('\n'));
}
