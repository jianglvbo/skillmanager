---
name: manage-skills
description: Manage the user's shared agent-skill library via skills-manager-cli — install, update, remove, deploy or undeploy skills per agent, organize them into folders, search, and adopt existing skills. Use this whenever the user wants Claude Code, Codex, Cursor, or another agent to gain or lose a skill, wants to organize the central library, or asks what is installed or deployed. Prefer this over direct agent-folder installs because Skills Manager preserves source metadata, folder membership, updates, and cross-agent deployment state.
---

## Before doing anything

1. **Resolve the CLI first, then use the path it prints.** Run this once (POSIX
   shell):

   ```bash
   D="$HOME/.skills-manager/bin"
   B="$D/skills-manager-cli"; [ -e "$B" ] || B="$B.exe"   # .exe on Windows
   if [ -s "$D/.version" ] && [ -x "$B" ]; then
     echo "$B"
   elif [ -s "$D/.version" ] || [ -e "$B" ]; then
     echo BRIDGE_BROKEN
   else
     P="$(command -v skills-manager-cli 2>/dev/null || true)"
     [ -x "$P" ] && echo "$P"
   fi
   ```

   **Substitute the printed path into every command below**, wherever the
   examples write `$SM`. Do not carry `$SM` as a shell variable: each command
   you run is a new shell, so an assignment made here is gone by the next one.

   The three outcomes:

   - **A path under `~/.skills-manager/bin`** — the desktop app published this
     copy, and the `.version` stamp appears only after it has been verified, so
     it always matches the app the user is running. Use it.
   - **`BRIDGE_BROKEN`** — something the app left behind is here but does not
     add up: an unstamped binary, or a stamp with no binary beside it. Either is
     what a copy that failed half-way leaves. **Stop.** Do not go looking
     for another CLI: that binary may predate a safety fix, and the machine has
     a desktop app whose version nothing here can match. Ask the user to open
     the Skills Manager app once, which republishes it.
   - **A path from PATH** — nothing was ever published here, so there is no
     stale copy to worry about: this is a CLI-only machine (a server install, a
     standalone download, a hand-built binary). Use it, but note it can be
     older than a desktop app if one is also installed.

   If nothing is printed at all, this skill doesn't apply — fall back to
   find-skills, or tell the user to install Skills Manager.
2. **Always pass `--json` when you parse output yourself.** Pretty-printed output is for the user; JSON is for you. Errors include `ok=false`, a stable `code`, and `message` on stderr with a non-zero exit code.

```bash
"$SM" --json skills list
```

### When a deployment is refused

A deploy that would overwrite something that is not ours is refused outright —
nothing at those paths is deleted, and nothing else in the batch is applied.
That failure is machine-readable, so report the actual paths rather than the
sentence:

```json
{"ok": false, "code": "TARGET_CONFLICT", "kind": "target_conflict",
 "message": "Refusing to deploy: 1 of 2 target(s) …",
 "details": {"conflicts": [{"path": "/Users/me/.claude/skills/db",
                            "reason": "is not a managed deployment"}]}}
```

Tell the user which path is in the way, that its contents are untouched, and
offer the two ways out: adopt it into the library (`skills adopt`), or move it
aside and retry. Never delete it for them.

## Mental model

There's **one central library** at `~/.skills-manager/skills/` that all agents share. Each skill has source metadata, at most one **folder**, and zero or more real deployments in agent directories. A **folder** is both an organizing group and a unit of deployment: it records which agents it claims, and `folders deploy` pushes its whole subtree at once.

Keep these three states separate:
- **Library**: install/remove controls whether Skills Manager owns the skill.
- **Folder membership**: `folders add` / `folders move` organize the library only.
- **Deployment**: `skills deploy/undeploy` and `folders deploy/undeploy` control what an agent can actually see.

A folder claiming an agent does **not** mean its skills are deployed — the claim is
intent, the deployment is on disk. `folders show` reports both, and `skills sync`
re-asserts every folder's claim.

