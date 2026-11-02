#!/usr/bin/env python3
"""
nids_capture.py — Pi 4 Network Intrusion Detection Station
Sniffs packets on the mirror/tap interface, computes per-flow features,
triggers STA/LTA anomaly detection, and emits JSON events to Loki.

Requirements:
    pip install scapy requests numpy

Usage:
    sudo python3 nids_capture.py --iface eth1 --loki http://localhost:3100
"""

import argparse
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from threading import Thread, Lock

import numpy as np
import requests
from scapy.all import sniff, IP, TCP, UDP, ICMP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Flow key ───────────────────────────────────────────────────
@dataclass(frozen=True)
class FlowKey:
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    proto: str

# ── Per-flow statistics ────────────────────────────────────────
@dataclass
class FlowStats:
    pkt_count:  int   = 0
    byte_count: int   = 0
    syn_count:  int   = 0
    fin_count:  int   = 0
    rst_count:  int   = 0
    first_seen: float = 0.0
    last_seen:  float = 0.0
    iats:       list  = field(default_factory=list)   # inter-arrival times (s)
    pkt_sizes:  list  = field(default_factory=list)

    def update(self, pkt_len: int, flags: int = 0):
        now = time.time()
        if self.first_seen == 0.0:
            self.first_seen = now
        else:
            self.iats.append(now - self.last_seen)
        self.last_seen = now
        self.pkt_count  += 1
        self.byte_count += pkt_len
        self.pkt_sizes.append(pkt_len)
        self.syn_count += bool(flags & 0x02)
        self.fin_count += bool(flags & 0x01)
        self.rst_count += bool(flags & 0x04)

    def feature_vector(self) -> dict:
        duration = max(self.last_seen - self.first_seen, 1e-9)
        iats_arr = np.array(self.iats) if self.iats else np.array([0.0])
        sizes_arr = np.array(self.pkt_sizes) if self.pkt_sizes else np.array([0.0])
        return {
            "pkt_count":      self.pkt_count,
            "byte_count":     self.byte_count,
            "duration_s":     round(duration, 4),
            "bytes_per_s":    round(self.byte_count / duration, 2),
            "pkts_per_s":     round(self.pkt_count  / duration, 2),
            "mean_pkt_size":  round(float(sizes_arr.mean()), 2),
            "std_pkt_size":   round(float(sizes_arr.std()),  2),
            "mean_iat":       round(float(iats_arr.mean()),  6),
            "std_iat":        round(float(iats_arr.std()),   6),
            "syn_ratio":      round(self.syn_count / max(self.pkt_count, 1), 4),
            "fin_ratio":      round(self.fin_count / max(self.pkt_count, 1), 4),
            "rst_ratio":      round(self.rst_count / max(self.pkt_count, 1), 4),
        }

# ── Loki push helper ────────────────────────────────────────────
def push_to_loki(loki_url: str, stream_labels: dict, log_line: str):
    now_ns = str(int(time.time() * 1e9))
    payload = {
        "streams": [{
            "stream": stream_labels,
            "values": [[now_ns, log_line]],
        }]
    }
    try:
        r = requests.post(f"{loki_url}/loki/api/v1/push",
                          json=payload, timeout=5)
        r.raise_for_status()
    except Exception as e:
        log.warning("Loki push failed: %s", e)

# ── STA/LTA anomaly detector ────────────────────────────────────
class STALTA:
    """Short-term / long-term average ratio for burst detection."""
    def __init__(self, short_win=10, long_win=60, threshold=3.5):
        self.short_win = short_win
        self.long_win  = long_win
        self.threshold = threshold
        self.values: list = []

    def add(self, value: float) -> bool:
        self.values.append(value)
        if len(self.values) > self.long_win:
            self.values.pop(0)
        if len(self.values) < self.short_win:
            return False
        sta = np.mean(self.values[-self.short_win:])
        lta = np.mean(self.values)
        ratio = sta / max(lta, 1e-9)
        return ratio > self.threshold

# ── Main capture engine ─────────────────────────────────────────
class NIDSCapture:
    def __init__(self, iface: str, loki_url: str, export_interval: int = 10):
        self.iface           = iface
        self.loki_url        = loki_url
        self.export_interval = export_interval
        self.flows: dict[FlowKey, FlowStats] = {}
        self.lock            = Lock()
        self.pkt_rate_detector = STALTA(short_win=5, long_win=60, threshold=4.0)
        self.pkt_counts_per_sec: list[int] = []

    def _packet_callback(self, pkt):
        if not pkt.haslayer(IP):
            return
        ip   = pkt[IP]
        size = len(pkt)
        proto, sport, dport, flags = "OTHER", 0, 0, 0

        if pkt.haslayer(TCP):
            proto  = "TCP"
            sport  = pkt[TCP].sport
            dport  = pkt[TCP].dport
            flags  = pkt[TCP].flags
        elif pkt.haslayer(UDP):
            proto = "UDP"
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
        elif pkt.haslayer(ICMP):
            proto = "ICMP"

        key = FlowKey(ip.src, ip.dst, sport, dport, proto)
        with self.lock:
            if key not in self.flows:
                self.flows[key] = FlowStats()
            self.flows[key].update(size, flags)

    def _exporter_thread(self):
        """Periodically export flow features to Loki and detect anomalies."""
        classifier_url = "http://localhost:8765/classify"  # flow_classifier.py microservice
        while True:
            time.sleep(self.export_interval)
            with self.lock:
                snapshot = dict(self.flows)
                self.flows.clear()

            for key, stats in snapshot.items():
                feats = stats.feature_vector()
                event = {
                    "ts":       datetime.now(timezone.utc).isoformat(),
                    "src_ip":   key.src_ip,
                    "dst_ip":   key.dst_ip,
                    "src_port": key.src_port,
                    "dst_port": key.dst_port,
                    "proto":    key.proto,
                    **feats,
                }
                # Score via ML classifier
                try:
                    resp = requests.post(classifier_url, json=feats, timeout=2)
                    if resp.ok:
                        event["ml_label"]    = resp.json().get("label", "benign")
                        event["ml_score"]    = resp.json().get("score", 0.0)
                    else:
                        event["ml_label"] = "unknown"
                        event["ml_score"] = 0.0
                except Exception:
                    event["ml_label"] = "unknown"
                    event["ml_score"] = 0.0

                severity = "high" if event["ml_label"] not in ("benign","unknown") else "info"
                push_to_loki(
                    self.loki_url,
                    {"job": "nids", "severity": severity, "proto": key.proto},
                    json.dumps(event),
                )
                if severity == "high":
                    log.warning("⚠  ALERT  %s → %s:%s  [%s]  score=%.2f",
                                key.src_ip, key.dst_ip, key.dst_port,
                                event["ml_label"], event["ml_score"])

    def run(self):
        Thread(target=self._exporter_thread, daemon=True).start()
        log.info("🔍 Sniffing on interface: %s", self.iface)
        sniff(iface=self.iface, prn=self._packet_callback, store=False)

def main():
    parser = argparse.ArgumentParser(description="Pi 4 NIDS Capture Daemon")
    parser.add_argument("--iface", default="eth1",             help="Mirror/tap interface")
    parser.add_argument("--loki",  default="http://localhost:3100", help="Loki push URL")
    parser.add_argument("--interval", type=int, default=10,    help="Flow export interval (s)")
    args = parser.parse_args()

    engine = NIDSCapture(args.iface, args.loki, args.interval)
    engine.run()

if __name__ == "__main__":
    main()
