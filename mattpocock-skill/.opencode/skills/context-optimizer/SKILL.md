---
name: context-optimizer
description: Compresses long conversations into structured state, tracks decisions in MEMORY.md, enforces lean responses, and reduces token waste. Use when context exceeds 20 turns, sessions span many files, token limits approach, tasks restart after resets, or repetitive verbose responses degrade performance.
---

# Context Optimizer

## When to Trigger
- 20+ turns or token pressure
- Major phase done
- User says "continue"/"resume"
- Boilerplate detected
- Session reset

## Workflows

### 1. Snapshot Protocol
After milestone or every ~15 exchanges:
1. Generate:
   ```
   **Objective:** [1-line]
   **Done:** [max 5]
   **Decisions:** [X over Y, max 3]
   **Active File:** [file]
   **Blockers:** [issues]
   **Next:** [action]
   ```
2. Append to `.opencode/MEMORY.md` via `edit` tool.
3. New task: read MEMORY.md first.

### 2. Lean Communication
- **< 200 tokens** per response (excl. code)
- Reference code as `file.ts:42`
- Lists > paragraphs
- **Banned**: "Sure, I can help", "Let me know if", "Here is the result", "Based on the information", "I hope this helps", "Let me explain", restating user question

### 3. State File Protocol
```markdown
## Active Objective
[one sentence]

## Implementation Status
| File | Purpose | Status |

## Key Decisions
- YYYY-MM-DD [P0-P2]: topic — rationale

## Pending Tasks
- [ ] task
```
**P0** (architecture) — permanent. **P1** (active) — cross-session. **P2** (transient) — session-scoped.

### 4. Tool-Based State Management
| Action | Tool to Use |
|--------|-------------|
| Read state | `read .opencode/MEMORY.md` |
| Append snapshot | `edit` — match last line, append new content |
| Search decisions | `grep` with keyword or `P0` tag |
| Update status table | `edit` — replace target row |
| Check size | `bash` with `Measure-Object -Line` |
| Init file | `write` with template |

Prefer `grep` over reading full file when searching specific sections.

### 5. Auto-Compaction
When MEMORY.md > 200 lines or ~3K tokens:
1. Group snapshots older than last 3 into summary block.
2. Prefix with `## Archived (YYYY-MM-DD — YYYY-MM-DD)`.
3. Keep only: objective, decisions, final state per snapshot.
4. Discard per-step details, error logs, exploration branches.

### 6. Context Fingerprint
Generate when switching tasks:
```
Fingerprint: router=TanStack|state=Zustand|file=Login.tsx|task=auth
```
Store in MEMORY.md. Restores full context in one line.

### 7. Context Restoration
After reset:
1. Read MEMORY.md.
2. Read active file (from snapshot).
3. Reply:
   ```
   Restored: [objective]
   Fingerprint: [key=val|key=val]
   Next: [immediate step]
   ```
4. Never ask "where were we?" — MEMORY.md answers this.

## Checklist
- [ ] Under 3 sentences?
- [ ] Banned phrase used?
- [ ] MEMORY.md checked?
- [ ] Snapshot needed?
- [ ] MEMORY.md > 200 lines → compact?

## Advanced
See [EXAMPLES.md](EXAMPLES.md), [REFERENCE.md](REFERENCE.md).
