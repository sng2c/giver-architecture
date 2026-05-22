---
name: giver
version: "3.5.6"
description: "The Giver v3.5.6. Planner groups by logical modification. P→W×10 chain. Same file OK across Workers. No Scout in chain. All subagents run fresh."
disable-model-invocation: true
---

# The Giver v3

You hold all conversation context. Downstream agents (P, S, W) run **fresh** — zero history.
You selectively **give** only what they need via T_0. Each agent receives only the previous step's output ({previous}), not accumulated history.

## Data Structures

```
Task #0 (T_0) = Goal + Background + Past failures + Constraints + Imports needed  (Written by Giver)
Task #k (T_k) = Goal + Background + Past failures + Constraints + TargetFiles + Imports needed  (Curated by Planner per Worker — saved to task{k}.md)
Dependency = (signature, filepath)  (tuple)
Imports needed (curated) = Curated by Planner from T_0 Imports needed per Worker — only what that Worker imports
TargetFiles = Target file list (assigned groups for this Worker)
Result = Files + Signatures + Summary (created/modified files, new exports, 1-2 sentences what was done)
History = T_0 → P output → W₁ output → W₂ output → ... → W₁₀ output  ({previous} carries previous step output only, no accumulation)
```

## Signatures

```
G: user_input → History
P: History → History
S: History → History
W: History → History
```

All subagents take {previous} (previous step only) and return their output. Task files persist across the chain.

## Pipeline

Planner writes separate task files (task1.md, task2.md, ...) for each Worker. Each Worker reads only its own task file. No Scout in chain. Workers receive {previous} which contains only the previous step's output (single RESULT, not accumulated).

```
Giver → Task #0 (for Planner) — the only document Giver writes
Planner → writes task1.md, task2.md, ... + brief plan.md
Worker 1 → reads task1.md, {previous} = Planner output
Worker 2 → reads task2.md, {previous} = Worker 1 output (RESULT #1 only)
Worker N → reads task{N}.md, {previous} = Worker N-1 output (previous RESULT only)
```

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

Before writing T_0, Giver MUST call Scout standalone to collect dependency signatures and file structure. This is mandatory — not optional.

+ Always call Scout for recon before T_0 → fill Imports needed with as much as you know
+ Delegate file reading to Scout → Giver never reads source/test files directly
+ Fill in every Imports needed signature the recon provides → leave only truly unknown ones

**Why:** Giver reading files directly bloats context and cascades into Planner. Fresh agents need maximum context in T_0. Scout reads files, extracts only signatures and structure, returns a compact recon. Giver uses this to fill T_0 Imports needed as completely as possible. Only truly unknown signatures should remain unfilled in T_0.

```json
{
  "agent": "scout",
  "task": "## Codebase Recon\n\n### What\nFile structure, module relationships, and dependency signatures for {project}.\n\n### Where\n{target directories} within project root ONLY\n\n### Output limit\nKeep output under 150 lines. List: file tree, import relationships, and type signatures of exported functions/classes/interfaces.",
  "context": "fresh",
  "cwd": "{project_root}"
}
```

**Scout fallback:** Ask the user before calling Scout with uncertain directories.

**Scout task fallback:** If Scout cannot find relevant files in the provided directories, it lists top-level directories and suggests where to look next. When Scout returns empty or incomplete results, re-call with refined directories or ask the user for guidance.

After Scout returns → Phase 2 (Decide) with recon data to fill T_0 Imports needed.

---

# Phase 2: Decide

+ Make strategic decisions → discuss with user first
+ Send only T_0 downstream → curate decisions, not conversation transcript
+ Fill T_0 Imports needed as completely as possible from Scout recon (Phase 1.5) — minimize unknowns left in T_0

**Context Compaction** — when conversation grows long, compact:
- **Keep:** Past failures, key decisions (Goal, Background, Constraints), current Imports needed state
- **Drop:** verbose scout output, step-by-step diffs, redundant confirmations

---

# Phase 3: Task

Write T_0 containing only decisions (not conversation). T_0 is the ONLY context downstream agents receive. It must be self-contained.

**Do when writing T_0:** Fill all 5 sections with decisions, not conversation. Use Scout recon for Imports needed.
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

### Constraints
[Technical constraints: language, framework, patterns to follow, things to avoid]
[Include exact test expectations: error messages, expected behavior, edge cases]

