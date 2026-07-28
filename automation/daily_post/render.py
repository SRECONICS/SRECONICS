"""Auto-generates a title banner and a system block diagram for each post.

No external image-gen API is used or needed — everything is drawn
programmatically with Pillow, which keeps the pipeline dependency-light and
free of API keys/rate limits.
"""
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT_DIR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
]


def _font(name_bits, size):
    for d in FONT_DIR_CANDIDATES:
        for bit in name_bits:
            path = os.path.join(d, bit)
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _bold_font(size):
    return _font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"], size)


def _regular_font(size):
    return _font(["DejaVuSans.ttf", "LiberationSans-Regular.ttf"], size)


def _dark(hex_color, factor=0.35):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"


def render_banner(path, title, board_name, tags, accent):
    W, H = 1200, 630
    bg_top = "#0d1117"
    bg_bottom = _dark(accent, 0.18)
    img = Image.new("RGB", (W, H), bg_top)
    draw = ImageDraw.Draw(img)

    # simple vertical gradient
    top_rgb = (13, 17, 23)
    bot = bg_bottom.lstrip("#")
    bot_rgb = tuple(int(bot[i:i + 2], 16) for i in (0, 2, 4))
    for y in range(H):
        t = y / H
        r = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    draw.rectangle([(0, 0), (14, H)], fill=accent)

    draw.text((60, 50), "DEVNODE TECHNOLOGIES", font=_bold_font(26), fill=accent)
    draw.text((60, 90), "DAILY PROJECT SHOWCASE", font=_regular_font(20), fill="#9da7b3")

    wrapped = textwrap.wrap(title, width=24)
    y = 220
    for line in wrapped[:3]:
        draw.text((60, y), line, font=_bold_font(58), fill="#f0f3f6")
        y += 68

    draw.rounded_rectangle([(60, y + 20), (60 + 22 + len(board_name) * 15, y + 70)],
                            radius=10, fill=accent)
    draw.text((72, y + 32), board_name, font=_bold_font(24), fill="#0d1117")

    tag_y = H - 80
    x = 60
    for tag in tags[:4]:
        label = f"#{tag.replace(' ', '')}"
        w = 20 + len(label) * 11
        draw.rounded_rectangle([(x, tag_y), (x + w, tag_y + 40)], radius=8,
                                outline=accent, width=2)
        draw.text((x + 12, tag_y + 8), label, font=_regular_font(18), fill=accent)
        x += w + 14

    img.save(path, "PNG")


def render_block_diagram(path, board_name, components, accent):
    W, H = 1200, 700
    img = Image.new("RGB", (W, H), "#0d1117")
    draw = ImageDraw.Draw(img)

    draw.text((40, 30), f"System Block Diagram — {board_name}", font=_bold_font(30), fill="#f0f3f6")

    # Central board box
    board_w, board_h = 300, 120
    board_x = (W - board_w) // 2
    board_y = (H - board_h) // 2
    draw.rounded_rectangle(
        [(board_x, board_y), (board_x + board_w, board_y + board_h)],
        radius=14, fill=accent,
    )
    draw.text((board_x + 20, board_y + 45), board_name, font=_bold_font(22), fill="#0d1117")

    comps = components[:6]
    n = len(comps)
    box_w, box_h = 260, 70
    margin_top = 130
    margin_bottom = 100
    usable_h = H - margin_top - margin_bottom
    slot_h = usable_h / max(n, 1)

    for i, comp in enumerate(comps):
        left_side = i % 2 == 0
        slot_y = margin_top + i * slot_h + (slot_h - box_h) / 2
        box_x = 40 if left_side else W - 40 - box_w

        draw.rounded_rectangle(
            [(box_x, slot_y), (box_x + box_w, slot_y + box_h)],
            radius=10, outline="#c9d1d9", width=2, fill="#161b22",
        )
        wrapped = textwrap.wrap(comp, width=26)
        ty = slot_y + box_h / 2 - (len(wrapped) * 16) / 2
        for line in wrapped[:3]:
            draw.text((box_x + 14, ty), line, font=_regular_font(16), fill="#f0f3f6")
            ty += 18

        # connector line to the board
        if left_side:
            start = (box_x + box_w, slot_y + box_h / 2)
            end = (board_x, board_y + board_h / 2)
        else:
            start = (box_x, slot_y + box_h / 2)
            end = (board_x + board_w, board_y + board_h / 2)
        draw.line([start, end], fill=accent, width=3)
        draw.ellipse([end[0] - 5, end[1] - 5, end[0] + 5, end[1] + 5], fill=accent)

    img.save(path, "PNG")
