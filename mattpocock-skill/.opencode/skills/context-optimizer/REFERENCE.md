# Context Optimizer — Reference

## Token Economics

| Model | Typical Context Window | Safety Limit | When to Snapshot |
|-------|----------------------|--------------|------------------|
| GPT-4 | 8K / 32K | 60% of limit | ~5K / ~19K tokens |
| Claude 3 | 100K | 70% of limit | ~70K tokens |
| DeepSeek / Gemini | 128K | 70% of limit | ~90K tokens |

**Rule of thumb**: A single average exchange costs ~400 tokens (user + assistant). After 20 turns (~8K tokens), compression is mandatory.

## Compression Ratio Targets

| Strategy | Typical Ratio | Best For |
|----------|--------------|----------|
| Snapshot | 90% reduction | Conversation history |
| Decision log | 99% reduction | Architectural discussions |
| Status table | 95% reduction | Multi-file feature work |
| Context Restoration | 80% reduction | Session resume |

**Formula**: `tokens_saved = original - snapshot_size` — aim for `snapshot_size < 100` tokens.

## Priority Scoring Model

```
P0 (Critical)
  - Architecture decisions (framework, DB, API contracts)
  - Security/auth configuration
  - Data model schemas
  - Never evict; carry across all sessions

P1 (Active)
  - Current feature decisions
  - Active file mappings
  - Recently resolved blockers (~last 3)
  - Carry across session restarts; archive after feature ships

P2 (Transient)
  - Current task breakdown
  - Recent error messages (already fixed)
  - Temporary variable/function names being discussed
  - Scoped to one session; drop after snapshot
```

### Eviction Policy
- **P2** entries older than 1 session → auto-archived.
- **P1** entries older than 3 sessions → demote to P2.
- **P0** entries never demoted.

## Effective Snapshot Triggers

Not every message needs a snapshot. Use these decision points:

```
User submits a large task description     → snapshot user intent
User provides code/files                  → snapshot key files and their purposes
A tool returns an error or unexpected     → snapshot the error and attempted fix
A feature milestone is reached            → snapshot done list and next steps
User says "now let's move to X"          → snapshot current state before context switch
Context window is approaching limit       → force snapshot (highest priority)
```

## Multi-Session Context Chain

For projects spanning many sessions:

```
Session 1: Snapshot A ──→ MEMORY.md
Session 2: Read A → work → Snapshot B ──→ MEMORY.md (A + B)
Session 3: Read A + B → work → Snapshot C ──→ MEMORY.md (A + B + C)
```

Each session starts by reading the full chain, giving instant project-wide context without re-derivation.

## Tool-Based State Queries

Use OpenCode's native tools instead of reading full files:

| Goal | Tool + Pattern |
|------|----------------|
| Find P0 decisions | `grep "P0" .opencode/MEMORY.md` |
| Get last snapshot | `grep "Session Snapshot" .opencode/MEMORY.md` + read last match |
| Count MEMORY.md lines | `bash` → `(Get-Content .opencode/MEMORY.md).Length` |
| Find active file | `grep "Active File:" .opencode/MEMORY.md` (last match = current) |
| List pending tasks | `grep "- \[ \]" .opencode/MEMORY.md` |
| Read objective only | `grep "Active Objective" .opencode/MEMORY.md` — read 2 lines |
| Append snapshot | `read` last 3 lines of MEMORY.md → `edit` to append |

## Compaction Decision Tree

```
MEMORY.md > 200 lines?
├─ Yes → Need to compact?
│   ├─ Snapshots > 3 → Run compact (summarize old snapshots)
│   └─ Snapshots ≤ 3 → No action needed
├─ No → Continue monitoring
│
Objective changed?
├─ Yes → Snapshot current state first, then update objective
└─ No → Continue

P2 entries > 10?
├─ Yes → Archive old P2s (they're transient)
└─ No → Continue
```

## Prompt Efficiency Templates

### Minimal Task Prompt
```
Task: [one line]
Current state: [one line from MEMORY.md]
Files involved: [file.ts:line]
Expected output: [one line]
```

### Quick Fix Response
```
file:line — change — reason
```
