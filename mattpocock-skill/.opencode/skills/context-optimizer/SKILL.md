---
name: context-optimizer
description: Compresses long conversations into structured state, tracks decisions in MEMORY.md, enforces lean responses, and reduces token waste. Use when context exceeds 20 turns, sessions span many files, token limits approach, tasks restart after resets, or repetitive verbose responses degrade performance.
---

# Context Optimizer

## When to Trigger

Activate on any of these signals:
- Conversation > 20 turns or visible token pressure
- A major phase/subtask is completed
- User says "continue", "resume", "remember where we left off"
- Responses contain repeated explanations or boilerplate
- Session restart or context reset is detected

## Workflows

### 1. Context Compression (Snapshot Protocol)

After every major milestone or every ~15 exchanges:

1. Generate a **Snapshot** of the current state:

```
## Session Snapshot
**Objective:** [1-line goal]
**Done:** [completed items, max 5 bullets]
**Decisions:** [X chosen over Y because Z, max 3 items]
**Active File:** [currently editing file]
**Blockers:** [open questions or errors]
**Next:** [immediate action]
```

2. Merge this snapshot into `.opencode/MEMORY.md` at the end of the file.
3. When starting a new task, read MEMORY.md first — do not re-derive already-saved decisions.

### 2. Token Budgeting

- **Target**: Keep single responses under 200 tokens (excluding code blocks).
- **Code blocks**: Prefer editing existing files over printing full files in chat.
- **Reference**: Use `file.ts:42` notation for code locations instead of quoting blocks.
- **Lists**: Use numbered lists, not paragraphs, for multi-item answers.

### 3. Banned Response Patterns

Never output these phrases or their variants:
- "Sure, I can help with that" / "Let me know if you need anything else"
- "Here is the result:" / "The answer is:"
- "Based on the information provided..." / "I hope this helps"
- "Let me explain..." / "First, let me understand..."
- Re-stating the user's question verbatim
- Summarizing an action just performed if no tool output was generated

### 4. State File Protocol

Maintain `.opencode/MEMORY.md` with this structure:

```markdown
# MEMORY

## Active Objective
[one sentence]

## Implementation Status
| File | Purpose | Status |
|------|---------|--------|
| src/foo.ts | Core logic | done |
| src/bar.ts | Pending refactor | todo |

## Key Decisions
- [date] Decision: rationale (1 line each)

## Pending Tasks
- [ ] task
```

- **Write**: After completing a feature, decision, or architectural pivot.
- **Read**: First action after every context reset or new session start.
- **Never delete** old entries — append only.
- **Script**: Use `node scripts/memory-mgr.js <init|read|snapshot>` for automated state management.

## Checklist

Execute silently before each response:
- [ ] Can I answer in < 3 sentences?
- [ ] Am I about to use a banned phrase?
- [ ] Did I check MEMORY.md for existing decisions?
- [ ] Should I write a snapshot now?

## Advanced

See [EXAMPLES.md](EXAMPLES.md) for before/after compression demos.