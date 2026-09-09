# Pick the setup that fits your workflow

Naly Stack coordinates agents that can access the same board directory. You can run them
in normal terminal tabs, in tmux on your own computer, or in tmux on a remote host.
SSH is needed only for the last option. There is no Naly Stack web server to expose.

## Use terminal tabs without tmux

Follow [README steps 1–3](../README.md#get-started) to install Naly Stack, create worktrees,
and write a sessions file. Stop before `naly up`. From the project directory:

```bash
export SQUAD_DIR="$PWD/.squad"
naly skills sync
naly up --dry-run
```

Neither command needs tmux. The first installs shared skill links; the second prints
one `cd ... && env ...` launch command per agent, followed by skill-link comments.
Copy each complete launch command into a separate terminal tab and run it. Ignore
lines starting with `#`. You can also use your editor's integrated terminal tabs.

Those commands include the shared board path, session identity, role, skills path,
agent flags, and onboarding prompt. Use the generated commands to keep the setup
consistent with the sessions file. They launch with the same YOLO defaults as tmux;
use `naly up --dry-run --no-yolo` for the CLIs' normal permissions instead.

Add work from your project terminal:

```bash
naly add "Implement the feature" --role default
naly board
```

Tell the appropriate agent to check its board and inbox if it is waiting for input.
Naly Stack does not automatically wake an idle agent when you add a task. Keep the agent
tabs open while they work; this setup does not add tmux's detach/reattach behavior.

## Start with two agents from one provider

You do not need multiple providers. A builder and a reviewer can both use Codex,
both use Claude Code, or use different models within the same CLI.

From your project directory, with Naly Stack initialized and `SQUAD_DIR` set:

```bash
git worktree add -b squad/build ../app-build
git worktree add -b squad/check ../app-check

printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
  builder ../app-build 'Implement assigned tasks and hand off for review.' codex '' default \
  reviewer ../app-check 'Review handed-off branches and run project checks.' codex '' review \
  > "$SQUAD_DIR/sessions"

naly add "Implement the feature" --role default
naly up
```

Replace `codex` with `claude` for either row if that is the CLI you use. Leave the
model column blank to preserve its configured model. For terminal tabs, replace the
last command with the sync-and-preview commands above.

A reviewer can wait until a branch is ready. You can also run sessions sequentially:
the board persists on disk, so the next session can read the handoff even after the
previous agent exits. Leave a committed branch and sufficient notes; the board does
not preserve the model's private conversation or automatically recover unfinished work.

## Use tmux locally

Run the [README quickstart](../README.md#get-started) entirely on your computer.
No SSH account, server, IP address, or port forwarding is involved.

| Action | Default tmux keys / command |
|---|---|
| Move to another pane | Ctrl-b, then an arrow key |
| Zoom the current pane / restore the layout | Ctrl-b, then z |
| Detach and leave the session running | Ctrl-b, then d |
| Return to the squad | Run `naly up` from the project terminal |

Detach before closing the terminal window to deliberately leave the session running.
The computer must stay on and awake for agents to keep working. Agent crashes and
machine restarts are not recovered by Naly Stack. More background:
[tmux's official guide](https://github.com/tmux/tmux/wiki).

## Run on a remote host, only if you want to

This is useful when you want the processes to live on another machine—for example,
a development computer you leave running while connecting from your laptop.

Install Naly Stack, tmux, git, Python, and the agent CLIs **on the remote host**. Sign in to
the agent providers there. Keep all of the squad's worktrees and its board on that
host. From your laptop:

```bash
ssh user@your-host
```

Then, in the remote shell:

```bash
cd /path/to/project
export SQUAD_DIR="$PWD/.squad"
naly up
```

Detach with Ctrl-b, then d before leaving. Reconnect by SSH and run `naly up` again.
The agents run on the host, so closing the laptop's connection doesn't terminate
their tmux session. The remote host must remain running.

### Port forwarding is for your app, not Naly Stack

If an agent starts a web app on the host, you may want a tunnel to preview that app
in your laptop's browser. For an app actually listening on remote port 4000:

```bash
ssh -N -L 4000:127.0.0.1:4000 user@your-host
```

Open `http://localhost:4000` on the laptop. The tunnel doesn't start the app; its dev
server must already be running on the remote host at that address and port. SSH
`connect failed: Connection refused` messages when using the tunnel indicate that
the remote forwarding destination is refusing the connection. Check the app's
listening address and port on the host. No forwarding is needed for the Naly Stack board
or tmux itself.

## Check in from your phone

A phone SSH client can attach to the same tmux session using the SSH steps above.
That gives you the terminal layout and access to all its panes. Keep the host awake
and online; tmux preserves processes when you disconnect, not when the host shuts down.

Provider apps offer another way to steer supported sessions:

- **Claude:** run `/remote-control` (or `/rc`) inside an existing Claude Code session,
  then open its session link in the Claude app or find it in the app's Code list.
  See [Claude Remote Control](https://code.claude.com/docs/en/remote-control).
- **Codex:** use the desktop app's Remote setup to pair your phone, then open Remote
  in the ChatGPT mobile app to access supported host chats. The documented setup
  requires a supported desktop host; it is not automatic access to arbitrary Codex
  CLI panes. Follow [Remote connections](https://learn.chatgpt.com/docs/remote-connections)
  for current requirements and setup.

Naly Stack does not create or pair these connections. A provider app controls its
connected sessions, not the whole tmux layout. For an agent reached through an app
to join the team, it must have access to the same board, its own session identity,
and the coordination instructions described above.

## Working across separate computers

Two independent checkouts, each with its own `.squad`, are two independent boards.
Git push/pull, file copies, and syncing folders do not create a shared atomic lock.
For the documented remote setup, run the agents together on one host and connect to
it. Distributed coordination between independent computers is not implemented.
