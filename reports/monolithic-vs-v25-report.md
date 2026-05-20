# Monolithic vs Giver v2.5 — Controlled Experiment Report

## Experiment Setup

**Task**: Redbis coding test — implement 10 source modules for a Redis-protocol middleware proxy from scratch.

**Approaches compared**:
- **Monolithic**: Single worker, no architecture
- **Giver v2.4**: 3 chains, file-count splitting, Planner→Scout→Worker
- **Giver v2.5**: 3 chains, dependency-depth splitting, Dependency Interface Provision

**v2.5 changes from v2.4**:
1. **Dependency Interface Provision**: Worker brief includes type signatures for all imported modules (no "see xxx.ts")
2. **Worker scope self-containment**: Brief provides everything the Worker needs
3. **Dependency-depth splitting**: Scout analyzes dependencies before splitting decision
4. **Interface verification between chains**: After each chain, verify actual interfaces match briefed interfaces

## Results

### Per-Chain Comparison

| | v2.4 | v2.5 | Change |
|---|------|------|--------|
| **Chain 1** (foundation) | | | |
| Planner | 30,630 🟢 | 43,164 🟢 | +41% |
| Scout | 13,689 🟢 | 43,573 🟢 | +218% |
| Worker | 170,412 🟡 | 132,450 🟡 | -22% |
| Chain total | 214,731 | 219,187 | +2% |
| **Chain 2** (mid-layer) | | | |
| Planner | 46,003 🟢 | 53,218 🟢 | -16% |
| Scout | 14,265 🟢 | 6,835 🟢 | +52% |
| Worker | 76,780 🟢 | 88,942 🟡 | -16% |
| Chain total | 137,048 | 148,995 | +9% |
| **Chain 3** (deep deps) | | | |
| Planner | 48,791 🟢 | — | — |
| Scout | 31,337 🟢 | — | — |
| Worker | 208,547 🟠 | 75,148 🟢 | **-64%** |
| Chain total | 288,675 | 75,148 | **-74%** |

### Chain 3 Detail: The Deep Dependencies Case

v2.5 chain 3 eliminates the Planner and Scout entirely. The Giver writes the Worker brief directly, including:
- Full Dependency Interfaces for IStorage, RESP, Config, Logger
- Detailed implementation specs for each file
- Explicit instruction: "do NOT read these files, use these signatures"

Result: Worker input drops from 208K 🟠 to 75K 🟢 — a **64% reduction** for the most problematic case.

### Overall Comparison

| Metric | Monolithic | v2.4 | v2.5 |
|--------|-----------|------|------|
| Total input tokens | 857,363 🔴 | 640,454 | 443,330 |
| vs Monolithic | — | +25% | **+48%** |
| Ideal agents (≤80K) | 0/1 (0%) | 7/9 (78%) | 5/7 (71%) |
| Waste tokens (>80K) | 777,363 | 218,959 | 61,392 |
| Waste rate | 90.7% | 34.2% | **13.8%** |

### Key Improvement: Waste Reduction

| Metric | v2.4 | v2.5 | Change |
|--------|------|------|--------|
| Waste tokens | 218,959 | 61,392 | **-72%** |
| Waste rate | 34.2% | 13.8% | -20.4pp |

## Analysis

### What Worked

1. **Dependency Interface Provision eliminates Worker over-reading** (chain 3: 208K → 75K, -64%)
   - Worker received full type signatures in brief → no need to read dependency files
   - Direct Worker-only chain for simple delegation (Giver writes brief directly)

2. **Worker-only chain for deep dependencies** (chain 3: no Planner or Scout needed)
   - When Dependency Interfaces are complete, the Giver can skip Planner and Scout
   - Saves Planner (49K) and Scout (31K) overhead = 80K saved

3. **Waste rate dropped from 34% to 14%**

### What Didn't Work

1. **Chain 1 Scout increased 3x** (14K → 44K)
   - Scout was asked for both recon and dependency analysis
   - But this is 44K 🟢 — still within ideal range

2. **Chain 2 Worker slightly worse** (77K → 89K)
   - Worker received Dependency Interfaces in brief, but still read some files
   - 89K is 🟡 (borderline), not ideal 🟢

3. **Ideal rate dropped from 78% to 71%** (7/9 → 5/7)
   - But total agents decreased: 7/9 means 2 agents over 80K, 5/7 means 2 agents over 80K
   - Same number of violations, fewer total agents

### Structural Finding: Three Agent Patterns

v2.5 revealed three distinct patterns:

| Pattern | When | Agents | v2.5 Example |
|---------|------|--------|---------------|
| **Full chain** | New area, need recon + planning | Planner→Scout→Worker | Chain 1 |
| **Focused chain** | Known area, need verification | Planner→Scout→Worker | Chain 2 |
| **Worker-only** | Clear scope, Dependency Interfaces provided | Worker only | Chain 3 |

The **Worker-only** pattern is new in v2.5 and only works when:
- Dependency Interfaces are complete and verified
- Scope is clearly defined
- No ambiguity about what to implement

## Conclusion

v2.5 achieves the biggest single-step improvement in the Giver architecture:

- **Total tokens: 640K → 443K** (-31% vs v2.4, -48% vs monolithic)
- **Waste rate: 34% → 14%** (from 1 in 3 tokens wasted to 1 in 7)
- **Chain 3 Worker: 208K → 75K** (-64%, from 🟠 to 🟢)

The Dependency Interface Provision is the key innovation — it enables the Worker-only pattern and reduces Worker over-reading by providing everything the Worker needs in the brief.