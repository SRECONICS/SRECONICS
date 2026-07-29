"""State persistence for the daily posting pipeline.

The state file is the single source of truth for:
  - which board rotation slot is next (rotation is driven by post COUNT, not
    calendar day, so a missed/failed run never skips a board out of order)
  - which (core idea, twist) combination has already been used per board, so
    nothing repeats even after the 6-day cycle comes back around
"""
import json
import os

STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          "automation", "state", "history.json")


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"total_posts": 0, "boards": {}, "posts": []}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")
