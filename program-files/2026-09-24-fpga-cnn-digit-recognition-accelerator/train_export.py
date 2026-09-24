"""
train_export.py — MNIST Training & HLS Weight Export
Board  : PYNQ-Z2 (Zynq-7020 SoC)
Project: FPGA CNN Inference Accelerator for Digit Recognition
DevNode Technologies — 2026-09-24

Run on a PC / Colab to:
  1. Train a small CNN on MNIST
  2. Post-training quantise to 8-bit integers
  3. Export weights as C header files for Vitis HLS synthesis
  4. Export as numpy .npz for the software fallback in main.py

Usage:
  pip install tensorflow numpy
  python train_export.py

Outputs:
  weights.npz           — NumPy weights for SW fallback
  hls_weights/          — C header files for Vitis HLS IP synthesis
"""

import os
import json
import struct
import numpy as np

# ── Try TensorFlow; gracefully degrade to random weights for demo ─────────────
try:
    import tensorflow as tf
    from tensorflow.keras import layers, models, datasets

    TF_AVAILABLE = True
    print("[TF] TensorFlow available — will train real model")

except ImportError:
    TF_AVAILABLE = False
    print("[WARN] TensorFlow not installed — generating random demo weights")


# ── CNN architecture (must match HLS overlay topology in main.py) ─────────────
def build_model():
    m = models.Sequential([
        layers.Input((28, 28, 1)),
        layers.Conv2D(8,  (3, 3), activation="relu", name="conv1"),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(16, (3, 3), activation="relu", name="conv2"),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(128, activation="relu", name="dense1"),
        layers.Dense(10,  activation="softmax", name="dense2"),
    ])
    return m


# ── Training ──────────────────────────────────────────────────────────────────
def train(epochs: int = 5, batch_size: int = 128):
    (x_tr, y_tr), (x_te, y_te) = datasets.mnist.load_data()
    x_tr = x_tr.astype("float32")[..., np.newaxis] / 255.0
    x_te = x_te.astype("float32")[..., np.newaxis] / 255.0

    model = build_model()
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    model.summary()

    model.fit(x_tr, y_tr, epochs=epochs, batch_size=batch_size,
              validation_data=(x_te, y_te))

    loss, acc = model.evaluate(x_te, y_te, verbose=0)
    print(f"\n[TRAIN] Test accuracy: {acc*100:.2f}%  loss: {loss:.4f}")
    return model


# ── 8-bit post-training quantisation ─────────────────────────────────────────
def quantise_layer(W: np.ndarray, bits: int = 8):
    """
    Min-max symmetric quantisation.
    Returns (W_q, scale, zero_point) where W_q is int8.
    """
    wmax   = np.max(np.abs(W))
    scale  = wmax / (2**(bits-1) - 1)
    W_q    = np.clip(np.round(W / (scale + 1e-12)), -(2**(bits-1)), 2**(bits-1)-1).astype(np.int8)
    return W_q, float(scale), 0


# ── Extract & quantise all weights ───────────────────────────────────────────
def extract_weights(model=None):
    """Returns dict of layer_name → {W_q, b_q, scale_W, scale_b}."""
    if model is not None and TF_AVAILABLE:
        layer_names = ["conv1", "conv2", "dense1", "dense2"]
        raw = {}
        for name in layer_names:
            lyr      = model.get_layer(name)
            W, b     = lyr.get_weights()
            raw[name] = (W, b)
    else:
        # Random demo weights (same shapes as real topology)
        rng = np.random.default_rng(42)
        raw = {
            "conv1":  (rng.standard_normal((3,3,1,8)).astype(np.float32)*0.1,
                       np.zeros(8, np.float32)),
            "conv2":  (rng.standard_normal((3,3,8,16)).astype(np.float32)*0.1,
                       np.zeros(16, np.float32)),
            "dense1": (rng.standard_normal((400,128)).astype(np.float32)*0.05,
                       np.zeros(128, np.float32)),
            "dense2": (rng.standard_normal((128,10)).astype(np.float32)*0.05,
                       np.zeros(10, np.float32)),
        }

    quantised = {}
    for name, (W, b) in raw.items():
        W_q, sW, _ = quantise_layer(W)
        b_q, sb, _ = quantise_layer(b)
        quantised[name] = {"W_q": W_q, "b_q": b_q,
                           "scale_W": sW, "scale_b": sb}
        print(f"  {name}: W{W.shape} b{b.shape}  scale_W={sW:.6f}")

    return quantised


