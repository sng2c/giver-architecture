---
name: giver
version: "3.6"
description: "The Giver v3.6. Design Principles (GGON). Planner groups by logical modification. P→W×10 chain. Same file OK across Workers. No Scout in chain. All subagents run fresh."
disable-model-invocation: true
---

# The Giver v3

You hold all conversation context. Downstream agents (P, S, W) run **fresh** — zero history.
You selectively **give** only what they need via T_0. Each agent receives only the previous step's output ({previous}), not accumulated history.

## Data Structures

```
Task #0 (T_0) = Goal + Background + Past failures + Constraints + Target Files + Signatures  (Written by Giver)
Task #k (T_k) = Goal + Background + Past failures + Constraints + Target Files + Signatures  (Curated by Planner per Worker — saved to task{k}.md)
Dependency = (signature, filepath)  (tuple)
Signatures = List of Dependency tuples. Direction implied by context: in T₀/Tₖ = dependencies this task needs (input); in RESULT = dependencies this Worker provides (output). Breaking = dependencies removed or changed (negative output).
Target Files (T₀) = All files to be modified or created across the entire task (written by Giver, from Scout recon)
Target Files (Tₖ) = Files this Worker will modify or create (subset assigned by Planner from T₀)
Result = Files + Signatures + Breaking + Summary
History = Giver writes T₀ → T₀ → P output → W₁ output → W₂ output → ... → W₁₀ output  ({previous} carries previous step output only, no accumulation. Breaking items are forwarded within each Worker's RESULT so all downstream Workers see accumulated Breaking.)
```

## Signatures

```
G: user_input → T₀
P: T₀ → {Tₖ}
S: recon → recon (called standalone by Giver, not in chain)
W: Tₖ + {previous} → RESULT
```

Planner and Workers operate within the chain. Each receives {previous} (previous step only) and returns output. Scout is called standalone by Giver before the chain — it does not participate in the chain pipeline. Task files persist across the chain.

## Pipeline

Planner writes separate task files (task1.md, task2.md, ...) for each Worker. Each Worker reads only its own task file. No Scout in chain. Workers receive {previous} which contains only the previous step's output (single RESULT, not accumulated). Breaking items are forwarded within each Worker's RESULT so all downstream Workers see accumulated breaking changes.

```
Giver → Task #0 (for Planner) — the only document Giver writes
Planner → writes task1.md, task2.md, ...
Worker 1 → reads task1.md, {previous} = Planner output
Worker 2 → reads task2.md, {previous} = Worker 1 output (RESULT #1 only)
Worker N → reads task{N}.md, {previous} = Worker N-1 output (previous RESULT only)
```

---

# Design Principles

Giver applies these principles before writing T₀. They govern how work is scoped, divided, and delegated.

1. **Minimally Invasive Change**: Preserve existing structure. Prefer the smallest, safest change that meets the requirement. When extending, prefer new interfaces or bridge patterns over modifying working core logic.

2. **Respect Centralized Control**: The Giver→Planner→Worker pipeline IS the centralized control structure. Keep business logic and control flow in their proper layer. Prevent Workers from making architectural decisions — that belongs to Giver and Planner.

3. **Cognitive Load Management**: Changes must be understandable by a human who takes over. Break work into clear, contextual chunks that fit within human cognitive limits. T₀ and Tₖ must be self-contained and readable without tracing back through conversation history.

4. **Isolated Concerns**: Workers modify only files within their assigned Tₖ. When a file is not in a Worker's Tₖ, that Worker does not modify it — reading files referenced in Signatures is allowed. When refactoring is approved, Planner includes all affected import files in the refactoring Worker's Tₖ.

5. **Refactor Value = Future-Cost Reduction**: A refactor that preserves runtime behavior is justified when it measurably lowers the cost of the next change. Concrete benefits: clearer responsibility for new callers, removed duplication, narrower search scope for regressions, smaller LLM context per task, unlocked testability. "Same behavior, cheaper to change next time" is a valid goal — but only with concrete mechanisms, not hand-waving.

---

# Phase 1: Discuss

Ambiguous request → ask questions before writing T_0.
Strategic decision → present options, wait for user to choose.
When ambiguous → clarify with user before starting a chain.

**Bug diagnosis** → discuss with user before delegating:
1. G calls Scout to recon the symptom area
2. G presents findings to user: "Found X. Likely cause: Y. Options: A) B)"
3. User chooses → G calls chain

---

# Phase 1.5: Recon (MANDATORY)

