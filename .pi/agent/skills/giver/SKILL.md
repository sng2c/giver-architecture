---
name: giver
version: "3.0"
description: "The Giver v3. Discuss → Recon → Decide → Task → Chain → Verify → Iterate. Each Worker accumulates Dependencies via {previous}. All subagents run fresh."
disable-model-invocation: true
---

# The Giver v3

You hold all conversation context. Downstream agents (P, S, W) run **fresh** — zero history.
You selectively **give** only what they need via T_0 and History accumulation.

## Data Structures

```
T_0 = Goal + Background + Past failures + Constraints + Imports needed  (G가 작성)
T_k = Goal + Background + Past failures + Constraints + TargetFiles + CuratedDeps  (P가 Worker별 큐레이팅)
Dependency = (시그니처, 파일경로)  (튜플)
CuratedDeps = init Dependencies 큐레이팅  (Worker가 임포트하는 것만)
TargetFiles = 타겟 파일목록  (Worker당 최대 3개)
Result = 상태 + 메시지 + 새의존성  (성공/실패, 자유텍스트, 새시그니처)
History = T_0 → P출력 → S출력 → W출력 → ...  ({previous}는 직전 스텝만 전달, 새의존성은 Worker가 수동 누적)
```

## Signatures

```
G: user_input → History
P: History → History
S: History → History
W: History → History
```

All subagents take {previous} (previous step only) and return their output. Files (plan.md, context.md) persist across the chain.

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

# Phase 1.5: Recon

When Giver needs to understand the codebase before writing T_0 → call Scout standalone.

+ Need dependency signatures → call Scout for recon before T_0
+ Need file structure or module relationships → call Scout for recon before T_0
+ Do NOT read source/test files directly as Giver → delegate to Scout

**Why:** Giver reading files directly bloats context and cascades into Planner. Scout reads files, extracts only signatures and structure, returns a compact recon. Giver uses this to fill Imports needed in T_0.

```json
{
  "agent": "scout",
  "task": "# Codebase Recon\n\n## What\nFile structure, module relationships, and dependency signatures for {project}.\n\n## Where\n{target directories} ONLY\n\n## Output limit\nKeep output under 150 lines. List: file tree, import relationships, and type signatures of exported functions/classes/interfaces.",
  "context": "fresh",
  "cwd": "{project_root}"
}
```

After Scout returns → Phase 2 (Decide) with recon data to fill T_0 Imports needed.

---

# Phase 2: Decide

+ Make strategic decisions → discuss with user first
+ Send only T_0 downstream → curate decisions, not conversation transcript
+ Use Scout recon (Phase 1.5) to fill Imports needed

**Context Compaction** — when conversation grows long, compact:
- **Keep:** Failures, key decisions (Objective, Context, Limits), current Dependencies state
- **Drop:** verbose scout output, step-by-step diffs, redundant confirmations

---

# Phase 3: Task

Write T_0 containing only decisions (not conversation). T_0 is the ONLY context downstream agents receive. It must be self-contained.

**Do when writing T_0:** Fill all 5 sections with decisions, not conversation. Use Scout recon for Imports needed.
**Avoid when writing T_0:** Empty sections, conversation transcript, or reading files directly (delegate to Scout).

```markdown
## Task #0 (Planner)

### Goal
[One sentence: what needs to be done and why]

### Background
[Decisions only: what was decided, why, business context. NOT "user said..."]

### Past failures
[First attempt: "None — first attempt."]
[Retry: structured failure log — what failed, why, what to avoid]

### Constraints
[Technical constraints: language, framework, patterns to follow, things to avoid]

### Imports needed
[Type signatures for every imported module outside Target Files]
[Format: `functionName(params): ReturnType — path/to/file.ts`]
[If unknown → run Scout FIRST, then include here]
[Write the actual signatures — do not write "see xxx.ts"]
```

---

# Phase 4: Chain

Call chains (P→S→W or P→S→W→S→W→...).

