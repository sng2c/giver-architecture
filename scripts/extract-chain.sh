#!/bin/bash
# extract-chain.sh — Extract chain run data to JSON
# Usage: ./extract-chain.sh [chain-id]
#   No args: extract all chains
#   With arg: extract specific chain

set -euo pipefail

CHAINDIR="/tmp/pi-subagents-uid-0/chain-runs"
ARTIFACTS_DIR=""  # auto-detect

# Find artifacts directory for the project
for session_dir in ~/.pi/agent/sessions/*/subagent-artifacts; do
    if [ -d "$session_dir" ]; then
        # Use the most recent one that has chain meta files
        if ls "$session_dir"/*_meta.json 1>/dev/null 2>&1; then
            ARTIFACTS_DIR="$session_dir"
            break
        fi
    fi
done

extract_chain() {
    local chain_id="$1"
    local chain_path="$CHAINDIR/$chain_id"

    [ -d "$chain_path" ] || { echo "Chain $chain_id not found" >&2; return 1; }

    # Chain-level data
    local has_plan="false"
    local has_progress="false"
    local num_tasks=0

    [ -f "$chain_path/plan.md" ] && has_plan="true"
    [ -f "$chain_path/progress.md" ] && has_progress="true"
    num_tasks=$(ls "$chain_path"/task*.md 2>/dev/null | wc -l)

    echo "  {"
    echo "    \"chain_id\": \"$chain_id\","
    echo "    \"has_plan\": $has_plan,"
    echo "    \"has_progress\": $has_progress,"
    echo "    \"num_tasks\": $num_tasks,"

    # Plan size
    if [ -f "$chain_path/plan.md" ]; then
        local plan_size=$(wc -c < "$chain_path/plan.md")
        echo "    \"plan_size_bytes\": $plan_size,"
    fi

    # Task sizes
    echo "    \"tasks\": ["
    local first=true
    for task_file in "$chain_path"/task*.md; do
        [ -f "$task_file" ] || continue
        local task_name=$(basename "$task_file")
        local task_size=$(wc -c < "$task_file")
        [ "$first" = "false" ] && echo ","
        printf "      {\"name\": \"%s\", \"size_bytes\": %d}" "$task_name" "$task_size"
        first=false
    done
    echo ""
    echo "    ],"

    # Agent data from meta files
    echo "    \"agents\": ["
    local first_agent=true

    if [ -n "$ARTIFACTS_DIR" ]; then
        for meta_file in "$ARTIFACTS_DIR"/${chain_id}*_meta.json; do
            [ -f "$meta_file" ] || continue
            [ "$first_agent" = "false" ] && echo ","
            first_agent=false

            python3 -c "
import json, sys
with open('$meta_file') as f:
    m = json.load(f)
u = m.get('usage', {})
print(f'{{\"agent\": \"{m.get(\"agent\", \"?\")}\", \"model\": \"{m.get(\"model\", \"?\")}\",  \"exit_code\": {m.get(\"exitCode\", -1)}, \"tokens_in\": {u.get(\"input\", 0)}, \"tokens_out\": {u.get(\"output\", 0)}, \"turns\": {u.get(\"turns\", 0)}}')
" 2>/dev/null || true
        done
    fi
    echo "    ]"
    echo "  }"
}

# Main
echo "{"
echo "\"extracted_at\": \"$(date -Iseconds)\","
echo "\"chain_dir\": \"$CHAINDIR\","
echo "\"artifacts_dir\": \"$ARTIFACTS_DIR\","
echo "\"chains\": ["

if [ -n "${1:-}" ]; then
    extract_chain "$1"
else
    first=true
    for chain_path in "$CHAINDIR"/*/; do
        [ -d "$chain_path" ] || continue
        chain_id=$(basename "$chain_path")
        [ "$first" = "false" ] && echo ","
        first=false
        extract_chain "$chain_id"
    done
fi

echo ""
echo "  ]"
echo "}"