# ── Export NumPy weights (for SW fallback in main.py) ────────────────────────
def export_numpy(quantised: dict, path: str = "weights.npz"):
    arrays = {}
    meta   = {}
    for name, d in quantised.items():
        arrays[f"{name}_W_q"] = d["W_q"]
        arrays[f"{name}_b_q"] = d["b_q"]
        meta[name] = {"scale_W": d["scale_W"], "scale_b": d["scale_b"]}
    np.savez(path, **arrays)
    with open(path.replace(".npz", "_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[EXPORT] NumPy weights → {path}")


# ── Export C headers for Vitis HLS ───────────────────────────────────────────
def _array_to_c(arr: np.ndarray, name: str, dtype_c: str = "int8_t") -> str:
    flat  = arr.flatten()
    total = len(flat)
    lines = [f"static const {dtype_c} {name}[{total}] = {{"]
    for i in range(0, total, 16):
        chunk = flat[i:i+16]
        lines.append("  " + ", ".join(str(int(v)) for v in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)

def export_hls_headers(quantised: dict, out_dir: str = "hls_weights"):
    os.makedirs(out_dir, exist_ok=True)
    for name, d in quantised.items():
        lines = [
            f"// {name} weights — auto-generated by train_export.py",
            f"// DevNode Technologies  —  2026-09-24",
            f"// scale_W = {d['scale_W']:.8f}   scale_b = {d['scale_b']:.8f}",
            "#pragma once",
            "#include <stdint.h>",
            "",
            _array_to_c(d["W_q"], f"{name}_W"),
            "",
            _array_to_c(d["b_q"], f"{name}_b"),
        ]
        hdr = os.path.join(out_dir, f"{name}_weights.h")
        with open(hdr, "w") as fh:
            fh.write("\n".join(lines))
        print(f"[HLS] {hdr}")

    # Master include
    master = os.path.join(out_dir, "all_weights.h")
    with open(master, "w") as fh:
        fh.write("// Master weight include — generated by train_export.py\n")
        fh.write("#pragma once\n")
        for name in quantised:
            fh.write(f'#include "{name}_weights.h"\n')
    print(f"[HLS] {master}")


# ── Verify round-trip ─────────────────────────────────────────────────────────
def verify_roundtrip(quantised: dict):
    """Quick sanity-check: dequantise and ensure magnitude is plausible."""
    for name, d in quantised.items():
        W_deq = d["W_q"].astype(np.float32) * d["scale_W"]
        print(f"  {name}: max(|W_deq|)={np.max(np.abs(W_deq)):.4f}  "
              f"mean={np.mean(W_deq):.6f}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  MNIST CNN  Train → Quantise → Export")
    print("  DevNode Technologies — PYNQ-Z2 Project")
    print("=" * 60)

    model = train(epochs=5) if TF_AVAILABLE else None

    print("\n[QUANTISE]")
    quantised = extract_weights(model)

    print("\n[VERIFY]")
    verify_roundtrip(quantised)

    export_numpy(quantised)
    export_hls_headers(quantised)

    print("\nDone! Next steps:")
    print("  1. Add hls_weights/*.h to your Vitis HLS project")
    print("  2. Synthesise → export IP → add to Vivado block design")
    print("  3. Generate bitstream → copy cnn_mnist.bit next to main.py")
    print("  4. Run: python main.py  on the PYNQ-Z2")
