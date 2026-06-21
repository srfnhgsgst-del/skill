# Context Optimizer — Examples

## 1. Lean Response Patterns

### Bad (~120 tokens)
> Sure, I can help you fix that bug. Based on the information you've
> provided, let me first understand the issue. The error occurs because
> the function `calculateTotal` is not handling null values properly.
> Let me explain what's happening: when the input is null, the function
> tries to call `.reduce()` on it, which throws a TypeError. I'll now
> edit the file to add a null check. Let me know if you need anything else.

### Good (~15 tokens)
> `calculateTotal` in `src/billing.ts:42` — null guard missing before `.reduce()`.

## 2. Snapshot Compression

### Before (raw conversation history, ~800 tokens)
```
User: I need a login page
AI: Sure, I can help with that. Let me understand the requirements...
User: Use React and TypeScript
AI: Good choice. React with TypeScript is great for type safety...
User: Add form validation for email format
AI: Let me add email validation. I'll use a regex pattern...
User: Also add password minimum 8 chars
AI: I'll adjust the password validation to require 8 characters...
User: Use shadcn components for the form
AI: shadcn is a great choice. Let me install it first...
User: Add a "remember me" checkbox
AI: Let me add the checkbox component...
User: Now style it with Tailwind
AI: I'll add Tailwind classes for styling...
User: Add error message display below each field
AI: I'll add error message components...
```

### After (snapshot in MEMORY.md, ~90 tokens)
```
## Snapshot: Login Page
Objective: Build React+TS login page with shadcn form components
Done: Email regex validation, password min-8, remember-me checkbox
Active File: src/pages/Login.tsx
Next: Add Tailwind styling, error display, connect to auth endpoint
```

## 3. State File Before/After

### Before (scattered context)
User has to re-explain: "We're using React Router v6, right?"
"No, we switched to TanStack Router in the last session."

### After (MEMORY.md preserved)
```
## Key Decisions
- 2026-06-14: router — TanStack Router over React Router v6 (file-based routing)
- 2026-06-14: state — Zustand over Redux (simpler API, smaller bundle)
- 2026-06-14: validation — zod over yup (TypeScript-first inference)
```

New session: reads MEMORY.md → immediately knows tech stack without asking.

## 4. Token Budget Enforcement

### Before (~350 tokens per file fix)
```
AI: To fix the authentication bug, I need to read these 5 files:
[reads all 5 files in parallel → outputs full contents → explains each → edits 1 line]
```

### After (~80 tokens)
```
AI: [reads only the relevant function at auth.ts:56-72 → edits 1 line]
auth.ts:62 — `token.expiresIn` → `token.expires_in` (camelCase mismatch)
```

## 6. Context Restoration

### Bad (no MEMORY.md — wastes ~200 tokens asking questions)
```
AI: Welcome back! Where were we? What were you working on last time?
    Can you remind me what stack we're using?
    What was the last file you were editing?
```

### Good (reads MEMORY.md — restores in ~30 tokens)
```
AI:
## Restored
**Objective:** Build payment checkout flow
**State:** src/pages/Checkout.tsx — form validation done, wiring API pending
**Next:** Connect submit handler to `/api/checkout` endpoint
```

## 7. Priority-Based Retention

### Before (MEMORY.md has mixed priorities, hard to distinguish critical from transient)
```
## Key Decisions
- 2026-06-14: router — TanStack Router over React Router v6
- 2026-06-14: state — Zustand over Redux
- 2026-06-21: temp var name — renamed `data` to `payload` in checkout handler

Without priority tags, "temp var rename" is as prominent as "router choice".
```

### After (P0 critical — always preserved; P2 transient — dropped after session)
```
## Key Decisions
- [P0] 2026-06-14: router — TanStack Router over React Router v6
- [P0] 2026-06-14: state — Zustand over Redux
- [P2] 2026-06-21: temp var name — renamed `data` to `payload`

After session end, P2 entry archived. Start of next session only sees P0.
```

## 8. Response Format Standards

| Context | Format |
|---------|--------|
| Bug fix | `file:line — change: reason` |
| Feature status | Table with File / Purpose / Status |
| List options | `1. option (trade-off)` |
| Confirmation | Single word or emoji |
| Code location | `file.ts:42` notation |