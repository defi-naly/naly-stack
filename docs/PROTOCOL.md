# Protocol

The rules a session follows when there is shared work in flight. This is the human-
readable contract; the bundled skill supplies the same rules to Claude Code and Codex. The launcher
links it into both providers’ skill directories and includes an onboarding prompt.

You are one of several sessions working in parallel for the same person. **You cannot
see the other sessions' conversations.** You coordinate only through `squad` and the
`.squad/` directory.

## Identity (once per session)

```
naly name <you>        # e.g. naly name alice   — a readable handle on the board
```

The launcher sets `SQUAD_NAME` for you; if it did, you're already named.

## The loop — run this at every task boundary

1. **Look before you leap.** `naly board` and `naly inbox`. See what's claimed, what's
   in flight, and what's waiting for you. Never start something already owned.
2. **Claim atomically.** `naly claim <id>` — proceed **only** if it prints `CLAIMED`.
   If it prints `DENIED`, that task is taken; pick another.
3. **Work.** You may fan out your own subagents for your claimed slice — encouraged.
   They're yours; don't claim more tasks than you're actively working.
4. **Hand off or finish.**
   - Done and ready to ship: `naly done <id>`.
   - Needs review first: `naly handoff <id> --to <reviewer> --review --notes "what to check"`.
   - Passing to someone else: `naly handoff <id> --to <who> --notes "why"`.
   - Stopping mid-task: `naly release <id>` so someone else can take it.
5. **Share what matters.** `naly log "the decision / the gotcha"` broadcasts a note to
   every session's inbox. Use it for cross-cutting findings, not chatter.

## Splitting a large request

Whoever picks up a big ask **decomposes it into tasks first** — one claimable unit each
— *before* anyone codes:

```
naly add "Extract the parser"      --notes "pure fn, no IO"
naly add "Wire the parser into CLI" --notes "depends on the extract"
naly add "Docs + examples"
```

Then sessions claim independently. If a unit depends on another, say so in its notes.
This is what stops slices from overlapping.

## Don't clobber — use worktrees

Two sessions editing the same files in the same tree will clobber each other. For
parallel coding, each session works in **its own git worktree/branch** and the Reviewer
integrates. See [CONCEPTS.md](./CONCEPTS.md#worktrees).

## Review pipeline

If your squad runs a Reviewer/Integrator:

- **Builders** build on their own `wt-*` branch, then
  `naly handoff <id> --to <reviewer> --review --branch wt-<you> --notes "<acceptance>"`.
- **The Reviewer** sweeps `naly inbox`, pulls the branch into its own worktree, runs
  the project's checks, then `naly pass <id>` (integrate + done) or
  `naly fail <id> "<reason>"` (back to the builder). Optionally `naly claim rev:<id>`
  first so two reviewers don't collide on the same review.
- Keep the project's verification steps in `.squad/project-checks.md` (copy the
  template) so every reviewer runs the same checks for a given kind of change.

## Don't

- Don't work on a task you didn't claim, or that another session owns.
- Don't silently expand scope into another session's slice — `naly add` a new task.
- Don't treat the board as durable memory; long-lived facts belong in project docs.
- Don't run a second dev server / build in another session's worktree.

## Mixed providers

Use the shared `SQUAD_DIR` supplied by the launcher. Task roles describe specialties,
not vendors: use `naly add "..." --role frontend` or `--role default` for the example
squad. `assigned` is enforced at claim time. Read any `skills` listed on the task
from `$SQUAD_DIR/skills`. Handoff notes should include the branch/commit, changed
files, checks, and next steps: a peer cannot see your model's conversation or tools.