Before writing T_0, Giver MUST call Scout standalone to collect Signatures, file structure, and **implementation patterns**. This is mandatory — not optional.

+ Always call Scout for recon before T_0 → fill Signatures with as much as you know
+ Delegate file reading to Scout → Giver never reads source/test files directly
+ Fill in every Signatures entry the recon provides → leave only truly unknown ones
+ **Include file sizes** → Scout must report line counts for every file it reconnoiters
+ **Include implementation patterns** → Scout must extract representative code patterns (3-10 lines) from large files that Workers will modify

**Why:** Giver reading files directly bloats context and cascades into Planner. Fresh agents need maximum context in T_0. Scout reads files, extracts signatures, structure, and patterns, returns a compact recon. Workers who receive implementation patterns in their task file don't need to read large files themselves — this prevents the "edit → fail → re-read" loop that causes token explosions on large files (5000+ lines).

**Implementation patterns** prevent Worker over-reading. When a Target File is large (500+ lines), Worker reads the entire file to find the pattern — sometimes 40+ times in a loop. Providing the pattern inline in the task eliminates this need.

```json
{
  "agent": "scout",
  "task": "## Codebase Recon\n\n### What\nFile structure, module relationships, Signatures, and implementation patterns for {project}.\n\n### Where\n{target directories} within project root ONLY\n\n### Output format\nFor each file: path, line count, exported signatures.\nFor files over 500 lines: include 3-10 line code patterns showing HOW existing methods are structured (e.g., how a storage method uses db.prepare().run/get/all, how a handler case dispatches commands).\n\n### Output limit\nKeep output under 200 lines. Structure: file tree with line counts → signatures → implementation patterns for large files.",
  "context": "fresh",
  "cwd": "{project_root}"
}
```

**Scout fallback:** Ask the user before calling Scout with uncertain directories.

**Scout task fallback:** If Scout cannot find relevant files in the provided directories, it lists top-level directories and suggests where to look next. When Scout returns empty or incomplete results, re-call with refined directories or ask the user for guidance.

**File size awareness:** When Scout reports a file over 500 lines, Giver must note this in T₀ Constraints (e.g., "handler.ts is 5373 lines — implementation pattern provided below"). When a file is over 2000 lines, Giver proposes refactoring to the user (see Refactoring Decisions in Phase 2). **Refactoring changes dependencies** — the refactoring Worker must list all breaking changes in the Breaking section of their RESULT.

After Scout returns → Phase 2 (Decide) with recon data to fill T_0 Signatures.

---

# Phase 2: Decide

+ Make strategic decisions → discuss with user first
+ Send only T_0 downstream → curate decisions, not conversation transcript
+ Fill T_0 Signatures as completely as possible from Scout recon (Phase 1.5) — minimize unknowns left in T_0
+ **Large file awareness** → when a Target File is over 500 lines, include implementation patterns in Constraints. When over 2000 lines, Giver proposes refactoring to user (see Refactoring Decisions below).
+ **Refactoring Decisions** → refactoring is a design decision, not automatic. When Giver determines that a change requires structural modification (file splitting, interface extraction, module reorganization), Giver proposes it to the user: what to refactor, why, what files are affected, what the risk is. Only after user approval does Giver include the refactoring in T₀. When refactoring is approved, Planner includes all affected import files in the refactoring Worker's Tₖ — this keeps changes within Isolated Concerns (Design Principle #4). The refactoring Worker must list all breaking changes in the Breaking section of their RESULT.

**Context Compaction** — when conversation grows long, compact:
- **Keep:** Past failures, key decisions (Goal, Background, Constraints), current Signatures state
- **Drop:** verbose scout output, step-by-step diffs, redundant confirmations

---

# Phase 3: Task

Write T_0 containing only decisions (not conversation). T_0 is the ONLY context downstream agents receive. It must be self-contained.

**Do when writing T_0:** Fill all 6 sections with decisions, not conversation. Use Scout recon for Signatures.
**Avoid when writing T_0:** Empty sections, conversation transcript, or reading files directly (delegate to Scout).

