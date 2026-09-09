#!/usr/bin/env bash
# Naly Stack installer — symlinks the CLI + launcher onto your PATH. No sudo, no dependencies
# beyond bash + git (Python 3 for launch/routing/skills; tmux for `naly up`).
#
#   ./install.sh                 # links into ~/.local/bin
#   BIN=/usr/local/bin ./install.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${BIN:-$HOME/.local/bin}"
mkdir -p "$BIN"

chmod +x "$ROOT/bin/squad" "$ROOT/launcher/squad-up" "$ROOT/launcher/squad-learn" "$ROOT/launcher/naly-ui"
ln -sf "$ROOT/bin/naly" "$BIN/naly"
ln -sf "$ROOT/bin/squad"          "$BIN/squad"
ln -sf "$ROOT/launcher/squad-up"  "$BIN/squad-up"
ln -sf "$ROOT/launcher/squad-learn" "$BIN/squad-learn"
ln -sf "$ROOT/launcher/naly-ui" "$BIN/naly-ui"
echo "linked:  $BIN/naly  →  $ROOT/bin/naly"
echo "linked:  $BIN/squad  →  $ROOT/bin/squad"
echo "linked:  $BIN/squad-up  →  $ROOT/launcher/squad-up"

case ":$PATH:" in
  *":$BIN:"*) : ;;
  *) echo
     echo "⚠  $BIN is not on your PATH. Add this to your shell profile:"
     echo "     export PATH=\"$BIN:\$PATH\"" ;;
esac

cat <<EOF

Naly Stack installed. Quickstart:
  cd your-project
  naly init
  naly name you
  naly add "first task"
  naly board
  naly ui                 # live dashboard at http://127.0.0.1:4310

For a mixed Claude/Codex squad:
  cp templates/sessions.example your-project/.squad/sessions
  # Edit paths, per-session agent/model, and roles.
  cd your-project
  naly up --dry-run
  naly up

Claude and Codex launch in YOLO mode by default (no tool approval prompts).
Use naly up --no-yolo to keep CLI permission defaults.
The launcher needs Python 3 + tmux. It links the shared squad skill for both CLIs.
For standalone sessions, follow docs/SETUPS.md to sync skills and generate launch commands.
The onboarding prompt tells agents to read the coordination skill.
You can also copy templates/CLAUDE-snippet.md or templates/AGENTS-snippet.md
into your agent instructions.
EOF
