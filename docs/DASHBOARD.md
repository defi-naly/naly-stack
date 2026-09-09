# Live local dashboard

Install Naly Stack with `./install.sh`, then run this from your project:

```bash
naly init  # only needed if the project has no board yet
naly ui
```

Open the URL printed in the terminal. The default is **http://127.0.0.1:4310**.
Use `naly ui --port 4311` if that port is occupied. `SQUAD_DIR` selects the shared
board, just as it does for other commands. `SQUAD_SESSIONS` selects a custom sessions
file when needed. Python 3.8+ is required; tmux and agent CLIs are not needed to view
the board. Keep this terminal open, or run the dashboard in its own tmux window.

## What you can control

The board refreshes every two seconds and shows task ownership, notes, branches,
skills, and review verdicts. Search across task titles, notes, owners, and skills.
The team overview reads your sessions file and roster; the model is the configured
model, not a runtime measurement. An agent with no recent event may still be working.

- Create a task, optionally choosing a role and shared skills. Role assignment uses
  the same routing rules as `naly add --role`.
- Open a queued or blocked task to hand it to a known agent. It becomes blocked /
  handed off until that agent claims it; its inbox gets a handoff event.
- Open a task awaiting review to pass it or return it with a required reason.
  These actions use the CLI's review and learning records.

The UI uses the identity `dashboard`. It does not impersonate an agent, claim work
on your behalf, execute arbitrary commands, or apply skill proposals. Tell idle agents
to check their inbox after assigning work. Active agents should hand off their own
tasks from their terminal sessions. Inspect code and checks before passing a review;
the dashboard does not run those checks for you.

If a task changed after you opened it, its action is rejected. Reopen it to inspect
the latest state. Dashboard requests are serialized, but CLI task updates remain
cooperative and are not a transaction across all fields. Avoid changing the same
task simultaneously from its agent session and dashboard. Temporary intermediate
states may be visible while a CLI command updates multiple fields.

## Remote access

Run `naly ui` on the host alongside the board and agents. From your laptop:

```bash
ssh -N -L 4310:127.0.0.1:4310 user@your-host
```

Open **http://127.0.0.1:4310** on your laptop. Use the same port on both sides; if you
choose `--port 4311`, use 4311 throughout the tunnel command and browser URL.
The host must stay awake and the dashboard process must remain running. A phone
browser can use a phone SSH client's equivalent local tunnel. Native Claude and
ChatGPT mobile sessions are separate from this browser dashboard.

The server binds only to `127.0.0.1` and checks the request host, origin, and a
per-process token for writes. It is for your local machine or SSH tunnel, with no
public hosting or multi-user authentication. Board text is rendered as text, not HTML.
All frontend assets are bundled locally; the page makes no external requests.

Stop the server with Ctrl-C. This leaves your agents, board, and tmux sessions intact.
