#!/usr/bin/env python3
"""analyze-chains.py — Analyze extracted chain data

Reads JSON from extract-chain.sh output or directly from chain directories.
Produces comparison reports, token analysis, and version metrics.

Usage:
    ./extract-chain.sh > chains.json
    python3 scripts/analyze-chains.py chains.json

    # Or direct:
    python3 scripts/analyze-chains.py --dir /tmp/pi-subagents-uid-0/chain-runs

    # Compare two versions:
    python3 scripts/analyze-chains.py v3.5.json v3.5.3.json --compare
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict


def load_data(source):
    """Load chain data from JSON file"""
    with open(source) as f:
        return json.load(f)


def extract_from_dir(chain_dir, artifacts_dir=None):
    """Extract chain data directly from directory"""
    chain_path = Path(chain_dir)
    chains = []
    
    for cp in sorted(chain_path.iterdir()):
        if not cp.is_dir():
            continue
        
        chain_id = cp.name
        task_files = sorted(cp.glob("task*.md"))
        plan_file = cp / "plan.md"
        progress_file = cp / "progress.md"
        
        chain_data = {
            "chain_id": chain_id,
            "has_plan": plan_file.exists(),
            "has_progress": progress_file.exists(),
            "num_tasks": len(task_files),
            "tasks": [],
            "agents": [],
        }
        
        if plan_file.exists():
            chain_data["plan_size_bytes"] = plan_file.stat().st_size
        
        for tf in task_files:
            chain_data["tasks"].append({
                "name": tf.name,
                "size_bytes": tf.stat().st_size,
            })
        
        # Extract agent data from meta files
        if artifacts_dir:
            ap = Path(artifacts_dir)
            for meta_file in sorted(ap.glob(f"{chain_id}*_meta.json")):
                try:
                    with open(meta_file) as f:
                        m = json.load(f)
                    u = m.get("usage", {})
                    chain_data["agents"].append({
                        "agent": m.get("agent", "?"),
                        "model": m.get("model", "?"),
                        "exit_code": m.get("exitCode", -1),
                        "tokens_in": u.get("input", 0),
                        "tokens_out": u.get("output", 0),
                        "turns": u.get("turns", 0),
                    })
                except Exception:
                    pass
        
        chains.append(chain_data)
    
    return chains


def analyze(data):
    """Analyze chain data and return metrics"""
    chains = data.get("chains", [])
    if not chains:
        print("No chains found")
        return None
    
    metrics = {
        "total_chains": len(chains),
        "total_tokens_in": 0,
        "total_tokens_out": 0,
        "total_turns": 0,
        "by_agent": defaultdict(lambda: {"in": 0, "out": 0, "turns": 0, "count": 0, "success": 0, "fail": 0}),
        "by_chain": [],
    }
    
    for chain in chains:
        chain_metrics = {
            "chain_id": chain["chain_id"],
            "num_tasks": chain.get("num_tasks", 0),
            "has_plan": chain.get("has_plan", False),
            "tokens_in": 0,
            "tokens_out": 0,
            "turns": 0,
            "agents": [],
        }
        
        for agent in chain.get("agents", []):
            ti = agent.get("tokens_in", 0)
            to = agent.get("tokens_out", 0)
            tu = agent.get("turns", 0)
            ag = agent.get("agent", "?")
            ec = agent.get("exit_code", -1)
            
            metrics["total_tokens_in"] += ti
            metrics["total_tokens_out"] += to
            metrics["total_turns"] += tu
            
            metrics["by_agent"][ag]["in"] += ti
            metrics["by_agent"][ag]["out"] += to
            metrics["by_agent"][ag]["turns"] += tu
            metrics["by_agent"][ag]["count"] += 1
            if ec == 0:
                metrics["by_agent"][ag]["success"] += 1
            else:
                metrics["by_agent"][ag]["fail"] += 1
            
            chain_metrics["tokens_in"] += ti
            chain_metrics["tokens_out"] += to
            chain_metrics["turns"] += tu
            chain_metrics["agents"].append(agent)
        
        # Task size stats
        task_sizes = [t.get("size_bytes", 0) for t in chain.get("tasks", [])]
        chain_metrics["task_sizes"] = task_sizes
        chain_metrics["plan_size"] = chain.get("plan_size_bytes", 0)
        
        metrics["by_chain"].append(chain_metrics)
    
    return metrics


def print_report(metrics, label=""):
    """Print analysis report"""
    if not metrics:
        return
    
    header = f"Chain Analysis Report"
    if label:
        header += f" — {label}"
    print("=" * 70)
    print(f"  {header}")
    print("=" * 70)
    
    print(f"\n📊 Overview")
    print(f"   Chains:     {metrics['total_chains']}")
    print(f"   Tokens in:  {metrics['total_tokens_in']:>10,}")
    print(f"   Tokens out: {metrics['total_tokens_out']:>10,}")
    print(f"   Turns:     {metrics['total_turns']:>10,}")
    
    print(f"\n📋 Per-Agent Breakdown")
    print(f"   {'Agent':10s} {'In':>10s} {'Out':>8s} {'Turns':>6s} {'Calls':>5s} {'Pass':>4s} {'Fail':>4s}")
    for ag, data in sorted(metrics["by_agent"].items()):
        print(f"   {ag:10s} {data['in']:>10,} {data['out']:>8,} {data['turns']:>6,} {data['count']:>5,} {data['success']:>4,} {data['fail']:>4,}")
    
    print(f"\n📋 Per-Chain Breakdown")
    print(f"   {'Chain':10s} {'Tasks':>5s} {'In':>10s} {'Out':>8s} {'Turns':>6s} {'Plan':>6s} {'Agents':>20s}")
    for cm in metrics["by_chain"]:
        agents_str = "→".join(a.get("agent", "?")[:1].upper() for a in cm["agents"])
        plan_size = f"{cm.get('plan_size', 0)/1024:.1f}K" if cm.get('plan_size', 0) else "-"
        print(f"   {cm['chain_id'][:10]:10s} {cm['num_tasks']:>5,} {cm['tokens_in']:>10,} {cm['tokens_out']:>8,} {cm['turns']:>6,} {plan_size:>6s} {agents_str:>20s}")
    
    # Isolation metrics
    print(f"\n🔒 Isolation Metrics (v3.5+)")
    for cm in metrics["by_chain"]:
        agents = cm["agents"]
        if len(agents) < 2:
            continue
        
        chain_id = cm["chain_id"][:10]
        # Find planner and worker tokens
        planner_in = sum(a["tokens_in"] for a in agents if a["agent"] == "planner")
        worker_inputs = [a["tokens_in"] for a in agents if a["agent"] == "worker"]
        
        if planner_in > 0:
            print(f"   {chain_id}: Planner {planner_in:,} → W1 {worker_inputs[0]:,}" + 
                  (f" → W2 {worker_inputs[1]:,}" if len(worker_inputs) > 1 else "") +
                  (f" → W3 {worker_inputs[2]:,}" if len(worker_inputs) > 2 else ""))


def compare(metrics1, metrics2, label1="v1", label2="v2"):
    """Compare two sets of metrics"""
    print("=" * 70)
    print(f"  Comparison: {label1} vs {label2}")
    print("=" * 70)
    
    def delta(v1, v2):
        if v1 == 0:
            return "N/A"
        pct = (v2 - v1) / v1 * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.0f}%"
    
    print(f"\n{'Metric':20s} {label1:>12s} {label2:>12s} {'Delta':>10s}")
    print("-" * 56)
    
    pairs = [
        ("Chains", metrics1["total_chains"], metrics2["total_chains"]),
        ("Tokens in", metrics1["total_tokens_in"], metrics2["total_tokens_in"]),
        ("Tokens out", metrics1["total_tokens_out"], metrics2["total_tokens_out"]),
        ("Turns", metrics1["total_turns"], metrics2["total_turns"]),
    ]
    
    for name, v1, v2 in pairs:
        print(f"  {name:18s} {v1:>12,} {v2:>12,} {delta(v1, v2):>10s}")
    
    # Per-agent comparison
    all_agents = set(list(metrics1["by_agent"].keys()) + list(metrics2["by_agent"].keys()))
    print(f"\n  {'Per-Agent':18s} {'v1 In':>10s} {'v2 In':>10s} {'Delta':>10s}")
    print("-" * 50)
    for ag in sorted(all_agents):
        v1 = metrics1["by_agent"].get(ag, {"in": 0})
        v2 = metrics2["by_agent"].get(ag, {"in": 0})
        print(f"  {ag:18s} {v1['in']:>10,} {v2['in']:>10,} {delta(v1['in'], v2['in']):>10s}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Giver chain data")
    parser.add_argument("files", nargs="*", help="JSON files from extract-chain.sh")
    parser.add_argument("--dir", help="Chain runs directory")
    parser.add_argument("--artifacts", help="Subagent artifacts directory")
    parser.add_argument("--compare", action="store_true", help="Compare two JSON files")
    parser.add_argument("--output", "-o", help="Output JSON file")
    args = parser.parse_args()
    
    if args.dir:
        # Direct extraction from directory
        chains = extract_from_dir(args.dir, args.artifacts)
        data = {
            "extracted_at": __import__("datetime").datetime.now().isoformat(),
            "chain_dir": str(args.dir),
            "chains": chains,
        }
        if args.output:
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Saved to {args.output}")
        
        metrics = analyze(data)
        print_report(metrics)
        return
    
    if not args.files:
        print("Usage: analyze-chains.py <json-file> [json-file2] [--compare]")
        print("       analyze-chains.py --dir <chain-runs-dir> [--artifacts <dir>]")
        sys.exit(1)
    
    datasets = []
    for f in args.files:
        data = load_data(f)
        metrics = analyze(data)
        datasets.append((f, metrics))
    
    if args.compare and len(datasets) == 2:
        compare(datasets[0][1], datasets[1][1], 
                label1=Path(args.files[0]).stem,
                label2=Path(args.files[1]).stem)
    else:
        for label, metrics in datasets:
            print_report(metrics, label=label)


if __name__ == "__main__":
    main()