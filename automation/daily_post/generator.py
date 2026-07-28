"""Generates the next unique project idea for whichever board is due today."""
import random

from .boards import BOARD_BY_KEY, BOARD_ROTATION, TWISTS, twist_compatible


def _combo_order(seed, core_ideas):
    """Deterministic shuffle of every compatible (core_idx, twist_idx) pair.

    Seeded so the order is stable across runs (no external randomness
    needed), but looks unpredictable rather than a plain nested loop.
    Re-shuffled with a bumped seed for each extra lap once the full
    cross-product has been used once, so the generator never runs out.
    """
    combos = [
        (c, t)
        for c in range(len(core_ideas))
        for t in range(len(TWISTS))
        if twist_compatible(core_ideas[c], TWISTS[t])
    ]
    rng = random.Random(seed)
    rng.shuffle(combos)
    return combos


def next_post(state):
    """Return (board, core_idea, twist, lap, rotation_index) for today's post
    and mutate `state` in place to record the choice as consumed.
    """
    rotation_index = state["total_posts"] % len(BOARD_ROTATION)
    board_key = BOARD_ROTATION[rotation_index]
    board = BOARD_BY_KEY[board_key]

    board_state = state["boards"].setdefault(board_key, {"used_count": 0})
    used_count = board_state["used_count"]

    combos = _combo_order(board_key, board["core_ideas"])
    combo_size = len(combos)

    lap = used_count // combo_size  # which "lap" around the full combo space
    offset_in_lap = used_count % combo_size

    if lap > 0:
        combos = _combo_order(f"{board_key}::lap{lap}", board["core_ideas"])

    core_idx, twist_idx = combos[offset_in_lap]

    core_idea = board["core_ideas"][core_idx]
    twist = TWISTS[twist_idx]

    board_state["used_count"] = used_count + 1
    state["total_posts"] += 1

    return board, core_idea, twist, lap, rotation_index