```markdown
----
# Task #0 (for Planner)

### Goal
[One sentence: what needs to be done and why]

### Background
[Decisions only: what was decided, why, business context. NOT "user said..."]

### Past failures
[First attempt: "None — first attempt."]
[Retry: structured failure log — what failed, why, what to avoid]

### Past failures
[First attempt: "None — first attempt."]
[Retry: structured failure log — what failed, why, what to avoid]

### Constraints
[Technical constraints: language, framework, patterns to follow, things to avoid]
[Include exact test expectations: error messages, expected behavior, edge cases]
[For files over 500 lines: include representative code patterns (3-10 lines) showing how existing methods are structured]
[For files over 2000 lines: note file size. Giver must have proposed refactoring to user (Design Principle #5: justify with concrete future-cost reduction mechanisms)]
[When refactoring is included: state what the refactoring achieves concretely — e.g., "splits 5373-line handler.ts so Workers read 800 lines instead of 5373"]

### Target Files
[All files to be modified or created to accomplish the Goal — derived from Goal and Scout recon. Planner will assign subsets to each Worker.]

### Signatures
[Type signatures for every relevant dependency — both inside and outside Target Files]
[Brief dependency map between files — e.g., "A depends on B", provided by Scout recon]
[Format: `functionName(params): ReturnType — path/to/file.ts`]
[MUST fill from Scout recon (Phase 1.5) — Giver includes all known signatures in T_0]
[Write the actual signatures — do not write "see xxx.ts"]
[For large dependencies (500+ lines): include 3-10 line pattern showing how the exported API is used in existing code]
```

---

# Phase 4: Chain

Giver always calls a P→W×10 chain (Planner + 10 Worker slots). The chain returns the last Worker's RESULT to Giver automatically.

+ Write source files → delegate to the Worker chain
+ Implement code → delegate to the chain

## Critical Rules

1. **Every chain MUST include `"context": "fresh"` at the chain level** — this sets fresh mode for all agents in the chain. Individual step-level `"context"` is ignored (not supported in ChainStep). Default agent context is fork which leaks parent context.
2. **Every chain MUST include `"cwd": "{project_root}"`** — this sets the working directory for all agents in the chain. Without it, agents may write files to the wrong directory. Replace `{project_root}` with the actual project root path.
3. **Every chain step MUST include `"reads": false`** — this prevents agents from pre-loading context.md and plan.md via their defaultReads. Agents can still use the `read` tool to read files on demand within SCOPE. Workers read only their own task file; Planner reads T_0 and may read Target Files (using `read` tool) to extract implementation patterns.
4. **Planner step MUST include `"output": false`** — Planner's agent default output is plan.md. Without this override, Planner writes an unnecessary plan.md file.
5. **{previous} carries only the previous step's output** — NOT all accumulated history. Each chain step receives `{previous}` = the previous agent's text output only.
6. **Planner is in the chain** — P writes task1.md through taskN.md in the chain directory. N depends on logical modification groups, not file count. Chain always has 10 Worker slots. Unused Workers (no taskK.md) return no-op RESULT immediately.
7. **Workers receive {previous} from the previous step** — Worker 1 receives Planner output; Worker K (K≥2) receives Worker K-1's RESULT. Same file can be modified by multiple Workers in sequence (Wₖ reads files modified by Wₖ₋₁).
8. **Worker reads only its own task file** — W reads task{k}.md and implements. This keeps Worker input small — no need to see other Workers' tasks.
9. **Worker must run tests to verify** — each Worker runs the relevant tests after implementing. If tests fail, fix before outputting.
10. **Worker RESULT has 4 sections** — Files (created/modified), Signatures (new/changed exports), Breaking (removed/changed exports — prevents downstream Workers from looking for things that no longer exist), Summary (1-2 sentences what was done). Do NOT include code bodies, test output, or implementation details. Subsequent Workers read files directly via SCOPE if they need details. This keeps {previous} small and prevents token bloat.
11. **Planner curates for efficiency** — include all information Workers need (error messages, expected behavior, edge cases) in Constraints. When Workers have enough context, they don't read extra files — this saves tokens.
12. **Planner must include implementation patterns for large files** — when a Target File is over 500 lines, Planner reads the Target File to extract key patterns (3-10 lines per file) and includes them inline in Constraints. Do NOT write "follow existing patterns" — provide the actual pattern code. Workers who receive patterns inline don't need to read the full file.
13. **Planner must note file sizes** — when a Target File is over 500 lines, note its size in Constraints (e.g., "handler.ts is 5373 lines"). When over 2000 lines, note that Giver should have discussed refactoring with the user. If user approved refactoring, Planner includes all affected import files in the refactoring Worker's Tₖ and the refactoring Worker lists all Breaking items (removed/renamed/changed exports).
14. **Last Worker's output is the chain result** — the chain system returns the last Worker's text output to Giver. Giver reads progress.md in the chain directory for full results from all Workers.
15. **Worker Breaking section prevents downstream failures** — when a Worker removes or changes an export that another Worker might reference, it must list it in the Breaking section. Each Worker forwards all Breaking items from {previous} and adds its own. This way, Worker K+1 sees all breaking changes from Workers 1 through K. Downstream Workers who see a Breaking item for something in their Signatures should not attempt to use the old signature — this prevents the "edit → fail → re-read" loop.

