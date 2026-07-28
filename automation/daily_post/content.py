"""Assembles a full post (title, body markdown, tags, image paths) from a
board + core idea + twist combination produced by generator.next_post().
"""
import datetime


def compute_fields(board, core_idea, twist, lap):
    """Compute title/description/components/tags, before images are rendered."""
    title = core_idea["title"]
    if twist:
        title = f"{title} — {twist['title_suffix']}"
    if lap > 0:
        title = f"{title} (Mk {lap + 1})"

    description = core_idea["focus"]
    if twist:
        description = f"{description} {twist['sentence']}"

    self_refs = board.get("self_refs", [])
    all_components = list(core_idea["components"])
    if twist:
        all_components += twist.get("extra_components", [])
    components = [c for c in all_components if not any(ref in c for ref in self_refs)]

    tags = list(dict.fromkeys(core_idea["tags"] + (twist.get("extra_tags", []) if twist else [])))

    return {"title": title, "description": description, "components": components, "tags": tags}


def build_post(board, core_idea, twist, lap, image_paths, post_date=None):
    post_date = post_date or datetime.date.today()
    fields = compute_fields(board, core_idea, twist, lap)
    title, description, components, tags = (
        fields["title"], fields["description"], fields["components"], fields["tags"]
    )

    lines = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"**Board:** {board['name']} — {board['tier']}")
    lines.append(f"**Date:** {post_date.isoformat()}")
    lines.append("")
    lines.append("### Overview")
    lines.append(description)
    lines.append("")
    lines.append("### Key Components / Peripherals")
    for c in components:
        lines.append(f"- {c}")
    lines.append("")

    for img in image_paths:
        lines.append(f"![{title}]({img['url']})")
        lines.append("")

    lines.append("### Tags")
    lines.append(" ".join(f"`{t}`" for t in tags))
    lines.append("")
    lines.append("---")
    lines.append(
        "*Posted automatically as part of DevNode Technologies' daily project "
        "showcase rotation (Pico W → Zero 2 W → Pi 3 → Pi 4 → Pi 5 → PYNQ-Z2).*"
    )

    body = "\n".join(lines)
    return {
        "title": title,
        "body": body,
        "tags": tags,
        "components": components,
        "description": description,
    }
