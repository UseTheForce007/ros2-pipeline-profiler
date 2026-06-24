import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from .visualizer import write_html, render_summary_table


def generate_comparison_report(results_list: list, output_path: str):
    labels = []
    for r in results_list:
        lbl = r.get("rmw_label", "unknown")
        labels.append(lbl)

    figs = []

    fig = _comparison_cdf(results_list, labels)
    if fig:
        figs.append(("CDF Comparison", fig))

    fig = _comparison_box(results_list, labels)
    if fig:
        figs.append(("Box Plot Comparison", fig))

    fig = _comparison_bars(results_list, labels)
    if fig:
        figs.append(("Latency Comparison (p50/p90/p99)", fig))

    # Build combined summary table
    summary_html = _comparison_summary_table(results_list, labels)

    parts = [f"""<html><head><title>DDS Comparison Report</title>
<style>
table {{ border-collapse: collapse; margin: 10px 0; }}
th, td {{ border: 1px solid #999; padding: 6px 12px; text-align: right; }}
th {{ background: #eee; }}
.best {{ background: #c8e6c9; }}
.worst {{ background: #ffcdd2; }}
</style>
</head><body>
<h1>DDS Comparison Report</h1>"""]

    parts.append(summary_html)

    for i, (title, fig) in enumerate(figs):
        parts.append(f"<h2>{title}</h2>")
        include_js = "cdn" if i == 0 else False
        parts.append(fig.to_html(full_html=False, include_plotlyjs=include_js))

    parts.append("</body></html>")

    with open(output_path, "w") as f:
        f.write("\n".join(parts))


def _get_stage_keys(results_list: list) -> list:
    keys = set()
    for r in results_list:
        keys.update(r.get("summary", {}).keys())
    return sorted(keys)


def _comparison_cdf(results_list: list, labels: list) -> go.Figure | None:
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    fig = None

    # Collect all unique stage/metric names
    all_metrics = set()
    for r in results_list:
        for k in r.get("stage_latencies", {}):
            all_metrics.add(("process", k))
        for k in r.get("transport_latencies", {}):
            all_metrics.add(("transport", k))

    if not all_metrics:
        return None

    n = len(all_metrics)
    fig = make_subplots(rows=n, cols=1, subplot_titles=[f"{t} {k}" for t, k in sorted(all_metrics)])

    for idx, (mtype, mname) in enumerate(sorted(all_metrics)):
        src = "stage_latencies" if mtype == "process" else "transport_latencies"
        for ri, r in enumerate(results_list):
            vals = r.get(src, {}).get(mname, [])
            if not vals:
                continue
            s = pd.Series(sorted(vals))
            cdf = s.rank(pct=True)
            label = labels[ri] if ri < len(labels) else f"run_{ri}"
            color = colors[ri % len(colors)]
            fig.add_trace(go.Scatter(
                x=s, y=cdf, mode="lines", name=label,
                line=dict(color=color),
                legendgroup=label,
                showlegend=(idx == 0),
            ), row=idx + 1, col=1)

    fig.update_layout(title="Latency CDF by RMW Implementation",
                      height=250 * n)
    fig.update_xaxes(title_text="Latency (ms)")
    fig.update_yaxes(title_text="Cumulative Probability")
    return fig


def _comparison_box(results_list: list, labels: list) -> go.Figure | None:
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    added = set()

    for ri, r in enumerate(results_list):
        label = labels[ri] if ri < len(labels) else f"run_{ri}"
        color = colors[ri % len(colors)]
        for name, vals in r.get("stage_latencies", {}).items():
            if not vals:
                continue
            trace_label = f"{label} / {name}"
            fig.add_trace(go.Box(y=vals, name=trace_label,
                                 marker_color=color, legendgroup=label,
                                 showlegend=label not in added))
            added.add(label)

    fig.update_layout(title="Processing Latency Distribution by RMW",
                      yaxis_title="Latency (ms)")
    return fig


def _comparison_bars(results_list: list, labels: list) -> go.Figure | None:
    summary_keys = _get_stage_keys(results_list)
    if not summary_keys:
        return None

    n = len(summary_keys)
    fig = make_subplots(rows=n, cols=1,
                        subplot_titles=summary_keys)

    for idx, key in enumerate(summary_keys):
        metrics = ["p50_ms", "p90_ms", "p99_ms"]
        for mi, metric in enumerate(metrics):
            vals = []
            for r in results_list:
                s = r.get("summary", {}).get(key, {})
                vals.append(s.get(metric, 0))
            fig.add_trace(go.Bar(
                name=metric,
                x=labels,
                y=vals,
                offsetgroup=mi,
                legendgroup=metric,
                showlegend=(idx == 0),
            ), row=idx + 1, col=1)

    fig.update_layout(title="Latency Comparison (p50/p90/p99)",
                      barmode="group",
                      height=250 * n)
    return fig


def _comparison_summary_table(results_list: list, labels: list) -> str:
    keys = _get_stage_keys(results_list)
    if not keys:
        return ""

    html = ["<h2>Summary Comparison</h2>",
            "<table><tr><th>Metric</th>"]
    for label in labels:
        html.append(f"<th colspan='3'>{label}</th>")
    html.append("</tr><tr><th></th>")
    for _ in labels:
        html.append("<th>p50</th><th>p90</th><th>p99</th>")
    html.append("</tr>")

    for key in keys:
        html.append(f"<tr><td style='text-align:left'>{key}</td>")
        best_p99 = float("inf")
        best_ri = 0
        for ri, r in enumerate(results_list):
            s = r.get("summary", {}).get(key, {})
            p99 = s.get("p99_ms", 0)
            if p99 < best_p99 and p99 > 0:
                best_p99 = p99
                best_ri = ri

        for ri, r in enumerate(results_list):
            s = r.get("summary", {}).get(key, {})
            p50 = s.get("p50_ms", 0)
            p90 = s.get("p90_ms", 0)
            p99 = s.get("p99_ms", 0)
            cls = "best" if ri == best_ri else ""
            html.append(f"<td class='{cls}'>{p50:.3f}</td>")
            html.append(f"<td class='{cls}'>{p90:.3f}</td>")
            html.append(f"<td class='{cls}'>{p99:.3f}</td>")
        html.append("</tr>")

    html.append("</table>")
    return "\n".join(html)
