# Walkthrough: two sessions, one feature

A realistic slice of a squad day. `alice` and `bob` share a machine and a repo; each has
its own git worktree. Commands are prefixed with the session for clarity — in reality each
runs in its own pane where `SQUAD_NAME` is already set.

```bash
# --- planning: whoever picks up the ask decomposes it first ---
alice$ naly add "Extract the CSV parser"      --notes "pure fn, no IO"
alice$ naly add "Wire parser into the CLI"    --notes "depends on the extract"
alice$ naly add "Docs + example"

# --- both grab work; the lock prevents competing claims for the same task ---
alice$ naly claim t1        # CLAIMED t1 → alice
bob$   naly claim t1        # DENIED t1 — already owned by alice
bob$   naly claim t2        # CLAIMED t2 → bob   (bob picks a different slice)

# --- alice finishes her slice on her branch and sends it for review ---
alice$ naly handoff t1 --to bob --review --branch wt-alice --notes "check header row + empty file"

# --- bob checks his inbox at his next task boundary ---
bob$   naly inbox
#   14:02:10  alice -> bob     handoff  t1  ·  for review: check header row + empty file

bob$   # pull wt-alice, run the project checks (see .squad/project-checks.md) ...
bob$   naly fail t1 "empty-file case throws"      # back to alice with a reason
# ...alice fixes, re-hands-off, bob re-checks...
bob$   naly pass t1                                # t1 → done

# --- a cross-cutting finding goes to everyone ---
alice$ naly log "CSV delimiter is ';' in prod exports, not ','"
bob$   naly inbox
#   14:20:41  alice -> *       note     -   ·  CSV delimiter is ';' in prod exports, not ','

alice$ naly board             # the whole picture, always accurate
```

The point: nobody edited a shared board by hand, nobody stepped on anyone's task, and the
review gate is a real state a task passes through — not a Slack message someone forgot.
