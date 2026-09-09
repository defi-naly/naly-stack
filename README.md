<div align="center">

# Naly Stack

### Different models. One team.

**Let Claude build the interface. Let Codex build the engine. Give them a shared board, shared skills, and a way to hand work to each other.**

[Choose your setup](#choose-your-setup) · [Get started](#get-started) · [Live dashboard](#live-dashboard) · [How it works](#how-it-works) · [Shared skills](#one-skill-library-every-agent) · [Learning](#turn-repeated-feedback-into-shared-lessons) · [Commands](#command-reference)

MIT · Local-first · Any model · Shared lessons

</div>

---

**Run locally on your own computer, or connect over SSH to a remote machine.**
Use terminal tabs or tmux to manage your agents; tmux lets you detach and return to
running sessions in either setup. Keep the agents and shared board on the same machine.
Choose one provider or mix models to suit each job.

Your best frontend agent doesn't have to be your best backend agent.

Naly Stack brings independent coding sessions together over a small, inspectable task board.
Pick the CLI and model for each role. Run each agent in its own worktree. Share the
same skills across providers. Pass finished work to another agent for review, with a
branch and the context it needs to continue.

```text
                         You: “Build account settings”
                                      │
                        Decompose and assign by role
                                      │
                  ┌───────────────────┴───────────────────┐
                  ▼                                       ▼
           frontend · Claude                       builder · Codex
           Design the settings UI                  Implement the API
           worktree: app-frontend                  worktree: app-builder
                  │                                       │
                  └───────────────────┬───────────────────┘
                                      ▼
                              reviewer · Codex
                          Check, integrate, give feedback

                    One board · Atomic claims · Shared skills
```

The coordinating session turns your request into tasks. Naly Stack handles assignment,
claims, and handoffs. You can inspect the board or jump into any agent's terminal.

## What you can do

| Capability | What it means in practice |
|---|---|
| **Mix providers and models** | Claude Code for design, Codex for implementation, a different model for review. Configure each session independently. |
| **Route by specialty** | `--role frontend` assigns UI work to your frontend session. Unmatched roles fall back to your default session. |
| **Work in parallel** | Give each builder a worktree so their edits stay separate. Atomic task claims stop two sessions from claiming the same task at once. |
| **Share skills once** | Your design system, testing workflow, and project knowledge come from one library linked into both providers. |
| **Hand off across models** | Pass a task, branch, and notes to a peer. Its inbox records the handoff. |
| **Review before finishing** | Use the review workflow to return changes with feedback or mark them passed after checking. |
| **Keep agents moving** | Claude and Codex launch in YOLO mode by default, without tool approval prompts. |
| **Learn from corrections** | Record outcomes and check results, surface recurring feedback, and review proposed changes to shared skills. |
| **Manage a live board** | Open `naly ui` to see tasks, configured agents, and activity. Create tasks, route by role, hand off queued work, and review results. |

## Live dashboard

From your initialized project, run:

```bash
naly ui
```

Open **http://127.0.0.1:4310**. The dashboard refreshes from the same task files every
two seconds, including changes agents make through the CLI. No npm install, database,
or hosted account is needed; the server uses Python's standard library.

- **Follow work:** queued, in progress, review, blocked, and completed tasks.
- **See your team:** providers, models, open tasks, and recorded session status.
- **Direct tasks:** create work, route it by role, or hand off queued and blocked tasks.
- **Review results:** inspect branch and handoff notes, pass a review, or return it with feedback.

The dashboard records actions as `dashboard` through the existing CLI and event feed.
New launches record process status and exit codes separately from task completion.
A running process may be waiting for input. The UI does not stream conversations or
wake idle agents. Learning
proposals remain available through `naly insights` and `naly proposal` in the terminal.
For remote access and operating details, see [Dashboard setup](docs/DASHBOARD.md).

## Start with the team you need

Two sessions are enough to start. Add another role when there is independent work
for it; you don't need three subscriptions or a permanent reviewer.

| Your workflow | A useful starting team | What Naly Stack adds |
|---|---|---|
| Building a product alone | Frontend + backend | Split UI and API work while keeping contracts and ownership visible. |
| Maintaining a library | Builder + reviewer, using the same CLI if you prefer | A separate review conversation with explicit checks and feedback. |
| Shipping a website | Design + implementation | Share the design system and hand off decisions with the branch. |
| Tackling a migration | Two builders owning separate components | Parallel edits in separate worktrees, with one place to track progress. |
| Switching models mid-task | One active session at a time | Keep task state, skill sources, and handoff notes available to the next model. |

For a small change, a single agent is often enough. Naly Stack is useful when coordinating
work takes effort: deciding who owns it, passing context, reusing instructions, and
checking what is actually finished. Extra sessions still consume provider usage;
parallel work is most useful when tasks can proceed independently.

## Choose your setup

| Setup | What you need | Where the agents run |
|---|---|---|
| **Local terminal tabs** | Your terminal, git, Bash, Python, and agent CLIs | On your computer. No tmux or SSH required. |
| **Local tmux squad** | The same tools, plus tmux | On your computer, together in one detachable terminal workspace. |
| **Remote tmux squad** | The tools installed on a remote host, plus SSH access | Together on that host; your laptop connects to their terminal. |

The board and skill library work independently of tmux. `naly up` uses tmux to
launch and manage the terminal sessions. For tabs or an editor's integrated terminal,
follow the [setup guide](docs/SETUPS.md#use-terminal-tabs-without-tmux).

### Why use tmux on your own laptop?

[tmux](https://github.com/tmux/tmux/wiki) keeps terminal programs in a session you can
detach from and return to. With Naly Stack, that means:

- **One launch:** start the configured team with `naly up`.
- **One view:** see agents side by side and jump into the one that needs direction.
- **Keep the workspace:** detach, close the terminal window, then reattach to the
  same running sessions instead of opening tabs and rebuilding the layout.
- **Reconnect remotely:** if you later run the squad on another machine, tmux keeps
  those terminal sessions alive through an SSH disconnect.

You can get the same board, claims, handoffs, and shared skills in normal tabs.
Choose tmux for session management. It doesn't make models smarter, restart crashed
agents, or keep your laptop working while it is asleep or powered off.

## Get started

This quickstart runs **locally with tmux**. You need **Bash, git, Python 3.8+, and
tmux**, plus the agent CLIs you want to run. Prefer normal terminal tabs? Follow
steps 1–3, then use the [tab launch instructions](docs/SETUPS.md#use-terminal-tabs-without-tmux).
Install and sign in to Claude Code and/or Codex first. Naly Stack uses their existing
accounts and model settings; it doesn't provide model access.

### 1. Install Naly Stack

```bash
git clone https://github.com/defi-naly/naly-stack.git ~/dev/naly-stack
cd ~/dev/naly-stack
./install.sh
export PATH="$HOME/.local/bin:$PATH"
```

The installer links `naly` and the supporting commands into `~/.local/bin`. Keep that directory on
your PATH. The task board alone needs only Bash + git; Python powers the launcher,
role resolution, and skill linking.

### 2. Give each agent a worktree

From an existing project with at least one commit:

```bash
cd /path/to/your-project
naly init
export SQUAD_DIR="$PWD/.squad"

git worktree add -b squad/frontend ../app-frontend
git worktree add -b squad/builder ../app-builder
git worktree add -b squad/reviewer ../app-reviewer
```

All agents share the board at `SQUAD_DIR`. Each gets its own files and branch.
Naly Stack doesn't create worktrees or merge branches for you; your agents use normal git
commands as part of the workflow.

### 3. Choose your team

This creates a sessions file with real tab separators:

```bash
printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
  frontend ../app-frontend 'Design and implement the UI.' claude '' frontend \
  builder ../app-builder 'Build APIs and other implementation.' codex '' default \
  reviewer ../app-reviewer 'Review handoffs, run checks, and integrate.' codex '' review \
  > "$SQUAD_DIR/sessions"
```

The six columns are **name, working directory, launch prompt, agent command, model,
role**. Empty model columns preserve your CLI's configured model. To pin a model,
put the identifier accepted by that CLI in the fifth column.

Prefer editing a template? Copy [sessions.example](templates/sessions.example) to
`.squad/sessions` and change the worktree paths.

### 4. Add work and launch

```bash
naly add "Build the account settings UI" --role frontend \
  --notes "Profile form, validation, loading and error states. Coordinate API shape with builder."
naly add "Implement the account settings API" --role default \
  --notes "Profile read/update endpoints and tests. Coordinate the contract with frontend."

naly up --dry-run       # inspect the commands and skill links without launching
naly up                # launch the agents in tmux and attach
```

Each agent receives its identity, role, shared board path, and onboarding instructions.
The launcher links the coordination skill into its worktree before starting it.
Agents are instructed to inspect the board and inbox, then claim suitable work.

In tmux, use **Ctrl-b, then an arrow key** to switch panes. Use **Ctrl-b, then d** to
detach while the sessions continue. Run `naly up` to attach again.

## How it works

### A task has one claimant

```bash
naly claim t1
# CLAIMED t1 → frontend
```

A claim uses an atomic `mkdir` lock. If two sessions race for the same task, one
wins and the other receives `DENIED`. Role-assigned tasks also reject claims from
other sessions. This coordinates task ownership; agents still need to follow the
protocol and use separate worktrees to avoid overlapping file edits.

### Roles describe the work, not the vendor

```bash
naly add "Refine the onboarding flow" --role frontend
naly add "Add webhook retries" --role default
naly add "Review the onboarding changes" --role review
```

The CLI records the matching session in the task's `assigned` field and sends it an
inbox event. An unknown role uses the single `default` session. Missing or ambiguous
routes fail before a task is created. Omit `--role` to leave a task open to anyone.

The agent decomposing the request chooses the role. Naly Stack does not classify natural
language itself, wake idle models, or run a background scheduling loop. Sessions
check the board and inbox at task boundaries; you can also direct them in their panes.

### Handoffs carry context across models

From the frontend session, after committing its changes:

```bash
naly handoff t1 --to reviewer --review --branch squad/frontend \
  --notes "Profile UI ready. Form tests pass. Check keyboard navigation and API integration."
```

From the reviewer session:

```bash
naly inbox
naly show t1
naly claim rev:t1
# Inspect the branch, integrate as appropriate, and run the project's checks.
naly pass t1
# Or return feedback:
# naly fail t1 "Keyboard focus disappears after saving."
```

`pass` records the verdict; it does not run tests or merge git branches. The reviewer
does that work. Keep the verification steps in `.squad/project-checks.md` using the
[project checks template](templates/project-checks.md).

For a transfer of implementation work, omit `--review`:

```bash
naly handoff t2 --to frontend \
  --notes "API committed on squad/builder. Wire the form to PATCH /api/profile; see endpoint tests."
```

Agents cannot see each other's conversations. Include the branch or commit, changed
files, checks run, decisions, and next steps so the next model can continue.

## One skill library, every agent

A useful skill shouldn't be trapped in one provider's setup.

```text
.squad/skills/
├── frontend-design/      → design rules and UI workflow
│   └── SKILL.md
├── api-conventions/      → contracts, errors, and testing patterns
│   └── SKILL.md
└── project-review/       → your project's review process
    └── SKILL.md
           │
           ├── app-frontend/.claude/skills/   Claude discovers the skills
           └── app-builder/.agents/skills/   Codex discovers the same sources
```

Place skill folders in `$SQUAD_DIR/skills`, or link existing ones from your skillbank:

```bash
mkdir -p "$SQUAD_DIR/skills"
ln -s /absolute/path/to/frontend-design "$SQUAD_DIR/skills/frontend-design"
naly skills sync

naly add "Polish the settings page" --role frontend --skills frontend-design
```

`sync` links every shared skill into **both** `.agents/skills` and `.claude/skills` in
**every configured worktree**. `naly up` does this too. The bundled coordination skill
is included automatically. A task's `--skills` field tells the agent which shared
instructions to read before working; it doesn't restrict other available skills.

Edit the source once and both agents read the same content. After adding a new skill,
run `naly skills sync` again and reload or restart sessions as needed for discovery.
Existing skills are never overwritten: a conflicting destination stops the sync with
its path. `squad` and `synced` are reserved names.

Share portable Markdown and relative resources. Provider-specific hooks, tool
integrations, credentials, and plugin configuration aren't translated. The linking
uses the documented [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills)
and [Claude Code skill discovery](https://code.claude.com/docs/en/skills) paths.

## Turn repeated feedback into shared lessons

Your corrections can outlast a model session. Naly Stack now records what happened on a
task and helps you turn repeated feedback into a shared instruction:

```text
Task → attempt snapshot → checks and feedback → repeated correction
                                                     │
                                                     ▼
                                    Proposed skill diff → your review → shared source
```

Claims snapshot the configured agent/model and the listed skills' `SKILL.md` hashes.
Normal pass/fail/done commands record workflow outcomes. Add real check results and
explicit feedback when reviewing work:

```bash
naly check t1 -- npm test
naly outcome t1 --decision revised --source human \
  --reason "Too many competing primary actions." \
  --changes "Reduced three prominent actions to one." \
  --correction action-hierarchy --skill frontend-design --kind preference \
  --lesson "Keep one primary action per screen."

naly insights
naly insights --propose
naly proposal show PROPOSAL_ID
# After reviewing and approving this specific change:
naly proposal apply PROPOSAL_ID
```

The task must list `frontend-design` in `--skills` when claimed. Record human feedback
only when it actually came from the user; agent feedback defaults to source `agent`.
Patterns require three distinct tasks with the same correction tag, skill, kind, and
source. Proposals additionally need a matching explicit lesson on three tasks. Skill
changes remain unapplied until you review and apply them; changed sources are protected
by a hash check.

This first version is local and deterministic. It separates preferences from reported
defects and real check exit codes, leaves unknown model identities unknown, and makes
no model-ranking claims. It doesn't infer new rules from conversations or automatically
choose models. See [Learning](docs/LEARNING.md) for attribution, evidence, and limitations.
Existing installations should rerun `./install.sh` to link the new learning helper.
Try the isolated synthetic walkthrough with `bash examples/learning-demo.sh`; it
creates a temporary board and makes no model calls.

## YOLO mode by default

New Claude and Codex sessions launch with their native approval bypass:

| Agent | Flag added by Naly Stack |
|---|---|
| Claude Code | `--dangerously-skip-permissions` |
| Codex | `--dangerously-bypass-approvals-and-sandbox` |

This removes tool approval prompts; the Codex flag also disables its command sandbox.
Agents run with your account's filesystem and command access. Login, first-run trust
setup, operating-system restrictions, and organization policy remain outside Naly Stack's
control.

To use the CLIs' normal permission settings instead:

```bash
naly up --no-yolo
```

The setting applies to newly launched sessions. Attaching to an existing tmux session
doesn't change its running agents. Explicit flags in your configured agent command
are preserved, including any bypass flags you added yourself.

## Configure your team

| Setting | Purpose |
|---|---|
| `SQUAD_DIR` | Shared board path. The launcher passes the same absolute path into every worktree. |
| `SQUAD_SESSION` | tmux session name; defaults to `squad`. Use a different name for another team. |
| `SQUAD_AGENT` | Default command for rows with an empty agent column; otherwise `claude`. |
| `SQUAD_SESSIONS` | Alternate sessions file. Passed to agents so routing uses the same roster. |
| `SQUAD_NAME` | Session identity, set separately for each agent by the launcher. |
| `SQUAD_AGENT_KIND` / `SQUAD_MODEL` | Configured agent/model labels supplied by the launcher for attempt snapshots. |
| `SQUAD_ROLE` | Session specialty, taken from its sessions row. |
| `SQUAD_SKILLS_DIR` | Shared skill library path, set by the launcher. |
| `SQUAD_YOLO` | `1` by default, `0` with `--no-yolo`; supplied to agents and custom wrappers. |

```bash
naly up /path/to/sessions --dry-run
SQUAD_SESSION=another-team naly up /path/to/sessions
```

Relative worktree paths resolve from the directory where you run the command. Old
two- and three-column files still work. Agent commands accept quoted arguments; shell
operators are not evaluated.

### Other agent CLIs

The board and protocol don't depend on a model provider. A custom CLI or wrapper can
occupy any session row. It receives the onboarding prompt as the final argument and
`--model <value>` if the model column is set.

Claude and Codex have built-in permission adapters. For other CLIs, the wrapper must
read `SQUAD_YOLO` and apply its own permission settings; Naly Stack doesn't invent flags for
unknown programs. The shared board and skills are available through the environment.

### Standalone sessions

See [Setups](docs/SETUPS.md) for terminal tabs, a two-session team, and optional
remote access. SSH is only a way to reach a different computer; Naly Stack needs no
network ports or tunnels of its own.

You can use the board without the tmux launcher. Set `SQUAD_DIR` and a stable
`SQUAD_NAME` in each terminal, then follow the [protocol](docs/PROTOCOL.md). For startup
instructions, use [AGENTS-snippet.md](templates/AGENTS-snippet.md) for Codex or
[CLAUDE-snippet.md](templates/CLAUDE-snippet.md) for Claude Code. The bundled Claude
plugin is also available under [plugin/](plugin/).

## Command reference

| Command | Purpose |
|---|---|
| `naly init` | Create the board; repeat calls preserve inbox history. |
| `naly up [file] [--dry-run] [--no-yolo]` | Preview or launch a team; attach if already running. |
| `naly skills sync [file]` | Link the shared skill library into session worktrees. |
| `naly add "title" [--role role] [--skills a,b] [--notes "…"]` | Create and optionally assign a task. |
| `naly claim <id>` | Atomically claim a task; proceed only on `CLAIMED`. |
| `naly handoff <id> --to <name> [--review] [--branch b] [--notes "…"]` | Transfer work or request review. |
| `naly pass <id>` / `naly fail <id> "reason"` | Record a review verdict. |
| `naly done <id>` / `naly release <id>` | Finish or return a task to backlog. |
| `naly outcome <id> [--decision …]` | Inspect history or record explicit feedback. |
| `naly check <id> -- <command>` | Execute a check and record its exit code. |
| `naly insights [--json] [--propose]` | Inspect repeated corrections and draft skill changes. |
| `naly proposal show <id>` / `apply <id>` | Review or explicitly apply a skill proposal. |
| `naly board` / `naly inbox` | See the team state or your new notifications. |
| `naly show <id>` / `naly list [--status s] [--mine]` | Inspect tasks. |
| `naly status` / `naly roster` / `naly whoami` | Inspect claims and identities. |
| `naly name <name>` | Register a friendly name for a stable session identity. |
| `naly log "message"` | Share a decision through all inboxes. |

## What lives on disk

```text
.squad/
├── sessions              # team configuration
├── skills/               # shared skill sources or links
├── tasks/t1              # title, status, owner, assignment, branch, notes
├── locks/t1/owner        # local atomic claim
├── roster/               # identities and inbox cursors
├── learning/             # attempt snapshots, feedback, checks, and proposals
├── events.log            # notification history
└── config                # project metadata
```

All coordinating sessions must share one filesystem. Locks are local, not distributed.
The protocol coordinates cooperating agents; it is not an access-control boundary or
a filesystem lock on the source code.

Generated skill links contain absolute local paths. Keep those links out of commits
and recreate them on each machine. Version shared skill sources and reusable team
configuration as appropriate; task state and machine-specific paths can stay local.
Naly Stack adds no service fee, but your agent providers' usage and account limits still apply.

## Develop and contribute

```bash
python3 -m unittest discover -s tests -v
bash -n bin/squad install.sh
git diff --check
```

Tests use temporary boards/worktrees and stub CLIs/tmux, without paid model calls.
They cover mixed launch commands, permission defaults, routing, claims, handoffs,
review, skill sharing, conflict preservation, three-column session files, and the learning
loop from attempt snapshots to stale-safe skill proposals. Live model
behavior is not covered by this suite.

See [Concepts](docs/CONCEPTS.md), [Protocol](docs/PROTOCOL.md), and the
[walkthrough](examples/walkthrough.md) for more detail. Issues and pull requests are
welcome, especially reproducible coordination failures and adapters for more CLIs.

## License

[MIT](LICENSE).
