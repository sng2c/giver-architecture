---
name: giver
version: "3.5.1"
description: "The Giver v3.5.1. Discuss → Recon → Decide → Task → Chain → Verify → Iterate. Pipeline: P→W→W→... Workers pass {previous}. No Scout in chain. All subagents run fresh."
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

Planner writes separate task files (task1.md, task2.md, ...) for each Worker batch. Each Worker reads only its own task file. No Scout in chain. Workers receive {previous} with brief plan summary + accumulated RESULTs.

```
Giver → Task #0 (for Planner) — the only document Giver writes
Planner → writes task1.md, task2.md, ... + brief plan.md
Worker 1 → reads task1.md, {previous} = plan summary
Worker 2 → reads task2.md, {previous} = plan summary + RESULT #0
Worker N → reads task{N}.md, {previous} = plan summary + RESULTS
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

Call chains (P→W or P→W→W→...).

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
8. **Worker must report files created/modified** — each Worker lists what files it created or modified in RESULT, so subsequent Workers know what changed via {previous}.
9. **Planner curates for efficiency** — include all information Workers need (error messages, expected behavior, edge cases) in Constraints. When Workers have enough context, they don't read extra files — this saves tokens.

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
# RESULT #0 (by Worker 1)

All tests pass.
## Files created
- src/foo.ts
- src/bar.ts

## Files modified
- src/utils.ts

## Imports needed (new signatures)
export function fName(params): RetType — src/foo.ts
export class CName { method(params): RetType } — src/bar.ts
```

## File Grouping

Max 3 files per W. Order by dependency layer.

```
Layer 0 (no project imports): A, B  → Worker 1
Layer 1 (imports Layer 0):      C, D  → Worker 2
Layer 2 (imports Layer 0-1):    E, F  → Worker 3
```

| Files | Chain                    | Batches |
|-------|--------------------------|---------|
| 1-3   | P→W                      | 1       |
| 4-6   | P→W→W                    | 2       |
| 7-9   | P→W→W→W                  | 3       |
| 3+N   | P→W×N                    | N       |

## Template: 1-3 files (1 batch)

Giver fills in {placeholders} and invokes the chain. Giver writes ONLY Task #0. Planner writes separate task files (task1.md, task2.md, ...) per Worker batch. Each Worker reads only its own task file.

```json
{
  "chain": [
    {
      "agent": "planner",
      "task": "----\n# Task #0 (for Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints, framework, patterns}\n\n### Imports needed\n{dependency signatures with file paths}\n\n---\n\n## Your Role\n\nYou are the Planner. Write task1.md, task2.md, etc. (one per Worker batch) in H document format. Also write plan.md as a brief overview.\n\nCurate Task #0 into T_k for each Worker file. task1.md MUST use this format:\n\n----\n## PLAN (by Planner)\n{overall plan — file grouping, dependency layer order, integration points}\n\n----\n# Task #1 (for Worker 1)\n\n### Goal\n(curate Task #0's Goal for this Worker)\n\n### Background\n(curate Task #0's Background for this Worker)\n\n### Past failures\n(curate Task #0's Past failures for this Worker)\n\n### Constraints\n(curate Task #0's Constraints for this Worker)\n\n### Target Files\n- path/to/file1.ts\n- path/to/file2.ts\n\n### Imports needed\n(curate Task #0's Imports needed for this Worker)\n----\n\n## Working Rules\n\n- Curate from Task #0 only — read NO source or test files. T_0 contains all information you need.\n- Curate per Worker — include ONLY what that Worker needs.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n- Curate for efficiency — include enough context in Constraints so Workers don't need to read extra files.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "worker",
      "task": "Read task1.md from the chain directory. Implement the Target Files listed there.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite RESULT:\n\n----\n# RESULT #0 (by Worker 1)\n\nAll tests pass.\n## Files created\n- src/foo.ts\n\n## Files modified\n- (none)\n\n## Imports needed (new signatures)\nexport function fName(params): RetType — path/to/file.ts\n\n{previous}"
    }
  ],
  "context": "fresh",
  "cwd": "{project_root}"
}
```

---

## Template: 4-6 files (2 batches)

