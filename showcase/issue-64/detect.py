#!/usr/bin/env python3
"""
detect.py — TFLite object detection with motion pre-filter
Issue #64 · sreconics/sreconics · Board: Raspberry Pi 3

Runs MobileNetV2 SSD (TFLite) on PiCamera2 frames.
A frame-diff pre-filter skips inference when nothing has changed,
keeping CPU temperature below ~68 °C during 24/7 operation.

Requirements:
    pip install picamera2 tflite-runtime opencv-python-headless Pillow
    # TFLite model: download MobileNetSSD_quant.tflite from TF Hub
    # Labels:       coco_labels.txt

Usage:
    python detect.py [--model MODEL] [--labels LABELS] [--threshold 0.5]
                     [--save-dir /path/to/events] [--no-preview]
"""

import argparse
import os
import time
import datetime
import threading
import queue

import cv2
import numpy as np

# ── Configuration ────────────────────────────────────────────────────────────
FRAME_W, FRAME_H = 640, 480
FPS_TARGET        = 6          # target inference fps
MOTION_THRESHOLD  = 0.4        # fraction of pixels changed → trigger inference
MIN_DIFF_AREA     = 2500       # min contour area (px²) to count as motion
ALERT_CLASSES     = {"person", "cat", "dog", "car", "truck", "bicycle"}
SAVE_COOLDOWN_S   = 5          # seconds between saves for same class
# ─────────────────────────────────────────────────────────────────────────────


def load_labels(path: str) -> list[str]:
    with open(path) as f:
        return [ln.strip() for ln in f.readlines()]


def load_model(model_path: str):
    try:
        import tflite_runtime.interpreter as tflite
        interp = tflite.Interpreter(model_path=model_path)
    except ImportError:
        import tensorflow as tf
        interp = tf.lite.Interpreter(model_path=model_path)
    interp.allocate_tensors()
    return interp


def preprocess(frame: np.ndarray, input_shape) -> np.ndarray:
    """Resize and expand dims to match model input."""
    h, w = input_shape[1], input_shape[2]
    resized = cv2.resize(frame, (w, h))
    return np.expand_dims(resized, axis=0).astype(np.uint8)


def motion_detected(prev_gray: np.ndarray, curr_gray: np.ndarray) -> bool:
    """Return True when frame difference exceeds threshold."""
    diff = cv2.absdiff(prev_gray, curr_gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) > MIN_DIFF_AREA:
            return True
    return False


def run_inference(interp, frame: np.ndarray, labels: list[str], threshold: float):
    in_details  = interp.get_input_details()
    out_details = interp.get_output_details()

    input_data = preprocess(frame, in_details[0]["shape"])
    interp.set_tensor(in_details[0]["index"], input_data)
    interp.invoke()

    boxes   = interp.get_tensor(out_details[0]["index"])[0]   # [N,4] ymin,xmin,ymax,xmax (0-1)
    classes = interp.get_tensor(out_details[1]["index"])[0]   # [N] class ids
    scores  = interp.get_tensor(out_details[2]["index"])[0]   # [N] confidence
    count   = int(interp.get_tensor(out_details[3]["index"])[0])

    detections = []
    for i in range(count):
        if scores[i] >= threshold:
            cls_id  = int(classes[i])
            cls_name = labels[cls_id] if cls_id < len(labels) else str(cls_id)
            box = boxes[i]  # (ymin, xmin, ymax, xmax) normalised
            detections.append({"class": cls_name, "score": float(scores[i]), "box": box})
    return detections


def annotate(frame: np.ndarray, detections: list[dict]) -> np.ndarray:
    h, w = frame.shape[:2]
    out = frame.copy()
    for det in detections:
        ymin, xmin, ymax, xmax = det["box"]
        x0, y0 = int(xmin * w), int(ymin * h)
        x1, y1 = int(xmax * w), int(ymax * h)
        color = (0, 200, 80) if det["class"] in ALERT_CLASSES else (150, 150, 150)
        cv2.rectangle(out, (x0, y0), (x1, y1), color, 2)
        label = f"{det['class']} {det['score']:.0%}"
        cv2.putText(out, label, (x0, max(y0 - 8, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return out


def save_event(frame: np.ndarray, detections: list[dict], save_dir: str,
               last_save: dict, alert_queue: "queue.Queue"):
    os.makedirs(save_dir, exist_ok=True)
    now = datetime.datetime.now()
    for det in detections:
        cls = det["class"]
        if cls not in ALERT_CLASSES:
            continue
        elapsed = now.timestamp() - last_save.get(cls, 0)
        if elapsed < SAVE_COOLDOWN_S:
            continue
        fname = now.strftime(f"%Y%m%d_%H%M%S_{cls}.jpg")
        path  = os.path.join(save_dir, fname)
        cv2.imwrite(path, frame)
        last_save[cls] = now.timestamp()
        print(f"[EVENT] Saved {path}  ({det['score']:.0%} confidence)")
        alert_queue.put({"path": path, "class": cls, "score": det["score"], "time": now.isoformat()})


def camera_loop(args, frame_queue: "queue.Queue"):
    """Produce frames from PiCamera2 into a shared queue."""
    from picamera2 import Picamera2
    cam = Picamera2()
    cfg = cam.create_video_configuration(main={"size": (FRAME_W, FRAME_H), "format": "RGB888"})
    cam.configure(cfg)
    cam.start()
    try:
        while True:
            frame = cam.capture_array()
            if not frame_queue.full():
                frame_queue.put(frame)
            time.sleep(1 / FPS_TARGET)
    finally:
        cam.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",     default="MobileNetSSD_quant.tflite")
    parser.add_argument("--labels",    default="coco_labels.txt")
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--save-dir",  default="/media/usb/events")
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()

    print(f"[detect.py] Loading model: {args.model}")
    interp = load_model(args.model)
    labels = load_labels(args.labels)
    print(f"[detect.py] {len(labels)} labels loaded.")

    frame_queue = queue.Queue(maxsize=2)
    alert_queue = queue.Queue()

    # Start camera thread
    cam_thread = threading.Thread(target=camera_loop, args=(args, frame_queue), daemon=True)
    cam_thread.start()

    # Import alert module lazily (requires Telegram token)
    try:
        import alert
        has_alert = True
    except ImportError:
        has_alert = False
        print("[detect.py] alert.py not found — Telegram notifications disabled.")

    prev_gray  = None
    last_save: dict[str, float] = {}
    frames_processed = 0

    print("[detect.py] Inference loop started (Ctrl+C to stop).")
    while True:
        try:
            frame = frame_queue.get(timeout=2)
        except queue.Empty:
            continue

        curr_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        if prev_gray is not None and not motion_detected(prev_gray, curr_gray):
            prev_gray = curr_gray
            continue  # skip inference — nothing moved

        prev_gray = curr_gray
        detections = run_inference(interp, frame, labels, args.threshold)
        frames_processed += 1

        if detections:
            bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            annotated = annotate(bgr, detections)
            save_event(annotated, detections, args.save_dir, last_save, alert_queue)
            if not args.no_preview:
                cv2.imshow("Pi3 AI Cam", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        # Drain alert queue → Telegram
        while has_alert and not alert_queue.empty():
            evt = alert_queue.get_nowait()
            try:
                alert.send_detection_alert(evt)
            except Exception as e:
                print(f"[alert] {e}")

    cv2.destroyAllWindows()
    print(f"[detect.py] Done. {frames_processed} frames processed.")


if __name__ == "__main__":
    main()
