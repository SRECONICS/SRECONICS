#!/usr/bin/env python3
"""
train_classifier.py — Train a Random Forest on CIC-IDS2017 features.
Download the dataset from:
  https://www.unb.ca/cic/datasets/ids-2017.html
Place the CSV files in ./cicids2017/

Requirements:
    pip install scikit-learn pandas joblib imbalanced-learn

Usage:
    python3 train_classifier.py --data ./cicids2017 --out model.pkl
"""

import argparse
import glob
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# Columns from CIC-IDS2017 that map to our flow feature names
COL_MAP = {
    "Total Fwd Packets":       "pkt_count",
    "Total Length of Fwd Packets": "byte_count",
    "Flow Duration":           "duration_s",
    "Flow Bytes/s":            "bytes_per_s",
    "Flow Packets/s":          "pkts_per_s",
    "Fwd Packet Length Mean":  "mean_pkt_size",
    "Fwd Packet Length Std":   "std_pkt_size",
    "Flow IAT Mean":           "mean_iat",
    "Flow IAT Std":            "std_iat",
    "SYN Flag Count":          "syn_ratio",
    "FIN Flag Count":          "fin_ratio",
    "RST Flag Count":          "rst_ratio",
    " Label":                  "label",
}

FEATURE_ORDER = [
    "pkt_count", "byte_count", "duration_s", "bytes_per_s", "pkts_per_s",
    "mean_pkt_size", "std_pkt_size", "mean_iat", "std_iat",
    "syn_ratio", "fin_ratio", "rst_ratio",
]

# Collapse fine-grained labels to broad threat classes
LABEL_MERGE = {
    "BENIGN": "benign",
    "DoS Hulk": "dos", "DoS GoldenEye": "dos", "DoS slowloris": "dos",
    "DoS Slowhttptest": "dos", "DDoS": "dos",
    "PortScan": "portscan",
    "FTP-Patator": "bruteforce", "SSH-Patator": "bruteforce",
    "Web Attack  Brute Force": "bruteforce",
    "Web Attack  XSS": "webattack",
    "Web Attack  Sql Injection": "webattack",
    "Bot": "bot",
    "Infiltration": "infiltration",
    "Heartbleed": "exploit",
}

def load_csvs(data_dir: str) -> pd.DataFrame:
    files = glob.glob(f"{data_dir}/*.csv")
    if not files:
        raise FileNotFoundError(f"No CSV files in {data_dir}")
    parts = []
    for f in files:
        log.info("Loading %s", f)
        df = pd.read_csv(f, usecols=list(COL_MAP.keys()), low_memory=False)
        df = df.rename(columns=COL_MAP)
        parts.append(df)
    return pd.concat(parts, ignore_index=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="./cicids2017")
    parser.add_argument("--out",  default="model.pkl")
    parser.add_argument("--n-estimators", type=int, default=150)
    args = parser.parse_args()

    df = load_csvs(args.data)
    df["label"] = df["label"].str.strip().map(LABEL_MERGE).fillna("other")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURE_ORDER)

    X = df[FEATURE_ORDER].values.astype(np.float32)
    enc = LabelEncoder()
    y   = enc.fit_transform(df["label"])

    log.info("Class distribution: %s", dict(zip(enc.classes_,
             np.bincount(y).tolist())))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42)

    log.info("Applying SMOTE to balance training set …")
    sm = SMOTE(random_state=42)
    X_train, y_train = sm.fit_resample(X_train, y_train)

    log.info("Training Random Forest (%d estimators) …", args.n_estimators)
    clf = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_features="sqrt",
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=enc.classes_))

    label_map = {int(i): str(c) for i, c in enumerate(enc.classes_)}
    joblib.dump({"model": clf, "label_map": label_map}, args.out)
    log.info("Saved: %s", args.out)

if __name__ == "__main__":
    main()
