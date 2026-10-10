#!/usr/bin/env bash
# Create a task file. Usage: scripts/new_task.sh "Title" [owner=unassigned] [prio=P1]
set -euo pipefail
cd "$(dirname "$0")/../coord/tasks"
title="$1"; owner="${2:-unassigned}"; prio="${3:-P1}"
last=$(ls T-*.md 2>/dev/null | sed -E 's/^T-([0-9]+).*/\1/' | sort -n | tail -1)
id=$(printf "T-%03d" $((10#${last:-0} + 1)))
slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g' | cut -c1-40)
file="$id-${slug:-task}.md"
cat > "$file" <<MD
---
id: $id
title: $title
owner: $owner
status: todo
prio: $prio
model: -
depends:
---
## Goal

## Acceptance
- [ ]

## Notes

## Thread

## Result
MD
echo "coord/tasks/$file"
