#!/usr/bin/env python3
"""
flow_classifier.py — Real-Time Flow Scoring Microservice
Loads a pre-trained Random Forest model (train_classifier.py) and exposes
a /classify endpoint. nids_capture.py posts JSON feature vectors here.

Requirements:
    pip install scikit-learn flask joblib

Train first:
    python3 train_classifier.py   # produces model.pkl

Then run:
    python3 flow_classifier.py --model model.pkl --port 8765
"""

import argparse
import logging
import os
from pathlib import Path

import joblib
import numpy as np
from flask import Flask, request, jsonify

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

app = Flask(__name__)

# ── Feature order must match train_classifier.py ────────────────
FEATURE_ORDER = [
    "pkt_count", "byte_count", "duration_s", "bytes_per_s", "pkts_per_s",
    "mean_pkt_size", "std_pkt_size", "mean_iat", "std_iat",
    "syn_ratio", "fin_ratio", "rst_ratio",
]

# Loaded at startup
model      = None
label_map  = None   # {0: "benign", 1: "portscan", 2: "dos", 3: "bruteforce", ...}

@app.post("/classify")
def classify():
    data = request.get_json(force=True)
    try:
        vec = np.array([[data.get(f, 0.0) for f in FEATURE_ORDER]])
        pred   = int(model.predict(vec)[0])
        proba  = float(model.predict_proba(vec)[0].max())
        label  = label_map.get(pred, "unknown")
        return jsonify({"label": label, "score": round(proba, 4), "class_id": pred})
    except Exception as e:
        log.error("classify error: %s", e)
        return jsonify({"label": "unknown", "score": 0.0, "error": str(e)}), 500

@app.get("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": model is not None})

def main():
    global model, label_map
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model.pkl",  help="Path to trained model.pkl")
    parser.add_argument("--port",  type=int, default=8765)
    args = parser.parse_args()

    if not Path(args.model).exists():
        log.error("model.pkl not found — run train_classifier.py first")
        raise SystemExit(1)

    bundle    = joblib.load(args.model)
    model     = bundle["model"]
    label_map = bundle["label_map"]
    log.info("Model loaded: %s classes", len(label_map))
    app.run(host="127.0.0.1", port=args.port, threaded=True)

if __name__ == "__main__":
    main()
