---
name: context-optimizer
description: Optimizes token usage and enhances long-term memory by implementing context compression, state tracking, and lean communication. Use when conversations become long, complex tasks require persistence, or token limits are a concern.
---

# Context Optimizer

## Core Objectives
- Minimize token waste by eliminating redundancy.
- Prevent context drift via structured state tracking.
- Maintain high-fidelity memory across long sessions.

## Workflows

### 1. Context Compression
When the conversation history grows long or a major phase is completed:
- **Snapshotting**: Summarize key decisions, completed tasks, and current blockers.
- **Pruning**: Identify and mentally archive redundant logs or repetitive error messages.
- **State Update**: Update the project's state file (e.g., `MEMORY.md` or `.opencode/state.json`) with the latest snapshot.

### 2. State Tracking (External Memory)
Avoid relying solely on the chat window for critical information.
- **Persistence**: Write key architectural decisions, variable mappings, and pending todos to a dedicated state file.
- **Loading**: At the start of a new session or after a context reset, read the state file first to restore the mental model.
- **Atomic Updates**: Only update the state file when a significant change occurs.

### 3. Lean Communication
- **No Preamble/Postamble**: Remove "Sure, I can help", "Here is the result", and "Let me know if...".
- **Direct Answers**: Provide**: Use lists, tables, or code blocks directly.
- **Implicit Context**: Refer to previous decisions via state file references rather than repeating them.

## Implementation Guide

### Memory File Template (`MEMORY.md`)
Maintain a file with the following structure:
- **Objective**: The ultimate goal of the current session.
- **Current State**: What is currently implemented/configured.
- **Key Decisions**: Why X was chosen over Y (to prevent re-litigating).
- **Pending**: Immediate next steps.
- **Context Map**: Mapping of critical files to their purposes.

## Checklists
- [ ] Is the response free of conversational filler?
- [ ] Has the external state file been updated after a major milestone?
- [ ] Is the current prompt focused on the immediate task without unnecessary history?
