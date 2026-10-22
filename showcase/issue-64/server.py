#!/usr/bin/env python3
"""
server.py — Flask MJPEG live stream + event gallery web UI
Issue #64 · sreconics/sreconics · Board: Raspberry Pi 3

Serves:
  GET /             → live annotated MJPEG stream page
  GET /stream       → raw MJPEG stream (embed in <img src>)
  GET /events       → paginated event gallery (JSON + HTML)
  GET /events/<img> → serve a saved event image
  DELETE /events/<img> → delete an event image

Requirements:
    pip install flask opencv-python-headless

Usage:
    # Start detect.py first (it writes annotated frames to /tmp/live_frame.jpg)
    python server.py [--host 0.0.0.0] [--port 5000] [--event-dir /media/usb/events]
"""

import argparse
import os
import glob
import time
import threading
import io

from flask import Flask, Response, jsonify, send_file, abort, request, render_template_string

app = Flask(__name__)

# Shared latest annotated frame (bytes)
_latest_frame: bytes = b""
_frame_lock = threading.Lock()
_event_dir  = "/media/usb/events"

# ── HTML templates ─────────────────────────────────────────────────────────

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pi 3 AI Security Camera</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0d1117; color: #e6edf3; font-family: monospace; }
    header { background: #161b22; padding: 12px 20px; border-bottom: 1px solid #21262d;
             display: flex; justify-content: space-between; align-items: center; }
    header h1 { font-size: 1.1rem; color: #58a6ff; }
    .badge { background: #c9310a; color: white; font-size: 0.75rem;
             padding: 3px 10px; border-radius: 12px; }
    .container { display: flex; gap: 16px; padding: 16px; }
    .stream-box { flex: 1; }
    .stream-box img { width: 100%; border: 2px solid #21262d; border-radius: 6px; }
    .sidebar { width: 280px; }
    .stat { background: #161b22; border: 1px solid #21262d; border-radius: 6px;
            padding: 10px; margin-bottom: 10px; }
    .stat h3 { font-size: 0.8rem; color: #8b949e; margin-bottom: 4px; }
    .stat p  { font-size: 1.3rem; color: #58a6ff; }
    .events-link { display: block; text-align: center; padding: 10px;
                   background: #1e2a3a; border: 1px solid #3a7bd5; border-radius: 6px;
                   color: #58a6ff; text-decoration: none; }
    footer { text-align: center; padding: 10px; color: #484f58; font-size: 0.7rem; }
  </style>
</head>
<body>
  <header>
    <h1>🔴 Pi 3 AI Security Camera</h1>
    <span class="badge">LIVE</span>
  </header>
  <div class="container">
    <div class="stream-box">
      <img src="/stream" alt="Live stream">
    </div>
    <div class="sidebar">
      <div class="stat"><h3>Board</h3><p>Raspberry Pi 3</p></div>
      <div class="stat"><h3>Model</h3><p>MobileNetV2 SSD</p></div>
      <div class="stat" id="evt-count"><h3>Events Today</h3><p>—</p></div>
      <a class="events-link" href="/events">📂 Event Gallery</a>
    </div>
  </div>
  <footer>sreconics/sreconics · Issue #64 · Auto-generated showcase</footer>
  <script>
    async function updateCount() {
      try {
        const r = await fetch('/events?count=1');
        const j = await r.json();
        document.querySelector('#evt-count p').textContent = j.total;
      } catch(_) {}
    }
    updateCount();
    setInterval(updateCount, 10000);
  </script>
</body>
</html>"""

GALLERY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Event Gallery — Pi 3 AI Cam</title>
  <style>
    * { box-sizing: border-box; }
    body { background: #0d1117; color: #e6edf3; font-family: monospace; padding: 16px; }
    h1 { color: #58a6ff; margin-bottom: 16px; font-size: 1.2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
    .card { background: #161b22; border: 1px solid #21262d; border-radius: 6px; overflow: hidden; }
    .card img { width: 100%; display: block; }
    .card-info { padding: 6px 8px; font-size: 0.75rem; color: #8b949e; }
    .card-info strong { color: #3fb950; }
    .del { background: none; border: 1px solid #c9310a; color: #c9310a;
           padding: 3px 8px; border-radius: 4px; cursor: pointer; font-size: 0.7rem; }
    .pagination { margin-top: 16px; display: flex; gap: 8px; }
    .pagination a { color: #58a6ff; text-decoration: none; padding: 6px 12px;
                    border: 1px solid #21262d; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>📂 Saved Detection Events ({{ total }})</h1>
  <div class="grid">
    {% for img in images %}
    <div class="card" id="c-{{ img }}">
      <img src="/events/{{ img }}" loading="lazy">
      <div class="card-info">
        <strong>{{ img.split('_')[2].split('.')[0] }}</strong><br>
        {{ img[:15] }}<br>
        <button class="del" onclick="del('{{ img }}')">Delete</button>
      </div>
    </div>
    {% endfor %}
  </div>
  <div class="pagination">
    {% if page > 0 %}<a href="?page={{ page-1 }}">← Prev</a>{% endif %}
    {% if has_next %}<a href="?page={{ page+1 }}">Next →</a>{% endif %}
  </div>
  <script>
    async function del(name) {
      await fetch('/events/' + name, {method: 'DELETE'});
      document.getElementById('c-' + name).remove();
    }
  </script>
</body>
</html>"""

# ── Frame producer (reads from detect.py's shared JPEG) ───────────────────

LIVE_FRAME_PATH = "/tmp/live_frame.jpg"


def _read_latest_frame() -> bytes:
    """Read the latest annotated frame written by detect.py."""
    try:
        with open(LIVE_FRAME_PATH, "rb") as f:
            return f.read()
    except FileNotFoundError:
        # Return a 1×1 black JPEG as placeholder
        import struct
        return (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
            b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
            b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1edL\xff\xc0\x00\x0b\x08"
            b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01"
            b"\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06"
            b"\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\x0f\xff\xd9"
        )


def _mjpeg_generator():
    while True:
        frame = _read_latest_frame()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )
        time.sleep(1 / 10)  # 10 fps cap for clients


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return INDEX_HTML


@app.route("/stream")
def stream():
    return Response(
        _mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/events")
def events():
    page     = int(request.args.get("page", 0))
    per_page = 20
    imgs     = sorted(
        [os.path.basename(p) for p in glob.glob(os.path.join(_event_dir, "*.jpg"))],
        reverse=True,
    )
    total    = len(imgs)
    if request.args.get("count"):
        return jsonify({"total": total})
    chunk    = imgs[page * per_page : (page + 1) * per_page]
    return render_template_string(
        GALLERY_HTML,
        images=chunk, total=total, page=page, has_next=len(imgs) > (page + 1) * per_page,
    )


@app.route("/events/<path:name>")
def serve_event(name: str):
    path = os.path.join(_event_dir, name)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype="image/jpeg")


@app.route("/events/<path:name>", methods=["DELETE"])
def delete_event(name: str):
    path = os.path.join(_event_dir, name)
    if os.path.isfile(path):
        os.remove(path)
        return jsonify({"deleted": name})
    abort(404)


# ── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",      default="0.0.0.0")
    parser.add_argument("--port",      type=int, default=5000)
    parser.add_argument("--event-dir", default="/media/usb/events")
    args = parser.parse_args()

    global _event_dir
    _event_dir = args.event_dir
    os.makedirs(_event_dir, exist_ok=True)

    print(f"[server.py] Starting Flask on {args.host}:{args.port}")
    print(f"[server.py] Event dir: {_event_dir}")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
