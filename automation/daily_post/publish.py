"""Publishes an already-generated post (see main.py --no-publish).

Reads assets/daily-posts/<slug>/post.json — written by main.py's generate()
step — and creates the GitHub issue. Kept as a separate step so the workflow
can commit+push the rendered images *before* the issue (and its embedded
raw.githubusercontent.com image links) goes live.

Usage:
    python -m automation.daily_post.publish --slug 2026-07-28-some-project
"""
import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from automation.daily_post import poster

ASSETS_DIR = os.path.join(REPO_ROOT, "assets", "daily-posts")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()

    post_json_path = os.path.join(ASSETS_DIR, args.slug, "post.json")
    with open(post_json_path, "r", encoding="utf-8") as f:
        record = json.load(f)

    poster.ensure_label(record["owner"], record["repo"], "showcase", "1f6feb",
                         "Automated daily project showcase post")
    issue = poster.create_issue(record["owner"], record["repo"], record["title"], record["body"], ["showcase"],
                                 assignees=[record["owner"]])

    print(f"Published: {issue['html_url']}")
    print("::RESULT::" + json.dumps({"slug": args.slug, "issue_url": issue["html_url"], "issue_number": issue["number"]}))


if __name__ == "__main__":
    main()