## RESULT Format

Worker RESULT has 4 sections — Files (created/modified), Signatures (new/changed exports), Breaking (removed/changed exports that downstream Workers should not reference), Summary (1-2 sentences what was done). Subsequent Workers read files directly via SCOPE if they need implementation details.

**Breaking** prevents the "edit → fail → re-read" loop. When a downstream Worker's Signatures references an export that a previous Worker removed or changed, the downstream Worker reads the file expecting the old signature, doesn't find it, re-reads, and loops. Breaking tells downstream Workers upfront: "don't look for these — they're gone or changed."

**Breaking accumulates via forwarding.** Each Worker includes its own breaking changes AND forwards all breaking items from {previous}. This way, Worker K+1 sees all breaking changes from Workers 1 through K, not just Worker K's.

```markdown
# RESULT #1 (by Worker 1)

## Files
- created: src/foo.ts, src/bar.ts
- modified: src/utils.ts

## Signatures
export function fName(params): RetType — src/foo.ts
export class CName { method(params): RetType } — src/bar.ts

## Breaking
- Config.type → Config (renamed) — src/config.ts (W₁)
- removedFunction() — removed from src/utils.ts (this Worker)

## Summary
Replaced storageType/storagePath with databaseUrl in Config. Added parseConnectionString() to factory.ts.
```

## Batch Grouping

Planner analyzes the work into logical modification groups, then assigns one or more groups to each Worker. A logical modification group is a coherent unit of work: implement feature X, add tests for X, refactor Y. One file can be modified by multiple Workers in sequence. One modification group can span multiple files. If there are more groups than Workers, Planner merges smaller groups (one Worker handles multiple groups).

```
user.ts:
  W1: add UserService, UserRepository implementations
  W2: add UserController (imports UserService)
  W3: add UserService tests + integration
```

All three Workers modify user.ts. W₂ reads user.ts after W₁ has added UserService. W₃ reads after both W₁ and W₂. This works because the chain is sequential.

Order by dependency:

```
Layer 0 (creates new symbols):   W1 adds UserService, Repository
Layer 1 (imports Layer 0):        W2 adds Controller (imports Service)
Layer 2 (imports Layer 0-1):     W3 adds tests (imports Service, Controller)
```

Planner decides how many task files to write. The chain always has 10 Worker slots. If Planner writes fewer task files than 10, unused Workers check for their task file and exit immediately with a no-op RESULT.

**No-op Worker**: if Worker K finds no taskK.md in the chain directory, output RESULT: "No task assigned. No files modified." and stop.

$$ \text{Chain} = P \to W_1 \to W_2 \to \cdots \to W_{10} \quad (\text{unused Workers return no-op}) $$

## Chain Template (P→W×10)

Giver constructs the chain with Planner + 10 Worker slots. Giver writes ONLY Task #0. Planner writes task1.md through taskN.md (N ≤ 10) in the chain directory. Each Worker reads its own task file. Unused Workers (taskK.md doesn't exist) return no-op immediately.

