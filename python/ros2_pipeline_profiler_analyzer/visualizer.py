import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from .analyzer import EVENT_PUBLISH, EVENT_RECEIVE, EVENT_PROCESS_START, EVENT_PROCESS_END


def generate_report(results: dict, output_path: str, pipeline_name: str = ""):
    figs = []

    fig = waterfall_chart(results)
    if fig:
        figs.append(("Latency Waterfall", fig))

    fig = latency_histogram(results)
    if fig:
        figs.append(("Latency Distribution", fig))

    fig = latency_over_time(results)
    if fig:
        figs.append(("Latency Over Time", fig))

    fig = cdf_curve(results)
    if fig:
        figs.append(("CDF Curve", fig))

    fig = box_plot(results)
    if fig:
        figs.append(("Box Plot", fig))

    _write_html(figs, results, output_path, pipeline_name)


def _html_header(title: str) -> str:
    return f"""<html><head><title>{title}</title></head><body>
<h1>{title}</h1>"""


def _html_footer() -> str:
    return "</body></html>"


def _summary_table(summary: dict) -> str:
    rows = []
    for name, stats in summary.items():
        rows.append(f"""<tr>
<td>{name}</td>
<td>{stats['count']}</td>
<td>{stats.get('mean_ms', 0):.3f}</td>
<td>{stats.get('p50_ms', 0):.3f}</td>
<td>{stats.get('p90_ms', 0):.3f}</td>
<td>{stats.get('p99_ms', 0):.3f}</td>
<td>{stats.get('min_ms', 0):.3f}</td>
<td>{stats.get('max_ms', 0):.3f}</td>
</tr>""")
    if not rows:
        return ""
    return f"""<h2>Summary</h2>
<table border="1" style="border-collapse: collapse;">
<tr><th>Stage</th><th>Count</th><th>Mean (ms)</th><th>p50 (ms)</th><th>p90 (ms)</th><th>p99 (ms)</th><th>Min (ms)</th><th>Max (ms)</th></tr>
{''.join(rows)}
</table>"""


def _write_html(figs: list, results: dict, output_path: str, pipeline_name: str):
    parts = [_html_header(pipeline_name or "Pipeline Profiler Report")]
    parts.append(_summary_table(results.get("summary", {})))
    for i, (title, fig) in enumerate(figs):
        parts.append(f"<h2>{title}</h2>")
        include_js = "cdn" if i == 0 else False
        parts.append(fig.to_html(full_html=False, include_plotlyjs=include_js))
    parts.append(_html_footer())

    with open(output_path, "w") as f:
        f.write("\n".join(parts))


def waterfall_chart(results: dict) -> go.Figure | None:
    chains = results.get("chains", [])
    events_by_id = results.get("events_by_id", {})
    if not chains or not events_by_id:
        return None

    # Collect ordered node names across all chains
    all_nodes = []
    for chain in chains:
        for mid in chain:
            for e in events_by_id.get(mid, []):
                if e["event_type"] == EVENT_PROCESS_START:
                    nm = e["source_node_name"]
                    if nm not in all_nodes:
                        all_nodes.append(nm)
                    break

    # Per node, collect the total latency for each chain
    node_data = {nm: [0.0] * len(chains) for nm in all_nodes}
    y_labels = []

    for i, chain in enumerate(chains):
        y_labels.append(f"msg {chain[0]}")
        for mid in chain:
            evs = events_by_id.get(mid, [])
            start_ts = None
            node_name = None
            for e in evs:
                if e["event_type"] == EVENT_PROCESS_START:
                    node_name = e["source_node_name"]
                    start_ts = e["timestamp_ns"]
                elif e["event_type"] == EVENT_PROCESS_END and start_ts is not None:
                    node_data[node_name][i] += (e["timestamp_ns"] - start_ts) / 1_000_000
                    start_ts = None

    fig = go.Figure()
    for nm in all_nodes:
        vals = node_data[nm]
        if any(v > 0 for v in vals):
            fig.add_trace(go.Bar(
                name=nm,
                x=vals,
                y=y_labels,
                orientation="h",
            ))

    fig.update_layout(barmode="stack", title="Per-Message Latency Waterfall",
                      xaxis_title="Latency (ms)", yaxis_title="Message")
    return fig


def latency_histogram(results: dict) -> go.Figure | None:
    stage_lat = results.get("stage_latencies", {})
    if not stage_lat:
        return None

    names = list(stage_lat.keys())
    fig = make_subplots(rows=len(names), cols=1,
                        subplot_titles=names)
    for i, name in enumerate(names):
        fig.add_trace(go.Histogram(x=stage_lat[name], nbinsx=30, name=name),
                      row=i + 1, col=1)

    fig.update_layout(title="Latency Distribution per Stage",
                      height=250 * len(names))
    return fig


def latency_over_time(results: dict) -> go.Figure | None:
    stage_lat = results.get("stage_latencies", {})
    if not stage_lat:
        return None

    fig = go.Figure()
    for name, vals in stage_lat.items():
        fig.add_trace(go.Scatter(
            y=vals, mode="markers+lines", name=name,
            line=dict(width=1),
        ))
        s = pd.Series(vals)
        rolling = s.rolling(window=10, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            y=rolling, mode="lines", name=f"{name} (avg 10)",
            line=dict(width=2, dash="dash"),
        ))

    fig.update_layout(title="Latency Over Time (per message sequence)",
                      xaxis_title="Message Sequence", yaxis_title="Latency (ms)")
    return fig


def cdf_curve(results: dict) -> go.Figure | None:
    stage_lat = results.get("stage_latencies", {})
    if not stage_lat:
        return None

    fig = go.Figure()
    for name, vals in stage_lat.items():
        s = pd.Series(sorted(vals))
        cdf = s.rank(pct=True)
        fig.add_trace(go.Scatter(
            x=s, y=cdf, mode="lines", name=name,
        ))

    fig.update_layout(title="CDF — Cumulative Distribution",
                      xaxis_title="Latency (ms)", yaxis_title="Cumulative Probability")
    return fig


def box_plot(results: dict) -> go.Figure | None:
    stage_lat = results.get("stage_latencies", {})
    if not stage_lat:
        return None

    fig = go.Figure()
    for name, vals in stage_lat.items():
        fig.add_trace(go.Box(y=vals, name=name))

    fig.update_layout(title="Latency Distribution (Box Plot)",
                      yaxis_title="Latency (ms)")
    return fig
