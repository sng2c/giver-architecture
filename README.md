# The Giver Architecture

Multi-agent orchestration pattern with context isolation, Dream Sharing, and sawtooth compaction.

## What is The Giver?

The Giver is the context keeper. One agent holds all conversation context and selectively transmits (**tx**) only what downstream agents need. Downstream agents (planner, scout, worker) run as **fresh** — zero history, every time.

This solves the fundamental problem of monolithic agent sessions: context grows exponentially, noise drowns signal, and by turn 200 the agent is paying for 199 previous turns it doesn't need.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **tx (transmission)** | The Giver transmits a 6-section contract to fresh agents. If it's not in the tx, the agent doesn't know it. |
| **Dream Sharing** | When a chain fails, the failure context is structured and transmitted to the next attempt. Fresh agents have zero memory — without Dream Sharing, they repeat the same mistakes. |
| **Sawtooth Compaction** | Context grows linearly during a chain (~1K/turn), then drops back to baseline after compaction. Linear + periodic = bounded context. |
| **Scout Before Worker** | Fresh workers have no implicit code knowledge. Scout provides live codebase orientation before every worker. |

## The 6-Section Contract (tx)

Every transmission MUST contain:

1. **Objective** — what needs to be done and why
2. **Context** — all relevant conversation context the agent cannot see
3. **Previous Failures** — structured failure log (Dream Sharing)
4. **Target Files** — exact file paths or "unknown"
5. **Constraints** — what to avoid, patterns to follow
6. **Scope Boundary** — what's in and out of scope

## Measured Results

| | Monolithic | Fork | The Giver | The Giver + Compaction |
|---|---|---|---|---|
| Context growth | Exponential (26–42×) | Exponential (10–20×) | Linear (10.1×) | **Convergence (sawtooth)** |
| P50 tokens/turn | ~100K | ~43K | ~21K | ~21K |
| Max single turn | 191K | 44–99K | 45K | 45K |
| Session limit | 200K → reset | Same | Linear growth | **Unlimited** |
| Worker context | 191K accumulated noise | Inherited noise | 5–15K brief | 5–15K brief |

## Files

| File | Path | Description |
|------|------|-------------|
| `SKILL.md` | `.pi/agent/skills/giver/SKILL.md` | The Giver skill — tx chain, Dream Sharing, 6-section contract |
| `planner.md` | `.pi/agents/planner.md` | pi-subagents planner override — fresh context mode |
| `worker.md` | `.pi/agents/worker.md` | pi-subagents worker override — fresh context mode |
| `ARCHITECTURE.md` | `ARCHITECTURE.md` | Architecture document with mermaid diagrams |

## Installation

Copy the `.pi/` directory structure to your project root:

```bash
cp -r .pi/ /your-project/.pi/
```

The skill will be activated automatically by pi-agent when the `giver` skill is triggered.

## Deploy

```bash
./scripts/deploy
```

Updates the GitHub gists with the latest versions of SKILL.md and ARCHITECTURE.md.

## License

MIT
