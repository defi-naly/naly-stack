# Project checks

Copy this to `.squad/project-checks.md` and fill it in for your repo. It's the
Reviewer's runbook: for a given kind of change, what must pass before it's `done`.
Keeping it here (not in each agent's head) means every reviewer runs the same checks.

## Always

- Read the diff for correctness.
- `<your lint command>`   e.g. `npm run lint`
- `<your build command>`  e.g. `npm run build`

## By area

| When the change touches… | Run |
|---|---|
| `src/api/**` | `<api tests>` |
| `src/ui/**`, components | `<component tests / screenshot check>` |
| `db/**`, migrations | `<migration dry-run / smoke>` |
| anything user-facing | `<the acceptance check for the task>` |

## Integration & shipping

- Only the Reviewer merges `wt-*` branches into the integration/shared branch.
- One concern per commit — never a `git add -A` catch-all (that's how one session's
  WIP gets swept into another's commit).
- Push after each clean integration; don't let reviewed work sit unpushed.
- If shipping to production is gated by a human, **surface the choice — never auto-ship.**
