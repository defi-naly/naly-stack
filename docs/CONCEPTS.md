# Concepts

## The problem

Run two or more agent sessions (Claude Code panes, other coding agents) on the same
project and they collide:

- **Double work** — both pick up the same task, unaware of each other.
- **Clobbering** — both edit the same files in the same working tree; one overwrites
  the other, or a `git add -A` sweeps up another session's half-finished work.
- **Silent drift** — work is marked "done" that was never verified, or a branch sits
  unpushed and un-reviewed while everyone assumes it shipped.

These are the classic multi-agent failure modes. squad exists to make parallel sessions
safe and legible without a server, a scheduler, or a rewrite of how you work.

## Task ownership and board state

`naly claim <id>` uses an atomic `mkdir` lock. Competing claims for the same
available task have one winner. Agents still need to follow the protocol: claims
do not prevent unclaimed work or lock source files.

Every task is a file under `.squad/tasks/`. `naly board` renders those files on
demand, so there is no separate board to maintain. Lock and task updates are not
a single transaction; interruptions or manual edits can leave inconsistent state.

## Roles

Roles are workflow conventions, not enforced permissions or Git protections. The recommended pattern is:

- **Builders** — claim a backlog task, build it in **their own git worktree**, hand it
  off for review. They never merge into the shared/integration branch themselves.
- **Planner** — *not a standing session.* Whoever first picks up a big request
  **decomposes it into board tasks** (one claimable unit each) before anyone codes, so
  the slices don't overlap. Research is on-demand, not an always-on session.
- **Reviewer / Integrator** — owns the `review → done` gate, runs the project's checks,
  and is the **only** session that integrates work and gates what ships. Pull-model: it
  sweeps its `inbox` at each task boundary rather than being pushed to.

## The pipeline

```
backlog ──claim──▶ doing ──handoff --review──▶ review ──pass──▶ done
                     ▲                            │
                     └──────────── fail ──────────┘
                     └──handoff --to X──▶ blocked (reassigned)
```

Status lives in the task file; the verbs move it. A `fail` sends it back to the owner
with a reason; a `pass` closes it. The review path is a convention: `naly done` can close a task directly. Enforce
required reviews with your repository controls when needed.

## Inbox vs feed

Two different questions, two different views:

- **The feed** (`naly board` → *Recent*) is *everything that happened* — every add,
  claim, done. Ambient awareness.
- **The inbox** (`naly inbox`) is *what happened FOR YOU* — a task handed to you, a
  review request, a pass/fail on your work, or a broadcast note. It advances a per-
  session cursor, so each session sees each item once. This is the notification layer,
  poll-model: cheap to check at every task boundary, no daemon, no push.

Routine claim/done events go to the feed. Adding an assigned task also notifies
its target, so the inbox includes new assignments as well as handoffs.

## Worktrees

The claim lock stops two sessions taking the same *task*; it does **not** stop two
sessions editing the same *files*. For real parallel coding, give each session its own
[git worktree](https://git-scm.com/docs/git-worktree) on its own branch:

```
git worktree add ../proj-alice   -b wt-alice
git worktree add ../proj-bob     -b wt-bob
```

Each session works in its own tree, commits to its own branch, and the Reviewer
integrates. This is what prevents the clobbering failure mode at the disk level.

## The filesystem boundary

The locks are **local-filesystem atomic**. All coordinating sessions must share one
filesystem — the same machine (multiple panes/worktrees), or the same checkout on a
shared mount. squad is not a distributed lock service; it's a coordination layer for
agents working the same box. Keep all agents and the board on the same host for the simplest setup. You can
connect to that host over SSH, but SSH is optional when everything runs locally.
Copying or git-syncing a board between independent machines does not share its locks
and cannot preserve atomic claims. See [Setups](SETUPS.md) for local and remote use.
