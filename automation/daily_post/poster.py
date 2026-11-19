"""Publishes the generated post as a GitHub Issue labeled 'showcase'.

Auth: uses GH_POST_TOKEN if present (a personal access token from a real
account, so the post looks human-authored) and falls back to GITHUB_TOKEN
(the default token Actions provides, which posts as github-actions[bot]).
See docs/AUTOMATION.md for the human-authorship setup step.
"""
import os

import requests

API_ROOT = "https://api.github.com"


def _token():
    return os.environ.get("GH_POST_TOKEN") or os.environ["GITHUB_TOKEN"]


def _headers():
    return {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def ensure_label(owner, repo, name, color, description):
    resp = requests.get(f"{API_ROOT}/repos/{owner}/{repo}/labels/{name}", headers=_headers(), timeout=30)
    if resp.status_code == 200:
        return
    resp = requests.post(
        f"{API_ROOT}/repos/{owner}/{repo}/labels",
        headers=_headers(),
        json={"name": name, "color": color, "description": description},
        timeout=30,
    )
    if resp.status_code not in (201, 422):  # 422 = already exists (race)
        resp.raise_for_status()


def count_label_issues(owner, repo, label):
    """Total number of issues (open+closed) carrying `label`, via the Search API.

    Used only as a drift check against automation/state/history.json's
    total_posts -- NOT as a source for the rotation index itself. If a post
    is ever created out-of-band (manually, or by some other script) without
    going through main.py/generate(), history.json's total_posts will stop
    matching this count, and callers should treat that as a hard error
    rather than silently continuing to compute rotation from a now-stale
    history.json.
    """
    resp = requests.get(
        f"{API_ROOT}/search/issues",
        headers=_headers(),
        params={"q": f"repo:{owner}/{repo} label:{label} type:issue"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["total_count"]


def create_issue(owner, repo, title, body, labels, assignees=None):
    payload = {"title": title, "body": body, "labels": labels}
    if assignees:
        payload["assignees"] = assignees
    resp = requests.post(
        f"{API_ROOT}/repos/{owner}/{repo}/issues",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
