# Daily Project Showcase — Automation

Publishes one project-idea post per day as a GitHub Issue labeled
`showcase`, cycling through 6 boards, with zero manual input once set up.

## How it works

- **Rotation**: `automation/daily_post/boards.py` lists the 6 boards in
  order (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2). The board for
  "today" is `total_posts % 6`, driven by how many posts have actually been
  made — not the calendar date — so a missed run never skips a board out of
  turn.
- **Uniqueness**: each board has 12 hand-written core project ideas, and
  there are 10 generic "twist" modifiers (solar-powered, offline-first,
  mesh-networked, etc.). The generator pairs them up, skipping any pairing
  that would read as redundant (e.g. a solar-powered project idea never gets
  stamped "Solar-Powered Edition" too). That gives ~100+ non-repeating
  combinations per board — about 2 years of daily rotation before a board's
  pool cycles back (verified by simulation; see `automation/state/history.json`
  for the running record of everything already posted).
- **Images**: a title banner and a system block diagram are rendered with
  Pillow at post time — no external image-gen API, no API key, no rate
  limit.
- **Publishing**: `automation/daily_post/main.py` (generate step) writes the
  images + updates `automation/state/history.json`, the workflow commits
  those to the repo, then `automation/daily_post/publish.py` creates the
  GitHub Issue (label `showcase`) with the images embedded via
  `raw.githubusercontent.com` links — that ordering matters, so images exist
  before the issue references them.
- **Schedule**: `.github/workflows/daily-project-post.yml` runs on a daily
  cron (09:00 UTC) plus `workflow_dispatch` for manual runs/testing.

## Required one-time setup

1. **Merge this branch into `main`.** GitHub only evaluates `schedule:`
   triggers from the repository's default branch, so the daily cron will
   not fire until this is merged. Until then, use the "Run workflow" button
   (Actions tab → "Daily Project Showcase Post" → Run workflow) to test it
   manually — this works from any branch.
2. **Nothing else is required for the pipeline to run.** The default
   `GITHUB_TOKEN` that Actions provides automatically is enough to create
   labels/issues and push commits (repo Settings → Actions → General →
   Workflow permissions must allow "Read and write permissions", which is
   the default for most repos).

## Optional: making posts look human-authored

By default, issues are created by `github-actions[bot]`, which is clearly
a bot in the GitHub UI. If you want posts attributed to a real account
(e.g. a `DevNode-Bot` account, or your own):

1. Create a Personal Access Token (fine-grained, scoped to just this repo,
   with **Issues: Read and write** and **Contents: Read and write**) from
   whichever account you want posts attributed to.
2. Add it as a repository secret named `GH_POST_TOKEN` (Settings → Secrets
   and variables → Actions → New repository secret).
3. The workflow already prefers `GH_POST_TOKEN` over `GITHUB_TOKEN` when
   present (see `automation/daily_post/poster.py`).

Note: each post is auto-assigned to the repo owner so a GitHub notification
fires on every post — but GitHub does not notify you of your own actions.
If `GH_POST_TOKEN` belongs to the repo owner's own account, assignment
notifications won't fire (self-assignment is silent). To get both a
human-looking author *and* a real notification, use a separate account
(e.g. `DevNode-Bot`, added as a collaborator) for `GH_POST_TOKEN` rather
than your own account.

## Testing locally

```bash
pip install -r automation/requirements.txt
python -m automation.daily_post.main --owner <owner> --repo <repo> --no-publish
```

This writes rendered images and a `preview.md` under
`assets/daily-posts/<date>-<slug>/` without calling the GitHub API, so you
can review a post before it ever goes live.

## Extending the content pool

To keep the rotation going well past its current ~2-year runway, add more
entries to a board's `core_ideas` list in `automation/daily_post/boards.py`
(or new entries to `TWISTS`) at any point — the generator picks them up
automatically the next time it runs.