Project workspaces (a repo's own `.agents/skills`) are a separate destination that
this CLI does not write to: the desktop app's workspace tags do that, so send the
user there for per-project deployment rather than trying to script it.

## Install

```bash
# From skills.sh marketplace
"$SM" skills install vercel-labs/agent-skills@react-best-practices

# Any git URL (use /tree/branch/subpath form when the skill lives in a sub-directory)
"$SM" skills install https://github.com/anthropics/skills.git
"$SM" skills install https://github.com/foo/bar/tree/main/skills/baz

# Local folder
"$SM" skills install ./my-skill

# Force a source type when the ref is ambiguous
"$SM" skills install foo/bar --skillssh
"$SM" skills install ./looks-like/owner-repo --local
```

**Default is library-only** — the skill enters the DB but doesn't appear in any agent yet. Prefer an explicit follow-up deployment so scope is unambiguous:

```bash
"$SM" skills deploy <skill> --agent claude_code --agent codex
```

`--folder REF` files the install into that folder and applies the folder's claimed
agents in the same step, so a skill added to a curated folder lands where the rest
of the folder already is.

**Ref resolution** is deterministic, no path-existence guessing:
1. Starts with `./`, `../`, `/`, or `~/` → local path
2. Contains `://`, ends in `.git`, or starts with `git@` → git URL
3. Matches `owner/repo`, `owner/repo/skill`, or `owner/repo@skill` → skillssh
4. Otherwise → error; pass `--local` / `--git` / `--skillssh` to disambiguate

**Always verify after install** with `skills list` or `skills show <name>` so you can confirm the skill landed and report the folder and deployment state back to the user.

## Search

```bash
"$SM" --json skills search "react performance" --limit 5
```

Each result has `install_ref` (paste straight into `skills install`), `installs` (popularity proxy), and `skills_sh_url`. Show the top 1–3 with install counts before installing — anything with 10K+ installs is battle-tested; anything under 100 needs a careful look at the source repo.

## Update / Check

```bash
# Re-fetch one skill (git/skillssh re-clones, local/import re-imports source dir)
"$SM" skills update <skill-name-or-id>

# Re-fetch all eligible skills
"$SM" skills update --all

# Just probe remote revisions, don't touch files
"$SM" skills check --all
```

`check` is the dry-run partner of `update`. Local-only skills (no git source) are reported as `skipped: true`.

**An update replaces the skill's directory wholesale**, so anything written inside it that the new version does not have would be destroyed. When the CLI detects that, it applies nothing and reports the paths instead:

```jsonc
{ "name": "ppt-master", "refreshed": false,
  "held_back_removals": ["library: templates/mine.pptx"] }
```

The field is omitted entirely when nothing is held back, so test for its presence rather than for an empty array. `refreshed: false` *with* `held_back_removals` is **not a failure and not something to retry** — the skill is untouched and still on its old version. Show the user the listed paths and ask. There is no CLI flag to override this; only the desktop app can confirm and proceed, because only a person can say those files are expendable. The paths are prefixed with where they live (`library`, or an agent key for a deployed copy).

Note what this does *not* cover: a file the user edited that the new version also ships is reported as surviving, because its path survives — the update overwrites their edits silently. Warn anyone keeping local modifications inside a skill folder.

## Remove

```bash
# Always preview first when removing more than one
"$SM" skills remove <skill> --dry-run

# --yes is required for the actual delete; --json mode does NOT auto-confirm
"$SM" skills remove <skill> --yes
```

Remove deletes the central-library copy, all synced targets across agents, and the DB row. It's not reversible without re-installing.

## Deploy / Undeploy

```bash
"$SM" skills deploy <skill> --agent claude_code
"$SM" skills undeploy <skill> --agent codex
"$SM" skills deploy <skill-a> <skill-b> --agent codex --dry-run
"$SM" skills deploy <skill> --agent claude_code --agent codex
"$SM" --json skills status <skill>
```

These commands change real managed deployments without deleting the central-library copy or changing folder membership. `skills enable/disable` are deprecated compatibility commands and do not change deployment; never use them.

`skills deploy` and `skills undeploy` always require at least one explicit `--agent`, whether the command names one skill or several. `skills status` also reports target rows left by a custom agent that is no longer registered, so stale deployments stay visible and can be cleaned with an explicit undeploy while the row exists.

## Re-assert folder deployments

```bash
# Fill in everything every folder claims that is missing on disk — safe, no writes
"$SM" skills sync --dry-run

# Same, for one folder (id or name)
"$SM" skills sync --folder "Web Dev"

# Only one agent's copies
"$SM" skills sync --tool claude_code
```

`sync` is **additive**: it pushes claimed pairs that are absent, and never removes
a deployment a folder no longer claims. Use `folders undeploy` for that. It refuses
rather than silently doing nothing when no folder claims an agent yet.

## Adopt skills installed elsewhere

When skills already live in an agent's directory (e.g. installed via `npx skills add` or manual `git clone`) but aren't in the central library, pull them in:

```bash
# Dry-run scan first — lists candidates without writing
"$SM" skills adopt ~/.claude/skills --dry-run

# Adopt everything found — each becomes source_type=local (can't auto-update from git)
"$SM" skills adopt ~/.claude/skills

# Adopt a single skill and pin it to a git source so `update` works later
"$SM" skills adopt ~/.claude/skills/react-best-practices \
  --git-url https://github.com/vercel-labs/agent-skills/tree/main/react-best-practices

# Or pass --git-subpath explicitly when the URL is just the repo root
"$SM" skills adopt ~/.claude/skills/react-best-practices \
  --git-url https://github.com/vercel-labs/agent-skills \
  --git-subpath react-best-practices

# Skill lives at the repo root? Pass an empty subpath
"$SM" skills adopt ~/.claude/skills/my-skill \
  --git-url https://github.com/me/my-skill --git-subpath ""
```

`adopt` auto-excludes anything already in the DB or already a sync target, so it's safe to re-run. `--git-url` requires either a URL with a subpath (`/tree/branch/path`) or an explicit `--git-subpath` — without that, future `update` would re-clone the wrong directory, so the CLI refuses to guess.

`--git-url` only applies at the moment of adoption, while the directory is still unmanaged. Once a skill is in the library, use `set-source` below.

## Re-point a skill at a git source

```bash
# Preview: resolves the source and reports whether content differs. It clones to
# a temp dir, but writes nothing to the library or the DB.
"$SM" --json skills set-source <skill> --git-url you/skills --subpath my-skill --dry-run

# A GitHub /tree/ URL carries the branch and subpath already
"$SM" skills set-source <skill> --git-url https://github.com/you/skills/tree/main/my-skill
```

This is how a `local` skill becomes git-backed so `update` works, and how a
skill pointed at the wrong repo gets corrected. It updates the row **in place**,
so the skill id survives and the folder membership and per-agent
deployments keyed to it all stay intact.

- The flag is `--subpath` here, not `--git-subpath` — that one belongs to `adopt`. Pass `--subpath ""` when the skill is at the repo root, which must itself hold a `SKILL.md`.
- `--branch` overrides a branch encoded in the URL.
- The report carries `content_changed` — a single boolean, **not** a file list. It compares the new source against the hash currently recorded for the library copy, not a fresh hash of the directory on disk, so edits made inside the central copy afterwards do not register as a difference. When it is `false` the library copy is left untouched and those edits survive; copy-mode deployments are re-synced either way.

**`--force` is destructive, and nothing stands between it and the user's files.**
A content difference is refused without it. With it, the whole skill directory is
replaced — staged, swapped in, and the old copy deleted — so anything in the
library copy that the new source does not ship is gone. Unlike `skills update`,
this path has **no** `held_back_removals` check: nothing is withheld, and nothing
asks. `--dry-run` cannot tell you which files are at stake, only that something
differs. Never pass `--force` on the user's behalf — report `content_changed:
true`, say that proceeding overwrites the library copy wholesale, and let them
decide.

## Folders

A folder holds skills — one folder per skill — and declares the agents it deploys
to. A reference is an id or a name, and everything below a folder counts: `show`,
`deploy`, `undeploy` and `delete` all walk the subtree.

```bash
"$SM" --json folders list
"$SM" --json folders show "Web Dev"       # skills, claimed agents, and what is on disk
"$SM" folders create "Web Dev"
"$SM" folders create "Git" --parent "Web Dev"
"$SM" folders rename "Web Dev" "Frontend"
"$SM" folders move "Git" --parent "Frontend"    # omit --parent for the library root
"$SM" folders add "Frontend" <skill>...         # membership: moves them out of the old folder

# Read or replace the agents this folder deploys to
"$SM" --json folders targets "Frontend"
"$SM" folders targets "Frontend" --agent claude_code --agent codex

# Push or pull the whole subtree
"$SM" folders deploy "Frontend"                  # to the agents it claims
"$SM" folders deploy "Frontend" --agent codex
"$SM" folders undeploy "Frontend"

"$SM" folders delete "Frontend" --dry-run
"$SM" folders delete "Frontend" --yes
"$SM" folders delete "Frontend" --undeploy --yes
```

`deploy` and `undeploy` with no `--agent` use the folder's own claimed targets, and
**refuse** when it claims none — point it at an agent with `folders targets` first.
`targets` replaces the whole set, so the difference is exactly what gets deployed or
taken back, and `--dry-run` reports that difference without writing.

`folders delete` removes the folder only: its skills stay in the library, re-homed
to whatever the folder's own parent was, and its subfolders come up with it. Without
`--undeploy` the deployed copies stay on every agent's disk, which is usually not
what "delete this group" means to a user — ask before choosing.

Useful queries:

```bash
"$SM" --json skills list --folder "Frontend"     # includes subfolders
"$SM" --json skills list --unfiled
"$SM" --json skills list --deployed-to codex
"$SM" --json skills list --source git
```

## Health check

When sync misbehaves or a command errors in a confusing way:

```bash
"$SM" --json repo status    # base dir, skill and folder counts
"$SM" --json agents list    # detected agents and their target paths
"$SM" --json folders show "Frontend"   # claimed agents vs what is on disk
"$SM" agents enable codex
"$SM" agents disable claude_code
```

`repo status`, `agents list`, and `folders show` are read-only and are the first checks for "why isn't this skill showing up in Cursor" questions. `agents disable` is a real mutation: it removes every managed deployment for that agent. `agents enable` makes the agent globally available again; it does not decide what should live there, so follow up with an explicit `skills deploy` or `folders deploy`.

Use `agents disable <agent>` when the user wants the whole Agent integration turned off or wants every managed skill removed from it. If they only want one skill or one folder's worth taken away while keeping the Agent available for future deployments, use `skills undeploy` or `folders undeploy` instead.

## Typical workflows

### "Find me a skill for X" / "Install a skill that does X"

1. `skills search "X" --limit 5` — show the top 1–3 hits with install counts and source.
2. If a clear winner: `skills install <install_ref>`.
3. If ambiguous: ask the user to pick.
4. Deploy it to the agent(s) the user requested with `skills deploy`.
5. `skills status <name>` to confirm the library and deployment state.

### "What skills do I have?"

```bash
"$SM" --json skills list
```

The `folder_id`, `folder`, `deployed_to`, and `source_type` fields are usually the most informative. The legacy `enabled` field is not deployment state.

### "Pull in the skills already installed in my agent directories"

1. `skills adopt ~/.claude/skills --dry-run` (and any other agent dirs the user mentions) — show the candidate list.
2. After user confirms: `skills adopt ~/.claude/skills`.
3. For any adopted skill where the user knows the original repo, restore the update link with `skills set-source <skill> --git-url ... --subpath ...`.

### "Update everything"

```bash
"$SM" skills check --all     # see what has upstream changes
"$SM" skills update --all    # apply
```

Report which skills actually refreshed (`refreshed: true` in the JSON) vs which were already up-to-date.

## Pitfalls

- **Install succeeded but skill doesn't appear in the agent** → install defaults to library-only. Use `skills deploy <skill> --agent <key>`.
- **Folder membership changed but agent files did not** → membership is organization only. Follow with `folders deploy` or `skills deploy` when the user also asked to make it visible.
- **`folders deploy` / `folders undeploy` / `skills sync` refuse with "claims no agent"** → the folder has no targets yet. Set them with `folders targets <FOLDER> --agent <KEY>`, or pass `--agent` on the deploy itself.
- **Adopted skills can't be `update`d from git** → `npx skills add` and manual `git clone` don't leave source metadata, so adopt has to treat them as `local`. Re-point them with `skills set-source`. Do **not** reach for `adopt --git-url` here: adopt only ever creates new library entries, and it fails *late* — `--dry-run` returns `ok: true` with the skill sitting in `skipped`, and only the real run errors with `--git-url requires exactly one adoptable skill, found 0`. Do **not** remove-then-reinstall either — that drops the skill id, and with it the folder membership and every per-agent deployment keyed to it.
- Use `--dry-run` before bulk remove, folder delete, deploy, or undeploy operations. Use `check` before `update`.
