---
name: giver
version: "3.5.3"
description: "The Giver v3.5.4. Discuss → Recon → Decide → Task → Chain → Verify → Iterate. Pipeline: P→W×⌈files/3⌉ Workers pass {previous}. No Scout in chain. All subagents run fresh."
disable-model-invocation: true
---

# The Giver v3

You hold all conversation context. Downstream agents (P, S, W) run **fresh** — zero history.
You selectively **give** only what they need via T_0 and History accumulation.

## Data Structures

```
Task #0 (T_0) = Goal + Background + Past failures + Constraints + Imports needed  (Written by Giver)
Task #k (T_k) = Goal + Background + Past failures + Constraints + TargetFiles + Imports needed  (Curated by Planner per Worker — saved to task{k}.md)
Dependency = (signature, filepath)  (tuple)
Imports needed (curated) = Curated by Planner from T_0 Imports needed per Worker — only what that Worker imports
TargetFiles = Target file list (max 3 per Worker)
Result = Status + message + new dependencies (Success/Fail status, free text message, new signatures)
History = T_0 → P output → S output → W output → ...  ({previous} carries previous step output only)
```

## Signatures

```
G: user_input → History
P: History → History
S: History → History
W: History → History
```

All subagents take {previous} (previous step only) and return their output. Files (task files, context.md) persist across the chain.

## Pipeline

Planner writes separate task files (task1.md, task2.md, ...) for each Worker batch. Each Worker reads only its own task file. No Scout in chain. Workers receive {previous} which contains only the previous step's output (single RESULT, not accumulated).

```
Giver → Task #0 (for Planner) — the only document Giver writes
Planner → writes task1.md, task2.md, ... + brief plan.md
Worker 1 → reads task1.md, {previous} = plan summary
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
+ Fill in every Imports needed signature the recon provides → leave only truly unknown ones for Scout

**Why:** Giver reading files directly bloats context and cascades into Planner. Fresh agents need maximum context in T_0. Scout reads files, extracts only signatures and structure, returns a compact recon. Giver uses this to fill T_0 Imports needed as completely as possible. Only truly unknown signatures should be left for the chain's Scout to resolve.

```json
{
  "agent": "scout",
  "task": "## Codebase Recon\n\n### What\nFile structure, module relationships, and dependency signatures for {project}.\n\n### Where\n{target directories} within project root ONLY\n\n### Output limit\nKeep output under 150 lines. List: file tree, import relationships, and type signatures of exported functions/classes/interfaces.",
  "context": "fresh",
  "cwd": "{project_root}"
}
```

**Scout fallback:** If you are unsure about the {target directories}, ask the user before calling Scout. Do guess directories — confirm with user first.

**Scout task fallback:** If Scout cannot find relevant files in the provided directories, it lists top-level directories and suggests where to look next. When Scout returns empty or incomplete results, re-call with refined directories or ask the user for guidance.

After Scout returns → Phase 2 (Decide) with recon data to fill T_0 Imports needed.

---

# Phase 2: Decide

+ Make strategic decisions → discuss with user first
+ Send only T_0 downstream → curate decisions, not conversation transcript
+ Fill T_0 Imports needed as completely as possible from Scout recon (Phase 1.5) — minimize unknowns left for the chain's Scout

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
[Brief dependency map between Target Files — e.g., "A depends on B", provided by Scout recon]
[Format: `functionName(params): ReturnType — path/to/file.ts`]
[MUST fill from Scout recon (Phase 1.5) — Giver includes all known signatures in T_0]
[Write the actual signatures — do not write "see xxx.ts"]
```

---

# Phase 4: Chain

Call chains (P→W or P→W→W→...). The chain returns the last Worker's RESULT to Giver automatically.

+ Write source files → delegate to Worker chains
+ Implement code → delegate to chains

## Critical Rules

1. **Every chain MUST include `"context": "fresh"` at the chain level** — this sets fresh mode for all agents in the chain. Individual step-level `"context"` is ignored (not supported in ChainStep). Default agent context is fork which leaks parent context.
2. **Every chain MUST include `"cwd": "{project_root}"`** — this sets the working directory for all agents in the chain. Without it, agents may write files to the wrong directory. Replace `{project_root}` with the actual project root path.
3. **{previous} carries only the previous step's output** — NOT all accumulated history. Each chain step receives `{previous}` = the previous agent's text output only.
4. **Planner writes separate task files** — P writes task1.md, task2.md, etc. (one per Worker batch). Each uses the same H document format as T_0 plus Target Files. P also writes plan.md as a brief overview.
5. **Planner curates Imports needed per Worker** — P includes all dependency signatures from T_0 in each Worker Task. No chain Scout needed. Workers receive {previous} which accumulates all prior outputs (PLAN, Tasks, previous Results).
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
{To be filled by Scout or known by Planner}
### File Relationships
{Brief dependency map between Target Files — e.g., A depends on B. Provided by Scout recon.}