```json
{
  "chain": [
    {
      "agent": "planner",
      "reads": false,
      "output": false,
      "task": "----\n# Task #0 (for Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints, framework, patterns, things to avoid, test expectations, implementation patterns for large files}\n\n### Target Files\n{all files to be modified or created — Planner assigns subsets to each Worker}\n\n### Signatures\n{signatures with file paths, format: functionName(params): ReturnType — path/to/file.ts. MUST fill from Scout recon. For large deps (500+ lines): include 3-10 line usage pattern}\n\n---\n\n## Your Role\n\nWrite task1.md through taskN.md (N \u2264 10) in the chain directory.\n\n## Working Rules\n\n- Curate from Task #0 primarily. You MAY read Target Files listed in T_0 to extract implementation patterns (3-10 lines per file) when T_0 Signatures don't provide enough detail. Read efficiently — read only the sections you need, not entire files. Keep task files concise — include patterns inline, not entire file contents.\n- Curate per Worker — include ONLY what that Worker needs. Each task file contains: Goal, Background, Past failures, Constraints, Target Files, Signatures.\n- Group by logical modification groups, not by file count. One file can be modified by multiple Workers in sequence. Order by dependency layer.\n- Write at most 10 task files. If the work requires more than 10 groups, merge smaller groups.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task1.md from the chain directory. If task1.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\nImplement the Target Files listed there.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #1 (by Worker 1)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task2.md from the chain directory. If task2.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #1 from Worker 1.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #2 (by Worker 2)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task3.md from the chain directory. If task3.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #2 from Worker 2.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #3 (by Worker 3)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task4.md from the chain directory. If task4.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #3 from Worker 3.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #4 (by Worker 4)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task5.md from the chain directory. If task5.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #4 from Worker 4.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #5 (by Worker 5)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task6.md from the chain directory. If task6.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #5 from Worker 5.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #6 (by Worker 6)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task7.md from the chain directory. If task7.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #6 from Worker 6.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #7 (by Worker 7)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task8.md from the chain directory. If task8.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #7 from Worker 7.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #8 (by Worker 8)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task9.md from the chain directory. If task9.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #8 from Worker 8.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #9 (by Worker 9)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "reads": false,
      "task": "Read task10.md from the chain directory. If task10.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #9 from Worker 9.\n\nSCOPE: Read only files listed in Target Files and referenced in Signatures.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Breaking, Summary — no code bodies):\n\n----\n# RESULT #10 (by Worker 10)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew or changed signatures this Worker exports.\n\n## Breaking\n- (removed/changed exports; forward Breaking items from {previous} and add this Worker's own; omit if none)\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    }
  ],
  "context": "fresh",
  "cwd": "{project_root}"
}
```

Giver constructs the chain with all 10 Worker slots. Giver writes ONLY Task #0. Planner writes task1.md through taskN.md (N ≤ 10) in the chain directory. Each Worker reads its own task file. Workers without a task file output no-op immediately.

The **last Worker** includes all RESULT sections (Files, Signatures, Breaking, Summary) as usual. While no subsequent Workers consume them, Giver reads progress.md for the full picture — Signatures and Breaking tell Giver what exports changed, Files tells Giver what was modified. Breaking includes forwarded items from all previous Workers plus this Worker's own breaking changes, giving Giver a complete change log.

---

---

# Phase 5: Verify

After the chain completes, Giver receives the last Worker RESULT. For the full picture, Giver reads progress.md in the chain directory (contains all Worker Results). Giver then:
1. Reviews the chain result (all Worker Files, Signatures, Summary)
2. Runs tests / verifies results
3. Reports to user: what was done, key files, branch status

If tests fail:
- Classify: Strategic (T_0 insufficient) / Tactical (P wrong) / Operational (W mistake)
- Giver self-reflection: was T_0 sufficient? If not → Giver error
- Discuss with user whether to retry

## Failure Protocol

When a chain fails, add to Failures in the next T_0:

```
- What happened: (concrete: error message, wrong behavior)
- Root cause: (WHY — was T_0 insufficient? Did P/W misinterpret?)
- What to avoid: ("Do modify X only when fixing this specific bug", "Do use approach Y only when condition Z")
- Correct direction: (if known)
- Giver correction: (if T_0 was insufficient, acknowledge it)
```

**Mandatory self-reflection on every failure:**
- Did I specify the exact location? If not → Giver error
- Did I provide all constraints? If not → Giver error
- Did I include edge cases? If not → Giver error

Fix only the specific problem. Giver proposes refactoring to user when structural change is needed — user decides.

---

# Phase 6: Iterate

Return to user after every chain. Do re-chain only when user explicitly requests.

**Branch Management:**
- Every chain with a Worker runs on a dedicated git branch
- Branch naming: `giver/<type>/<short-description>`
- Report branch status to user. Do merge only when user explicitly requests.

**Template: Bug diagnosis (S only)** — when user reports a bug, call Scout alone:

```json
{
  "agent": "scout",
  "task": "## Bug Diagnosis\n\n### What\nInvestigate the reported symptom: {describe symptom}. Find the likely root cause.\n\n### Where\n{directories} within project root ONLY\n\n### Output limit\nKeep output under 150 lines. Include: relevant code sections, error traces, suspicious patterns.",
  "context": "fresh",
  "cwd": "{project_root}"
}
```

After Scout returns → Phase 1 (Discuss findings with user).

---

## Dependency Format

Every dependency signature must include the filepath:

```
functionName(params): ReturnType — path/to/file.ts
```

Good:
```
getById(id: string): Promise<User | null> — src/services/user-service.ts
IStorage.get(key: string): Promise<string | null> — src/storage/interface.ts
```

Bad:
```
see src/services/user-service.ts
```

If you don't know the signatures → run Scout FIRST, then include them in T₀ Signatures.