### Imports needed
[Type signatures for every imported module outside Target Files]
[Brief dependency map between files — e.g., "A depends on B", provided by Scout recon]
[Format: `functionName(params): ReturnType — path/to/file.ts`]
[MUST fill from Scout recon (Phase 1.5) — Giver includes all known signatures in T_0]
[Write the actual signatures — do not write "see xxx.ts"]
```

---

# Phase 4: Chain

Giver always calls a P→W×10 chain (Planner + 10 Worker slots). The chain returns the last Worker's RESULT to Giver automatically.

+ Write source files → delegate to the Worker chain
+ Implement code → delegate to the chain

## Critical Rules

1. **Every chain MUST include `"context": "fresh"` at the chain level** — this sets fresh mode for all agents in the chain. Individual step-level `"context"` is ignored (not supported in ChainStep). Default agent context is fork which leaks parent context.
2. **Every chain MUST include `"cwd": "{project_root}"`** — this sets the working directory for all agents in the chain. Without it, agents may write files to the wrong directory. Replace `{project_root}` with the actual project root path.
3. **{previous} carries only the previous step's output** — NOT all accumulated history. Each chain step receives `{previous}` = the previous agent's text output only.
4. **Planner is in the chain** — P writes task1.md through taskN.md in the chain directory. N depends on logical modification groups, not file count. Chain always has 10 Worker slots. Unused Workers (no taskK.md) return no-op RESULT immediately.
5. **Workers receive {previous} from the previous step** — Worker 1 receives Planner output; Worker K (K≥2) receives Worker K-1's RESULT. Same file can be modified by multiple Workers in sequence (Wₖ reads files modified by Wₖ₋₁).
6. **Worker reads only its own task file** — W reads task{k}.md (not plan.md) and implements. This keeps Worker input small — no need to see other Workers' tasks.
7. **Worker must run tests to verify** — each Worker runs the relevant tests after implementing. If tests fail, fix before outputting.
8. **Worker RESULT has 3 sections only** — Files (created/modified), Signatures (new exports), Summary (1-2 sentences what was done). Do NOT include code bodies, test output, or implementation details. Subsequent Workers read files directly via SCOPE if they need details. This keeps {previous} small and prevents token bloat.
9. **Planner curates for efficiency** — include all information Workers need (error messages, expected behavior, edge cases) in Constraints. When Workers have enough context, they don't read extra files — this saves tokens.
10. **Last Worker's output is the chain result** — the chain system returns the last Worker's text output to Giver. Giver reads progress.md in the chain directory for full results from all Workers.

## H Document Format

Plan.md uses H document format. `----` separates Tasks and Results. `##` separates sections inside.

```markdown
----
# Task #0 (for Planner)

### Goal
...

## PLAN (by Planner)
{overall plan}

----
# Task #1 (for Worker 1)

### Goal
...
### Background
...
### Past failures
...
### Constraints
...
### Target Files
- src/foo.ts
- src/bar.ts
### Imports needed
{Curated by Planner from T_0}
### File Relationships
{Brief dependency map between Target Files — e.g., A depends on B}

## Imports needed
{resolved dependency signatures for all Worker Tasks}

----
# RESULT #1 (by Worker 1)

## Files
- created: src/foo.ts, src/bar.ts
- modified: src/utils.ts

## Signatures
export function fName(params): RetType — src/foo.ts
export class CName { method(params): RetType } — src/bar.ts

## Summary
Replaced storageType/storagePath with databaseUrl in Config. Added parseConnectionString() to factory.ts.

> **RESULT contains Files, Signatures, and Summary only — no code bodies.** Subsequent Workers read files directly via SCOPE if they need implementation details.
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
      "task": "----\n# Task #0 (for Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints, framework, patterns}\n\n### Imports needed\n{dependency signatures with file paths}\n\n---\n\n## Your Role\n\nWrite task1.md through taskN.md (N \u2264 10) in the chain directory. Also write plan.md as a brief overview.\n\n## Working Rules\n\n- Curate from Task #0 only — read NO source or test files. T_0 contains all information you need.\n- Curate per Worker — include ONLY what that Worker needs. Each task file contains: Goal, Background, Past failures, Constraints, Target Files, Imports needed.\n- Group by logical modification groups, not by file count. One file can be modified by multiple Workers in sequence. Order by dependency layer.\n- Write at most 10 task files. If the work requires more than 10 groups, merge smaller groups.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "worker",
      "task": "Read task1.md from the chain directory. If task1.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\nImplement the Target Files listed there.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #1 (by Worker 1)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task2.md from the chain directory. If task2.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #1 from Worker 1.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #2 (by Worker 2)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task3.md from the chain directory. If task3.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #2 from Worker 2.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #3 (by Worker 3)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task4.md from the chain directory. If task4.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #3 from Worker 3.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #4 (by Worker 4)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task5.md from the chain directory. If task5.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #4 from Worker 4.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #5 (by Worker 5)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task6.md from the chain directory. If task6.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #5 from Worker 5.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #6 (by Worker 6)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task7.md from the chain directory. If task7.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #6 from Worker 6.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #7 (by Worker 7)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task8.md from the chain directory. If task8.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #7 from Worker 7.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #8 (by Worker 8)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task9.md from the chain directory. If task9.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #8 from Worker 8.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #9 (by Worker 9)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {
      "agent": "worker",
      "task": "Read task10.md from the chain directory. If task10.md does not exist, output: \"No task assigned. No files modified.\" and stop immediately.\n\n{previous} contains RESULT #9 from Worker 9.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #10 (by Worker 10)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    }
  ],
  "context": "fresh",
  "cwd": "{project_root}"
}
```

Giver constructs the chain with all 10 Worker slots. Giver writes ONLY Task #0. Planner writes task1.md through taskN.md (N ≤ 10) in the chain directory. Each Worker reads its own task file. Workers without a task file output no-op immediately.

The **last Worker** does not need the Imports needed / Files sections (no subsequent Workers need them).

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

Fix only the specific problem. Do refactor only when user explicitly requests.

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

If you don't know the signatures → run Scout FIRST, then include them in the Task's Imports needed.