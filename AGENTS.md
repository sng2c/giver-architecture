# AGENTS.md - Giver Architecture

## Project Overview
Giver is a theoretical framework and a Pi coding agent skill designed for high-scale pipeline orchestration. It implements a "Steering Isolation" pattern to solve the problem of context pollution in multi-agent workflows.

The core philosophy is that **Context = Steering (Direction) $\cup$ I/O (Code, Logs, Trace)**. By isolating steering from I/O at agent boundaries, Giver prevents the exponential growth of context and reduces agent drift in long chains.

## Project Structure
```text
giver-architecture/
├── skills/giver/        # The actual Pi agent skill (SKILL.md)
├── reports/            # Research reports (v1 through v25f) comparing monolithic vs. pipeline
│   └── redbis-data/    # Dataset from Redbis comparison experiments
├── scripts/             # Data extraction and chain analysis tools
├── giver-principles.md # Formal logical principles and mathematical models
└── package.json        # Pi skill package metadata
```

## Build & Test Commands
This project is a **Pi Skill package**. It does not have a standalone build process.
- **Integration**: The skill is loaded by the Pi agent via the `pi-subagents` framework.
- **Verification**: Validated through the reports in `reports/` by analyzing chain efficiency and result accuracy.

## Conventions & Patterns

### The 3-Tier Pipeline
The standard workflow follows this sequence:
`Giver` $\xrightarrow{T_0}$ `Planner` $\xrightarrow{\{T_k\}}$ $\prod$ `Workers` $\xrightarrow{R_k}$ `Giver`

### Core Principles
1. **Isolation**: Only pass $\text{steer}(\cdot)$ downstream. Discard $\text{io}(\cdot)$ at every boundary.
2. **No I/O Backflow**: Workers must return a `RESULT` containing summaries and breaking changes, but **never** the full source code. 
3. **Independence**: Every sub-agent (Planner, Worker) runs in a `fresh` context, independent of the parent's conversation history.
4. **Lossy Compression**: History is maintained through combined results $R_k = W_k(\ldots, R_{k-1})$, where each step compresses the previous state into steering only.

## Boundaries & Constraints
- **Strict RESULT Format**: If a Worker includes raw code in its `RESULT`, it violates the 3rd principle and causes context pollution.
- **Complexity Limit**: The pipeline is typically bounded to a maximum of 10 Worker slots.
- **Pure-Rand**: The project uses `pure-rand` for deterministic simulation in reports.
