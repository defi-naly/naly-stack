---
name: squad
description: >-
  Coordinate with other parallel agent sessions (Claude Code, Codex, or other CLIs) through the shared `squad`
  board to coordinate task ownership, handoffs, and review. Use whenever the
  `SQUAD_NAME` env var is set, a `.squad/` directory exists in the project, or the
  user mentions a squad, parallel sessions, or running multiple agents at once.
---

# Naly Stack coordination

You may be one of several agent sessions working in parallel for the same person on
the same machine. **You cannot see the other sessions' conversations.** You coordinate
only through the `squad` CLI and the `.squad/` directory. This skill is how you behave
when that's the case.

## First, am I in a squad?

You are if **any** of these is true:
- `SQUAD_NAME` is set (`echo $SQUAD_NAME` — if non-empty, that IS your identity).
- `.squad/` exists here (`naly board` shows a roster or tasks).
- The user says so.

If none hold and you're working solo, ignore this skill.

## The rules (non-negotiable when in a squad)

1. **Look before you leap.** At every task boundary run `naly board` and `naly inbox`
   before picking up shared work. Never start something another session owns.
2. **Claim atomically.** `naly claim <id>` — proceed **only** if it prints `CLAIMED`.
   `DENIED` means it's taken; choose another task.
3. **Announce by doing.** Claiming sets the task to `doing` with you as owner — the
   board updates itself. You don't hand-edit anything.
4. **Hand off, don't hoard.** Finish with `naly done <id>`; send for review with
   `naly handoff <id> --to <reviewer> --review --notes "<what to check>"`; drop a task
   you've stopped on with `naly release <id>`.
5. **No double work.** Never touch a task another session owns. Decompose a big request
   into board tasks (`naly add …`) **before** coding so slices don't overlap. You may
   spawn your own subagents for your claimed slice.
6. **Own tree per session.** For parallel file edits, work in your own git worktree/
   branch — don't edit the same files as another session in the same tree.

## Command reference

```
naly board                     rendered board: roster · tasks by status · recent
naly inbox                     what happened FOR YOU since you last looked
naly add "<title>" [--notes …] create a backlog task (prints its id)
naly claim <id>                atomically take it — proceed only on CLAIMED
naly handoff <id> --to <who> [--review] [--branch wt-x] [--notes …]
naly pass <id> | fail <id> "<why>"     reviewer verdict
naly done <id> | release <id>          finish / give back
naly log "<note>"              broadcast a shared decision to every inbox
naly list [--status s] [--mine] · show <id> · status · whoami
```

## At the start of a session

If `SQUAD_NAME` isn't already your identity, register once: `naly name <you>`. Then
`naly board` + `naly inbox`, and wait for the user's direction or claim an unowned
task per the rules above.

## Routing and shared skills

Sessions may use different providers and models. The launcher sets `SQUAD_DIR` to
one absolute board path across worktrees; preserve it in every squad command.
`SQUAD_ROLE` describes your specialty, not your provider.

When splitting work, route frontend/design tasks with `naly add "..." --role frontend`
and other implementation with `--role default` if those roles are configured in
`$SQUAD_DIR/sessions`. For another specialty, use its configured role. Unmatched roles
fall back to the single default session; ambiguous routes fail instead of guessing.
Routing is chosen by the agent when decomposing the request, not inferred by the CLI.
Tasks without a role stay open to any session. Check `naly show <id>`; `assigned`
identifies the intended peer. Handoff to another peer with `--to <session-name>`.

Use `--skills name,name` when adding a task to identify the relevant shared skills.
Read those skills from `$SQUAD_DIR/skills/<name>/SKILL.md` before working. The shared
library is also linked into each worktree's `.agents/skills` and `.claude/skills`.
When improving an authorized shared skill, edit its source once and tell peers which
skill changed in the handoff notes. Run `naly skills sync` after adding a new skill;
peers may need to reload skills or restart to discover it.

Keep shared skills in portable Markdown with relative resource paths. Provider-only
tools, hooks, credentials, and plugin configuration are not shared by these links.
Never assume that another session can use your tools or see your conversation.
Include branch/commit, changed files, checks run, and next steps in handoff notes.


## Record outcomes and improve shared skills

Claims snapshot the configured agent/model and hashes of the task's listed SKILL.md
files when the learning helper is installed. `naly pass`, `fail`, and `done` record
workflow verdicts. These are not human acceptance or proof that tests ran.

Run project checks through `naly check <id> -- <command> [args...]` when useful: it
executes the command and records its exit code against the current attempt. It does
not rerun automatically. Inspect attempts, checks, and feedback with `naly outcome <id>`.

Record substantive feedback with `naly outcome <id> --decision accepted|revised|rejected
--reason "..." --changes "what was corrected"`. The source defaults to `agent`.
Use `--source human` only for feedback explicitly supplied by the user, preserving its
meaning. Do not label your own judgment or an automatic review as human feedback.

For a repeated correction, add `--correction <stable-tag> --skill <listed-skill>
--kind preference|defect`. Use preference for style/taste and defect for a reported
correctness issue. A proposed portable instruction can be recorded with `--lesson
"..."`; preserve the user's scope instead of turning a one-off request into a general rule.

`naly insights` reports evidence across distinct tasks. `naly insights --propose`
drafts changes only when the same lesson occurs on at least three distinct tasks
within the same skill/tag/kind/source group. It makes no model calls and does not
infer causes, rankings, or new rules from free text. Do not duplicate feedback to
manufacture this threshold.

Review `naly proposal show <id>` and its evidence with the user. Apply a proposal
with `naly proposal apply <id>` only when the user authorizes that specific skill
change; permission to implement a task or record feedback does not authorize applying
proposals. The command checks for changes since drafting and updates the shared source.
After applying, tell peers to reload the skill. Current model context may still contain
the old instructions.
