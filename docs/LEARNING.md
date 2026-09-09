# Learn from completed work

Naly Stack's learning layer keeps local evidence of what happened on your tasks. It can
surface repeated corrections and turn an explicitly suggested lesson into a skill
change for review. It uses Python's standard library: no API calls, embeddings,
telemetry, or background process.

## Setup

From the Naly Stack checkout:

```bash
./install.sh
```

The installer links `squad-learn` alongside `squad` and `squad-up`. The launcher supplies `SQUAD_AGENT_KIND` and `SQUAD_MODEL`. Claims still work without the learning
helper or Python, but print a warning that learning was skipped. A failed learning
record does not undo a successful board action.

## 1. Capture the work as it happens

Add the skills relevant to the task, then claim it in the agent session:

```bash
naly add "Simplify account settings" --role frontend --skills frontend-design
naly claim t1
```

Each successful claim of a real task creates a new attempt snapshot containing:

- Task ID, title, owner, role, time, and recording session.
- Configured agent and model labels, plus where that metadata came from.
- SHA-256 hashes of the listed skills' `SKILL.md` contents at claim time.

A re-claim after rework creates another attempt. Review locks such as `rev:t1` do
not create builder attempts. A missing skill is recorded with a null hash. A hash
identifies the available instruction file, not proof that the agent read it; resource
files under the skill are not fingerprinted in this version.

A CLI's default or internally switched model cannot be observed reliably here.
Unspecified models are labeled `unknown (CLI default)`. Even a pinned identifier is
a configured label, not independently verified runtime telemetry. Manual sessions
can set `SQUAD_AGENT_KIND` and `SQUAD_MODEL`; otherwise the matching sessions row is
used when available. Do not infer model performance from missing or stale metadata.

For tasks with no snapshot, `naly outcome capture t1` takes a snapshot **now**.
It cannot reconstruct the original model or skill contents. Old task history is not
silently backfilled.

## 2. Record actual check results

```bash
naly check t1 -- python3 -m unittest discover -s tests
```

Naly Stack executes the command directly, streams its output, and records its argv,
working directory, elapsed time, and exit code. It returns the command's exit status.
No shell expansion is added; use an explicit shell command if that is what you intend.
A command that exits zero is a recorded observation, not proof that the task is correct.
A check attaches to the latest captured attempt as of command startup.

Commands and feedback are stored locally as entered. Full test output is not saved.

## 3. Separate completion, review, and human judgment

Normal commands automatically record **workflow** outcomes:

| Board command | Learning outcome |
|---|---|
| `naly pass t1` | accepted, source `workflow` |
| `naly fail t1 "reason"` | revised, source `workflow` |
| `naly done t1` | unassessed, source `workflow` |

Explicit feedback has source `agent` by default. To record the user's actual decision:

```bash
naly outcome t1 --decision revised --source human \
  --reason "The screen has too many competing primary actions." \
  --changes "Reduced three prominent actions to one." \
  --correction action-hierarchy --skill frontend-design --kind preference \
  --lesson "Keep one primary action per screen."
```

`--decision` accepts `accepted`, `revised`, or `rejected`. Revised/rejected decisions
need a reason. `--changes` is an optional description of the intervention, not an
automatically captured code diff. The task's current branch field is also recorded.

Use `--kind preference` for taste, style, or project conventions; use `defect` for a
reported correctness problem. These labels are supplied by the recorder, not inferred
or verified by Naly Stack. Likewise, `--source human` is provenance asserted by the caller,
not authentication. An agent must only use it for feedback actually given by the user.

A correction requires a stable tag, reason, kind, and a skill listed on the captured
attempt. Reuse a tag for the same issue on future tasks. `--lesson` is an optional,
explicitly proposed instruction; Naly Stack never invents one from your reason text.

```bash
naly outcome t1                   # JSON history: attempts, checks, and feedback
naly outcome t1 --attempt ATTEMPT_ID --decision accepted --source human
```

Without `--attempt`, feedback attaches to the latest attempt. Use its ID when reviewing
an older attempt after new work has begun. Records are append-only; later feedback
preserves earlier evidence. For the model/role summary, a task contributes only its
latest attempt, and the latest human decision on that attempt takes precedence over
agent/workflow reports. Historical corrections remain visible after acceptance.

## 4. See recurring patterns

```bash
naly insights
naly insights --json
```

The report contains descriptive counts by role, configured model, and feedback
source. It doesn't rank models or change routing. Tasks have different difficulty,
reviewers, skills, and acceptance criteria; the counts are not a controlled comparison.

Correction patterns require **three distinct task IDs** sharing a skill, correction
tag, kind, and source. Ten records about one task count once. Preferences and defects
are kept separate, as are human and agent feedback. Pattern evidence includes task
IDs, attempt IDs, reasons, and immutable event IDs so you can inspect the source.
Patterns cover the local recorded history, including older skill versions; they do
not imply that an issue still exists in the current version.

## 5. Propose, review, and apply a skill change

```bash
naly insights --propose
naly proposal show PROPOSAL_ID
```

A proposal needs the **same exact lesson text on at least three distinct tasks** in
one pattern group. If equally frequent lessons conflict, no proposal is generated.
This is deliberately a first, deterministic version: no semantic clustering or
LLM-generated rewriting. Similar feedback phrased differently can still show as a
pattern when its tag matches, but won't silently become a new instruction.

The proposal includes the evidence, original skill hash, and proposed full content.
A companion Markdown file under `.squad/learning/proposals/` shows a diff. `proposal
show` displays the authoritative JSON; review that content and its evidence before
applying. Proposals append the lesson to the skill and never apply automatically.

Once you have approved the specific change:

```bash
naly proposal apply PROPOSAL_ID
```

The apply command checks that the skill still matches its original hash, atomically
updates the shared source, and records the before/after hashes in an audit event.
If the skill changed in the meantime, it refuses to overwrite it: regenerate and
review a fresh proposal. Applying twice also refuses. Symlinked skill sources remain
symlinks; both providers see the source update. Reload skills or restart active agents
as appropriate. Source control remains the way to review and revert skill history.

## Storage and current boundaries

```text
.squad/learning/
├── events/<id>.json      # versioned attempt, check, outcome, and skill-update records
└── proposals/<id>.json  # proposed content, original hash, and supporting evidence
              <id>.md   # companion review diff
```

Each event is written separately and published with an atomic rename, so concurrent
writers don't share an append buffer. The board is still designed for cooperating
local sessions, not adversarial users. Skill applications serialize within a board;
external editors and other boards do not participate in that lock.

This release establishes **record → inspect → propose → explicitly apply**. Automatic
model selection, causal performance claims, cost accounting, task dependency
scheduling, and semantic learning are not implemented.
