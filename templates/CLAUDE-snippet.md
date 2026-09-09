<!--
Fallback activation for agents that don't use the Claude Code plugin system.
Paste this section into your ~/.claude/CLAUDE.md (global) or a project CLAUDE.md.
The launcher links the coordination skill and supplies its onboarding prompt.
-->

# Parallel squad coordination

You may be one of several agent sessions running side-by-side for the same person.
You are part of a squad if any is true: **`$SQUAD_NAME` is set** (run `echo $SQUAD_NAME`
— if non-empty, that IS your identity), a **`.squad/` directory exists** here, or the
user says so. When in a squad you coordinate with the other sessions only through the
`squad` CLI (you cannot see their conversations), and you MUST:

1. **Look before you leap** — `naly board` and `naly inbox` before picking up shared work.
2. **Claim atomically** — `naly claim <id>`; proceed ONLY if it prints `CLAIMED`. If
   `DENIED`, the task is taken — choose another.
3. **Hand off, don't hoard** — `naly done <id>` to finish, `naly handoff <id> --to <who>
   [--review] --notes "…"` to pass on, `naly release <id>` if you stop mid-task.
4. **No double work** — never touch a task another session owns. Decompose a big request
   into `naly add` tasks BEFORE coding so slices don't overlap. Prefer a git worktree
   per session for parallel file edits.

If you're working solo, ignore this section.
