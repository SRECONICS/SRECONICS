"""Entrypoint: generate today's post and render its images.

Usage:
    python -m automation.daily_post.main --owner sreconics --repo sreconics [--no-publish]

By default this also publishes the GitHub issue immediately. Pass
--no-publish to only generate images/state/post.json (used by the workflow,
which commits+pushes the images first so the issue's embedded image URLs
resolve before anyone views it, then runs publish.py separately).
"""
import argparse
import datetime
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from automation.daily_post import content, generator, poster, render
from automation.daily_post.state import load_state, save_state

ASSETS_DIR = os.path.join(REPO_ROOT, "assets", "daily-posts")


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def generate(owner, repo, branch):
    state = load_state()

    # Drift guard: automation/state/history.json is supposed to be the one
    # and only source of truth for the rotation index (see generator.py).
    # That only holds if every published "showcase" issue actually went
    # through this function. If some issue got created out-of-band
    # (manually, or by a different script) without calling generate(),
    # history.json's total_posts silently falls behind the real issue
    # count and the next rotation_index computed below would be wrong --
    # which is exactly how issues #74-#76 skipped boards. Fail loudly
    # instead of guessing.
    try:
        live_count = poster.count_label_issues(owner, repo, "showcase")
    except Exception as exc:  # pragma: no cover - network/auth issues
        print(f"WARNING: could not verify history.json against GitHub ({exc}); proceeding anyway.")
        live_count = None

    if live_count is not None and live_count != state["total_posts"]:
        raise RuntimeError(
            "Rotation state drift detected: automation/state/history.json "
            f"says total_posts={state['total_posts']}, but GitHub currently has "
            f"{live_count} issue(s) labeled 'showcase'. At least one showcase "
            "post was created without going through automation/daily_post/main.py, "
            "so history.json is no longer an accurate record of the rotation. "
            "Reconcile automation/state/history.json (or at minimum fix "
            "total_posts and each board's used_count) with the actual boards "
            "used in the missing issue(s) before generating the next post."
        )

    board, core_idea, twist, lap, rotation_index = generator.next_post(state)

    post_date = datetime.date.today()
    slug = f"{post_date.isoformat()}-{slugify(core_idea['title'])}"
    post_dir = os.path.join(ASSETS_DIR, slug)
    os.makedirs(post_dir, exist_ok=True)

    banner_path = os.path.join(post_dir, "banner.png")
    diagram_path = os.path.join(post_dir, "diagram.png")

    accent = board["accent"]
    fields = content.compute_fields(board, core_idea, twist, lap)

    render.render_banner(banner_path, fields["title"], board["name"], fields["tags"], accent)
    render.render_block_diagram(diagram_path, board["name"], fields["components"], accent)

    raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/assets/daily-posts/{slug}"
    image_paths = [
        {"url": f"{raw_base}/banner.png"},
        {"url": f"{raw_base}/diagram.png"},
    ]

    post = content.build_post(board, core_idea, twist, lap, image_paths, post_date=post_date)

    with open(os.path.join(post_dir, "preview.md"), "w", encoding="utf-8") as f:
        f.write(f"# {post['title']}\n\n{post['body']}\n")

    post_record = {
        "date": post_date.isoformat(),
        "board": board["key"],
        "board_name": board["name"],
        "title": post["title"],
        "tags": post["tags"],
        "slug": slug,
        "owner": owner,
        "repo": repo,
    }
    with open(os.path.join(post_dir, "post.json"), "w", encoding="utf-8") as f:
        json.dump({**post_record, "body": post["body"]}, f, indent=2, ensure_ascii=False)

    state["posts"].append(post_record)
    save_state(state)

    print(f"--- Generated post for {post_date.isoformat()} ---")
    print(f"Board: {board['name']} (rotation slot {rotation_index + 1}/6)")
    print(f"Title: {post['title']}")
    print("::SLUG::" + slug)
    return slug, post


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", default="main", help="Branch images are committed to (used for raw image URLs)")
    parser.add_argument("--no-publish", action="store_true", help="Generate only; skip creating the GitHub issue")
    args = parser.parse_args()

    slug, post = generate(args.owner, args.repo, args.branch)

    if args.no_publish:
        return

    poster.ensure_label(args.owner, args.repo, "showcase", "1f6feb", "Automated daily project showcase post")
    issue = poster.create_issue(args.owner, args.repo, post["title"], post["body"], ["showcase"],
                                 assignees=[args.owner])
    print(f"Published: {issue['html_url']}")
    print("::RESULT::" + json.dumps({"slug": slug, "issue_url": issue["html_url"], "issue_number": issue["number"]}))


if __name__ == "__main__":
    main()
