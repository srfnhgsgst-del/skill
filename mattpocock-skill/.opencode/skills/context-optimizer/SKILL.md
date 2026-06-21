---
name: context-optimizer
description: Compresses long conversations into structured state, tracks decisions in MEMORY.md, enforces lean responses, and reduces token waste. Use when context exceeds 20 turns, sessions span many files, token limits approach, tasks restart after resets, or repetitive verbose responses degrade performance.
---

# Context Optimizer

## When to Trigger
- Conversation > 20 turns or visible token pressure
- Major phase/subtask completed
- User says "continue", "resume", "remember where we left off"
- Repeated explanations or boilerplate detected
- Session restart or context reset

## Workflows

### 1. Context Compression (Snapshot Protocol)
After every major milestone or every ~15 exchanges:

1. Generate **Snapshot**:
   ```
   **Objective:** [1-line goal]
   **Done:** [completed items, max 5]
   **Decisions:** [X over Y because Z, max 3]
   **Active File:** [current file]
   **Blockers:** [open issues]
   **Next:** [immediate action]
   ```
2. Append snapshot to `.opencode/MEMORY.md`.
3. On new task, read MEMORY.md first — do not re-derive saved decisions.

### 2. Lean Communication
- **Token budget**: responses under 200 tokens (excl. code blocks).
- **Reference code** as `file.ts:42`, don't quote blocks.
- **Use lists** over paragraphs for multi-item answers.
- **Banned phrases**: "Sure, I can help", "Let me know if", "Here is the result", "Based on the information", "I hope this helps", "Let me explain", re-stating user's question verbatim.

### 3. State File Protocol
Maintain `.opencode/MEMORY.md`:

```markdown
## Active Objective
[one sentence]

## Implementation Status
| File | Purpose | Status |
|------|---------|--------|

## Key Decisions
- YYYY-MM-DD: topic — rationale (1 line)

## Pending Tasks
- [ ] task
```

**Rules**: Write after every feature/decision pivot. Read first after context reset. Append only — never delete.

**Priority-Based Retention**: Tag entries with priority — `P0` (critical architecture), `P1` (active decisions), `P2` (transient task state). Only P0/P1 survive across session restarts; P2 is scoped to current session.

### 4. Context Restoration
When resuming after a reset:

1. Read `.opencode/MEMORY.md` → extract P0/P1 entries.
2. Read the active file to rebuild mental model.
3. Reply with a **Restoration Summary**:
   ```
   Restored: [objective]
   State: [current file + status]
   Next: [immediate step from MEMORY.md]
   ```
4. Do **not** ask the user "where were we?" — the state file answers this.

## Checklist
- [ ] Can I answer in < 3 sentences?
- [ ] Am I using a banned phrase?
- [ ] Did I check MEMORY.md first?
- [ ] Should I write a snapshot now?

## Advanced
See [EXAMPLES.md](EXAMPLES.md) for before/after demos.
See [REFERENCE.md](REFERENCE.md) for token economics and advanced strategies.
