# pi-the-giver

[![npm version](https://img.shields.io/npm/v/@sng2c/pi-the-giver?style=flat-square)](https://www.npmjs.com/package/@sng2c/pi-the-giver) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)

> *"If you're going to receive memories, they should be whole memories."*
> — Lois Lowry, *The Giver*

A Pi coding-agent skill that orchestrates a coding task across a **Planner + N Workers** pipeline with strict context isolation. You talk to **Giver**; Giver delegates. Giver never edits code — it is the memory keeper that distills context into task briefs and hands them to fresh, scope-bound Workers.

## Install

```bash
pi install npm:@sng2c/pi-the-giver
```

## Activate

```
/skill:giver
```

Or add it to your project instructions (`.pi/AGENTS.md`) so it activates automatically for coding tasks.

## Quick start

```
Use the giver skill to implement a user authentication module with login, signup, and password reset
```

Giver will run a Planner → Workers pipeline: write Task #0, call Planner standalone for the exact Worker count N, build a foreground chain of N Workers, then verify and report.

---

## The metaphor — why "The Giver"

In Lois Lowry's *The Giver*, one **Receiver of Memory** holds all of society's memories. Everyone else lives in **Sameness** — no history, no context, no accumulated noise. The Receiver transmits only what's needed, when it's needed. The **giving of pain** — legacy's hard truths, failures, constraints, things never to repeat — is distilled and injected into a blank-slate Receiver.

The skill is the novel, mapped onto a coding agent:

| Novel | Giver skill |
|---|---|
| Receiver holds all memories | Giver holds all conversation context |
| Community lives in Sameness | Workers and Scout run **fresh** — zero history |
| Receiver transmits only selected memories | Planner/Workers receive only T₀ / task files |
| Giving of pain — failures, constraints, never-repeat | `Past failures` + `Constraints` injected into T₀ |
| Memories never leak downward | Giver's conversation never crosses an agent boundary |
| Receiver transmits; does not fix the world | Giver delegates; never edits code directly |

The architecture is not a dressing on top of the skill — the skill *is* the metaphor. Giver is the memory keeper; every downstream agent is a blank-slate Receiver that gets only the distilled essentials.

---

## Why it's efficient — context isolation + separation of concerns

A coding agent reads files, writes code, and runs tests at every step. This **coding I/O** (source, test output, error logs) accumulates, and context grows exponentially:

$$
|\text{context}(n)| = |\text{context}(1)| \cdot r^{n-1} \quad (r > 1)
$$

As context grows, **steering** — the directional instructions ("make this file, fix that error", "use approach Y only when Z") — drowns in coding-I/O noise. The agent loses direction: modifying the wrong file, retrying an already-fixed error, drifting from the goal.

Giver attacks this on two orthogonal axes.

### Axis 1 — Context isolation (across agent boundaries)

Decompose context into **steering** (directional instructions) and **coding I/O** (execution artifacts). **Only steering crosses an agent boundary.** The coding I/O stays inside the agent that produced it.

- Giver's full conversation (~500K tokens of decisions, back-and-forth, discarded attempts) never reaches a Worker.
- Each Worker runs **fresh** and emits a tiny `RESULT` — `Files / Signatures / Breaking / Summary`, no code bodies, no test output.
- The next Worker receives prior `RESULT`s through **structural injection** (the framework's `[Read from:]` prefix on `results.md`), not the full execution trace of its siblings.

| Boundary | Crosses (steering) | Isolated (coding I/O) | Isolation |
|---|---|---|---|
| G → P | T₀ | Giver conversation | ~99% |
| P → Wₖ | taskₖ.md | Other Workers' tasks | 83–93% |
| Wₖ → G | RESULT | Full Worker execution | 98–99% |

> Isolation = 1 − (transmitted size / un-isolated context size).

### Axis 2 — Separation of concerns (within the pipeline)

Each role owns exactly one concern and carries no other's I/O:

| Role | Context | Owns | Does not do |
|---|---|---|---|
| **Giver** | conversation | decisions → T₀ | edit code |
| **Planner** | fresh | curate task files + exact N + layer order | implement |
| **Scout** | fresh | recon → signatures | implement |
| **Worker** | fresh | its scoped files + self-verification | touch others' scope |

Because concerns are separated, a Worker's context never bloats with another agent's decisions or execution. Because agents are isolated, the pipeline's total context grows **additively** (sum of small fresh contexts), not **exponentially** (one snowballing transcript).

### Structural, not instructional

results.md flows to downstream Workers via the framework's `[Read from: <chainDir>/results.md]` prefix — not by asking Workers to "please forward your output." The pipeline's correctness does not depend on an agent faithfully echoing prose. **Structure over instruction**: the mechanism works whether or not the agent is polite about it.

---

## Pipeline

```
Request → Giver (Discuss/Decide) → T₀ → Planner (standalone, fresh) → Plan (exact N + task files)
                                              ↓
                       Giver builds a foreground W×N chain
                                              ↓
   W₁ (reads task1.md)                → RESULT #1 → results.md
   W₂ (reads task2.md + results.md)   → RESULT #2 → results.md
   …                                   …
   W_N                                 → RESULT #N → results.md   → chain completes naturally
                                              ↓
                       Giver reads results.md, verifies, reports
```

- **Scout** is called standalone by Giver before the chain when signatures/target files need recon.
- **Planner** runs standalone (out of the chain) and returns the **exact** count N + dependency-layer ordering, so the chain is sized exactly — no empty slots.
- **Workers** run inside a single foreground chain, fresh, each receiving only its task file and the accumulated `results.md`.

## Why a sequential pipeline (not parallel)

Workers run **W₁ → W₂ → … → W_N in order**, not concurrently. The reason is **change-impact propagation**: a Worker's edits change the real state the next Worker must build on.

- **Same file, multiple concerns**: W₁ adds `UserService`, W₂ adds `UserController` that imports it, W₃ adds tests — all touch `user.ts`. W₂ must read `user.ts` *after* W₁ wrote it; W₃ after both. Parallel would freeze each Worker on a stale snapshot and collide on the shared file.
- **Export dependencies**: Layer 0 creates symbols, Layer 1 imports them, Layer 2 tests them. Wₖ's task references signatures that only exist once W_{k-1} has run. `results.md` carries the actual `Signatures` / `Breaking` forward so Wₖ builds on real exports, not assumed ones.
- **Breaking as a guardrail**: if Wₖ removes or renames an export, W_{k+1} sees it in `results.md` before starting — instead of reading a file, not finding the old symbol, and looping (the "edit → fail → re-read" trap).

Parallelism would require pre-partitioning files with **zero overlap** and **no cross-Worker dependencies** — workable only for independent chunks, and brittle: one shared file or one import edge breaks it. Sequential execution preserves Giver's decomposition freedom: split by *logical modification group*, let groups share files and depend on each other, and let each Worker build on the genuine post-change state. The cost (serial latency) is the price of correctness under shared state — and the chain's structural `[Read from: results.md]` injection makes that propagation reliable without prose instructions.

## Why no `completionGuard`

Earlier versions (v3.7.5) pre-committed to 10 fixed Worker slots and broke the unused tail via pi-subagents' `completionGuard` (a no-op Worker writing nothing → the chain error-signals completion). That hack existed only because the Planner ran *inside* the chain and decided N mid-run, forcing pre-committed slots.

v0.1.0 moves Planner **standalone**, so N is known *before* the chain is built. Giver builds a chain of **exactly N** Workers — no empty slots, no no-op, no `[CHAIN COMPLETED]`, no `completionGuard` repurposing. The chain completes naturally after W_N. (`append-step`/async was tried and rejected after e2e testing — see `docs/history.md`.)

## Dependency

Requires [pi-subagents](https://www.npmjs.com/package/pi-subagents) `latest` (foreground chain + structural `[Read from:]` reads injection).

## References

| File | Content |
|---|---|
| [skills/giver/SKILL.md](skills/giver/SKILL.md) | Full implementation — phases, templates, RESULT format, failure protocol |
| [giver-principles.md](giver-principles.md) | Mathematical definitions — 6 principles, sets, functions, invariants |
| [docs/insights.md](docs/insights.md) | Project insights from the v1–v3.7.x evolution |
| [docs/history.md](docs/history.md) | Version + design history (v1 → v0.1.0, incl. the append-step → Pattern C test journey) |

## Version history (abridged)

| Version | Date | Change |
|---|---|---|
| v3.0 | 2026-05 | Initial Planner → Workers pipeline |
| v3.6.3 | 2026-05 | Target verification scope (−81% verification I/O) |
| v3.7.0 | 2026-05 | results.md structural communication |
| v3.7.5 | 2026-05 | Fixed 10 slots + completionGuard workaround |
| v3.8.0 | 2026-07 | Pattern C — foreground W×N, exact N from standalone Planner (e2e tested) |
| **v0.1.0** | 2026-07 | Package renamed `@sng2c/giver-skill` → `@sng2c/pi-the-giver`; version reset. Architecture = Pattern C (v3.8.0 design) |

## License

MIT