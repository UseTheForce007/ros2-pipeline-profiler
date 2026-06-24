import json
from collections import defaultdict

import pandas as pd
import numpy as np

EVENT_PUBLISH = 0
EVENT_RECEIVE = 1
EVENT_PROCESS_START = 2
EVENT_PROCESS_END = 3


def analyze(df: pd.DataFrame) -> dict:
    events_by_id = _group_by_message_id(df)
    chains = _build_chains(events_by_id)
    stage_latencies = _compute_stage_latencies(events_by_id)
    transport_latencies = _compute_transport_latencies(df, events_by_id)
    e2e = _compute_e2e_latencies(events_by_id, chains)
    summary = _compute_summary(stage_latencies, transport_latencies, e2e)
    drops = _detect_drops(df)

    return {
        "events_by_id": dict(events_by_id),
        "stage_latencies": stage_latencies,
        "transport_latencies": transport_latencies,
        "e2e": e2e,
        "summary": summary,
        "drops": drops,
        "chains": chains,
        "chain_count": len(chains),
        "total_events": len(df),
    }


def _group_by_message_id(df: pd.DataFrame) -> dict:
    events_by_id = defaultdict(list)
    for _, row in df.iterrows():
        events_by_id[row["message_id"]].append(row.to_dict())
    for mid in events_by_id:
        events_by_id[mid].sort(key=lambda e: e["sys_timestamp_ns"])
    return events_by_id


def _build_chains(events_by_id: dict) -> list:
    roots = [mid for mid, evs in events_by_id.items()
             if any(e["parent_message_id"] == 0 and e["event_type"] == EVENT_PUBLISH for e in evs)]

    chains = []
    for root in roots:
        chain = [root]
        current = root
        while True:
            children = [mid for mid, evs in events_by_id.items()
                        if any(e["parent_message_id"] == current and e["event_type"] == EVENT_PUBLISH for e in evs)]
            if not children:
                break
            current = children[0]
            chain.append(current)
        chains.append(chain)
    return chains


def _compute_stage_latencies(events_by_id: dict) -> dict:
    stages = defaultdict(list)
    for mid, evs in events_by_id.items():
        node_name = None
        start_time = None
        for e in evs:
            if e["event_type"] == EVENT_PROCESS_START:
                node_name = e["source_node_name"]
                start_time = e["timestamp_ns"]
            elif e["event_type"] == EVENT_PROCESS_END and start_time is not None:
                lat = (e["timestamp_ns"] - start_time) / 1_000_000
                stages[node_name].append(lat)
                start_time = None
    return dict(stages)


def _compute_transport_latencies(df: pd.DataFrame, events_by_id: dict) -> dict:
    publishes = df[df["event_type"] == EVENT_PUBLISH]
    receives = df[df["event_type"] == EVENT_RECEIVE]
    merged = pd.merge(publishes, receives, on="message_id", suffixes=("_pub", "_recv"))
    merged = merged[merged["source_file_pub"] != merged["source_file_recv"]]

    has_send_ts = "send_timestamp_ns" in df.columns
    topics = defaultdict(list)
    for _, row in merged.iterrows():
        if has_send_ts:
            recv_ts = row["sys_timestamp_ns_recv"]
            pub_ts = row["send_timestamp_ns_pub"]
        else:
            recv_ts = row["timestamp_ns_recv"]
            pub_ts = row["timestamp_ns_pub"]
        if pd.notna(recv_ts) and pd.notna(pub_ts):
            lat = (recv_ts - pub_ts) / 1_000_000
            if lat > 0:
                topics[row["topic_pub"]].append(lat)
    return dict(topics)


def _compute_e2e_latencies(events_by_id: dict, chains: list) -> list:
    e2e_list = []
    for chain in chains:
        if len(chain) < 2:
            continue
        leaf = chain[-1]
        leaf_evs = events_by_id[leaf]
        if not leaf_evs:
            continue
        last_time = leaf_evs[-1]["sys_timestamp_ns"]

        root = chain[0]
        root_evs = events_by_id[root]
        origin_ts = None
        for e in root_evs:
            if e["event_type"] == EVENT_PUBLISH:
                origin_ts = e.get("origin_timestamp_ns") or e.get("sys_timestamp_ns") or e["timestamp_ns"]
                break
        if origin_ts is None:
            continue

        e2e_ms = (last_time - origin_ts) / 1_000_000
        if e2e_ms <= 0:
            continue
        e2e_list.append({
            "chain": chain,
            "e2e_ms": e2e_ms,
        })
    return e2e_list


def _compute_summary(stage_latencies: dict, transport_latencies: dict, e2e: list) -> dict:
    summary = {}
    for name, vals in stage_latencies.items():
        if not vals:
            continue
        s = pd.Series(vals)
        summary[f"process_{name}"] = {
            "count": len(vals),
            "mean_ms": s.mean(),
            "p50_ms": s.quantile(0.5),
            "p90_ms": s.quantile(0.9),
            "p99_ms": s.quantile(0.99),
            "min_ms": s.min(),
            "max_ms": s.max(),
            "jitter": s.std() / s.mean() if s.mean() > 0 else 0,
        }
    for topic, vals in transport_latencies.items():
        if not vals:
            continue
        s = pd.Series(vals)
        summary[f"transport_{topic}"] = {
            "count": len(vals),
            "mean_ms": s.mean(),
            "p50_ms": s.quantile(0.5),
            "p90_ms": s.quantile(0.9),
            "p99_ms": s.quantile(0.99),
            "min_ms": s.min(),
            "max_ms": s.max(),
        }
    if e2e:
        vals = [e["e2e_ms"] for e in e2e]
        s = pd.Series(vals)
        summary["e2e"] = {
            "count": len(vals),
            "mean_ms": s.mean(),
            "p50_ms": s.quantile(0.5),
            "p90_ms": s.quantile(0.9),
            "p99_ms": s.quantile(0.99),
            "min_ms": s.min(),
            "max_ms": s.max(),
            "jitter": s.std() / s.mean() if s.mean() > 0 else 0,
        }
    return summary


def _detect_drops(df: pd.DataFrame) -> list:
    drops = []
    for source_file in df["source_file"].unique():
        sub = df[(df["source_file"] == source_file) & (df["event_type"] == EVENT_PUBLISH)]
        ids = sorted(sub["message_id"].unique())
        for i in range(len(ids) - 1):
            gap = ids[i + 1] - ids[i]
            if gap > 1:
                drops.append({
                    "source_file": source_file,
                    "from_id": ids[i],
                    "to_id": ids[i + 1],
                    "count": gap - 1,
                })
    return drops


def save_results(results: dict, path: str, metadata: dict = None):
    safe = {
        "summary": results.get("summary", {}),
        "stage_latencies": {k: [float(v) for v in vals] for k, vals in results.get("stage_latencies", {}).items()},
        "transport_latencies": {k: [float(v) for v in vals] for k, vals in results.get("transport_latencies", {}).items()},
        "e2e": results.get("e2e", []),
        "drops": results.get("drops", []),
    }
    for key in ("chain_count", "total_events", "pipeline_name"):
        if key in results:
            safe[key] = results[key]
    if metadata:
        safe["metadata"] = metadata
    with open(path, "w") as f:
        json.dump(safe, f, indent=2)


def load_results(path: str) -> dict:
    with open(path) as f:
        return json.load(f)
