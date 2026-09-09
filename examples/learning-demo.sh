#!/usr/bin/env bash
# Synthetic, isolated walkthrough. No agents or model APIs are launched.
set -euo pipefail
SQUAD_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$SQUAD_SOURCE/bin:$SQUAD_SOURCE/launcher:$PATH"
SQUAD_DEMO_ROOT="$(mktemp -d)"
trap 'rm -rf "$SQUAD_DEMO_ROOT"' EXIT
export SQUAD_DIR="$SQUAD_DEMO_ROOT/.squad"
export SQUAD_NAME=demo-builder SQUAD_AGENT_KIND=demo SQUAD_MODEL=synthetic
cd "$SQUAD_DEMO_ROOT"
squad init >/dev/null
mkdir -p "$SQUAD_DIR/skills/design"
cat > "$SQUAD_DIR/skills/design/SKILL.md" <<'EOF'
---
name: design
description: Design interfaces for the demo project.
---

# Design
Follow the project's design conventions.
EOF
for number in 1 2 3; do
  squad add "Demo screen $number" --skills design >/dev/null
  squad claim "t$number" >/dev/null
  squad check "t$number" -- python3 -c 'print("Synthetic check passed")' >/dev/null
  squad outcome "t$number" --decision revised --source human \
    --reason 'Too many competing primary actions.' --changes 'Reduced to one primary action.' \
    --correction action-hierarchy --skill design --kind preference \
    --lesson 'Keep one primary action per screen.' >/dev/null
  squad done "t$number" >/dev/null
done
printf '%s\n' 'Synthetic demo data only — no real model evaluation.'
squad insights --propose
for proposal in "$SQUAD_DIR/learning/proposals/"*.md; do
  cat "$proposal"
done
