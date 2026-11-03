"""
Transfer-learning fine-tuning script to retrain the ASL classifier.
Quantises to INT8 TFLite for on-device inference on Pi 5.
"""

import tensorflow as tf
import numpy as np
from pathlib import Path

DATASET_DIR = "dataset/"
IMG_SIZE    = (224, 224)
BATCH_SIZE  = 32
EPOCHS      = 20
OUT_MODEL   = "models/asl_int8.tflite"
OUT_LABELS  = "models/labels.txt"


def build_datasets():
    ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR, image_size=IMG_SIZE, batch_size=BATCH_SIZE,
        label_mode="categorical", shuffle=True, seed=42,
    )
    classes = ds.class_names
    n       = len(ds)
    train   = ds.take(int(n * 0.85)).prefetch(tf.data.AUTOTUNE)
    val     = ds.skip(int(n * 0.85)).prefetch(tf.data.AUTOTUNE)
    return train, val, classes


def build_model(num_classes):
    base = tf.keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False
    x   = tf.keras.layers.GlobalAveragePooling2D()(base.output)
    x   = tf.keras.layers.Dense(128, activation="relu")(x)
    out = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(base.input, out)


def quantise_to_tflite(keras_model, rep_ds, out_path):
    def rep_gen():
        for imgs, _ in rep_ds.take(200):
            for img in imgs:
                yield [img[None].numpy().astype(np.float32)]

    conv = tf.lite.TFLiteConverter.from_keras_model(keras_model)
    conv.optimizations                 = [tf.lite.Optimize.DEFAULT]
    conv.representative_dataset        = rep_gen
    conv.target_spec.supported_ops     = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv.inference_input_type          = tf.int8
    conv.inference_output_type         = tf.int8
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(conv.convert())
    print(f"INT8 model saved → {out_path}")


if __name__ == "__main__":
    train_ds, val_ds, classes = build_datasets()
    Path(OUT_LABELS).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT_LABELS).write_text("\n".join(classes))

    model = build_model(len(classes))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(
        train_ds, validation_data=val_ds, epochs=EPOCHS,
        callbacks=[tf.keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True)],
    )
    quantise_to_tflite(model, train_ds, OUT_MODEL)
    print("Done. Run: python gesture_classifier.py")
