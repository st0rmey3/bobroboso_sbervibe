#!/usr/bin/env bash
# Task board from coord/tasks/*.md frontmatter. Usage: scripts/board.sh [owner|status]
set -euo pipefail
cd "$(dirname "$0")/../coord/tasks"
filter="${1:-}"
printf "%-6s %-4s %-8s %-11s %s\n" ID PRIO STATUS OWNER TITLE
for f in T-*.md; do
  awk -v file="$f" '
    /^---$/ { n++; next }
    n == 1 && /^[a-z]+:/ { k = $1; sub(":", "", k); v = $0; sub(/^[a-z]+: */, "", v); m[k] = v }
    END { printf "%-6s %-4s %-8s %-11s %s\n", m["id"], m["prio"], m["status"], m["owner"], m["title"] }
  ' "$f"
done | grep -v " done " | sort -k2,2 -k1,1 | { if [ -n "$filter" ]; then grep -w -- "$filter" || true; else cat; fi; }