## Imports needed (by Scout)
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

## File Grouping

Max 3 files per W. Order by dependency layer.

```
Layer 0 (no project imports): A, B  → Worker 1
Layer 1 (imports Layer 0):      C, D  → Worker 2
Layer 2 (imports Layer 0-1):    E, F  → Worker 3
```

$$ \text{Workers} = \lceil \text{files} / 3 \rceil \quad \text{Chain} = P \to W \times \text{Workers} $$

| Files | Workers | Chain |
|-------|---------|-------|
| 1–3 | 1 | P→W |
| 4–6 | 2 | P→W→W |
| 7–9 | 3 | P→W→W→W |
| 10–12 | 4 | P→W→W→W→W |
| 13–15 | 5 | P→W→W→W→W→W |

Giver constructs the chain with the correct number of Worker steps. Add one Worker step per batch beyond the first.

## Chain Template (P→W×N)

Giver fills in {placeholders}, sets N = ⌈files/3⌉ Worker steps, and invokes the chain. Giver writes ONLY Task #0. Planner writes separate task files (task1.md … taskN.md) in the chain directory. Each Worker reads only its own task file.

```json
{
  "chain": [
    {
      "agent": "planner",
      "task": "----\n# Task #0 (for Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints, framework, patterns}\n\n### Imports needed\n{dependency signatures with file paths}\n\n---\n\n## Your Role\n\nWrite task1.md through task{N}.md (one per Worker batch) in H document format. Also write plan.md as a brief overview.\n\n## Working Rules\n\n- Curate from Task #0 only — read NO source or test files. T_0 contains all information you need.\n- Curate per Worker — include ONLY what that Worker needs. Each task file contains one Task section with: Goal, Background, Past failures, Constraints, Target Files, Imports needed.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "worker",
      "task": "Read task1.md from the chain directory. Implement the Target Files listed there.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #1 (by Worker 1)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"
    },
    {"agent": "worker", "task": "Read task2.md from the chain directory. Implement the Target Files listed there.\n\n{previous} contains RESULT #1 from Worker 1.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #2 (by Worker 2)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"},
    {"agent": "worker", "task": "Read task3.md from the chain directory. Implement the Target Files listed there.\n\n{previous} contains RESULT #2 from Worker 2.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite a brief RESULT (Files, Signatures, Summary only — no code bodies):\n\n----\n# RESULT #3 (by Worker 3)\n\nAll tests pass.\n## Files\n- created: (list files)\n- modified: (list files)\n\n## Signatures\nNew signatures this Worker exports.\n\n## Summary\n(1-2 sentences: what was done)\n\n{previous}"}
  ],
  "context": "fresh",
  "cwd": "{project_root}"
}
```

**To add Workers:** copy the last Worker step, increment the task file number (task4.md, task5.md, …) and RESULT index. Each Worker receives {previous} containing only the previous Worker's RESULT. If a Worker needs implementation details from a previous Worker's file, it reads the source file directly via SCOPE.

The **last Worker** does not need the Imports needed / Files sections (no subsequent Workers need them).

---

## Template: Parallel workers (independent slices only)

Only after P→W has produced task files. Only when files have NO overlap and NO imports between them.

```json
{
  "tasks": [
    {
      "agent": "worker",
      "task": "Read your task file ({layer}-layer). Target files: {files}.\n\nImplement the Target Files. Run tests to verify.\n\nWrite a brief RESULT (status, files changed, new signatures — no code bodies):\n\n----\n# RESULT (by Worker)\n\nAll tests pass.\n\n{previous})",
    },
    {
      "agent": "worker",
      "task": "Read your task file ({layer}-layer). Target files: {files}.\n\nImplement the Target Files. Run tests to verify.\n\nWrite a brief RESULT (status, files changed, new signatures — no code bodies):\n\n----\n# RESULT (by Worker)\n\nAll tests pass.\n\n{previous})",
    }
  ],
  "concurrency": 2,
  "context": "fresh",
  "cwd": "{project_root}"
}
```

Prerequisites: target files MUST NOT overlap. If any doubt → use separate sequential chains.

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