+ Write source files → delegate to Worker chains
+ Implement code → delegate to chains

## Critical Rules

1. **Every chain MUST include `"context": "fresh"` at the chain level** — this sets fresh mode for all agents in the chain. Individual step-level `"context"` is ignored (not supported in ChainStep). Default agent context is fork which leaks parent context.
2. **Every chain MUST include `"cwd": "{project_root}"`** — this sets the working directory for all agents in the chain. Without it, agents may write files to the wrong directory. Replace `{project_root}` with the actual project root path.
3. **{previous} carries only the previous step's output** — NOT all accumulated history. Each chain step receives `{previous}` = the previous agent's text output only. For Dependencies to accumulate, each Worker must copy ALL previous Dependencies from `{previous}` and add its own (this is how Dependencies accumulate across Worker steps).
4. **Files persist across chain** — plan.md (P writes, all read) and context.md (S writes, W reads) are file-based and available to all subsequent agents regardless of `{previous}`.
5. **P writes plan.md** — P's output is a plan file, not inline text. W reads plan.md for its instructions.
6. **S writes context.md** — S's output is a recon file. W reads context.md for dependency details.
7. **W reads plan.md and context.md** — these are the two files W needs.
8. **Worker must output new Dependencies** — each Worker outputs its new interface signatures. The last Worker in a chain does NOT need the Dependencies output section (no subsequent Workers need it).
9. **Worker must run tests to verify** — each Worker runs the relevant tests after implementing. If tests fail, fix before outputting.

## File Grouping

Max 3 files per W. Order by dependency layer.

```
Layer 0 (no project imports): A, B  → Worker 1
Layer 1 (imports Layer 0):      C, D  → Worker 2
Layer 2 (imports Layer 0-1):    E, F  → Worker 3
```

| Files | Chain                    | Batches |
|-------|--------------------------|---------|
| 1-3   | P→S→W                    | 1       |
| 4-6   | P→S→W→S→W               | 2       |
| 7-9   | P→S→W→S→W→S→W           | 3       |
| 3N    | P→(S→W)×N                | N       |

## Template: 1-3 files (1 batch)

Giver fills in {placeholders} and invokes the chain.

