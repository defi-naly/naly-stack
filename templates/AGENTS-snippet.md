# Naly Stack sessions

When SQUAD_NAME is set, use SQUAD_DIR as the shared board and follow the squad skill
in .agents/skills/squad/SKILL.md. Run naly board and naly inbox at task boundaries,
claim before editing, respect task assignments, and include branch, checks, and next
steps in handoffs. Route frontend tasks with --role frontend and other work with
--role default when those roles exist in the shared sessions file. Read each task's
listed shared skills from $SQUAD_DIR/skills. Use a separate worktree for each session.