```json
{
  "chain": [
    {
      "agent": "planner",
      "task": "----\n# Task #0 (for Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints}\n\n### Imports needed\n{dependency signatures with file paths}\n\n---\n\n## Your Role\n\nWrite task1.md, task2.md, etc. (one per Worker batch) in H document format. Also write plan.md as a brief overview.\n\nEach task file MUST contain:\n\n----\n## PLAN (by Planner)\n{brief overview}\n\n----\n# Task #1 (for Worker 1)\n{curated sections}\n\n----\n# Task #2 (for Worker 2)\n{curated sections}\n----\n\nEach Task section uses the same format as Task #0 plus Target Files and curated Imports needed.\n\n## Working Rules\n\n- Curate from Task #0 only — read NO source or test files. T_0 contains all information you need.\n- Curate per Worker — include ONLY what that Worker needs.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n- Curate for efficiency — include enough context in Constraints so Workers don't need to read extra files.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "worker",
      "task": "Read task1.md from the chain directory. Implement the Target Files listed there.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite RESULT:\n\n----\n# RESULT #0 (by Worker 1)\n\nAll tests pass.\n## Files created\n- src/foo.ts\n\n## Files modified\n- (none)\n\n## Imports needed (new signatures)\nexport function fName(params): RetType — path/to/file.ts\n\n{previous}",
    },
    {
      "agent": "worker",
      "task": "Read task2.md from the chain directory. Implement the Target Files listed there.\n\n{previous} contains RESULT #0 from Worker 1.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite RESULT:\n\n----\n# RESULT #1 (by Worker 2)\n\nAll tests pass.\n## Files created\n- (list files)\n\n## Files modified\n- (list files)\n\n## Imports needed (accumulated)\nNew signatures this Worker exports.\n\n{previous}",
    }
  ],
  "context": "fresh",
  "cwd": "{project_root}"
}
```

---

## Template: 7+ files (3+ batches)

Add Worker steps for each additional batch. Each Worker receives {previous} containing accumulated RESULTs from previous Workers. Workers read only their own task{k}.md.

```json
{
  "chain": [
    {
      "agent": "planner",
      "task": "----\n# Task #0 (for Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints, framework, patterns}\n\n### Imports needed\n{dependency signatures with file paths}\n\n---\n\n## Your Role\n\nWrite task1.md, task2.md, task3.md, etc. (one per Worker batch) in H document format. Also write plan.md as a brief overview.\n\n## Working Rules\n\n- Curate from Task #0 only — read NO source or test files. T_0 contains all information you need.\n- Curate per Worker — include ONLY what that Worker needs.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "worker",
      "task": "Read task1.md from the chain directory. Implement the Target Files listed there.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite RESULT:\n\n----\n# RESULT #0 (by Worker 1)\n\nAll tests pass.\n## Files created\n- (list files)\n\n## Imports needed (new signatures)\nexport function fName(params): RetType — path/to/file.ts\n\n{previous}",
    },
    {
      "agent": "worker",
      "task": "Read task2.md from the chain directory. Implement the Target Files listed there.\n\n{previous} contains RESULT #0 from Worker 1.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite RESULT:\n\n----\n# RESULT #1 (by Worker 2)\n\nAll tests pass.\n## Files created\n- (list files)\n\n## Imports needed (new signatures)\nexport function fName(params): RetType — path/to/file.ts\n\n{previous}",
    },
    {
      "agent": "worker",
      "task": "Read task{N}.md from the chain directory. Implement the Target Files listed there.\n\n{previous} contains all previous Worker Results.\n\nSCOPE: Read only files listed in Target Files and Imports needed.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix before outputting.\n\nWrite RESULT:\n\n----\n# RESULT #N (by Worker N)\n\nAll tests pass.\n## Files created\n- (list files)\n\n## Files modified\n- (list files)\n\n## Imports needed\nNew signatures this Worker exports.\n\n{previous}",
    }
  ],
  "context": "fresh",
  "cwd": "{project_root}"
}
```

The **last Worker** does not need the Imports needed / Files sections (no subsequent Workers need them).

---

## Template: Parallel workers (independent slices only)

Only after P→W has produced task files. Only when files have NO overlap and NO imports between them.

```json
{
  "tasks": [
    {
      "agent": "worker",
      "task": "Read your task file ({layer}-layer). Target files: {files}.\n\nImplement the Target Files. Run tests to verify.\n\nWrite RESULT:\n\n----\n# RESULT (by Worker)\n\nAll tests pass.\n\n{previous})",
    },
    {
      "agent": "worker",
      "task": "Read your task file ({layer}-layer). Target files: {files}.\n\nImplement the Target Files. Run tests to verify.\n\nWrite RESULT:\n\n----\n# RESULT (by Worker)\n\nAll tests pass.\n\n{previous})",
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

1. Run tests / verify results
2. Report: what was done, key files, branch status
3. Discuss next steps

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