```json
{
  "chain": [
    {
      "agent": "planner",
      "task": "## Task #0 (Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints, framework, patterns}\n\n### Imports needed\n{dependency signatures with file paths, or 'None — Scout will collect'}\n\n---\n\n## Your Role\n\nYou are the Planner. Write plan.md covering the target files.\n\nCurate the Task above into a Worker Briefing for each Worker. plan.md MUST include a Worker Briefing section with:\n\n### Key Decisions\n(curate the Task's Context for this Worker — only what it needs to know)\n\n### Pitfalls & What to Avoid\n(curate the Task's Failures for this Worker — only relevant failures and what to avoid)\n\n### Constraints\n(curate the Task's Limits for this Worker — only relevant constraints)\n\n### Dependencies\n(CuratedDeps — curate the Task's Dependencies for this Worker. ONLY the interfaces the target files import. Include ONLY the interfaces the target files import)\n\n### Scope Boundary\n(what is IN and OUT of scope)\n\n## Working Rules\n\n- Read the context and scout recon before planning.\n- Read ONLY files listed in Target Files and referenced in Dependencies.\n- CuratedDeps: curate per Worker — include ONLY what that Worker's files import.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "scout",
      "task": "# Implementation Recon\n\n## What\nDependencies and interfaces that plan.md Worker Briefing references but doesn't fully specify.\n\n## Where\n{target directories from plan.md} ONLY\n\n## Output limit\nKeep output under 150 lines. Excerpt ONLY relevant functions and signatures.",
    },
    {
      "agent": "worker",
      "task": "Execute the plan in plan.md. Start by reading plan.md (especially the Worker Briefing section). Follow Key Decisions and Pitfalls strictly.\n\nSCOPE: Read ONLY the files listed in Target Files, Curated Dependencies, and their corresponding TEST FILES. Read ONLY Target Files, Curated Dependencies, and their test files.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports or TODO comments.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix the implementation before outputting.\n\nThen output new Dependencies:\n\n## Dependencies (new signatures)\n```typescript\nexport function fName(params): RetType\nexport class CName { method(params): RetType }\nexport interface IName { prop: Type }\n```\n\n{previous}",
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
      "task": "## Task #0 (Planner)\n\n### Goal\n{one sentence objective}\n\n### Background\n{decisions, context, business requirements}\n\n### Past failures\n{failure log or 'None — first attempt'}\n\n### Constraints\n{technical constraints}\n\n### Imports needed\n{dependency signatures or 'None — Scout will collect'}\n\n---\n\n## Your Role\n\nWrite plan.md covering ALL target files, organized into Worker sections.\n\nEach Worker section specifies:\n- Which 2-3 Target Files this Worker implements\n- CuratedDeps: ONLY the dependency interfaces this Worker's files import (curated from the Task's Dependencies)\n- Integration points with previous implementations\n\nplan.md MUST include Worker Briefing per batch:\n\n### Key Decisions (curate the Task's Context for this Worker)\n### Pitfalls & What to Avoid (curate the Task's Failures for this Worker)\n### Constraints (curate the Task's Limits for this Worker)\n### Dependencies (curated CuratedDeps for this Worker)\n### Scope Boundary\n\n## Working Rules\n\n- Read context and scout recon before planning.\n- Read ONLY files listed in Target Files and referenced in Dependencies.\n- CuratedDeps: curate per Worker — only what that Worker's files import.\n- Name exact files.\n- If underspecified, surface the ambiguity instead of guessing.\n\nIf blocked, use `contact_supervisor` with reason: \"need_decision\".",
    },
    {
      "agent": "scout",
      "task": "# Implementation Recon — Batch 1\n\n## What\nDependencies for Worker 1 files ({list files}) that plan.md references but doesn't fully specify.\n\n## Where\n{target directories from plan.md} ONLY\n\n## Output limit\nKeep output under 150 lines. Excerpt ONLY relevant functions and signatures.",
    },
    {
      "agent": "worker",
      "task": "Execute YOUR section of plan.md (Worker 1). Read plan.md for your Worker Briefing section.\n\n## Task #1 (Worker 1)\n\n### Target Files\n{2-3 target files for batch 1}\n\n### Curated Dependencies\n{curated dependencies for batch 1 — from plan.md Dependencies}\n\n---\n\nSCOPE: Read ONLY the files listed in Target Files, Curated Dependencies, and their corresponding TEST FILES. Read ONLY Target Files, Curated Dependencies, and their test files.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports or TODO comments.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix the implementation before outputting.\n\nAfter implementing, output ALL Dependencies (accumulated):\n\n## Dependencies (accumulated)\n```typescript\nexport function fName(params): RetType\nexport class CName { method(params): RetType }\nexport interface IName { prop: Type }\n```\nThis accumulated Dependencies will be used by the next Scout and Worker via {previous}. Include EVERYTHING.\n\n{previous}",
    },
    {
      "agent": "scout",
      "task": "# Implementation Recon — Batch 2\n\n## What\nDependencies for Worker 2 files ({list files}) that plan.md and {previous} don't fully specify.\n\n## Where\n{target directories from plan.md} ONLY\n\n## Output limit\nKeep output under 150 lines. Excerpt ONLY relevant functions and signatures.",
    },
    {
      "agent": "worker",
      "task": "Execute YOUR section of plan.md (Worker 2). Read plan.md for your Worker Briefing section.\n\nThe Scout's recon in {previous} includes accumulated Dependencies from Worker 1. Use those as your starting point.\n\n## Task #2 (Worker 2)\n\n### Target Files\n{2-3 target files for batch 2}\n\n### Curated Dependencies\n{curated dependencies for batch 2 — from plan.md Dependencies}\n\n---\n\nSCOPE: Read ONLY the files listed in Target Files, Curated Dependencies, and their corresponding TEST FILES. Read ONLY Target Files, Curated Dependencies, and their test files.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports or TODO comments.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix the implementation before outputting.\n\nAfter implementing, output ALL Dependencies (accumulated):\n\n## Dependencies (accumulated)\nInclude your new signatures plus any signatures from {previous} that this batch imports:\n```typescript\nexport function fName(params): RetType\nexport class CName { method(params): RetType }\nexport interface IName { prop: Type }\n```\nThis is the complete accumulated Dependencies. Include EVERYTHING from all previous Workers plus your own.\n\n{previous}",
    }
  ],
  "context": "fresh",
  "cwd": "{project_root}"
}
```

