import json
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def generate_heatmap_report(results_dir: str, output_path: str):
    results_dir = Path(results_dir)

    # Build matrix: rows = RMW, cols = QoS config, cell = results.json path
    configs = []  # list of (rmw, reliability, depth, results_dict)
    for rmw_dir in sorted(results_dir.iterdir()):
        if not rmw_dir.is_dir():
            continue
        rmw_name = rmw_dir.name
        for qos_dir in sorted(rmw_dir.iterdir()):
            if not qos_dir.is_dir():
                continue
            parts = qos_dir.name.split("_depth_")
            if len(parts) != 2:
                continue
            reliability = parts[0]
            depth = int(parts[1])

            # Average results across trials
            trial_results = []
            for trial_dir in sorted(qos_dir.iterdir()):
                if not trial_dir.is_dir():
                    continue
                results_file = trial_dir / "results.json"
                if results_file.exists():
                    with open(results_file) as f:
                        trial_results.append(json.load(f))

            if not trial_results:
                continue

            # Average summary metrics across trials
            merged = _merge_trials(trial_results)
            configs.append((rmw_name, reliability, depth, merged))

    if not configs:
        print("No results found in directory tree")
        return

    # Find unique RMWs and QoS keys
    rmws = sorted(set(c[0] for c in configs))
    qos_keys = sorted(set(f"{c[1]}_depth_{c[2]}" for c in configs),
                      key=_qos_sort_key)

    # Determine which metrics to show
    sample = configs[0][3]
    summary = sample.get("summary", {})
    metrics = [k for k in summary if "transport" in k or "e2e" in k or "process" in k]

    # Build heatmap data for each metric
    metric_tables = {}
    for metric in metrics:
        table = []
        for rmw in rmws:
            row = []
            for qk in qos_keys:
                parts = qk.split("_depth_")
                reliability = parts[0]
                depth = int(parts[1])
                val = None
                for c in configs:
                    if c[0] == rmw and c[1] == reliability and c[2] == depth:
                        s = c[3].get("summary", {}).get(metric, {})
                        val = s.get("p99_ms", None)
                        break
                row.append(val if val is not None else 0)
            table.append(row)
        metric_tables[metric] = table

    # Build figures
    metric_labels = {
        "e2e": "End-to-End p99 (ms)",
        "transport_/image": "Transport /image p99 (ms)",
        "transport_/processed": "Transport /processed p99 (ms)",
        "process_processing_node": "Processing (blur) p99 (ms)",
        "process_control_node": "Control overhead p99 (ms)",
    }

    figs = []
    for metric in metrics:
        table = metric_tables[metric]
        if not table:
            continue

        title = metric_labels.get(metric, f"{metric} p99 (ms)")

        # Color scale: green=fast, yellow, red=slow
        zmin = min(min(r) for r in table) if table else 0
        zmax = max(max(r) for r in table) if table else 1
        if zmax == zmin:
            zmax = zmin + 1

        fig = go.Figure(data=go.Heatmap(
            z=table,
            x=qos_keys,
            y=rmws,
            text=[[f"{v:.3f}" for v in row] for row in table],
            texttemplate="%{text}",
            textfont={"size": 14},
            colorscale="RdYlGn_r",  # red=high latency, green=low
            zmin=zmin,
            zmax=zmax,
            hovertemplate="RMW: %{y}<br>QoS: %{x}<br>p99: %{text}ms<extra></extra>",
        ))

        fig.update_layout(
            title=title,
            xaxis_title="QoS Configuration",
            yaxis_title="RMW Implementation",
            height=300 + len(rmws) * 60,
        )
        figs.append((title, fig))

    # Write HTML
    parts = [f"""<html><head><title>RMW × QoS Latency Heatmap</title>
<style>
table {{ border-collapse: collapse; margin: 10px 0; }}
th, td {{ border: 1px solid #999; padding: 6px 12px; text-align: right; }}
th {{ background: #eee; }}
</style>
</head><body>
<h1>RMW × QoS Latency Heatmap</h1>
<p>Each cell shows the p99 latency (ms), averaged over trials.
Color scale: green = fast, red = slow — relative to that metric's range.</p>"""]

    for i, (title, fig) in enumerate(figs):
        include_js = "cdn" if i == 0 else False
        parts.append(fig.to_html(full_html=False, include_plotlyjs=include_js))
        parts.append(f"<h3>{title} — Values</h3>")
        parts.append(_metric_table(metric_tables[list(metric_tables.keys())[list(figs).index((title, fig))]], qos_keys, rmws))

    parts.append("</body></html>")

    with open(output_path, "w") as f:
        f.write("\n".join(parts))

    print(f"Heatmap report → {output_path}")


def _merge_trials(trial_results: list) -> dict:
    """Average summary metrics across trials."""
    if not trial_results:
        return {}
    if len(trial_results) == 1:
        return trial_results[0]

    merged = {"summary": {}}
    all_keys = set()
    for tr in trial_results:
        all_keys.update(tr.get("summary", {}).keys())

    for key in all_keys:
        vals = []
        for tr in trial_results:
            s = tr.get("summary", {}).get(key)
            if s:
                vals.append(s)
        if not vals:
            continue
        merged["summary"][key] = {
            "p50_ms": sum(v["p50_ms"] for v in vals) / len(vals),
            "p90_ms": sum(v["p90_ms"] for v in vals) / len(vals),
            "p99_ms": sum(v["p99_ms"] for v in vals) / len(vals),
            "mean_ms": sum(v["mean_ms"] for v in vals) / len(vals),
            "count": sum(v["count"] for v in vals),
        }
    return merged


def _qos_sort_key(qk: str) -> tuple:
    """Sort QoS keys: best_effort before reliable, shallower depth first."""
    parts = qk.split("_depth_")
    reliability = parts[0]
    depth = int(parts[1])
    return (0 if reliability == "best_effort" else 1, depth)


def _metric_table(table: list, columns: list, rows: list) -> str:
    html = ["<table><tr><th>RMW</th>"]
    for col in columns:
        html.append(f"<th>{col}</th>")
    html.append("</tr>")
    for i, row in enumerate(rows):
        html.append(f"<tr><td style='text-align:left'>{row}</td>")
        for v in table[i]:
            html.append(f"<td>{v:.3f}</td>")
        html.append("</tr>")
    html.append("</table>")
    return "\n".join(html)