---

## Template: 7+ files (3+ batches)

Add S→W pairs for each additional batch. Pattern:

```json
{
  "agent": "scout",
  "task": "# Implementation Recon — Batch N\n\n## What\nDependencies for Worker N files ({list files}) that plan.md and {previous} don't fully specify.\n\n## Where\n{target directories from plan.md} ONLY\n\n## Output limit\nKeep output under 150 lines. Excerpt ONLY relevant functions and signatures.",
},
{
  "agent": "worker",
  "task": "Execute YOUR section of plan.md (Worker N). Read plan.md for your Worker Briefing section.\n\nThe Scout's recon in {previous} includes accumulated Dependencies from previous Workers. Use those as your starting point.\n\n## Task #N (Worker N)\n\n### Target Files\n{2-3 target files for batch N}\n\n### Curated Dependencies\n{curated dependencies for batch N — from plan.md Dependencies}\n\n---\n\nSCOPE: Read ONLY the files listed in Target Files, Curated Dependencies, and their corresponding TEST FILES. Read ONLY Target Files, Curated Dependencies, and their test files.\n\nIMPORTANT: Write actual source files to disk. Write actual source code, not progress reports or TODO comments.\n\nAfter implementing, run the relevant tests to verify. If tests fail, fix the implementation before outputting.\n\nAfter implementing, output ALL Dependencies (accumulated):\n\n## Dependencies (accumulated)\nInclude your new signatures plus any signatures from {previous} that this batch imports.\nThis is the complete accumulated Dependencies. Include EVERYTHING from all previous Workers plus your own.\n\n{previous}",
}
```

The **last Worker** does not need the Dependencies output section (no subsequent Workers).

---

## Template: Parallel workers (independent slices only)

Only after P→S→W has produced plan.md. Only when files have NO overlap and NO imports between them.

```json
{
  "tasks": [
    {
      "agent": "worker",
      "task": "Execute the {layer}-layer portion of plan.md. Target files: {files}.\n\n## Task #1 (Worker)\n\n### Goal\n{curated objective for this slice}\n\n### Target Files\n{target files for this slice}\n\n### Curated Dependencies\n{curated dependencies for this slice}\n\n---\n\nSCOPE: Read ONLY the files listed in Target Files, Curated Dependencies, and their corresponding TEST FILES.\n\n{previous}",
    },
    {
      "agent": "worker",
      "task": "Execute the {layer}-layer portion of plan.md. Target files: {files}.\n\n## Task #1 (Worker)\n\n### Goal\n{curated objective for this slice}\n\n### Target Files\n{target files for this slice}\n\n### Curated Dependencies\n{curated dependencies for this slice}\n\n---\n\nSCOPE: Read ONLY the files listed in Target Files, Curated Dependencies, and their corresponding TEST FILES.\n\n{previous}",
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
  "task": "# Bug Diagnosis\n\n## What\nInvestigate the reported symptom: {describe symptom}. Find the likely root cause.\n\n## Where\n{directories} ONLY\n\n## Output limit\nKeep output under 150 lines. Include: relevant code sections, error traces, suspicious patterns.",
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

If you don't know the signatures → run Scout FIRST, then include them in the Task's Dependencies.