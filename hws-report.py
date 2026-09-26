#!/usr/bin/env python3
"""hws-report — Self-contained interactive HTML report from hws YAML output."""

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
import plotly.graph_objects as go

# Prefer the C-accelerated loader (libyaml) when available; falls back to the
# pure-Python SafeLoader transparently otherwise.
_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

_LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 152.51483 56.285943">'
    '<g transform="translate(-31.99399,-74.551448)">'
    '<path style="fill:#6081ff;fill-opacity:1" d="'
    'm 98.908744,130.72303 c -0.68571,-0.14773 -1.56079,-0.65442 -2.06479,-1.19555'
    ' -1.146238,-1.2307 -1.925607,-3.24488 -4.247067,-10.97605'
    ' -2.146481,-7.14844 -2.838378,-9.20979 -3.528509,-10.5124'
    ' -0.698809,-1.31899 -1.555556,-2.12709 -2.508619,-2.36619'
    ' -0.365525,-0.0917 -2.456221,-0.15397 -5.185378,-0.15446'
    ' -3.967304,-7.2e-4 -4.622339,-0.0321 -4.946113,-0.23696'
    ' -1.178554,-0.74579 -1.039616,-3.1385 0.209262,-3.6038'
    ' 0.888422,-0.33101 8.52023,-1.12424 9.950958,-1.03428'
    ' 4.117683,0.25891 6.333374,2.38785 8.388726,8.06029'
    ' 0.906321,2.5013 1.064781,3.00449 2.90845,9.23589'
    ' 0.71346,2.41141 1.37194,4.562 1.4633,4.77908'
    ' 0.36173,0.85955 0.44765,0.47704 2.529936,-11.26338'
    ' 0.79818,-4.5003 1.92371,-10.95206 2.50118,-14.337242'
    ' 2.42167,-14.19616 3.094,-17.34054 4.10411,-19.19425'
    ' 1.39985,-2.56892 4.24782,-3.15726 6.09296,-1.25868'
    ' 1.68024,1.72891 2.2489,4.1349 5.27903,22.3356'
    ' 1.24931,7.504022 3.1077,18.124092 3.5859,20.492112'
    ' 0.12868,0.63721 0.32159,1.62647 0.42869,2.19835'
    ' 0.19337,1.03251 0.37351,1.4834 0.53454,1.33793'
    ' 0.0462,-0.0417 0.77521,-2.58144 1.62007,-5.64381'
    ' 1.78734,-6.47855 2.7457,-9.52797 3.54185,-11.26988'
    ' 1.83578,-4.01651 4.34383,-5.71476 8.07632,-5.46863'
    ' 0.7494,0.0494 2.50937,0.28352 3.91105,0.52024'
    ' 1.99106,0.33625 2.63155,0.50087 2.92814,0.7526'
    ' 0.86433,0.73359 0.89211,2.42833 0.0523,3.1871'
    ' l -0.45484,0.41092 -3.41867,8.7e-4'
    ' c -1.88027,4.3e-4 -3.68105,0.0666 -4.00173,0.14712'
    ' -0.61189,0.15355 -1.6906,1.0877 -2.10948,1.82679'
    ' -0.39335,0.69405 -1.32312,3.43666 -2.25173,6.6421'
    ' -0.48457,1.67268 -1.32452,4.57271 -1.86655,6.44452'
    ' -1.40931,4.86679 -1.68947,5.73536 -2.23465,6.92799'
    ' -1.00098,2.18976 -2.30172,3.25117 -3.99664,3.26127'
    ' -2.54999,0.0152 -4.05282,-1.96068 -5.14769,-6.76806'
    ' -0.78425,-3.44354 -2.63745,-13.78019 -4.65078,-25.940862'
    ' -1.58928,-9.59935 -2.1956,-12.81663 -2.41539,-12.81663'
    ' -0.26909,0 -0.83007,2.93117 -3.02379,15.799722'
    ' -2.22252,13.03744 -3.79427,21.43135 -4.52595,24.17077'
    ' -0.88383,3.30908 -2.14724,5.08874 -3.89481,5.48629'
    ' -0.786216,0.17886 -0.904786,0.18057 -1.633546,0.0236 z"/>'
    '<g style="font-weight:bold;font-size:50.8px;font-family:\'DejaVu Sans Mono\';fill:#4d4d4d"'
    ' transform="translate(116.70508,-13.108291)">'
    '<path style="font-size:74.0833px;font-family:\'DejaVu Sans\'" d="'
    'm -43.979745,119.27537 v 24.67031 H -57.0022 v -4.01525 -14.79496'
    ' q 0,-5.3175 -0.253214,-7.30704 -0.217041,-1.98954 -0.795817,-2.93005'
    ' -0.759643,-1.26607 -2.061889,-1.95337 -1.302245,-0.72347 -2.966225,-0.72347'
    ' -4.051431,0 -6.366534,3.14709 -2.315103,3.11092 -2.315103,8.64546'
    ' v 19.93159 H -84.71109 V 87.659739 h 12.950108 v 21.704091'
    ' q 2.930052,-3.545 6.22184,-5.20898 3.291787,-1.70015 7.27087,-1.70015'
    ' 7.017656,0 10.635005,4.30464 3.653522,4.30465 3.653522,12.51603 z"/>'
    '<path style="font-size:74.0833px;font-family:\'DejaVu Sans\'" d="'
    'm 65.090714,103.64842 v 9.83919 q -4.15995,-1.73633 -8.03051,-2.60449'
    ' -3.87056,-0.86817 -7.30704,-0.86817 -3.6897,0 -5.49837,0.94051'
    ' -1.7725,0.90434 -1.7725,2.82154 0,1.55546 1.33842,2.38745'
    ' 1.37459,0.83199 4.88342,1.2299 l 2.27893,0.32556'
    ' q 9.9477,1.26607 13.38418,4.15995 3.43649,2.89388 3.43649,9.07954'
    ' 0,6.47506 -4.7749,9.73067 -4.7749,3.25561 -14.25236,3.25561'
    ' -4.01525,0 -8.3199,-0.65112 -4.26847,-0.61495 -8.79016,-1.88102'
    ' v -9.83919 q 3.87057,1.88102 7.922,2.82153 4.0876,0.94052 8.28373,0.94052'
    ' 3.79821,0 5.71541,-1.04904 1.91719,-1.04903 1.91719,-3.11092'
    ' 0,-1.73632 -1.33842,-2.56831 -1.30224,-0.86817 -5.24515,-1.33842'
    ' l -2.27893,-0.28939 q -8.64547,-1.0852 -12.11812,-4.01526'
    ' -3.47266,-2.93005 -3.47266,-8.89868 0,-6.43888 4.41317,-9.5498'
    ' 4.41317,-3.11092 13.52888,-3.11092 3.58118,0 7.52409,0.54261'
    ' 3.94291,0.5426 8.57311,1.70015 z"/>'
    '</g></g></svg>'
)


# ── CLI ────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a self-contained interactive HTML report from hws YAML output."
    )
    p.add_argument("inputs", nargs="+", metavar="input",
                   help="Path(s) to hws YAML file(s). Pass two or more to enable "
                        "comparison mode (overlay one series per file on every plot).")
    p.add_argument("-o", "--output", help="Output HTML file (default: <input>_report.html).")
    p.add_argument("--title", help="Report title (default: derived from filename).")
    p.add_argument(
        "--cdn",
        action="store_true",
        help="Load Plotly.js from CDN instead of embedding it (smaller file, requires internet).",
    )
    p.add_argument("--view-config", metavar="FILE",
                   help="YAML file defining named views (optional).")
    p.add_argument("--custom-plots", metavar="FILE",
                   help="JSON file of custom plot configs to pre-load in the Custom Plots tab.")
    return p.parse_args()


# ── YAML loading ───────────────────────────────────────────────────────

def load_documents(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [d for d in yaml.load_all(f, Loader=_YAML_LOADER) if isinstance(d, dict)]


def iter_samplers(docs: List[Dict[str, Any]]):
    """
    Yield (rank, sampler_key, sampler_dict) for both YAML formats.

    MPI format:     top-level doc has a 'rank' key; samplers are 'sampler_N' sub-dicts.
    Non-MPI format: each doc is a sampler directly (no 'rank' key).
    """
    for doc in docs:
        if "rank" in doc:
            rank = doc["rank"]
            for key, val in doc.items():
                if key.startswith("sampler_") and isinstance(val, dict):
                    yield rank, key, val
        else:
            device_id = doc.get("device_identification", "unknown")
            yield None, device_id, doc


# ── Metric discovery ───────────────────────────────────────────────────

_META_KEYS = frozenset({
    "device_identification", "version", "start_time",
    "events", "sampling_interval", "time_points",
})


def get_time_axis(sampler: Dict) -> Tuple[Optional[str], Optional[List[float]]]:
    tp = sampler.get("time_points")
    if not isinstance(tp, dict):
        return None, None
    unit = tp.get("unit")
    vals = tp.get("values")
    return (unit, vals) if isinstance(vals, list) and vals else (None, None)


def get_events(sampler: Dict) -> List[Tuple[float, str]]:
    ev = sampler.get("events")
    if not isinstance(ev, dict):
        return []
    times = ev.get("time_points", {}).get("values", [])
    names = ev.get("names", [])
    if isinstance(times, list) and isinstance(names, list):
        return list(zip(times, names))
    return []


def _is_plottable(vals, n: int) -> bool:
    return (
        n > 0
        and isinstance(vals, list)
        and len(vals) == n
        and all(isinstance(x, (int, float)) for x in vals)
    )


def discover_metrics(
    sampler: Dict, n: int
) -> Tuple[List[Tuple[str, str, str, List[float]]], List[Tuple[str, str, str]]]:
    """Single-pass metric discovery.

    Returns (time_series, static_info):
      time_series:  [(group, metric, unit, values), ...] — plottable list metrics.
      static_info:  [(group, key, display_string), ...]  — non-time-series fields.
    """
    time_series: List[Tuple[str, str, str, List[float]]] = []
    static_info: List[Tuple[str, str, str]] = []
    for group_name, group_val in sampler.items():
        if group_name in _META_KEYS or not isinstance(group_val, dict):
            continue
        for metric_name, node in group_val.items():
            if not isinstance(node, dict):
                continue
            vals = node.get("values")
            unit = node.get("unit", "")
            if _is_plottable(vals, n):
                time_series.append((group_name, metric_name, unit, vals))
            else:
                if isinstance(vals, list):
                    raw = str(vals)
                    display = (raw[:100] + "…") if len(raw) > 100 else raw
                elif vals is None:
                    display = "—"
                else:
                    display = str(vals)
                if unit and unit not in ("string", "int", "float", "bool"):
                    display = f"{display} {unit}"
                static_info.append((group_name, metric_name, display))
    return time_series, static_info


# ── Unit conversion ────────────────────────────────────────────────────

def convert_unit(unit: str, values: List[float]) -> Tuple[str, List[float]]:
    if unit == "B":
        return "GiB", [v / 1_073_741_824.0 for v in values]
    if unit == "percentage":
        return "%", values
    return unit, values


# ── Figure builder ─────────────────────────────────────────────────────

def _stagger_events(
    events: List[Tuple[float, str]],
    t_min: float,
    t_max: float,
) -> List[Tuple[float, str, float]]:
    """Return (t, name, y_paper) with y staggered so close labels don't overlap."""
    if not events:
        return []
    LEVELS = [0.97, 0.82, 0.67, 0.52]
    threshold = ((t_max - t_min) or 1.0) * 0.06
    last_t: Dict[int, float] = {}
    result = []
    for t, name in sorted(events, key=lambda e: e[0]):
        chosen = 0
        for idx in range(len(LEVELS)):
            if t - last_t.get(idx, -1e18) >= threshold:
                chosen = idx
                break
        last_t[chosen] = t
        result.append((t, name, LEVELS[chosen]))
    return result


def build_figure(
    rank,
    sampler: Dict,
    group: str,
    metric: str,
    unit: str,
    values: List[float],
) -> go.Figure:
    time_unit, time_points = get_time_axis(sampler)
    unit_label, y_vals = convert_unit(unit, values)
    t_unit = time_unit or "s"
    u_disp = unit_label if unit_label else "—"
    device_id = sampler.get("device_identification", "device")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_points,
        y=y_vals,
        mode="lines+markers",
        line=dict(color="#6081ff"),
        marker=dict(size=4, color="#6081ff"),
        name=metric,
        hovertemplate=(
            f"t: %{{x:.4f}} {t_unit}<br>"
            f"{metric}: %{{y:.4g}} {u_disp}"
            "<extra></extra>"
        ),
        hoverlabel=dict(bgcolor="#6081ff", bordercolor="#6081ff", font_color="#ffffff"),
    ))

    t_min = time_points[0] if time_points else 0.0
    t_max = time_points[-1] if time_points else 1.0
    for t, event_name, y_paper in _stagger_events(get_events(sampler), t_min, t_max):
        fig.add_vline(
            x=t,
            line_dash="dot",
            line_color="rgba(120,120,120,0.55)",
        )
        fig.add_annotation(
            x=t,
            y=y_paper,
            xref="x",
            yref="paper",
            text=str(event_name),
            showarrow=False,
            font=dict(size=10, color="rgba(80,80,80,0.9)"),
            xanchor="left",
            yanchor="top",
            textangle=-90,
            bgcolor="rgba(255,255,255,0.72)",
            borderpad=2,
        )

    rank_prefix = f"Rank {rank}  ·  " if rank is not None else ""
    fig.update_layout(
        title=dict(
            text=f"{rank_prefix}{device_id}  —  {group}.{metric}",
            font=dict(size=12),
        ),
        xaxis_title=f"Time [{t_unit}]",
        yaxis_title=f"{metric} [{u_disp}]",
        height=315,
        margin=dict(l=65, r=20, t=70, b=45),
        hovermode="closest",
        showlegend=False,
    )
    return fig


# ── HTML builder ───────────────────────────────────────────────────────

_DEFAULT_VIEWS = [{"name": "All", "include_metrics": "all", "group_by": ["device"], "columns": None}]

_VALID_LEVELS = {"rank", "device", "group"}


def _normalize_group_by(raw) -> List[str]:
    if isinstance(raw, list):
        levels = [str(x) for x in raw if str(x) in _VALID_LEVELS]
    else:
        s = str(raw) if raw else "device"
        levels = [s] if s in _VALID_LEVELS else ["device"]
    return levels or ["device"]


def load_view_config(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.load(f, Loader=_YAML_LOADER)
    raw = cfg.get("views", []) if isinstance(cfg, dict) else []
    views = []
    for v in raw:
        if not isinstance(v, dict) or not v.get("name"):
            continue
        inc = v.get("include_metrics", "all")
        if isinstance(inc, list):
            inc = [str(x) for x in inc]
        else:
            inc = "all"
        views.append({
            "name": str(v["name"]),
            "include_metrics": inc,
            "group_by": _normalize_group_by(v.get("group_by", "device")),
            "columns": v.get("columns", None),
        })
    return views


def load_custom_plots(path: str, plots_js: List[Dict],
                      sources: Optional[List[Dict]] = None) -> List[Dict]:
    """Load a custom_plots.json and resolve series to current plotIds.

    In comparison mode each series also carries a `source` (source id); labels
    are prefixed with the source label and event keys are `plotId@sourceId`.
    """
    # Build lookup: (group, metric, device, rank) -> plotId
    lookup = {(p["group"], p["metric"], p["device"], p["rank"]): p["id"] for p in plots_js}
    compare_mode = bool(sources) and len(sources) > 1
    source_labels = {s["id"]: s["label"] for s in (sources or [])}

    def _label(s, source_id):
        rank_str = f" (rank {s['rank']})" if s.get("rank") not in (None, "none") else ""
        prefix = f"{source_labels.get(source_id, source_id)} · " if compare_mode else ""
        return f"{prefix}{s['device']}{rank_str} · {s['metric']}"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = []
    for cp in data.get("custom_plots", []):
        entry: Dict[str, Any] = {
            "unit": None, "title": cp.get("title", ""), "series": [], "eventSeries": [],
        }
        for s in cp.get("series", []):
            key = (s.get("group", ""), s.get("metric", ""), s.get("device", ""), s.get("rank") or "none")
            plot_id = lookup.get(key)
            if not plot_id:
                print(f"Warning: series not found in data: {key}, skipping.")
                continue
            if entry["unit"] is None:
                entry["unit"] = next(p["unit"] for p in plots_js if p["id"] == plot_id)
            source_id = s.get("source", "s0")
            entry["series"].append({
                "plotId": plot_id,
                "sourceId": source_id,
                "color": s.get("color", "#6081ff"),
                "label": _label(s, source_id),
            })
        if not entry["series"]:
            continue
        for es in cp.get("event_series", []):
            key = (es.get("group", ""), es.get("metric", ""), es.get("device", ""), es.get("rank") or "none")
            plot_id = lookup.get(key)
            if plot_id:
                entry["eventSeries"].append(f"{plot_id}@{es.get('source', 's0')}")
        result.append(entry)
    return result


_CSS = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #f0f4f8;
  color: #1e293b;
  font-size: 14px;
  line-height: 1.5;
}
.app { display: flex; min-height: 100vh; }

/* ── Sidebar ── */
.sidebar {
  width: 230px;
  min-width: 230px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.sidebar-filters {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 0.875rem 0.5rem;
  min-height: 0;
}
.sidebar-logo {
  flex-shrink: 0;
  padding: 0.75rem 0.875rem 0.875rem;
  border-top: 1px solid #f1f5f9;
}
.sidebar-logo svg {
  width: 100%;
  height: auto;
  display: block;
}
.sidebar-heading {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: #94a3b8;
  margin-bottom: 1rem;
}
.sidebar-filters.filters-disabled { opacity: 0.45; pointer-events: none; }
.sidebar-filters.filters-disabled > .sidebar-heading::after {
  content: ' — inactive on this tab';
  font-weight: 400; text-transform: none; letter-spacing: normal; color: #94a3b8;
}
.filter-group {
  margin-bottom: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
  overflow: hidden;
}
.filter-group > summary {
  list-style: none;
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  padding: 0.5rem 0.75rem;
  background: #f8fafc;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  user-select: none;
}
.filter-group > summary::-webkit-details-marker { display: none; }
.filter-group > summary::before {
  content: "▸";
  font-size: 0.6rem;
  color: #94a3b8;
  transition: transform 0.15s;
  flex-shrink: 0;
}
.filter-group[open] > summary::before { transform: rotate(90deg); }
/* Per-rank device sub-group (MPI: device ids are not unique across ranks). */
.device-rank-group { border-top: 1px solid #f1f5f9; }
.device-rank-group:first-child { border-top: none; }
.device-rank-group > summary {
  list-style: none;
  cursor: pointer;
  font-size: 0.8rem;
  color: #374151;
  padding: 0.32rem 0.75rem 0.32rem 0.6rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  user-select: none;
}
.device-rank-group > summary::-webkit-details-marker { display: none; }
.device-rank-group > summary::after {
  content: "▸";
  font-size: 0.55rem;
  color: #cbd5e1;
  transition: transform 0.15s;
  margin-left: auto;
  flex-shrink: 0;
}
.device-rank-group[open] > summary::after { transform: rotate(90deg); }
.device-rank-toggle {
  margin-top: 0;
  accent-color: #3b82f6;
  cursor: pointer;
  flex-shrink: 0;
}
.device-rank-group .filter-items { padding-left: 1.1rem; }
/* Per-group metric sub-group: an expandable group whose summary carries a
   parent checkbox that toggles all of the group's individual metrics. */
.metric-group-filter { border-top: 1px solid #f1f5f9; }
.metric-group-filter:first-child { border-top: none; }
.metric-group-filter > summary {
  list-style: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.32rem 0.75rem 0.32rem 0.6rem;
  user-select: none;
}
.metric-group-filter > summary::-webkit-details-marker { display: none; }
.metric-group-filter > summary::after {
  content: "▸";
  font-size: 0.55rem;
  color: #cbd5e1;
  transition: transform 0.15s;
  margin-left: auto;
  flex-shrink: 0;
}
.metric-group-filter[open] > summary::after { transform: rotate(90deg); }
.metric-group-filter > summary > span {
  font-size: 0.8rem;
  color: #374151;
  word-break: break-all;
}
.metric-group-toggle {
  margin-top: 0;
  accent-color: #3b82f6;
  cursor: pointer;
  flex-shrink: 0;
}
.metric-group-filter .filter-items { padding-left: 1.55rem; }
.filter-items { padding: 0.4rem 0.6rem 0.1rem; }
.filter-item {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  padding: 0.18rem 0;
  cursor: pointer;
}
.filter-item input[type=checkbox] {
  margin-top: 2px;
  accent-color: #3b82f6;
  cursor: pointer;
  flex-shrink: 0;
}
.filter-item span {
  font-size: 0.8rem;
  color: #374151;
  word-break: break-all;
}
.toggle-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.3rem 0.6rem 0.4rem;
  border-top: 1px solid #f1f5f9;
}
.toggle-btn {
  font-size: 0.7rem;
  color: #94a3b8;
  cursor: pointer;
  background: none;
  border: none;
  padding: 0;
  text-decoration: underline;
}
.toggle-btn:hover { color: #64748b; }

/* ── Main ── */
.main { flex: 1; padding: 1.75rem 2rem; min-width: 0; }
.report-header { margin-bottom: 1.75rem; }
.report-title { font-size: 1.45rem; font-weight: 700; color: #0f172a; }
.report-subtitle { font-size: 0.8rem; color: #94a3b8; margin-top: 0.3rem; }

/* ── Sampler sections ── */
.sampler-section { margin-bottom: 2.5rem; }
.sampler-section.hidden { display: none; }

.sampler-header {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem 1.2rem;
  margin-bottom: 0.75rem;
}
.sampler-title {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.35rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.run-badge {
  font-size: 0.7rem;
  font-weight: 600;
  background: #e0f2fe;
  color: #0284c7;
  border-radius: 4px;
  padding: 1px 6px;
}
.sampler-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
  font-size: 0.8rem;
  color: #64748b;
}
.sampler-meta-row b { color: #334155; }

details.static-info { margin-top: 0.55rem; }
details.static-info > summary {
  list-style: none;
  cursor: pointer;
  font-size: 0.77rem;
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  user-select: none;
}
details.static-info > summary::-webkit-details-marker { display: none; }
details.static-info > summary::before {
  content: "▸";
  font-size: 0.6rem;
  transition: transform 0.15s;
}
details.static-info[open] > summary::before { transform: rotate(90deg); }
.info-grid {
  display: grid;
  grid-template-columns: minmax(130px, auto) 1fr;
  gap: 0.12rem 1rem;
  margin-top: 0.5rem;
  font-size: 0.77rem;
  max-width: 760px;
}
.info-grid dt { color: #94a3b8; font-weight: 500; padding-right: 0.25rem; }
.info-grid dd { color: #334155; word-break: break-word; }

/* ── Plot grid ── */
.plots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
  gap: 0.75rem;
}
.plot-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.5rem 0.5rem 0.15rem;
  transition: box-shadow 0.2s;
}
.plot-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.07); }
.plot-card.hidden { display: none !important; }
.custom-plot-card.hidden { display: none !important; }
/* Pin the overview plot height to the figure's layout height (build_figure: height=315).
   A fixed container height keeps Plotly.Plots.resize() stable; without it, repeated
   resize/re-render cycles read clientHeight from the content and the plot creeps taller. */
.plot-div { height: 315px; }

/* ── No time-series message ── */
.no-ts-msg {
  font-size: 0.82rem;
  color: #94a3b8;
  font-style: italic;
  padding: 0.25rem 0 0.5rem;
}

/* ── No-results ── */
.no-results {
  display: none;
  text-align: center;
  padding: 4rem 2rem;
  color: #94a3b8;
  font-size: 1rem;
}
.no-results.visible { display: block; }

/* ── Responsive ── */
@media (max-width: 640px) {
  .app { flex-direction: column; }
  .sidebar {
    width: 100%;
    min-width: 0;
    height: auto;
    position: static;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
  }
  .main { padding: 1rem; }
  .plots-grid { grid-template-columns: 1fr; }
}

/* ── View tab bar ── */
.view-tabs {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}
.view-tab {
  padding: 0.3rem 0.85rem;
  font-size: 0.8rem;
  font-family: inherit;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  background: #fff;
  color: #475569;
  transition: background 0.12s, color 0.12s;
}
.view-tab:hover { background: #f1f5f9; }
.view-tab.active { background: #6081ff; color: #fff; border-color: #6081ff; }

/* ── Group-mode sections ── */
.view-group-section { margin-bottom: 2rem; }
.view-group-title {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.75rem;
  padding-bottom: 0.35rem;
  border-bottom: 2px solid #e2e8f0;
}
/* Nested (inner) section titles */
.view-group-section .view-group-section { margin-bottom: 1.25rem; }
.view-group-section .view-group-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: #475569;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 0.5rem;
}
/* Third nesting level */
.view-group-section .view-group-section .view-group-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: #64748b;
  border-bottom: 1px dashed #f1f5f9;
}
/* Collapsible summary titles */
summary.view-group-title {
  list-style: none;
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
summary.view-group-title::-webkit-details-marker { display: none; }
summary.view-group-title::before {
  content: "▸";
  font-size: 0.6rem;
  color: #94a3b8;
  flex-shrink: 0;
  transition: transform 0.15s;
}
details[open] > summary.view-group-title::before { transform: rotate(90deg); }

/* ── Device badge (injected in group mode) ── */
.view-device-badge {
  font-size: 0.7rem;
  color: #6081ff;
  font-weight: 600;
  padding: 0.15rem 0.5rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Expand button (appears on card hover) ── */
.plot-card { position: relative; }
/* Shift mode bar left so it clears the expand button in the top-right corner */
.plot-card .modebar-container { right: 34px !important; }
.expand-btn {
  position: absolute;
  top: 0.45rem; right: 0.45rem;
  opacity: 1;
  transition: opacity 0.15s;
  background: rgba(255,255,255,0.85);
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  padding: 3px 5px;
  cursor: pointer;
  color: #64748b;
  line-height: 1;
  z-index: 1;
}
.expand-btn:hover { background: #fff; color: #0f172a; border-color: #94a3b8; }

/* ── Modal overlay ── */
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  z-index: 1000;
  align-items: center;
  justify-content: center;
}
.modal-overlay.open { display: flex; }
.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 92vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.4);
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
#modal-title { font-size: 0.9rem; font-weight: 600; color: #0f172a; }
#modal-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.25rem;
  color: #64748b;
  padding: 0.2rem 0.4rem;
  line-height: 1;
  border-radius: 4px;
  flex-shrink: 0;
}
#modal-close:hover { background: #f1f5f9; color: #0f172a; }
.modal-body { flex: 1; overflow-y: auto; min-height: 0; }
#modal-plot { display: block; }

/* ── Touchscreen-demo "feature disabled" popup ── */
.demo-modal-content { width: auto; max-width: 420px; }
.demo-modal-body { padding: 1.1rem 1.25rem 1.4rem; font-size: 0.88rem; line-height: 1.5; color: #374151; }

/* ── Custom plot builder ── */
.custom-view-toolbar { margin-bottom: 1rem; display: flex; align-items: center; gap: 0.6rem; }
.new-plot-btn {
  padding: 0.4rem 1rem; font-size: 0.82rem; font-family: inherit;
  background: #6081ff; color: #fff; border: none; border-radius: 6px; cursor: pointer;
}
.new-plot-btn:hover { background: #4f6de8; }
.toolbar-secondary-btn {
  padding: 0.4rem 0.9rem; font-size: 0.82rem; font-family: inherit; line-height: 1.25;
  background: #fff; color: #475569; border: 1px solid #e2e8f0;
  border-radius: 6px; cursor: pointer; user-select: none;
  display: inline-flex; align-items: center;
}
.toolbar-secondary-btn:hover:not(:disabled) { background: #f1f5f9; border-color: #cbd5e1; }
.toolbar-secondary-btn:disabled { opacity: 0.4; cursor: default; }
.custom-plot-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 0.75rem 0.75rem 0.35rem;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.custom-plot-header { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.custom-plot-title-input {
  font-size: 0.9rem; font-weight: 600; color: #0f172a; flex: 1; min-width: 0;
  border: none; background: transparent; outline: none; font-family: inherit;
  border-bottom: 1px solid transparent; padding: 1px 2px; transition: border-color 0.15s;
}
.custom-plot-title-input:focus { border-bottom-color: #6081ff; }
.custom-plot-title-input::placeholder { color: #94a3b8; font-weight: 400; }
.custom-plot-unit-badge {
  font-size: 0.72rem; background: #e0f2fe; color: #0284c7;
  border-radius: 4px; padding: 1px 6px;
}
.custom-delete-btn {
  background: none; border: none; cursor: pointer; color: #94a3b8;
  font-size: 1rem; line-height: 1; padding: 2px 5px; border-radius: 4px;
}
.custom-delete-btn:hover { color: #ef4444; background: #fef2f2; }
.series-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; min-height: 1.4rem; }
.series-chip {
  display: flex; align-items: center; gap: 0.3rem;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 99px; padding: 0.15rem 0.5rem;
  font-size: 0.75rem; color: #374151; max-width: 100%;
}
.series-chip-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.series-chip-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.series-chip-remove {
  background: none; border: none; cursor: pointer; color: #94a3b8;
  font-size: 0.9rem; line-height: 1; padding: 0 2px; flex-shrink: 0;
}
.series-chip-remove:hover { color: #ef4444; }
.add-series-btn {
  font-size: 0.77rem; padding: 0.25rem 0.6rem; border-radius: 5px;
  border: 1px dashed #cbd5e1; background: none; cursor: pointer; color: #64748b;
  align-self: flex-start;
}
.add-series-btn:hover { background: #f1f5f9; border-color: #94a3b8; }
.series-picker {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 0.65rem 0.75rem; display: flex; flex-direction: column; gap: 0.45rem;
}
.series-picker-label { font-size: 0.78rem; color: #475569; font-weight: 500; margin-bottom: -0.15rem; }
.series-picker select {
  width: 100%; font-size: 0.8rem; padding: 0.28rem 0.35rem;
  border: 1px solid #cbd5e1; border-radius: 5px; background: #fff; color: #1e293b;
}
.series-picker-actions { display: flex; gap: 0.5rem; margin-top: 0.1rem; }
.picker-add-btn {
  font-size: 0.78rem; padding: 0.28rem 0.8rem; background: #6081ff;
  color: #fff; border: none; border-radius: 5px; cursor: pointer;
}
.picker-add-btn:hover { background: #4f6de8; }
.picker-add-btn:disabled { background: #cbd5e1; cursor: default; }
.picker-cancel-btn {
  font-size: 0.78rem; padding: 0.28rem 0.75rem; background: none;
  border: 1px solid #e2e8f0; border-radius: 5px; cursor: pointer; color: #64748b;
}
.picker-cancel-btn:hover { background: #f1f5f9; }
.series-device-list {
  max-height: 110px; overflow-y: auto;
  border: 1px solid #cbd5e1; border-radius: 5px; background: #fff;
}
.series-device-option {
  padding: 0.28rem 0.6rem; font-size: 0.8rem; cursor: pointer; color: #374151;
  user-select: none;
}
.series-device-option:hover { background: #f1f5f9; }
.series-device-option.selected { background: #eff6ff; color: #2563eb; font-weight: 500; }
.series-preview-area { display: none; flex-direction: column; gap: 0.15rem; }
.series-preview-label {
  font-size: 0.68rem; color: #94a3b8; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.08em;
}
.series-preview-plot { height: 140px; border-radius: 4px; overflow: hidden; }
.custom-events-section { display: flex; flex-direction: column; gap: 0.25rem; }
.custom-events-header {
  font-size: 0.7rem; color: #94a3b8; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.07em;
}
.custom-events-items { display: flex; flex-wrap: wrap; gap: 0.15rem 0.9rem; }
.custom-events-item {
  display: flex; align-items: center; gap: 0.35rem;
  font-size: 0.77rem; color: #374151; cursor: pointer;
}
.custom-events-item input[type=checkbox] {
  accent-color: #6081ff; cursor: pointer; flex-shrink: 0; margin-top: 1px;
}
.custom-plot-empty {
  font-size: 0.82rem; color: #94a3b8; font-style: italic;
  padding: 2rem 0; text-align: center;
}
.custom-plot-div { min-height: 315px; }
/* Custom expand button: always visible (no hover needed) */
.custom-plot-card .expand-btn { opacity: 0.6; position: static; }
.custom-plot-card .expand-btn:hover { opacity: 1; }

/* ── Download format picker ── */
.dl-menu {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.12);
  overflow: hidden;
  min-width: 72px;
}
.dl-item {
  display: block;
  width: 100%;
  padding: 0.42rem 0.85rem;
  font-size: 0.82rem;
  font-family: inherit;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  color: #374151;
}
.dl-item:hover { background: #f1f5f9; }
.dl-menu hr { border: none; border-top: 1px solid #e2e8f0; margin: 2px 0; }
.src-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 5px; flex-shrink: 0; }
.event-control { margin-top: 0.6rem; padding-top: 0.6rem; border-top: 1px solid #e2e8f0; }
.event-control .sidebar-heading { margin-bottom: 0.35rem; }

/* ── Energy Dashboard ── */
.energy-dashboard-container { display: flex; flex-direction: column; gap: 1.5rem; }
.energy-kpi-row { display: flex; gap: 1rem; flex-wrap: wrap; }
.tab-spacer { flex: 1; min-width: 0.5rem; pointer-events: none; }
.energy-kpi-tile {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 1rem 1.5rem; flex: 1; min-width: 160px;
}
.energy-kpi-tile--tip { cursor: help; position: relative; }
.energy-kpi-tile--tip::after {
  content: attr(data-tip);
  position: absolute;
  top: calc(100% + 10px); left: 50%; transform: translateX(-50%);
  background: #1e293b; color: #f8fafc;
  font-size: 0.7rem; line-height: 1.5; padding: 0.45rem 0.7rem;
  border-radius: 6px; width: max-content; max-width: 260px;
  white-space: normal; text-align: left;
  pointer-events: none; opacity: 0; transition: opacity 0.12s;
  z-index: 200; box-shadow: 0 4px 14px rgba(0,0,0,0.25);
}
.energy-kpi-tile--tip::before {
  content: '';
  position: absolute;
  top: calc(100% + 4px); left: 50%; transform: translateX(-50%);
  border: 6px solid transparent; border-bottom-color: #1e293b;
  pointer-events: none; opacity: 0; transition: opacity 0.12s; z-index: 201;
}
.energy-kpi-tile--tip:hover::after,
.energy-kpi-tile--tip:hover::before { opacity: 1; }
.energy-kpi-value { font-size: 1.8rem; font-weight: 700; color: #0f172a; line-height: 1.1; }
.energy-kpi-unit { font-size: 0.85rem; color: #64748b; font-weight: 400; }
.energy-kpi-label {
  font-size: 0.75rem; color: #94a3b8; margin-top: 0.35rem;
  text-transform: uppercase; letter-spacing: 0.07em;
}
.energy-kpi-source-col {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 0.75rem 1rem; flex: 1; min-width: 200px;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.energy-kpi-source-col .energy-kpi-tile {
  background: #f8fafc; border-color: #f1f5f9; padding: 0.6rem 0.75rem;
}
.energy-kpi-source-label {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.07em; padding-bottom: 0.4rem; border-bottom: 2px solid;
  margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.3rem;
}
.energy-section-title { font-size: 0.9rem; font-weight: 600; color: #0f172a; margin-bottom: 0.6rem; }
.energy-chart-block {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 1rem 0.75rem 0.25rem;
  overflow: hidden;
}
.energy-plot-div { width: 100%; }
"""

_JS_TEMPLATE = """\
(function () {
  var PLOTS = __PLOTS_JSON__;
  var VIEWS = __VIEWS_JSON__;
  var SOURCES = __SOURCES_JSON__;
  var COMPARE_MODE = __COMPARE_MODE__;
  var _sourceById = {};
  SOURCES.forEach(function(s) { _sourceById[s.id] = s; });
  var _activeViewIdx = 0;
  var _cardHome = {};
  var _expandSvg = __EXPAND_SVG_JSON__;
  var _customPlots = __CUSTOM_PLOTS_JSON__;
  var _CUSTOM_COLORS = ['#6081ff','#f97316','#22c55e','#a855f7','#ef4444','#0ea5e9','#eab308','#ec4899'];
  var _seriesByUnit = {};
  // devkey -> {label, rank}. devkey is the composite (rank, device) filter key;
  // device ids are not unique across MPI ranks, so grouping/labels key on it.
  var _devkeyInfo = {};

  var _dlIcon = {
    width: 1000, height: 1000,
    path: 'M500,750 L500,350 M250,500 L500,300 L750,500 M100,50 L900,50',
    transform: 'matrix(1 0 0 -1 0 1000)',
  };

  function _showDlMenu(gd) {
    var prev = document.getElementById('_dl_menu');
    if (prev) { prev.remove(); if (prev._gd === gd) return; }
    var rect = gd.getBoundingClientRect();
    var menu = document.createElement('div');
    menu.id = '_dl_menu';
    menu._gd = gd;
    menu.className = 'dl-menu';
    menu.style.cssText = 'position:fixed;z-index:9999;top:' +
      (rect.top + 36) + 'px;right:' + (window.innerWidth - rect.right + 2) + 'px;';
    ['PNG', 'SVG'].forEach(function(fmt) {
      var btn = document.createElement('button');
      btn.className = 'dl-item';
      btn.textContent = fmt;
      btn.onclick = function(e) {
        e.stopPropagation();
        menu.remove();
        openDemoModal(_DEMO_MSG);  // touchscreen-demo: downloads disabled
      };
      menu.appendChild(btn);
    });
    var pdfBtn = document.createElement('button');
    pdfBtn.className = 'dl-item';
    pdfBtn.textContent = 'PDF';
    pdfBtn.onclick = function(e) {
      e.stopPropagation();
      menu.remove();
      openDemoModal(_DEMO_MSG);  // touchscreen-demo: downloads disabled
    };
    menu.appendChild(pdfBtn);
    var isEnergyPlot = gd.classList && gd.classList.contains('energy-plot-div');
    if (!isEnergyPlot) {
      var sep = document.createElement('hr');
      menu.appendChild(sep);
      var dataBtn = document.createElement('button');
      dataBtn.className = 'dl-item';
      dataBtn.textContent = 'Data (JSON)';
      dataBtn.onclick = function(e) {
        e.stopPropagation();
        menu.remove();
        openDemoModal(_DEMO_MSG);  // touchscreen-demo: downloads disabled
      };
      menu.appendChild(dataBtn);
    }
    document.body.appendChild(menu);
    setTimeout(function() {
      function handler(e) {
        if (!menu.contains(e.target)) { menu.remove(); document.removeEventListener('click', handler); }
      }
      document.addEventListener('click', handler);
    }, 0);
  }

  function _exportPlotData(gd) {
    if (!gd._fullLayout) return;
    var xLayout = gd._fullLayout.xaxis;
    var yLayout = gd._fullLayout.yaxis;
    var isXZoomed = xLayout && xLayout.autorange === false;
    var isYZoomed = yLayout && yLayout.autorange === false;
    var xRange = (isXZoomed && xLayout) ? xLayout.range : null;
    var yRange = (isYZoomed && yLayout) ? yLayout.range : null;

    function filterXY(xArr, yArr) {
      if (!xRange && !yRange) return { x: xArr.slice(), y: yArr.slice() };
      var fx = [], fy = [];
      for (var i = 0; i < xArr.length; i++) {
        var xOk = !xRange || (xArr[i] >= xRange[0] && xArr[i] <= xRange[1]);
        var yOk = !yRange || (yArr[i] >= yRange[0] && yArr[i] <= yRange[1]);
        if (xOk && yOk) { fx.push(xArr[i]); fy.push(yArr[i]); }
      }
      return { x: fx, y: fy };
    }
    function filterEvents(evts) {
      if (!evts) return [];
      return evts.filter(function(ev) {
        return !xRange || (ev[0] >= xRange[0] && ev[0] <= xRange[1]);
      }).map(function(ev) { return { x: ev[0], label: ev[1] }; });
    }
    function getAxisLabel(titleField) {
      if (!titleField) return '';
      return typeof titleField === 'string' ? titleField : (titleField.text || '');
    }
    function sanitize(s) { return (s || '').replace(/[^\\w-]/g, '_').replace(/_+/g, '_'); }

    var source;
    if (gd.id === 'modal-plot') {
      source = gd._exportSource;
    } else {
      var customCard = gd.closest && gd.closest('.custom-plot-card');
      source = customCard
        ? { type: 'custom', idx: parseInt(customCard.dataset.customIdx, 10) }
        : { type: 'regular', plotId: gd.id };
    }
    if (!source) return;

    var out = { format_version: '1.0' };
    var filename;

    if (source.type === 'regular') {
      var p = plotMap[source.plotId];
      if (!p) return;
      out.meta = { device: p.device, rank: p.rank, group: p.group, metric: p.metric };
      out.x_axis = { label: getAxisLabel(p.layout && p.layout.xaxis && p.layout.xaxis.title) };
      out.y_axis = { label: getAxisLabel(p.layout && p.layout.yaxis && p.layout.yaxis.title) };
      if (COMPARE_MODE && p.sources) {
        // Each visible source becomes one series of the overlay.
        out.type = 'overlay';
        out.title = p.label;
        var checkedSrc = getChecked('source');
        var evSel = getChecked('eventsrc');
        out.series = [];
        p.sources.forEach(function(sid, i) {
          if (!checkedSrc.has(sid)) return;
          var tr = p.data[i];
          var sLabel = _sourceLabel(sid);
          out.series.push({
            label: sLabel,
            meta: { source: sLabel, device: p.device, rank: p.rank, group: p.group, metric: p.metric },
            data: filterXY(tr.x, tr.y),
            events: evSel.has(sid) ? filterEvents((p.eventsBySource || {})[sid] || []) : [],
          });
        });
      } else {
        var trace = p.data[0];
        out.type = 'single';
        out.title = p.label;
        out.data = filterXY(trace.x, trace.y);
        out.events = filterEvents(p.events);
      }
      filename = sanitize(p.device + '_' + p.metric) + '.json';
    } else if (source.type === 'custom') {
      var cp = _customPlots[source.idx];
      if (!cp || cp.series.length === 0) return;
      var fp = plotMap[cp.series[0].plotId];
      out.type = 'overlay';
      out.title = cp.title || ('Custom Plot ' + (source.idx + 1));
      out.x_axis = { label: getAxisLabel(fp && fp.layout && fp.layout.xaxis && fp.layout.xaxis.title) };
      out.y_axis = { label: cp.unit || '' };
      out.series = cp.series.map(function(s) {
        var sp = plotMap[s.plotId];
        if (!sp) return null;
        var t = _traceForSeries(sp, s);
        var hasEvents = cp.eventSeries && cp.eventSeries.indexOf(_seriesKey(s)) >= 0;
        var meta = { device: sp.device, rank: sp.rank, group: sp.group, metric: sp.metric };
        if (COMPARE_MODE) meta.source = _sourceLabel(s.sourceId);
        return {
          label: s.label,
          meta: meta,
          data: filterXY(t.x, t.y),
          events: hasEvents ? filterEvents(_eventsForSeries(sp, s)) : [],
        };
      }).filter(function(x) { return x; });
      filename = sanitize(cp.title || 'custom_plot') + '.json';
    } else {
      return;
    }

    out.view = {
      x_range: xRange ? [xRange[0], xRange[1]] : null,
      y_range: yRange ? [yRange[0], yRange[1]] : null,
      zoomed: !!(xRange || yRange),
    };

    var blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  var _dlBtn = {
    name: 'Download (PNG / SVG / PDF / Data)',
    icon: _dlIcon,
    click: _showDlMenu,
  };

  var _dlBtnNoData = {
    name: 'Download (PNG / SVG / PDF)',
    icon: _dlIcon,
    click: _showDlMenu,
  };

  document.querySelectorAll('.plot-card').forEach(function(card) {
    var btn = card.querySelector('[data-plot-id]');
    if (btn) _cardHome[btn.dataset.plotId] = { parent: card.parentNode, next: card.nextSibling };
  });

  function _metricMatches(card, inclMetrics) {
    if (inclMetrics === 'all') return true;
    var g = card.dataset.group;
    var m = card.dataset.metric;
    for (var i = 0; i < inclMetrics.length; i++) {
      var spec = inclMetrics[i];
      if (spec === g) return true;
      if (spec === g + '.' + m) return true;
    }
    return false;
  }

  function _restoreToDevice() {
    // Reverse DOM order so that when we insert card X before h.next(X),
    // h.next(X) has already been restored to its original parent.
    // Forward order fails when multiple cards from the same grid are in a
    // view-group-section: inserting A before B throws if B is still in the
    // view-group-section rather than in A's original parent.
    var toRestore = Array.from(document.querySelectorAll('.view-group-section .plot-card'));
    toRestore.reverse().forEach(function(card) {
      var btn = card.querySelector('[data-plot-id]');
      var pid = btn && btn.dataset.plotId;
      if (pid && _cardHome[pid]) {
        var h = _cardHome[pid];
        h.parent.insertBefore(card, h.next);
      }
      var badge = card.querySelector('.view-device-badge');
      if (badge) badge.remove();
    });
    document.querySelectorAll('.view-group-section').forEach(function(s) { s.remove(); });
    document.querySelectorAll('.sampler-section').forEach(function(s) { s.style.display = ''; });
  }

  function _getCardKey(card, level) {
    if (level === 'rank')   return card.dataset.rank;
    // Group on the composite devkey so same-named devices on different ranks are
    // never merged into one section.
    if (level === 'device') return card.dataset.devkey;
    if (level === 'group')  return card.dataset.group;
    return 'unknown';
  }

  function _getLevelTitle(level, key, rankGrouped) {
    if (level === 'rank') return key === 'none' ? 'All Devices' : 'Rank ' + key;
    if (level === 'device') {
      var info = _devkeyInfo[key];
      if (!info) return key;
      var t = info.label;
      if (!rankGrouped && info.rank && info.rank !== 'none') t += '  (rank ' + info.rank + ')';
      return t;
    }
    return key;
  }

  function _sortLevelKeys(keys, level) {
    if (level === 'rank') {
      return keys.sort(function(a, b) {
        if (a === 'none' && b === 'none') return 0;
        if (a === 'none') return -1;
        if (b === 'none') return 1;
        return parseInt(a) - parseInt(b);
      });
    }
    if (level === 'device') {
      // Sort by display label, then rank, so devices read alphabetically.
      return keys.sort(function(a, b) {
        var ia = _devkeyInfo[a] || {}, ib = _devkeyInfo[b] || {};
        var la = ia.label || a, lb = ib.label || b;
        if (la !== lb) return la < lb ? -1 : 1;
        return (parseInt(ia.rank) || 0) - (parseInt(ib.rank) || 0);
      });
    }
    return keys.sort();
  }

  // Recursively build nested .view-group-section DOM from a pre-filtered card list.
  // levels: array of level names e.g. ['rank', 'device', 'group']
  // container/refNode: insertion point (refNode may be null → appendChild)
  function _buildNestedSections(cards, levels, container, refNode, rankGrouped) {
    var level = levels[0];
    var restLevels = levels.slice(1);
    var isLeaf = restLevels.length === 0;

    var keyOrder = [];
    var byKey = {};
    cards.forEach(function(card) {
      var k = _getCardKey(card, level);
      if (!byKey[k]) { byKey[k] = []; keyOrder.push(k); }
      byKey[k].push(card);
    });
    _sortLevelKeys(keyOrder, level);

    keyOrder.forEach(function(k) {
      var sec = document.createElement('details');
      sec.className = 'view-group-section';
      sec.open = true;
      var titleEl = document.createElement('summary');
      titleEl.className = 'view-group-title';
      titleEl.textContent = _getLevelTitle(level, k, rankGrouped);
      sec.appendChild(titleEl);

      if (isLeaf) {
        var showBadge = level !== 'device';
        var grid = document.createElement('div');
        grid.className = 'plots-grid';
        byKey[k].forEach(function(card) {
          if (showBadge && !card.querySelector('.view-device-badge')) {
            var badge = document.createElement('div');
            badge.className = 'view-device-badge';
            var bl = card.dataset.deviceLabel || card.dataset.device;
            // Device ids are not unique across MPI ranks; disambiguate the badge
            // with the rank unless the view is already grouped by rank.
            if (!rankGrouped && card.dataset.rank && card.dataset.rank !== 'none') {
              bl += '  (rank ' + card.dataset.rank + ')';
            }
            badge.textContent = bl;
            card.insertBefore(badge, card.firstChild);
          }
          grid.appendChild(card);
        });
        sec.appendChild(grid);
      } else {
        _buildNestedSections(byKey[k], restLevels, sec, null, rankGrouped);
      }

      if (refNode) {
        container.insertBefore(sec, refNode);
      } else {
        container.appendChild(sec);
      }
    });
  }

  // ── Custom Plot Builder ──────────────────────────────────────────────

  // A custom-plot series identifies one curve: a plot card + a source file.
  function _seriesKey(s) { return s.plotId + '@' + (s.sourceId || 's0'); }

  // The Plotly trace for a given series (the source-indexed trace in compare
  // mode, or the single trace in single-file mode).
  function _traceForSeries(p, s) {
    var i = 0;
    if (p.sources && s && s.sourceId) {
      var k = p.sources.indexOf(s.sourceId);
      if (k >= 0) i = k;
    }
    return p.data[i] || p.data[0];
  }

  // Events for a given series' source. Single-file plots carry a flat `events`
  // array; compare plots carry `eventsBySource`.
  function _eventsForSeries(p, s) {
    if (p.eventsBySource) return p.eventsBySource[(s && s.sourceId) || 's0'] || [];
    return p.events || [];
  }

  // Build unit catalog from PLOTS metadata (populated once after PLOTS is available)
  function _initSeriesCatalog() {
    PLOTS.forEach(function(p) {
      var u = p.unit !== undefined ? p.unit : '';
      if (!_seriesByUnit[u]) _seriesByUnit[u] = [];
      _seriesByUnit[u].push(p);
      if (p.devkey && !_devkeyInfo[p.devkey]) {
        _devkeyInfo[p.devkey] = { label: p.device, rank: p.rank };
      }
    });
  }

  function _buildEventAnnotations(idx) {
    var cp = _customPlots[idx];
    if (!cp.eventSeries || cp.eventSeries.length === 0) return { shapes: [], annotations: [] };
    // Map seriesKey → series object
    var byKey = {};
    cp.series.forEach(function(s) { byKey[_seriesKey(s)] = s; });
    // Collect events as [t, name, color]
    var allEvents = [];
    cp.eventSeries.forEach(function(key) {
      var s = byKey[key];
      if (!s) return;
      var p = plotMap[s.plotId];
      if (!p) return;
      var color = s.color || '#6081ff';
      _eventsForSeries(p, s).forEach(function(ev) { allEvents.push([ev[0], ev[1], color]); });
    });
    if (allEvents.length === 0) return { shapes: [], annotations: [] };
    var tMin = Infinity, tMax = -Infinity;
    cp.series.forEach(function(s) {
      var src = plotMap[s.plotId];
      var tr = src ? _traceForSeries(src, s) : null;
      if (tr && tr.x && tr.x.length) {
        tMin = Math.min(tMin, tr.x[0]);
        tMax = Math.max(tMax, tr.x[tr.x.length - 1]);
      }
    });
    if (!isFinite(tMin)) { tMin = 0; tMax = 1; }
    // Inline stagger — same algorithm as Python _stagger_events, carrying color through
    var LEVELS = [0.97, 0.82, 0.67, 0.52];
    var threshold = ((tMax - tMin) || 1.0) * 0.06;
    var lastT = {};
    var shapes = [], annotations = [];
    allEvents.slice().sort(function(a, b) { return a[0] - b[0]; }).forEach(function(ev) {
      var t = ev[0], name = ev[1], color = ev[2], chosen = 0;
      for (var li = 0; li < LEVELS.length; li++) {
        if (t - (lastT[li] !== undefined ? lastT[li] : -1e18) >= threshold) { chosen = li; break; }
      }
      lastT[chosen] = t;
      var yPaper = LEVELS[chosen];
      shapes.push({ type: 'line', x0: t, x1: t, xref: 'x', yref: 'paper',
        y0: 0, y1: 1, line: { dash: 'dot', color: color, width: 1.5 } });
      annotations.push({ x: t, y: yPaper, xref: 'x', yref: 'paper',
        text: String(name), showarrow: false,
        font: { size: 10, color: color },
        xanchor: 'left', yanchor: 'top', textangle: -90,
        bgcolor: 'rgba(255,255,255,0.72)', borderpad: 2 });
    });
    return { shapes: shapes, annotations: annotations };
  }

  function _buildCustomTraces(idx) {
    return _customPlots[idx].series.map(function(s) {
      var src = plotMap[s.plotId];
      var t = Object.assign({}, _traceForSeries(src, s));
      t.line       = Object.assign({}, t.line,   { color: s.color });
      t.marker     = Object.assign({}, t.marker, { color: s.color });
      t.hoverlabel = { bgcolor: s.color, bordercolor: s.color, font: { color: '#ffffff' } };
      t.name       = s.label;
      t.showlegend = true;
      return t;
    });
  }

  function _buildCustomLayout(idx) {
    var cp = _customPlots[idx];
    var ev = _buildEventAnnotations(idx);
    // Derive time unit from first series' x-axis layout (falls back to "s")
    var xLabel = 'Time [s]';
    if (cp.series.length > 0) {
      var fp = plotMap[cp.series[0].plotId];
      var xt = fp && fp.layout && fp.layout.xaxis && fp.layout.xaxis.title;
      if (xt) xLabel = typeof xt === 'string' ? xt : (xt.text || xLabel);
    }
    return {
      title: { text: cp.title || '', font: { size: 12 } },
      height: 315,
      margin: { l: 65, r: 20, t: 50, b: 80 },
      hovermode: 'closest',
      showlegend: true,
      legend: { orientation: 'h', y: -0.42, x: 0, xanchor: 'left', font: { size: 11 } },
      yaxis: { title: { text: cp.unit || '' } },
      xaxis: { title: { text: xLabel } },
      shapes: ev.shapes,
      annotations: ev.annotations,
    };
  }

  function _renderChips(idx, el) {
    el.innerHTML = '';
    _customPlots[idx].series.forEach(function(s, si) {
      var chip = document.createElement('span');
      chip.className = 'series-chip';
      var dot = document.createElement('span');
      dot.className = 'series-chip-dot';
      dot.style.background = s.color;
      chip.appendChild(dot);
      var lbl = document.createElement('span');
      lbl.className = 'series-chip-label';
      lbl.textContent = s.label;
      chip.appendChild(lbl);
      var rm = document.createElement('button');
      rm.className = 'series-chip-remove';
      rm.textContent = '×';
      rm.title = 'Remove series';
      rm.dataset.si = si;
      rm.dataset.idx = idx;
      rm.onclick = function() { _removeSeries(idx, si); };
      chip.appendChild(rm);
      el.appendChild(chip);
    });
  }

  function _refreshCustomCard(idx) {
    var cp = _customPlots[idx];
    var card = document.querySelector('.custom-plot-card[data-custom-idx="' + idx + '"]');
    if (!card) return;
    var badge = card.querySelector('.custom-plot-unit-badge');
    if (badge) {
      badge.style.display = cp.unit ? '' : 'none';
      badge.textContent = cp.unit ? 'Y: ' + cp.unit : '';
    }
    var chipsEl = card.querySelector('.series-chips');
    if (chipsEl) _renderChips(idx, chipsEl);
    var picker = card.querySelector('.series-picker');
    if (picker) picker.remove();

    // Update events selector
    var evSection = card.querySelector('.custom-events-section');
    if (evSection) {
      var evItems = evSection.querySelector('.custom-events-items');
      evItems.innerHTML = '';
      var hasAnyEvents = false;
      cp.series.forEach(function(s) {
        var p = plotMap[s.plotId];
        if (!p || _eventsForSeries(p, s).length === 0) return;
        hasAnyEvents = true;
        var lbl = document.createElement('label');
        lbl.className = 'custom-events-item';
        var cb = document.createElement('input');
        cb.type = 'checkbox';
        var skey = _seriesKey(s);
        cb.checked = cp.eventSeries.indexOf(skey) >= 0;
        (function(key, i, checkbox) {
          checkbox.onchange = function() {
            var pos = _customPlots[i].eventSeries.indexOf(key);
            if (checkbox.checked && pos < 0) _customPlots[i].eventSeries.push(key);
            if (!checkbox.checked && pos >= 0) _customPlots[i].eventSeries.splice(pos, 1);
            var pEl = document.querySelector('.custom-plot-card[data-custom-idx="' + i + '"] .custom-plot-div');
            if (pEl && pEl._fullLayout) _renderCustomPlotly(i, pEl);
          };
        })(skey, idx, cb);
        lbl.appendChild(cb);
        var nameEl = document.createElement('span');
        nameEl.textContent = s.label;
        lbl.appendChild(nameEl);
        evItems.appendChild(lbl);
      });
      evSection.style.display = hasAnyEvents ? '' : 'none';
    }

    var plotEl = card.querySelector('.custom-plot-div');
    var emptyEl = card.querySelector('.custom-plot-empty');
    if (cp.series.length > 0) {
      if (emptyEl) emptyEl.style.display = 'none';
      if (plotEl) { plotEl.style.display = ''; _renderCustomPlotly(idx, plotEl); }
    } else {
      if (plotEl) { plotEl.style.display = 'none'; if (plotEl._fullLayout) Plotly.purge(plotEl); }
      if (emptyEl) emptyEl.style.display = '';
    }
  }

  function _renderCustomPlotly(idx, el) {
    var traces = _buildCustomTraces(idx);
    var layout = _buildCustomLayout(idx);
    // Grow height + bottom margin together per extra legend row so the plot area
    // stays the same size. ~2 items fit per row for typical label lengths.
    var n = _customPlots[idx].series.length;
    var extraRows = Math.max(0, Math.ceil(n / 2) - 1);
    layout.height = 315 + extraRows * 24;
    layout.margin = { l: 65, r: 20, t: 50, b: 80 + extraRows * 24 };
    Plotly.react(el, traces, layout, {
      responsive: true, displayModeBar: true,
      modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toImage'],
      modeBarButtonsToAdd: [_dlBtn], displaylogo: false,
    });
  }

  function _openSeriesPicker(idx, card) {
    var existing = card.querySelector('.series-picker');
    if (existing) { existing.remove(); return; }
    var cp = _customPlots[idx];
    var lockedUnit = cp.unit;
    var selectedPlotId = null;
    var selectedSourceId = null;

    // Build map of "group.metric|||unit" -> {display, unit, metrickey, entries[]}
    var metricMap = {};
    PLOTS.forEach(function(p) {
      var key = p.group + '.' + p.metric + '|||' + (p.unit || '');
      if (!metricMap[key]) {
        metricMap[key] = {
          display: p.group + ' · ' + p.metric + (p.unit ? '  [' + p.unit + ']' : ''),
          unit: p.unit || '',
          metrickey: p.metrickey,
          entries: [],
        };
      }
      metricMap[key].entries.push(p);
    });

    var picker = document.createElement('div');
    picker.className = 'series-picker';

    var metricLabel = document.createElement('div');
    metricLabel.className = 'series-picker-label';
    metricLabel.textContent = 'Metric';
    picker.appendChild(metricLabel);
    var metricSel = document.createElement('select');

    // Sort: locked-unit options first, then others alphabetically
    var sortedKeys = Object.keys(metricMap).sort(function(a, b) {
      var ua = metricMap[a].unit, ub = metricMap[b].unit;
      if (lockedUnit) {
        if (ua === lockedUnit && ub !== lockedUnit) return -1;
        if (ub === lockedUnit && ua !== lockedUnit) return 1;
      }
      return metricMap[a].display < metricMap[b].display ? -1 : 1;
    });

    // (Re)build the metric dropdown, listing only metrics whose Metric Group
    // filter checkbox is currently checked. Preserves the current selection.
    function buildMetricOptions() {
      var fMetrics = getChecked('metric');
      var prev = metricSel.value;
      metricSel.innerHTML = '';
      var defOpt = document.createElement('option');
      defOpt.value = ''; defOpt.textContent = '— select metric —';
      defOpt.disabled = true;
      metricSel.appendChild(defOpt);

      var unitsSeen = [];
      var optsByUnit = {};
      var prevStillThere = false;
      sortedKeys.forEach(function(key) {
        if (!fMetrics.has(metricMap[key].metrickey)) return;
        if (key === prev) prevStillThere = true;
        var u = metricMap[key].unit;
        if (!optsByUnit[u]) { optsByUnit[u] = []; unitsSeen.push(u); }
        var opt = document.createElement('option');
        opt.value = key;
        opt.textContent = metricMap[key].display;
        if (lockedUnit && u !== lockedUnit) opt.disabled = true;
        optsByUnit[u].push(opt);
      });
      unitsSeen.forEach(function(u) {
        var grp = document.createElement('optgroup');
        grp.label = u ? '[' + u + ']' : '[no unit]';
        optsByUnit[u].forEach(function(opt) { grp.appendChild(opt); });
        metricSel.appendChild(grp);
      });
      metricSel.value = prevStillThere ? prev : '';
      if (!metricSel.value) defOpt.selected = true;
    }
    buildMetricOptions();
    metricSel._refreshOptions = buildMetricOptions;
    picker.appendChild(metricSel);

    var sourceLabel = document.createElement('div');
    sourceLabel.className = 'series-picker-label';
    sourceLabel.textContent = 'Source';
    picker.appendChild(sourceLabel);

    // Custom hoverable device list (replaces <select> for hover preview support)
    var deviceList = document.createElement('div');
    deviceList.className = 'series-device-list';
    picker.appendChild(deviceList);

    // Live preview chart area
    var previewArea = document.createElement('div');
    previewArea.className = 'series-preview-area';
    var previewLbl = document.createElement('div');
    previewLbl.className = 'series-preview-label';
    previewLbl.textContent = 'Preview';
    previewArea.appendChild(previewLbl);
    var previewPlotEl = document.createElement('div');
    previewPlotEl.className = 'series-preview-plot';
    previewArea.appendChild(previewPlotEl);
    picker.appendChild(previewArea);

    var actions = document.createElement('div');
    actions.className = 'series-picker-actions';
    var addBtn = document.createElement('button');
    addBtn.className = 'picker-add-btn';
    addBtn.textContent = 'Add';
    addBtn.disabled = true;
    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'picker-cancel-btn';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = function() {
      if (previewPlotEl._fullLayout) Plotly.purge(previewPlotEl);
      picker.remove();
    };
    actions.appendChild(addBtn);
    actions.appendChild(cancelBtn);
    picker.appendChild(actions);

    function _showPreview(plotId, sourceId) {
      var src = plotMap[plotId];
      if (!src) return;
      previewArea.style.display = 'flex';
      var previewColor = _nextUnusedColor(cp);
      var pt = Object.assign({}, _traceForSeries(src, { plotId: plotId, sourceId: sourceId }));
      pt.line       = Object.assign({}, pt.line,   { color: previewColor, width: 2 });
      pt.marker     = Object.assign({}, pt.marker, { color: previewColor, size: 3 });
      pt.showlegend = false;
      pt.hoverinfo  = 'none';
      var previewLayout = {
        height: 140,
        margin: { l: 42, r: 8, t: 6, b: 32 },
        showlegend: false,
        hovermode: false,
        xaxis: { tickfont: { size: 9 } },
        yaxis: { tickfont: { size: 9 }, title: { text: cp.unit || src.unit || '', font: { size: 9 } } },
        paper_bgcolor: '#f1f5f9',
        plot_bgcolor: '#f1f5f9',
      };
      Plotly.react(previewPlotEl, [pt], previewLayout, { responsive: false, displayModeBar: false });
    }

    function _populateDeviceList(key) {
      deviceList.innerHTML = '';
      selectedPlotId = null;
      selectedSourceId = null;
      addBtn.disabled = true;
      previewArea.style.display = 'none';
      if (previewPlotEl._fullLayout) Plotly.purge(previewPlotEl);
      if (!key || !metricMap[key]) return;
      var fDevices = getChecked('device');
      var fMetrics = getChecked('metric');
      var fSources = COMPARE_MODE ? getChecked('source') : null;
      metricMap[key].entries.forEach(function(p) {
        if (!fDevices.has(p.devkey) || !fMetrics.has(p.metrickey)) return;
        var srcList = (COMPARE_MODE && p.sources) ? p.sources : ['s0'];
        srcList.forEach(function(sid) {
          if (fSources && !fSources.has(sid)) return;
          var item = document.createElement('div');
          item.className = 'series-device-option';
          var rankStr = p.rank !== 'none' ? '  (rank ' + p.rank + ')' : '';
          var srcStr = COMPARE_MODE ? '  —  ' + _sourceLabel(sid) : '';
          item.textContent = p.device + rankStr + srcStr;
          item.addEventListener('mouseenter', function() { _showPreview(p.id, sid); });
          item.addEventListener('click', function() {
            deviceList.querySelectorAll('.series-device-option').forEach(function(o) {
              o.classList.remove('selected');
            });
            item.classList.add('selected');
            selectedPlotId = p.id;
            selectedSourceId = sid;
            addBtn.disabled = false;
            _showPreview(p.id, sid);
          });
          deviceList.appendChild(item);
        });
      });
      if (deviceList.children.length === 0) {
        var msg = document.createElement('div');
        msg.style.cssText = 'padding:0.35rem 0.6rem;font-size:0.78rem;color:#94a3b8;font-style:italic;';
        msg.textContent = 'No sources match current filters';
        deviceList.appendChild(msg);
      }
    }

    metricSel.addEventListener('change', function() {
      _populateDeviceList(metricSel.value);
    });

    addBtn.onclick = function() {
      if (selectedPlotId) {
        if (previewPlotEl._fullLayout) Plotly.purge(previewPlotEl);
        _addSeries(idx, selectedPlotId, selectedSourceId);
      }
    };

    var plotEl = card.querySelector('.custom-plot-div');
    card.insertBefore(picker, plotEl || null);
  }

  function _resolveSeriesId(group, metric, device, rank) {
    for (var i = 0; i < PLOTS.length; i++) {
      var p = PLOTS[i];
      if (p.group === group && p.metric === metric &&
          p.device === device && p.rank === String(rank)) return p.id;
    }
    return null;
  }

  function _updateExportBtnState() {
    var btn = document.querySelector('.custom-export-btn');
    if (btn) btn.disabled = _customPlots.length === 0;
  }

  function _nextUnusedColor(cp) {
    var used = cp.series.map(function(s) { return s.color; });
    for (var i = 0; i < _CUSTOM_COLORS.length; i++) {
      if (used.indexOf(_CUSTOM_COLORS[i]) < 0) return _CUSTOM_COLORS[i];
    }
    return _CUSTOM_COLORS[cp.series.length % _CUSTOM_COLORS.length];
  }

  function _sourceLabel(sourceId) {
    var s = _sourceById[sourceId];
    return s ? s.label : sourceId;
  }

  function _seriesLabel(p, sourceId) {
    var rankStr = p.rank !== 'none' ? ' (rank ' + p.rank + ')' : '';
    var srcPrefix = COMPARE_MODE ? (_sourceLabel(sourceId) + ' · ') : '';
    return srcPrefix + p.device + rankStr + ' · ' + p.metric;
  }

  function _addSeries(idx, plotId, sourceId) {
    var cp = _customPlots[idx];
    var p  = plotMap[plotId];
    if (!p) return;
    if (!cp.unit) cp.unit = p.unit || '';
    var color = _nextUnusedColor(cp);
    sourceId = sourceId || (p.sources ? p.sources[0] : 's0');
    cp.series.push({ plotId: plotId, sourceId: sourceId, color: color,
                     label: _seriesLabel(p, sourceId) });
    _refreshCustomCard(idx);
  }

  function _removeSeries(idx, si) {
    var removedKey = _seriesKey(_customPlots[idx].series[si]);
    _customPlots[idx].series.splice(si, 1);
    if (_customPlots[idx].series.length === 0) _customPlots[idx].unit = null;
    var ePos = _customPlots[idx].eventSeries.indexOf(removedKey);
    if (ePos >= 0) _customPlots[idx].eventSeries.splice(ePos, 1);
    _refreshCustomCard(idx);
  }

  function _renderCustomCard(idx, grid) {
    var card = document.createElement('div');
    card.className = 'custom-plot-card';
    card.dataset.customIdx = String(idx);

    // Header
    var header = document.createElement('div');
    header.className = 'custom-plot-header';
    var titleInput = document.createElement('input');
    titleInput.type = 'text';
    titleInput.className = 'custom-plot-title-input';
    titleInput.placeholder = 'Custom Plot ' + (idx + 1);
    titleInput.value = _customPlots[idx].title || '';
    titleInput.oninput = (function(i, inp) {
      return function() {
        _customPlots[i].title = inp.value;
        var pEl = document.querySelector('.custom-plot-card[data-custom-idx="' + i + '"] .custom-plot-div');
        if (pEl && pEl._fullLayout) _renderCustomPlotly(i, pEl);
      };
    })(idx, titleInput);
    header.appendChild(titleInput);
    var unitBadge = document.createElement('span');
    unitBadge.className = 'custom-plot-unit-badge';
    unitBadge.style.display = 'none';
    header.appendChild(unitBadge);
    var expandBtn = document.createElement('button');
    expandBtn.className = 'expand-btn';
    expandBtn.title = 'Expand plot';
    expandBtn.innerHTML = _expandSvg;
    expandBtn.onclick = (function(i) {
      return function(e) {
        e.stopPropagation();
        if (_customPlots[i].series.length === 0) return;
        openModal({ label: _customPlots[i].title || ('Custom Plot ' + (i + 1)),
                    data: _buildCustomTraces(i), layout: _buildCustomLayout(i),
                    _customIdx: i });
      };
    })(idx);
    header.appendChild(expandBtn);
    var delBtn = document.createElement('button');
    delBtn.className = 'custom-delete-btn';
    delBtn.title = 'Delete this plot';
    delBtn.textContent = '✕';
    delBtn.onclick = (function(i) { return function() { _deleteCustomPlot(i); }; })(idx);
    header.appendChild(delBtn);
    card.appendChild(header);

    // Chips
    var chipsEl = document.createElement('div');
    chipsEl.className = 'series-chips';
    card.appendChild(chipsEl);

    // Add series button
    var addBtn = document.createElement('button');
    addBtn.className = 'add-series-btn';
    addBtn.textContent = '+ Add Series';
    addBtn.onclick = (function(i) { return function() { _openSeriesPicker(i, card); }; })(idx);
    card.appendChild(addBtn);

    // Events selector (shown only when series with events exist)
    var evSection = document.createElement('div');
    evSection.className = 'custom-events-section';
    evSection.style.display = 'none';
    var evHeader = document.createElement('div');
    evHeader.className = 'custom-events-header';
    evHeader.textContent = 'Events from:';
    evSection.appendChild(evHeader);
    var evItems = document.createElement('div');
    evItems.className = 'custom-events-items';
    evSection.appendChild(evItems);
    card.appendChild(evSection);

    // Empty state
    var emptyEl = document.createElement('p');
    emptyEl.className = 'custom-plot-empty';
    emptyEl.textContent = 'Add a series to start';
    card.appendChild(emptyEl);

    // Plot div (hidden until a series is added)
    var plotEl = document.createElement('div');
    plotEl.className = 'custom-plot-div';
    plotEl.style.display = 'none';
    card.appendChild(plotEl);

    grid.appendChild(card);
  }

  function _deleteCustomPlot(idx) {
    // Purge the Plotly instance before removing the element
    var card = document.querySelector('.custom-plot-card[data-custom-idx="' + idx + '"]');
    if (card) {
      var plotEl = card.querySelector('.custom-plot-div');
      if (plotEl && plotEl._fullLayout) Plotly.purge(plotEl);
    }
    _customPlots.splice(idx, 1);
    var grid = document.querySelector('.custom-view-container .plots-grid');
    if (!grid) return;
    grid.innerHTML = '';
    _customPlots.forEach(function(_, i) {
      _renderCustomCard(i, grid);
      _refreshCustomCard(i);
    });
    _updateExportBtnState();
    applyFilters();
  }

  function _newCustomPlot(grid) {
    var idx = _customPlots.length;
    _customPlots.push({ unit: null, series: [], title: '', eventSeries: [] });
    _renderCustomCard(idx, grid);
    _updateExportBtnState();
  }

  function _exportCustomPlots() {
    openDemoModal(_DEMO_MSG);  // touchscreen-demo: export disabled
    return;
    var out = _customPlots.map(function(cp) {
      var byKey = {};
      cp.series.forEach(function(s) { byKey[_seriesKey(s)] = s; });
      return {
        title: cp.title || '',
        series: cp.series.map(function(s) {
          var p = plotMap[s.plotId];
          if (!p) return null;
          return { group: p.group, metric: p.metric, device: p.device, rank: p.rank,
                   source: s.sourceId || 's0', color: s.color };
        }).filter(function(x) { return x; }),
        event_series: (cp.eventSeries || []).map(function(key) {
          var s = byKey[key];
          if (!s) return null;
          var p = plotMap[s.plotId];
          if (!p) return null;
          return { group: p.group, metric: p.metric, device: p.device, rank: p.rank,
                   source: s.sourceId || 's0' };
        }).filter(function(x) { return x; }),
      };
    });
    var blob = new Blob([JSON.stringify({ custom_plots: out }, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'custom_plots.json';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function _importCustomPlots(file, grid) {
    openDemoModal(_DEMO_MSG);  // touchscreen-demo: import disabled (defense in depth)
    return;
    var reader = new FileReader();
    reader.onload = function(e) {
      try {
        var data = JSON.parse(e.target.result);
        (data.custom_plots || []).forEach(function(cp) {
          var entry = { unit: null, title: cp.title || '', series: [], eventSeries: [] };
          (cp.series || []).forEach(function(s) {
            var plotId = _resolveSeriesId(s.group, s.metric, s.device, s.rank);
            if (!plotId) return;
            if (!entry.unit) entry.unit = plotMap[plotId].unit || '';
            var sourceId = s.source || 's0';
            entry.series.push({ plotId: plotId, sourceId: sourceId, color: s.color,
                                label: _seriesLabel(plotMap[plotId], sourceId) });
          });
          if (entry.series.length === 0) return;
          (cp.event_series || []).forEach(function(s) {
            var plotId = _resolveSeriesId(s.group, s.metric, s.device, s.rank);
            if (plotId) entry.eventSeries.push(plotId + '@' + (s.source || 's0'));
          });
          _customPlots.push(entry);
        });
        grid.innerHTML = '';
        _customPlots.forEach(function(_, i) { _renderCustomCard(i, grid); _refreshCustomCard(i); });
        _updateExportBtnState();
      } catch(err) {
        alert('Failed to import custom plots: ' + err.message);
      }
    };
    reader.readAsText(file);
  }

  function _buildCustomView() {
    document.querySelectorAll('.sampler-section').forEach(function(s) { s.style.display = 'none'; });
    var container = document.createElement('div');
    container.className = 'custom-view-container';
    var toolbar = document.createElement('div');
    toolbar.className = 'custom-view-toolbar';
    var newBtn = document.createElement('button');
    newBtn.className = 'new-plot-btn';
    newBtn.textContent = '+ New Plot';
    toolbar.appendChild(newBtn);
    var exportBtn = document.createElement('button');
    exportBtn.className = 'toolbar-secondary-btn custom-export-btn';
    exportBtn.textContent = 'Export';
    exportBtn.disabled = _customPlots.length === 0;
    exportBtn.onclick = _exportCustomPlots;
    toolbar.appendChild(exportBtn);
    var importInput = document.createElement('input');
    importInput.type = 'file'; importInput.accept = '.json';
    importInput.style.display = 'none';
    var importLabel = document.createElement('label');
    importLabel.className = 'toolbar-secondary-btn';
    importLabel.textContent = 'Import';
    importLabel.appendChild(importInput);
    toolbar.appendChild(importLabel);
    container.appendChild(toolbar);
    var grid = document.createElement('div');
    grid.className = 'plots-grid';
    container.appendChild(grid);
    newBtn.onclick = function() { _newCustomPlot(grid); };
    importLabel.addEventListener('click', function(e) {
      e.preventDefault();  // touchscreen-demo: block native file picker
      openDemoModal(_DEMO_MSG);
    });
    importInput.onchange = function() {
      if (importInput.files[0]) { _importCustomPlots(importInput.files[0], grid); importInput.value = ''; }
    };
    _customPlots.forEach(function(_, i) { _renderCustomCard(i, grid); });
    var mainEl = document.querySelector('.main');
    var tabBar = document.getElementById('view-tabs');
    var refNode = tabBar ? tabBar.nextSibling : document.querySelector('.report-header').nextSibling;
    mainEl.insertBefore(container, refNode);
    // Cards are now in the document — restore series chips and charts from state.
    _customPlots.forEach(function(_, i) { _refreshCustomCard(i); });
  }

  // ── Energy Dashboard ─────────────────────────────────────────────────────

  function _fmtEnergy(joules) {
    if (Math.abs(joules) >= 1e6) return { val: (joules / 1e6).toFixed(2), unit: 'MJ' };
    if (Math.abs(joules) >= 1000) return { val: (joules / 1000).toFixed(2), unit: 'kJ' };
    return { val: joules.toFixed(1), unit: 'J' };
  }

  function _computeEnergyStats(energyPlots, powerPlots) {
    // Build power lookup: devkey|rank -> array of power plots (keep all, not just last).
    var pwMap = {};
    powerPlots.forEach(function(p) {
      var key = p.devkey + '|' + p.rank;
      if (!pwMap[key]) pwMap[key] = [];
      pwMap[key].push(p);
    });

    function _powerStats(pwArr, sid) {
      // Aggregate min/avg/max across all matching power plots for this source.
      var sumAvg = 0, mn = Infinity, mx = -Infinity, cnt = 0;
      pwArr.forEach(function(pw) {
        var pwTi = (COMPARE_MODE && pw.sources) ? pw.sources.indexOf(sid) : 0;
        if (pwTi < 0) return;
        var pwTr = pw.data[pwTi] || pw.data[0];
        if (!pwTr || !pwTr.y || !pwTr.y.length) return;
        var s = 0;
        pwTr.y.forEach(function(v) {
          s += v;
          if (v < mn) mn = v;
          if (v > mx) mx = v;
        });
        sumAvg += s / pwTr.y.length;
        cnt++;
      });
      if (!cnt) return { avgPower: null, minPower: null, maxPower: null };
      return { avgPower: sumAvg / cnt, minPower: mn, maxPower: mx };
    }

    var stats = [];
    var energySeen = {};  // track which devkey|rank|sid combos came from energyPlots
    energyPlots.forEach(function(p) {
      var pwArr = pwMap[p.devkey + '|' + p.rank] || [];
      var srcList = (COMPARE_MODE && p.sources) ? p.sources : ['s0'];
      srcList.forEach(function(sid, ti) {
        var tr = p.data[ti] || p.data[0];
        if (!tr || !tr.y || !tr.y.length) return;
        var totalEnergy = tr.y[tr.y.length - 1];
        var pw = _powerStats(pwArr, sid);
        energySeen[p.devkey + '|' + p.rank + '|' + sid] = true;
        stats.push({ devkey: p.devkey, device: p.device, rank: p.rank, sourceId: sid,
                     totalEnergy: totalEnergy,
                     avgPower: pw.avgPower, minPower: pw.minPower, maxPower: pw.maxPower });
      });
    });

    // Also include devices that have power_usage but no energy counter, so they
    // appear in the power chart even without energy data.
    powerPlots.forEach(function(p) {
      var srcList = (COMPARE_MODE && p.sources) ? p.sources : ['s0'];
      srcList.forEach(function(sid) {
        if (energySeen[p.devkey + '|' + p.rank + '|' + sid]) return;
        energySeen[p.devkey + '|' + p.rank + '|' + sid] = true;
        var pwArr = pwMap[p.devkey + '|' + p.rank] || [];
        var pw = _powerStats(pwArr, sid);
        if (pw.avgPower == null) return;
        stats.push({ devkey: p.devkey, device: p.device, rank: p.rank, sourceId: sid,
                     totalEnergy: null,
                     avgPower: pw.avgPower, minPower: pw.minPower, maxPower: pw.maxPower });
      });
    });

    return stats;
  }

  // Build per-source aggregate KPI values; returns { totalJ, peakW, peakDevice, peakRank, totalAvgW }
  function _energyColStats(sStats) {
    var totalJ = sStats.reduce(function(a, s) { return a + (s.totalEnergy || 0); }, 0);
    var peakEntry = null;
    sStats.forEach(function(s) {
      if (s.maxPower != null && (peakEntry === null || s.maxPower > peakEntry.maxPower))
        peakEntry = s;
    });
    var ap = sStats.filter(function(s) { return s.avgPower != null; });
    var totalAvgW = ap.length ? ap.reduce(function(a, s) { return a + s.avgPower; }, 0) : null;
    return {
      totalJ: totalJ,
      peakW: peakEntry ? peakEntry.maxPower : null,
      peakDevice: peakEntry ? peakEntry.device : null,
      peakRank: peakEntry ? peakEntry.rank : null,
      totalAvgW: totalAvgW,
    };
  }

  function _buildEnergyKpiRow(stats) {
    var row = document.createElement('div');
    row.className = 'energy-kpi-row';

    // tooltip = shown on hover via CSS data-tip; adds cursor:help + ⓘ indicator
    function makeTile(val, unit, label, tooltip) {
      var tile = document.createElement('div');
      tile.className = 'energy-kpi-tile' + (tooltip ? ' energy-kpi-tile--tip' : '');
      if (tooltip) tile.setAttribute('data-tip', tooltip);
      var vEl = document.createElement('div');
      vEl.className = 'energy-kpi-value';
      vEl.innerHTML = val + '<span class="energy-kpi-unit"> ' + unit + '</span>';
      tile.appendChild(vEl);
      var lEl = document.createElement('div');
      lEl.className = 'energy-kpi-label';
      lEl.textContent = label + (tooltip ? ' ⓘ' : '');
      tile.appendChild(lEl);
      return tile;
    }

    function peakTooltip(c) {
      if (!c.peakDevice) return null;
      var loc = (c.peakRank !== null && c.peakRank !== 'none')
        ? c.peakDevice + '  (rank ' + c.peakRank + ')'
        : c.peakDevice;
      return 'Highest instantaneous power sample. Observed on: ' + loc;
    }

    var avgPowerTip = 'Sum of per-device average power. Approximates total system draw during the run.';


    if (COMPARE_MODE && SOURCES.length > 1) {
      var bySource = {};
      stats.forEach(function(s) {
        if (!bySource[s.sourceId]) bySource[s.sourceId] = [];
        bySource[s.sourceId].push(s);
      });
      SOURCES.forEach(function(src) {
        var sStats = bySource[src.id];
        if (!sStats || !sStats.length) return;
        var col = document.createElement('div');
        col.className = 'energy-kpi-source-col';
        var srcLbl = document.createElement('div');
        srcLbl.className = 'energy-kpi-source-label';
        srcLbl.style.borderColor = src.color;
        srcLbl.style.color = src.color;
        var dot = document.createElement('span');
        dot.className = 'src-dot';
        dot.style.background = src.color;
        srcLbl.appendChild(dot);
        srcLbl.appendChild(document.createTextNode(src.label));
        col.appendChild(srcLbl);
        var c = _energyColStats(sStats);
        var fmt = _fmtEnergy(c.totalJ);
        col.appendChild(makeTile(fmt.val, fmt.unit, 'Total Energy'));
        if (c.peakW != null)
          col.appendChild(makeTile(c.peakW.toFixed(1), 'W', 'Peak Power', peakTooltip(c)));
        if (c.totalAvgW != null)
          col.appendChild(makeTile(c.totalAvgW.toFixed(1), 'W', 'Avg System Power', avgPowerTip));
        row.appendChild(col);
      });
    } else {
      var c = _energyColStats(stats);
      var fmt = _fmtEnergy(c.totalJ);
      row.appendChild(makeTile(fmt.val, fmt.unit, 'Total Energy (all devices)'));
      if (c.peakW != null)
        row.appendChild(makeTile(c.peakW.toFixed(1), 'W', 'Peak Power Observed', peakTooltip(c)));
      if (c.totalAvgW != null)
        row.appendChild(makeTile(c.totalAvgW.toFixed(1), 'W', 'Avg System Power', avgPowerTip));
    }
    return row;
  }

  // Sort devices by rank (numerically) then device name; build rank-band shapes for MPI grouping.
  function _energyDevOrder(stats) {
    var devOrder = [], devSeen = {};
    stats.forEach(function(s) {
      if (!devSeen[s.devkey]) {
        devSeen[s.devkey] = true;
        devOrder.push({ devkey: s.devkey, device: s.device, rank: s.rank });
      }
    });
    devOrder.sort(function(a, b) {
      if (a.rank === 'none' && b.rank === 'none') return a.device.localeCompare(b.device);
      if (a.rank === 'none') return -1;
      if (b.rank === 'none') return 1;
      var dr = parseInt(a.rank, 10) - parseInt(b.rank, 10);
      return dr !== 0 ? dr : a.device.localeCompare(b.device);
    });
    return devOrder;
  }

  // Returns { shapes, annotations } for alternating rank-group background bands.
  function _rankBandLayout(devOrder, hasMpi) {
    if (!hasMpi) return { shapes: [], annotations: [] };
    var groups = [], cur = null;
    devOrder.forEach(function(d, i) {
      if (d.rank !== (cur && cur.rank)) {
        cur = { rank: d.rank, start: i, end: i };
        groups.push(cur);
      } else { cur.end = i; }
    });
    var bandFills = ['rgba(200,215,245,0.55)', 'rgba(235,240,255,0.2)'];
    var shapes = groups.map(function(g, gi) {
      return {
        type: 'rect', layer: 'below',
        xref: 'paper', x0: 0, x1: 1,
        yref: 'y',
        y0: g.start - 0.5, y1: g.end + 0.5,
        fillcolor: bandFills[gi % 2],
        line: { width: 0 },
      };
    });
    var annotations = groups.filter(function(g) { return g.rank !== 'none'; }).map(function(g) {
      return {
        xref: 'paper', x: 1.01,
        yref: 'y', y: (g.start + g.end) / 2,
        text: '<b>Rank ' + g.rank + '</b>',
        showarrow: false,
        font: { size: 10, color: '#374151' },
        xanchor: 'left', yanchor: 'middle',
      };
    });
    return { shapes: shapes, annotations: annotations };
  }

  // Nudge the modebar left so it doesn't overlap the plot's right edge.
  function _nudgeModebar(el) {
    var mb = el.querySelector('.modebar');
    if (mb) mb.style.right = '20px';
  }

  function _renderEnergyBarChart(el, stats, mode) {
    var hasMpi = stats.some(function(s) { return s.rank !== 'none'; });
    var devOrder = _energyDevOrder(stats);
    function devLabel(d) {
      return (hasMpi && d.rank !== 'none') ? d.device + ' (rank ' + d.rank + ')' : d.device;
    }
    var yLabels = devOrder.map(devLabel);
    var leftMargin = Math.min(300, Math.max(140,
      yLabels.reduce(function(m, l) { return Math.max(m, l.length * 7); }, 0)));
    var chartH = Math.max(260, 48 * devOrder.length + 100);
    var bands = _rankBandLayout(devOrder, hasMpi);

    var srcList = (COMPARE_MODE && SOURCES.length > 1)
      ? SOURCES.filter(function(src) { return stats.some(function(s) { return s.sourceId === src.id; }); })
      : [{ id: 's0', label: null, color: '#6081ff' }];

    // In single-file MPI mode: colour each bar by its rank using the blue scale.
    var blueScale = ['#6081ff', '#3a5fd0', '#1e42a8', '#8099ff', '#9fb8ff',
                     '#c0d0ff', '#4a6fdf', '#2a4fb8', '#7090f0', '#aac0ff'];
    var rankBarColors = null;
    if (hasMpi && !(COMPARE_MODE && SOURCES.length > 1)) {
      var _rankIdx = {}, _ri = 0;
      devOrder.forEach(function(d) {
        if (_rankIdx[d.rank] === undefined) _rankIdx[d.rank] = _ri++;
      });
      rankBarColors = devOrder.map(function(d) {
        return blueScale[_rankIdx[d.rank] % blueScale.length];
      });
    }

    var traces = [];
    var layout = {
      margin: { l: leftMargin, r: hasMpi ? 68 : 20, t: 40, b: 50 },
      height: chartH,
      hovermode: 'closest',
      barmode: 'group',
      showlegend: COMPARE_MODE && SOURCES.length > 1,
      legend: { orientation: 'h', y: -0.15, x: 0, xanchor: 'left', font: { size: 11 } },
      shapes: bands.shapes,
      annotations: bands.annotations,
      yaxis: {
        automargin: true,
        autorange: 'reversed',
        categoryorder: 'array',
        categoryarray: yLabels,
      },
    };

    if (mode === 'energy') {
      // Aggregate energy across all matching stats (handles multiple docs per device).
      function energyFor(d, srcId) {
        var matching = stats.filter(function(st) {
          return st.devkey === d.devkey && st.sourceId === srcId && st.totalEnergy != null;
        });
        if (!matching.length) return null;
        return matching.reduce(function(a, st) { return a + st.totalEnergy; }, 0);
      }
      var allJ = [];
      srcList.forEach(function(src) {
        devOrder.forEach(function(d) {
          var e = energyFor(d, src.id);
          if (e != null) allJ.push(e);
        });
      });
      var maxJ = allJ.length ? Math.max.apply(null, allJ) : 0;
      var scale = maxJ >= 1e6 ? 1e6 : maxJ >= 1000 ? 1000 : 1;
      var unit  = maxJ >= 1e6 ? 'MJ' : maxJ >= 1000 ? 'kJ' : 'J';
      layout.xaxis = { title: { text: 'Energy [' + unit + ']' }, zeroline: true };
      srcList.forEach(function(src) {
        // Pre-compute rank totals for "X / Y total rank" tooltip.
        var rankTotalsJ = {};
        devOrder.forEach(function(d) {
          var e = energyFor(d, src.id);
          if (e != null) rankTotalsJ[d.rank] = (rankTotalsJ[d.rank] || 0) + e;
        });

        // Split bars into two traces: devices with energy data and power-only devices.
        var xVals = [], xNoData = [], custData = [], custNoData = [];
        devOrder.forEach(function(d) {
          var e = energyFor(d, src.id);
          if (e != null) {
            var fmt = _fmtEnergy(e);
            var fmtRank = _fmtEnergy(rankTotalsJ[d.rank] || 0);
            xVals.push(e / scale);
            xNoData.push(null);
            custData.push(fmt.val + ' ' + fmt.unit + ' / ' + fmtRank.val + ' ' + fmtRank.unit + ' (rank total)');
            custNoData.push(null);
          } else {
            xVals.push(null);
            xNoData.push(0);
            custData.push(null);
            custNoData.push('no energy counter');
          }
        });
        var namePart = src.label ? src.label + ': ' : '';
        traces.push({
          type: 'bar', orientation: 'h',
          name: src.label || 'Energy',
          x: xVals, y: yLabels,
          marker: { color: rankBarColors || src.color },
          hovertemplate: '<b>%{y}</b><br>' + namePart + '%{customdata}<extra></extra>',
          customdata: custData,
        });
        // Stub trace for power-only devices (gray, dotted outline).
        var hasNoData = xNoData.some(function(v) { return v !== null; });
        if (hasNoData) {
          traces.push({
            type: 'bar', orientation: 'h',
            name: 'no energy data',
            showlegend: false,
            x: xNoData, y: yLabels,
            width: 0.6,
            marker: { color: '#f1f5f9', line: { color: '#94a3b8', width: 1.5 } },
            hovertemplate: '<b>%{y}</b><br>no energy counter available<extra></extra>',
            customdata: custNoData,
          });
        }
      });

    } else {
      // Power mode — avg bar + error_x whiskers showing [min, max] range, same in single & compare.
      // Aggregate across all matching stats (handles multiple docs per device).
      function powerFor(d, srcId) {
        var matching = stats.filter(function(st) {
          return st.devkey === d.devkey && st.sourceId === srcId && st.avgPower != null;
        });
        if (!matching.length) return null;
        var sumAvg = 0, mn = Infinity, mx = -Infinity;
        matching.forEach(function(st) {
          sumAvg += st.avgPower;
          if (st.minPower != null && st.minPower < mn) mn = st.minPower;
          if (st.maxPower != null && st.maxPower > mx) mx = st.maxPower;
        });
        return { avg: sumAvg / matching.length,
                 min: isFinite(mn) ? mn : sumAvg / matching.length,
                 max: isFinite(mx) ? mx : sumAvg / matching.length };
      }
      layout.xaxis = { title: { text: 'Power [W]' }, zeroline: true };
      srcList.forEach(function(src) {
        var xAvg     = [], errPlus = [], errMinus = [], custData = [];
        devOrder.forEach(function(d) {
          var pw = powerFor(d, src.id);
          var avg = pw ? pw.avg : 0;
          var mn  = pw ? pw.min : avg;
          var mx  = pw ? pw.max : avg;
          xAvg.push(avg);
          errMinus.push(avg - mn);
          errPlus.push(mx - avg);
          if (!pw) { custData.push('n/a'); return; }
          custData.push('avg ' + avg.toFixed(1) + ' | min ' + mn.toFixed(1) + ' | max ' + mx.toFixed(1) + ' W');
        });
        traces.push({
          type: 'bar', orientation: 'h',
          name: src.label || 'Avg Power',
          x: xAvg, y: yLabels,
          marker: { color: rankBarColors || src.color },
          error_x: {
            type: 'data', symmetric: false,
            array: errPlus, arrayminus: errMinus,
            visible: true, color: '#1e293b',
            thickness: 1.5, width: 5,
          },
          hovertemplate: '<b>%{y}</b><br>' + (src.label ? src.label + ': ' : '') + '%{customdata}<extra></extra>',
          customdata: custData,
        });
      });
      layout.showlegend = COMPARE_MODE && SOURCES.length > 1;
    }

    Plotly.newPlot(el, traces, layout, {
      responsive: true, displayModeBar: true,
      modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toImage'],
      modeBarButtonsToAdd: [_dlBtnNoData], displaylogo: false,
    });
    _nudgeModebar(el);
  }

  function _renderRankChart(el, stats) {
    var ranks = [], rankSeen = {};
    stats.forEach(function(s) {
      if (!rankSeen[s.rank]) { rankSeen[s.rank] = true; ranks.push(s.rank); }
    });
    ranks.sort(function(a, b) {
      if (a === 'none') return -1; if (b === 'none') return 1;
      return parseInt(a, 10) - parseInt(b, 10);
    });
    var rankLabels = ranks.map(function(r) { return r === 'none' ? 'All' : 'Rank ' + r; });

    // Scale on max rank total (stack height) so the unit fits the tallest bar
    var srcIds = (COMPARE_MODE && SOURCES.length > 1)
      ? SOURCES.map(function(s) { return s.id; }) : ['s0'];
    var allTotals = [];
    ranks.forEach(function(r) {
      srcIds.forEach(function(sid) {
        allTotals.push(stats.filter(function(s) { return s.rank === r && s.sourceId === sid; })
                            .reduce(function(a, s) { return a + (s.totalEnergy || 0); }, 0));
      });
    });
    var maxTot = allTotals.length ? Math.max.apply(null, allTotals) : 0;
    var scale = maxTot >= 1e6 ? 1e6 : maxTot >= 1000 ? 1000 : 1;
    var unit  = maxTot >= 1e6 ? 'MJ' : maxTot >= 1000 ? 'kJ' : 'J';

    var traces = [];
    var barmode = 'stack';

    if (COMPARE_MODE && SOURCES.length > 1) {
      // Compare mode: one grouped bar per source (total energy all devices per rank)
      barmode = 'group';
      var srcList = SOURCES.filter(function(src) {
        return stats.some(function(s) { return s.sourceId === src.id; });
      });
      srcList.forEach(function(src) {
        var yVals = ranks.map(function(r) {
          return stats.filter(function(s) { return s.rank === r && s.sourceId === src.id; })
                      .reduce(function(a, s) { return a + (s.totalEnergy || 0); }, 0) / scale;
        });
        var custData = yVals.map(function(v) {
          var fmt = _fmtEnergy(v * scale); return fmt.val + ' ' + fmt.unit;
        });
        traces.push({
          type: 'bar', name: src.label || 'Energy',
          x: rankLabels, y: yVals,
          marker: { color: src.color },
          text: custData,
          textposition: 'outside',
          textfont: { color: src.color, size: 11 },
          cliponaxis: false,
          hovertemplate: '<b>%{x}</b><br>' + src.label + ': %{customdata}<extra></extra>',
          customdata: custData,
        });
      });
    } else {
      // Single mode: stacked bars by device name.
      // Use raw device names (no serial normalization) so each physical device
      // appears as its own coloured stack — avoids merging GPUs that share the
      // same base name but differ only in their hardware bus-ID suffix length.
      var devTypes = [], devTypeSeen = {};
      stats.forEach(function(s) {
        if (!devTypeSeen[s.device]) { devTypeSeen[s.device] = true; devTypes.push(s.device); }
      });
      devTypes.sort();

      // Pre-compute per-rank totals for the "X / Y (rank total)" tooltip.
      var rankTotalsJ = {};
      ranks.forEach(function(r) {
        rankTotalsJ[r] = stats.filter(function(st) {
          return st.rank === r && st.sourceId === 's0' && st.totalEnergy != null;
        }).reduce(function(a, st) { return a + st.totalEnergy; }, 0);
      });

      // Blue-scale palette derived from HWS brand blue (#6081ff)
      var devColors = ['#6081ff', '#3a5fd0', '#1e42a8', '#8099ff', '#9fb8ff',
                       '#c0d0ff', '#4a6fdf', '#2a4fb8', '#7090f0', '#aac0ff'];

      devTypes.forEach(function(dev, di) {
        var yVals = ranks.map(function(r) {
          var total = stats.filter(function(st) {
            return st.rank === r && st.device === dev &&
                   st.sourceId === 's0' && st.totalEnergy != null;
          }).reduce(function(a, st) { return a + st.totalEnergy; }, 0);
          return total / scale;
        });
        var custData = ranks.map(function(r) {
          var total = stats.filter(function(st) {
            return st.rank === r && st.device === dev &&
                   st.sourceId === 's0' && st.totalEnergy != null;
          }).reduce(function(a, st) { return a + st.totalEnergy; }, 0);
          if (total === 0) return 'n/a';
          var fmt = _fmtEnergy(total);
          var fmtRank = _fmtEnergy(rankTotalsJ[r] || 0);
          return fmt.val + ' ' + fmt.unit + ' / ' + fmtRank.val + ' ' + fmtRank.unit + ' (rank total)';
        });
        traces.push({
          type: 'bar', name: dev,
          x: rankLabels, y: yVals,
          marker: { color: devColors[di % devColors.length] },
          hovertemplate: '<b>%{x}</b> — ' + dev + ': %{customdata}<extra></extra>',
          customdata: custData,
        });
      });
    }

    // Annotations: rank-total label on top of each stacked bar (single mode only).
    var stackAnnotations = [];
    if (!(COMPARE_MODE && SOURCES.length > 1)) {
      ranks.forEach(function(r, ri) {
        var total = (typeof rankTotalsJ !== 'undefined' && rankTotalsJ[r]) || 0;
        if (!total) return;
        var fmt = _fmtEnergy(total);
        stackAnnotations.push({
          x: rankLabels[ri],
          y: total / scale,
          text: fmt.val + ' ' + fmt.unit,
          xanchor: 'center', yanchor: 'bottom',
          showarrow: false,
          font: { size: 11, color: '#1e293b', weight: 600 },
          yshift: 4,
        });
      });
    }

    Plotly.newPlot(el, traces, {
      margin: { l: 60, r: 20, t: 40, b: 60 },
      height: Math.max(300, 55 * ranks.length + 120),
      yaxis: { title: { text: 'Energy [' + unit + ']' } },
      xaxis: {},
      hovermode: 'closest',
      barmode: barmode,
      showlegend: true,
      annotations: stackAnnotations,
      legend: { orientation: 'h', y: -0.25, x: 0, xanchor: 'left', font: { size: 11 } },
    }, {
      responsive: true, displayModeBar: true,
      modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toImage'],
      modeBarButtonsToAdd: [_dlBtnNoData], displaylogo: false,
    });
    _nudgeModebar(el);
  }

  function _buildEnergyDashboard() {
    document.querySelectorAll('.sampler-section').forEach(function(s) { s.style.display = 'none'; });
    var container = document.createElement('div');
    container.className = 'energy-dashboard-container';
    var mainEl = document.querySelector('.main');
    var tabBar  = document.getElementById('view-tabs');
    var refNode = tabBar ? tabBar.nextSibling : document.querySelector('.report-header').nextSibling;
    mainEl.insertBefore(container, refNode);

    var energyPlots = PLOTS.filter(function(p) {
      return p.group === 'power' && p.metric === 'power_total_energy_consumed';
    });
    var powerPlots = PLOTS.filter(function(p) {
      return p.group === 'power' && p.metric === 'power_usage';
    });
    var stats = _computeEnergyStats(energyPlots, powerPlots);

    container.appendChild(_buildEnergyKpiRow(stats));

    function chartBlock(title) {
      var block = document.createElement('div');
      block.className = 'energy-chart-block';
      var ttl = document.createElement('div');
      ttl.className = 'energy-section-title';
      ttl.textContent = title;
      block.appendChild(ttl);
      var plotEl = document.createElement('div');
      plotEl.className = 'energy-plot-div';
      block.appendChild(plotEl);
      container.appendChild(block);
      return plotEl;
    }

    var hasMpi = stats.some(function(s) { return s.rank !== 'none'; });
    var rankTitle = (COMPARE_MODE && SOURCES.length > 1)
      ? 'Total Energy by Rank'
      : 'Total Energy by Rank  (stacked by device)';
    var rankEl  = hasMpi ? chartBlock(rankTitle) : null;
    var energyEl = chartBlock('Total Energy by Device');
    var powerEl  = chartBlock('Power Draw by Device  (avg ± min/max W)');

    if (rankEl) _renderRankChart(rankEl, stats);
    _renderEnergyBarChart(energyEl, stats, 'energy');
    _renderEnergyBarChart(powerEl,  stats, 'power');
  }

  function _isGroupedMode(v) {
    var levels = Array.isArray(v.group_by) ? v.group_by : [v.group_by || 'device'];
    return !(levels.length === 1 && levels[0] === 'device');
  }

  function applyView(idx) {
    var v = VIEWS[idx];
    if (!v) return;
    _activeViewIdx = idx;
    var sidebarFilters = document.querySelector('.sidebar-filters');
    if (sidebarFilters) {
      sidebarFilters.classList.toggle('filters-disabled', !!v.energy);
      sidebarFilters.title = v.energy
        ? "Filters don't affect the Energy Dashboard — it always aggregates all data."
        : '';
    }
    var prevCustom = document.querySelector('.custom-view-container');
    if (prevCustom) prevCustom.remove();
    var prevEnergy = document.querySelector('.energy-dashboard-container');
    if (prevEnergy) {
      prevEnergy.querySelectorAll('.energy-plot-div').forEach(function(el) {
        if (el._fullLayout) Plotly.purge(el);
      });
      prevEnergy.remove();
    }
    _restoreToDevice();
    document.querySelectorAll('.view-tab').forEach(function(btn, i) {
      btn.classList.toggle('active', i === idx);
    });
    if (v.custom) {
      _buildCustomView();
      return;
    }
    if (v.energy) {
      _buildEnergyDashboard();
      return;
    }
    if (_isGroupedMode(v)) {
      var levels = Array.isArray(v.group_by) ? v.group_by : [v.group_by];
      document.querySelectorAll('.sampler-section').forEach(function(s) { s.style.display = 'none'; });
      var filteredCards = Array.from(document.querySelectorAll('.plot-card')).filter(function(card) {
        return _metricMatches(card, v.include_metrics);
      });
      var mainEl = document.querySelector('.main');
      var tabBar = document.getElementById('view-tabs');
      var refNode = tabBar ? tabBar.nextSibling : document.querySelector('.report-header').nextSibling;
      _buildNestedSections(filteredCards, levels, mainEl, refNode, levels.indexOf('rank') >= 0);
    }
    document.querySelectorAll('.plots-grid').forEach(function(grid) {
      grid.style.gridTemplateColumns = v.columns ? 'repeat(' + v.columns + ', 1fr)' : '';
    });
    applyFilters();
    // Re-apply event selection to any cards that were cached while hidden on
    // another tab. Skip when single-file events are at their default (on) so the
    // single-file render path stays untouched.
    if (COMPARE_MODE || !getChecked('eventsrc').has('s0')) _applyAllPlotEvents();
    // Defer resize to next frame so the browser has recalculated grid layout first.
    // Only resize overview cards — the modal manages its own Plotly instance.
    requestAnimationFrame(function() {
      document.querySelectorAll('.plot-card:not(.hidden) .plot-div').forEach(function(el) {
        if (el._fullLayout) Plotly.Plots.resize(el);
      });
    });
  }

  // ── Lazy plot rendering with an LRU render budget ────────────────────────
  // Only plots near the viewport are rendered. Rendered plots are kept in an
  // LRU cache; once the live-instance count exceeds MAX_RENDERED, the
  // least-recently-seen offscreen plots are purged (and re-rendered on demand
  // if revisited). Currently-visible plots are never evicted. Zoom/pan state is
  // preserved across eviction.
  var MAX_RENDERED = 15;            // cap on live Plotly instances
  var RENDER_MARGIN = '300px 0px';  // pre-render just outside the viewport
  var _rendered = new Set();        // plot ids with a live instance
  var _visibleIds = new Set();      // plot ids currently intersecting (never evicted)
  var _lru = [];                    // rendered ids, oldest-first ... most-recent-last

  function _touch(id) {
    var i = _lru.indexOf(id);
    if (i !== -1) _lru.splice(i, 1);
    _lru.push(id);
  }

  function _renderCard(el) {
    var p = plotMap[el.id];
    if (!p) return;
    // Bake the current source visibility + event selection into the single
    // newPlot call so each render is ONE redraw (not newPlot+restyle+relayout).
    var data = p.data, layout = p.layout;
    if (COMPARE_MODE) {
      var checked = getChecked('source');
      data = p.data.map(function(tr, i) {
        var t = Object.assign({}, tr);
        if (p.sources) t.visible = checked.has(p.sources[i]);
        return t;
      });
      var ev = _plotEventLayout(p, true);
      layout = Object.assign({}, p.layout, { shapes: ev.shapes, annotations: ev.annotations });
    } else if (!getChecked('eventsrc').has('s0')) {
      // Single-file with events toggled off: render without the baked events.
      layout = Object.assign({}, p.layout, { shapes: [], annotations: [] });
    }
    Plotly.newPlot(el, data, layout, {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toImage'],
      modeBarButtonsToAdd: [_dlBtn],
      displaylogo: false,
    }).then(function () {
      if (el._savedView) Plotly.relayout(el, el._savedView);
    });
    _rendered.add(el.id);
    _touch(el.id);
    _enforceBudget();
  }

  function _evictCard(el) {
    var fl = el._fullLayout, sv = {};
    if (fl && fl.xaxis && fl.xaxis.autorange === false) sv['xaxis.range'] = fl.xaxis.range.slice();
    if (fl && fl.yaxis && fl.yaxis.autorange === false) sv['yaxis.range'] = fl.yaxis.range.slice();
    el._savedView = Object.keys(sv).length ? sv : null;
    Plotly.purge(el);
    _rendered.delete(el.id);
  }

  function _enforceBudget() {
    var i = 0;
    while (_rendered.size > MAX_RENDERED && i < _lru.length) {
      var id = _lru[i];
      if (_visibleIds.has(id) || !_rendered.has(id)) { i++; continue; }
      var el = document.getElementById(id);
      if (el) _evictCard(el);
      _lru.splice(i, 1);            // drop evicted id; do not advance i
    }
  }

  var _renderObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      var el = entry.target, id = el.id;
      if (entry.isIntersecting) {
        _visibleIds.add(id);
        if (_rendered.has(id)) { _touch(id); }
        else { _renderCard(el); }
      } else {
        _visibleIds.delete(id);
      }
    });
  }, { root: null, rootMargin: RENDER_MARGIN, threshold: 0 });

  function renderPlots() {
    document.querySelectorAll('.plot-div').forEach(function (el) {
      _renderObserver.observe(el);
    });
  }

  function getChecked(cat) {
    var cbs = document.querySelectorAll('input[data-cat="' + cat + '"]:checked');
    var s = new Set();
    cbs.forEach(function (cb) { s.add(cb.value); });
    return s;
  }

  // ── Comparison mode: per-source trace visibility + dynamic events ────────
  // Show/hide each trace of an overview plot according to the Source filter.
  function _applySourceVisibility(el, p) {
    if (!COMPARE_MODE || !el || !el._fullLayout || !p || !p.sources) return;
    var checked = getChecked('source');
    Plotly.restyle(el, { visible: p.sources.map(function(sid) { return checked.has(sid); }) });
  }

  // Build {shapes, annotations} for the events of the selected sources on a plot.
  // rotate=true → overview style (vertical labels); false → modal style.
  function _plotEventLayout(p, rotate) {
    var sel = getChecked('eventsrc');
    var all = [];
    if (COMPARE_MODE && p.sources) {
      p.sources.forEach(function(sid) {
        if (!sel.has(sid)) return;
        var color = _sourceById[sid] ? _sourceById[sid].color : '#6081ff';
        ((p.eventsBySource || {})[sid] || []).forEach(function(ev) { all.push([ev[0], ev[1], color, color]); });
      });
    } else {
      // Single-file: one implicit source 's0', gray styling (matches the baked look).
      if (sel.has('s0')) {
        (p.events || []).forEach(function(ev) {
          all.push([ev[0], ev[1], 'rgba(120,120,120,0.55)', 'rgba(80,80,80,0.9)']);
        });
      }
    }
    if (all.length === 0) return { shapes: [], annotations: [] };
    var tMin = Infinity, tMax = -Infinity;
    (p.data || []).forEach(function(t) {
      if (t.x && t.x.length) { tMin = Math.min(tMin, t.x[0]); tMax = Math.max(tMax, t.x[t.x.length - 1]); }
    });
    if (!isFinite(tMin)) { tMin = 0; tMax = 1; }
    var LEVELS = [0.97, 0.82, 0.67, 0.52];
    var threshold = ((tMax - tMin) || 1.0) * 0.06;
    var lastT = {};
    var shapes = [], annotations = [];
    all.slice().sort(function(a, b) { return a[0] - b[0]; }).forEach(function(ev) {
      var t = ev[0], name = ev[1], color = ev[2], fontColor = ev[3], chosen = 0;
      for (var li = 0; li < LEVELS.length; li++) {
        if (t - (lastT[li] !== undefined ? lastT[li] : -1e18) >= threshold) { chosen = li; break; }
      }
      lastT[chosen] = t;
      // Single-file omits width to match the baked add_vline styling exactly.
      var lineSpec = { dash: 'dot', color: color };
      if (COMPARE_MODE) lineSpec.width = 1.5;
      shapes.push({ type: 'line', x0: t, x1: t, xref: 'x', yref: 'paper', y0: 0, y1: 1,
        line: lineSpec });
      annotations.push({ x: t, y: LEVELS[chosen], xref: 'x', yref: 'paper',
        text: String(name), showarrow: false, font: { size: 10, color: fontColor },
        xanchor: 'left', yanchor: 'top', textangle: rotate ? -90 : 0,
        bgcolor: 'rgba(255,255,255,0.72)', borderpad: 2 });
    });
    return { shapes: shapes, annotations: annotations };
  }

  // Apply the current event-source selection to a rendered regular plot by
  // rebuilding the event shapes/annotations from raw data (robust — never reuses
  // Plotly-mutated objects). Works identically in single-file and compare mode.
  function _applyPlotEvents(el, p, rotate) {
    if (!el || !el._fullLayout || !p) return;
    var ev = _plotEventLayout(p, rotate);
    Plotly.relayout(el, { shapes: ev.shapes, annotations: ev.annotations });
  }

  function _applyAllSourceVisibility() {
    if (!COMPARE_MODE) return;
    document.querySelectorAll('.plot-card:not(.hidden) .plot-div').forEach(function(el) {
      if (el._fullLayout) _applySourceVisibility(el, plotMap[el.id]);
    });
  }

  function _applyAllPlotEvents() {
    document.querySelectorAll('.plot-card:not(.hidden) .plot-div').forEach(function(el) {
      if (el._fullLayout) _applyPlotEvents(el, plotMap[el.id], true);
    });
    if (modalOverlay && modalOverlay.classList.contains('open') &&
        modalPlotEl && modalPlotEl._fullLayout) {
      var src = modalPlotEl._exportSource;
      if (src && src.type === 'regular') _applyPlotEvents(modalPlotEl, plotMap[src.plotId], false);
    }
  }

  // True if any of an overview card's source traces is currently checked.
  function _cardSrcOk(card, checkedSources) {
    if (!checkedSources) return true;
    var pd = card.querySelector('.plot-div');
    var p = pd ? plotMap[pd.id] : null;
    if (!p || !p.sources) return true;
    return p.sources.some(function(sid) { return checkedSources.has(sid); });
  }

  // Metric Group parent checkboxes: reflect the combined state of each group's
  // individual metric checkboxes (checked / unchecked / indeterminate).
  function _syncMetricGroupToggles() {
    var counts = {};
    document.querySelectorAll('input[data-cat="metric"]').forEach(function (cb) {
      var g = cb.dataset.group;
      var c = counts[g] || (counts[g] = { total: 0, on: 0 });
      c.total++;
      if (cb.checked) c.on++;
    });
    document.querySelectorAll('.metric-group-toggle').forEach(function (tog) {
      var c = counts[tog.dataset.group] || { total: 0, on: 0 };
      tog.checked = c.total > 0 && c.on === c.total;
      tog.indeterminate = c.on > 0 && c.on < c.total;
    });
  }

  // Device Rank parent checkboxes: reflect the combined state of each rank's
  // individual device checkboxes (checked / unchecked / indeterminate).
  function _syncDeviceRankToggles() {
    var counts = {};
    document.querySelectorAll('input[data-cat="device"]').forEach(function (cb) {
      var r = cb.dataset.rank;
      if (r === undefined) return;
      var c = counts[r] || (counts[r] = { total: 0, on: 0 });
      c.total++;
      if (cb.checked) c.on++;
    });
    document.querySelectorAll('.device-rank-toggle').forEach(function (tog) {
      var c = counts[tog.dataset.rank] || { total: 0, on: 0 };
      tog.checked = c.total > 0 && c.on === c.total;
      tog.indeterminate = c.on > 0 && c.on < c.total;
    });
  }

  function applyFilters() {
    _syncMetricGroupToggles();
    _syncDeviceRankToggles();
    var devices = getChecked('device');
    var metrics = getChecked('metric');
    var sources = COMPARE_MODE ? getChecked('source') : null;
    var anyVisible = false;

    var v = VIEWS[_activeViewIdx];
    if (v && v.custom) {
      var container = document.querySelector('.custom-view-container');
      if (container) {
        _customPlots.forEach(function(cp, i) {
          var card = container.querySelector('.custom-plot-card[data-custom-idx="' + i + '"]');
          if (!card) return;
          // Empty cards (still being built) are always shown.
          var show = cp.series.length === 0 || cp.series.some(function(s) {
            var p = plotMap[s.plotId];
            if (!p) return false;
            return devices.has(p.devkey) && metrics.has(p.metrickey);
          });
          card.classList.toggle('hidden', !show);
          if (show) anyVisible = true;
        });
      }
      document.getElementById('no-results').classList.toggle('visible', !anyVisible);
      return;
    }
    if (v && v.energy) {
      document.getElementById('no-results').classList.toggle('visible', false);
      return;
    }
    if (v && _isGroupedMode(v)) {
      document.querySelectorAll('.view-group-section .plot-card').forEach(function(card) {
        var inView = _metricMatches(card, v.include_metrics);
        var devOk  = devices.has(card.dataset.devkey);
        var show = inView && metrics.has(card.dataset.metrickey) && devOk && _cardSrcOk(card, sources);
        card.classList.toggle('hidden', !show);
        if (show) anyVisible = true;
      });
      document.querySelectorAll('.view-group-section').forEach(function(sec) {
        sec.style.display = sec.querySelectorAll('.plot-card:not(.hidden)').length > 0 ? '' : 'none';
      });
      document.getElementById('no-results').classList.toggle('visible', !anyVisible);
      return;
    }

    document.querySelectorAll('.sampler-section').forEach(function (section) {
      var devOk  = devices.has(section.dataset.devkey);
      var sectionVisible = false;

      section.querySelectorAll('.plot-card').forEach(function (card) {
        var inView = _metricMatches(card, v.include_metrics);
        var show = devOk && metrics.has(card.dataset.metrickey) && inView && _cardSrcOk(card, sources);
        card.classList.toggle('hidden', !show);
        if (show) { sectionVisible = true; anyVisible = true; }
      });

      // Sections with no plot cards (device info only) follow the device filter only.
      if (section.dataset.hasPlots === 'false' && devOk) {
        sectionVisible = true;
        anyVisible = true;
      }

      section.classList.toggle('hidden', !sectionVisible);
    });

    document.getElementById('no-results').classList.toggle('visible', !anyVisible);

    // Update per-source trace visibility on the currently-rendered plots.
    _applyAllSourceVisibility();

    // If the series picker is open, refresh its metric dropdown (the metric
    // filter constrains the selectable metrics) and device list so it reflects
    // the updated filters immediately.
    var openMetricSel = document.querySelector('.series-picker select');
    if (openMetricSel) {
      if (openMetricSel._refreshOptions) openMetricSel._refreshOptions();
      openMetricSel.dispatchEvent(new Event('change'));
    }
  }

  document.querySelectorAll('.filter-item input[type=checkbox]').forEach(function (cb) {
    if (cb.dataset.cat === 'eventsrc') {
      cb.addEventListener('change', _applyAllPlotEvents);
    } else {
      cb.addEventListener('change', applyFilters);
    }
  });
  document.querySelectorAll('.toggle-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var cat     = btn.dataset.cat;
      var checked = btn.dataset.action === 'all';
      document.querySelectorAll('input[data-cat="' + cat + '"]').forEach(function (cb) {
        cb.checked = checked;
      });
      if (cat === 'eventsrc') _applyAllPlotEvents(); else applyFilters();
    });
  });
  // Metric Group parent toggle: check/uncheck all of the group's metrics.
  document.querySelectorAll('.metric-group-toggle').forEach(function (tog) {
    // Don't let a click on the checkbox expand/collapse its <details>.
    tog.addEventListener('click', function (e) { e.stopPropagation(); });
    tog.addEventListener('change', function () {
      var g = tog.dataset.group, on = tog.checked;
      document.querySelectorAll('input[data-cat="metric"]').forEach(function (cb) {
        if (cb.dataset.group === g) cb.checked = on;
      });
      applyFilters();
    });
  });
  // Device Rank parent toggle: check/uncheck all devices belonging to that rank.
  document.querySelectorAll('.device-rank-toggle').forEach(function (tog) {
    // Don't let a click on the checkbox expand/collapse its <details>.
    tog.addEventListener('click', function (e) { e.stopPropagation(); });
    tog.addEventListener('change', function () {
      var r = tog.dataset.rank, on = tog.checked;
      document.querySelectorAll('input[data-cat="device"]').forEach(function (cb) {
        if (cb.dataset.rank === r) cb.checked = on;
      });
      applyFilters();
    });
  });

  var plotMap = {};
  PLOTS.forEach(function(p) { plotMap[p.id] = p; });

  renderPlots();
  _initSeriesCatalog();
  _syncMetricGroupToggles();
  _syncDeviceRankToggles();

  // ── Plot expand modal ────────────────────────────────────────────────────
  var modalOverlay = document.getElementById('plot-modal');
  var modalPlotEl  = document.getElementById('modal-plot');
  var modalTitleEl = document.getElementById('modal-title');

  var DEFAULT_PLOT_H = Math.round(window.innerHeight * 0.82);

  function openModal(arg) {
    var p = (typeof arg === 'string') ? plotMap[arg] : arg;
    if (!p) return;
    modalPlotEl._exportSource = (typeof arg === 'string')
      ? { type: 'regular', plotId: arg }
      : { type: 'custom', idx: arg._customIdx };
    modalTitleEl.textContent = p.label || '';
    Plotly.purge(modalPlotEl);
    // Show overlay before rendering so clientWidth is a real layout value.
    modalOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    var h = DEFAULT_PLOT_H;
    modalPlotEl.style.height = h + 'px';
    var annotations = (p.layout.annotations || []).map(function(a) {
      return Object.assign({}, a, {textangle: 0});
    });
    // Compare overview plots carry no legend (for render parity with single
    // mode); show one in the expanded view, where its cost is irrelevant.
    var isCmpRegular = COMPARE_MODE && (typeof arg === 'string') && p.sources;
    var layout = Object.assign({}, p.layout, {
      annotations: annotations,
      autosize: false,
      width:  modalPlotEl.clientWidth,
      height: h,
      margin: { l: 60, r: 30, t: 45, b: isCmpRegular ? 80 : 60 },
      showlegend: isCmpRegular ? true : (p.layout.showlegend || false),
      legend: isCmpRegular
        ? { orientation: 'h', y: -0.12, x: 0, xanchor: 'left', font: { size: 11 } }
        : p.layout.legend,
    });
    Plotly.newPlot(modalPlotEl, p.data, layout, {
      responsive: false,
      displayModeBar: true,
      modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toImage'],
      modeBarButtonsToAdd: [_dlBtn],
      displaylogo: false,
    }).then(function() {
      // Regular plots: honor the current source filter + event-source selection.
      // Custom plots bake their own events into the layout above — leave as-is.
      var src = modalPlotEl._exportSource;
      if (src && src.type === 'regular') {
        var sp = plotMap[src.plotId];
        _applySourceVisibility(modalPlotEl, sp);
        _applyPlotEvents(modalPlotEl, sp, false);
      }
    });
  }

  function closeModal() {
    modalOverlay.classList.remove('open');
    document.body.style.overflow = '';
    Plotly.purge(modalPlotEl);
  }

  // Keep plot width correct when the browser window is resized.
  window.addEventListener('resize', function() {
    if (modalOverlay.classList.contains('open') && modalPlotEl.children.length) {
      Plotly.relayout(modalPlotEl, {width: modalPlotEl.clientWidth});
    }
  });

  document.querySelectorAll('.expand-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      openModal(btn.dataset.plotId);
    });
  });

  modalOverlay.addEventListener('click', function(e) {
    if (e.target === modalOverlay) closeModal();
  });

  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modalOverlay.classList.contains('open')) closeModal();
  });

  // ── Touchscreen-demo "feature disabled" modal ──────────────────────────
  var _DEMO_MSG = 'This feature is not available in the touchscreen demo. '
    + 'Please use the full hws visualizer.';
  var demoModalOverlay = document.getElementById('demo-modal');
  var demoModalMsgEl   = document.getElementById('demo-modal-msg');

  function openDemoModal(message) {
    demoModalMsgEl.textContent = message || _DEMO_MSG;
    demoModalOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeDemoModal() {
    demoModalOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }
  demoModalOverlay.addEventListener('click', function(e) {
    if (e.target === demoModalOverlay) closeDemoModal();
  });
  document.getElementById('demo-modal-close').addEventListener('click', closeDemoModal);
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && demoModalOverlay.classList.contains('open')) closeDemoModal();
  });

  if (VIEWS.length > 1) {
    document.querySelectorAll('.view-tab').forEach(function(btn, i) {
      btn.addEventListener('click', function() { applyView(i); });
    });
    applyView(0);
  }
})();
"""


_EXPAND_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13"'
    ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"'
    ' aria-hidden="true">'
    '<polyline points="15 3 21 3 21 9"/>'
    '<polyline points="9 21 3 21 3 15"/>'
    '<line x1="21" y1="3" x2="14" y2="10"/>'
    '<line x1="3" y1="21" x2="10" y2="14"/>'
    '</svg>'
)


def _esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# Separator joining rank and device into a unique composite filter key. In MPI
# runs the bare device_identification is NOT unique across ranks (e.g. every node
# reports "cpu_device", and GPUs can share a bus id on different nodes), so the
# Device filter keys on (rank, device) to keep them apart. The U+001F unit
# separator never occurs in a device id and survives HTML attributes / JSON.
_DEVKEY_SEP = ""


def _devkey(rank_str: str, device_id: str, run: int = 1) -> str:
    base = f"{rank_str}{_DEVKEY_SEP}{device_id}"
    return base if run <= 1 else f"{base}{_DEVKEY_SEP}#{run}"


def _metrickey(group: str, metric: str) -> str:
    """Composite (group, metric) filter key. Metric names can repeat across
    groups, so the per-metric filter keys on the pair. Same U+001F separator."""
    return f"{group}{_DEVKEY_SEP}{metric}"


def _get_plotly_js() -> str:
    try:
        import plotly.offline as plo
        return plo.get_plotlyjs()
    except (ImportError, AttributeError):
        pass
    import plotly
    js_path = os.path.join(
        os.path.dirname(plotly.__file__), "package_data", "plotly.min.js"
    )
    with open(js_path, encoding="utf-8") as f:
        return f.read()


def _device_checkbox(devkey: str, label: str, rank: str = "none") -> str:
    return (
        f'<label class="filter-item">'
        f'<input type="checkbox" data-cat="device" value="{_esc(devkey)}"'
        f' data-rank="{_esc(rank)}" checked>'
        f'<span>{_esc(label)}</span>'
        f'</label>'
    )


def _device_filter_items(device_entries: List[Dict[str, str]], is_mpi: bool) -> str:
    """Inner HTML of the Device filter group.

    MPI runs: one expandable sub-group per rank (device ids are not unique across
    ranks). Non-MPI: a flat checkbox list (single implicit rank).
    """
    if not is_mpi:
        flat = sorted(device_entries, key=lambda e: e["label"])
        return (
            '<div class="filter-items">'
            + "".join(_device_checkbox(e["key"], e["label"], "none") for e in flat)
            + '</div>'
        )

    by_rank: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for e in device_entries:
        by_rank[e["rank"]].append(e)

    def _rank_sort(r: str):
        return (0, int(r)) if r.isdigit() else (1, r)

    parts: List[str] = []
    for rank in sorted(by_rank, key=_rank_sort):
        devs = sorted(by_rank[rank], key=lambda e: e["label"])
        rank_label = "All Devices" if rank == "none" else f"Rank {_esc(rank)}"
        parts.append(
            '<details class="device-rank-group">'
            '<summary>'
            f'<input type="checkbox" class="device-rank-toggle" data-rank="{_esc(rank)}" checked>'
            f'<span>{rank_label}</span>'
            '</summary>'
            '<div class="filter-items">'
            + "".join(_device_checkbox(e["key"], e["label"], e["rank"]) for e in devs)
            + '</div>'
            '</details>'
        )
    return "".join(parts)


def _metric_filter_items(group_metrics: Dict[str, Set[str]]) -> str:
    """Inner HTML of the Metric Group filter.

    One expandable sub-group per metric group. The group's summary carries a
    parent checkbox that toggles all of the group's metric checkboxes (and
    reflects their combined state); each metric is individually selectable.
    Metrics are discovered from the data — nothing is hardcoded.
    """
    parts: List[str] = []
    for group in sorted(group_metrics):
        metrics = sorted(group_metrics[group])
        metric_cbs = "".join(
            f'<label class="filter-item">'
            f'<input type="checkbox" data-cat="metric" value="{_esc(_metrickey(group, m))}"'
            f' data-group="{_esc(group)}" checked>'
            f'<span>{_esc(m)}</span>'
            f'</label>'
            for m in metrics
        )
        parts.append(
            '<details class="metric-group-filter">'
            '<summary>'
            f'<input type="checkbox" class="metric-group-toggle" data-group="{_esc(group)}" checked>'
            f'<span>{_esc(group)}</span>'
            '</summary>'
            f'<div class="filter-items">{metric_cbs}</div>'
            '</details>'
        )
    return "".join(parts)


# Per-source colors (comparison mode). s0 = the current single-mode blue, so the
# base file looks unchanged. Mirrors the JS _CUSTOM_COLORS palette.
_SOURCE_COLORS = ['#6081ff', '#f97316', '#22c55e', '#a855f7',
                  '#ef4444', '#0ea5e9', '#eab308', '#ec4899']


def build_single_sections(docs: List[Dict[str, Any]]):
    """Single-file mode: one trace per
    (device, rank, group, metric) plot.

    Returns (sections_html, plots_js, device_entries, group_metrics, all_ranks_with_data).
    device_entries: ordered list of {"rank", "label", "key"} for the Device filter.
    group_metrics: mapping group -> set of metric names, for the Metric Group filter.
    """
    device_entries: List[Dict[str, str]] = []
    seen_devkeys: Set[str] = set()
    group_metrics: Dict[str, Set[str]] = defaultdict(set)
    all_ranks_with_data: Set[str] = set()

    plots_js: List[Dict] = []
    sections_html: List[str] = []
    pid = 0

    # Track how many times each (rank, device_id) pair appears (for run badges).
    # Keyed per-rank so the same device id on different MPI ranks (e.g. cpu_device
    # on every node) is not mislabeled as a duplicate run.
    device_run_count: Dict[Tuple[str, str], int] = defaultdict(int)

    for rank, sampler_key, sampler in iter_samplers(docs):
        device_id = sampler.get("device_identification", "unknown")
        time_unit, time_points = get_time_axis(sampler)
        n = len(time_points) if time_points is not None else 0

        metrics, static_info = discover_metrics(sampler, n)

        # Skip completely empty sampler dicts (no device id, no info, no metrics)
        if not device_id and not static_info and not metrics:
            continue

        rank_str = str(rank) if rank is not None else "none"
        device_run_count[(rank_str, device_id)] += 1
        run_idx = device_run_count[(rank_str, device_id)]
        devkey = _devkey(rank_str, device_id, run_idx)
        if devkey not in seen_devkeys:
            seen_devkeys.add(devkey)
            label = device_id if run_idx == 1 else f"{device_id} #{run_idx}"
            device_entries.append({"rank": rank_str, "label": label, "key": devkey})
        if rank is not None:
            all_ranks_with_data.add(rank_str)
        start_time = sampler.get("start_time", "")

        dur_str = ""
        if time_points and len(time_points) >= 2:
            dur = time_points[-1] - time_points[0]
            dur_str = f"{dur:.3f} {time_unit or 's'}"

        dev_name = next((v for g, k, v in static_info if k == "name"), "")

        # Static info table
        by_group_static: Dict[str, List] = defaultdict(list)
        for g, k, v in static_info:
            by_group_static[g].append((k, v))
        static_rows = "".join(
            f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>"
            for g in sorted(by_group_static)
            for k, v in by_group_static[g]
        )

        run_badge = f' <span class="run-badge">#{run_idx}</span>' if run_idx > 1 else ""
        rank_span = f'<span><b>Rank:</b> {_esc(str(rank))}</span>' if rank is not None else ""
        start_span = f'<span><b>Start:</b> {_esc(str(start_time))}</span>' if start_time else ""
        dur_span = f'<span><b>Duration:</b> {_esc(dur_str)}</span>' if dur_str else ""
        name_part = f" — {_esc(dev_name)}" if dev_name else ""

        static_block = (
            f'<details class="static-info"><summary>Device info</summary>'
            f'<dl class="info-grid">{static_rows}</dl></details>'
        ) if static_rows else ""

        header = (
            f'<div class="sampler-header">'
            f'<div class="sampler-title">{_esc(device_id)}{name_part}{run_badge}</div>'
            f'<div class="sampler-meta-row">{rank_span}{start_span}{dur_span}</div>'
            f'{static_block}'
            f'</div>'
        )

        # Plot cards, grouped by metric group
        by_gm: Dict[str, List] = defaultdict(list)
        for group, metric, unit, values in metrics:
            group_metrics[group].add(metric)
            by_gm[group].append((metric, unit, values))

        cards: List[str] = []
        for group in sorted(by_gm):
            for metric, unit, values in sorted(by_gm[group], key=lambda x: x[0]):
                pid += 1
                plot_id = f"p{pid}"
                metric_key = _metrickey(group, metric)
                fig = build_figure(rank, sampler, group, metric, unit, values)
                fig_dict = fig.to_dict()
                unit_label, _ = convert_unit(unit, values)
                plots_js.append({
                    "id":        plot_id,
                    "label":     f"{group} — {metric}",
                    "unit":      unit_label,
                    "group":     group,
                    "metric":    metric,
                    "metrickey": metric_key,
                    "device":    device_id,
                    "devkey":    devkey,
                    "rank":      rank_str,
                    "events":    [[t, str(name)] for t, name in get_events(sampler)],
                    "data":      fig_dict["data"],
                    "layout":    fig_dict["layout"],
                })
                cards.append(
                    f'<div class="plot-card"'
                    f' data-device="{_esc(device_id)}"'
                    f' data-device-label="{_esc(device_id)}"'
                    f' data-devkey="{_esc(devkey)}"'
                    f' data-group="{_esc(group)}"'
                    f' data-metric="{_esc(metric)}"'
                    f' data-metrickey="{_esc(metric_key)}"'
                    f' data-rank="{_esc(rank_str)}">'
                    f'<button class="expand-btn" data-plot-id="{plot_id}"'
                    f' title="Expand plot">{_EXPAND_SVG}</button>'
                    f'<div class="plot-div" id="{plot_id}"></div>'
                    f'</div>'
                )

        if cards:
            content = f'<div class="plots-grid">{"".join(cards)}</div>'
        else:
            content = '<p class="no-ts-msg">No time-series metrics available for this device.</p>'

        sections_html.append(
            f'<section class="sampler-section"'
            f' data-device="{_esc(device_id)}"'
            f' data-devkey="{_esc(devkey)}"'
            f' data-rank="{_esc(rank_str)}"'
            f' data-has-plots="{"true" if cards else "false"}">'
            f'{header}'
            f'{content}'
            f'</section>'
        )

    return sections_html, plots_js, device_entries, group_metrics, all_ranks_with_data


def build_compare_figure(rank, device_id, group, metric, card_series, sources_by_id):
    """Comparison mode: overlay one Scatter per source for a single
    (device, rank, group, metric). Traces are colored by source. No event
    shapes/annotations are baked in — events are applied dynamically client-side.

    card_series: list of {source_id, time_unit, time_points, unit, values} in
    source order (only sources that actually have this curve).
    """
    first = card_series[0]
    t_unit = first["time_unit"] or "s"
    first_unit_label, _ = convert_unit(first["unit"], first["values"])
    u_disp = first_unit_label if first_unit_label else "—"

    fig = go.Figure()
    for cs in card_series:
        _unit_label, y_vals = convert_unit(cs["unit"], cs["values"])
        src = sources_by_id[cs["source_id"]]
        fig.add_trace(go.Scatter(
            x=cs["time_points"],
            y=y_vals,
            mode="lines+markers",
            line=dict(color=src["color"]),
            marker=dict(size=4, color=src["color"]),
            name=src["label"],
            hovertemplate=(
                f"{src['label']}<br>"
                f"t: %{{x:.4f}} {t_unit}<br>"
                f"{metric}: %{{y:.4g}} {u_disp if u_disp != '—' else ''}"
                "<extra></extra>"
            ),
            hoverlabel=dict(bgcolor=src["color"], bordercolor=src["color"], font_color="#ffffff"),
        ))

    rank_prefix = f"Rank {rank}  ·  " if rank is not None else ""
    # Layout is intentionally identical to single-file build_figure (same margins,
    # no legend) so overview rendering and event relayouts cost the same. The
    # per-file color mapping is shown in the sidebar Source panel and on hover;
    # the legend is added only in the expanded modal (see openModal).
    fig.update_layout(
        title=dict(
            text=f"{rank_prefix}{device_id}  —  {group}.{metric}",
            font=dict(size=12),
        ),
        xaxis_title=f"Time [{t_unit}]",
        yaxis_title=f"{metric} [{u_disp}]",
        height=315,
        margin=dict(l=65, r=20, t=70, b=45),
        hovermode="closest",
        showlegend=False,
    )
    return fig


def build_compare_sections(sources: List[Dict[str, Any]]):
    """Comparison mode: one card per (device, rank, group, metric), overlaying
    one trace per source that has the curve.

    Returns (sections_html, plots_js, device_entries, group_metrics, all_ranks_with_data).
    device_entries: ordered list of {"rank", "label", "key"} for the Device filter.
    group_metrics: mapping group -> set of metric names, for the Metric Group filter.
    """
    sources_by_id = {s["id"]: s for s in sources}
    group_metrics: Dict[str, Set[str]] = defaultdict(set)
    all_ranks_with_data: Set[str] = set()

    # Index samplers across all sources, keyed by (device_id, rank_str).
    order: List[Tuple[str, str]] = []
    index: Dict[Tuple[str, str], Dict] = {}

    for s in sources:
        for rank, sampler_key, sampler in iter_samplers(s["docs"]):
            device_id = sampler.get("device_identification", "unknown")
            time_unit, time_points = get_time_axis(sampler)
            n = len(time_points) if time_points is not None else 0
            metrics, static_info = discover_metrics(sampler, n)
            if not device_id and not static_info and not metrics:
                continue
            rank_str = str(rank) if rank is not None else "none"
            key = (device_id, rank_str)
            if key not in index:
                index[key] = {"device_id": device_id, "rank": rank,
                              "rank_str": rank_str, "sources": {}}
                order.append(key)
            entry = index[key]
            if s["id"] in entry["sources"]:
                # Device appears multiple times within one file: keep the first
                # occurrence so the overlay stays unambiguous.
                continue
            metrics_map: Dict[Tuple[str, str], Tuple[str, List[float]]] = {}
            for group, metric, unit, values in metrics:
                metrics_map[(group, metric)] = (unit, values)
                group_metrics[group].add(metric)
            entry["sources"][s["id"]] = {
                "time_unit":   time_unit,
                "time_points": time_points,
                "events":      get_events(sampler),
                "metrics":     metrics_map,
                "static_info": static_info,
                "start_time":  sampler.get("start_time", ""),
            }
            if rank is not None:
                all_ranks_with_data.add(rank_str)

    # The index is keyed by (device_id, rank_str), so each entry is already a
    # unique device; devkey carries the rank to keep same-named devices apart.
    device_entries: List[Dict[str, str]] = []
    for (device_id, rank_str) in order:
        device_entries.append({
            "rank": rank_str,
            "label": device_id,
            "key": _devkey(rank_str, device_id),
        })

    plots_js: List[Dict] = []
    sections_html: List[str] = []
    pid = 0

    for key in order:
        entry = index[key]
        device_id = entry["device_id"]
        rank = entry["rank"]
        rank_str = entry["rank_str"]
        devkey = _devkey(rank_str, device_id)

        # Header data taken from the first present source (in source order).
        base_sd = None
        for s in sources:
            if s["id"] in entry["sources"]:
                base_sd = entry["sources"][s["id"]]
                break
        static_info = base_sd["static_info"] if base_sd else []
        start_time = base_sd["start_time"] if base_sd else ""
        time_unit = base_sd["time_unit"] if base_sd else None
        time_points = base_sd["time_points"] if base_sd else None

        dur_str = ""
        if time_points and len(time_points) >= 2:
            dur = time_points[-1] - time_points[0]
            dur_str = f"{dur:.3f} {time_unit or 's'}"
        dev_name = next((v for g, k, v in static_info if k == "name"), "")

        by_group_static: Dict[str, List] = defaultdict(list)
        for g, k, v in static_info:
            by_group_static[g].append((k, v))
        static_rows = "".join(
            f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>"
            for g in sorted(by_group_static)
            for k, v in by_group_static[g]
        )

        rank_span = f'<span><b>Rank:</b> {_esc(str(rank))}</span>' if rank is not None else ""
        start_span = f'<span><b>Start:</b> {_esc(str(start_time))}</span>' if start_time else ""
        dur_span = f'<span><b>Duration:</b> {_esc(dur_str)}</span>' if dur_str else ""
        name_part = f" — {_esc(dev_name)}" if dev_name else ""
        static_block = (
            f'<details class="static-info"><summary>Device info</summary>'
            f'<dl class="info-grid">{static_rows}</dl></details>'
        ) if static_rows else ""
        header = (
            f'<div class="sampler-header">'
            f'<div class="sampler-title">{_esc(device_id)}{name_part}</div>'
            f'<div class="sampler-meta-row">{rank_span}{start_span}{dur_span}</div>'
            f'{static_block}'
            f'</div>'
        )

        # Union of (group, metric) across sources; unit from the first source.
        gm_unit: Dict[Tuple[str, str], str] = {}
        for s in sources:
            sd = entry["sources"].get(s["id"])
            if not sd:
                continue
            for gm, (unit, _vals) in sd["metrics"].items():
                if gm not in gm_unit:
                    gm_unit[gm] = unit

        by_group: Dict[str, List[str]] = defaultdict(list)
        for (group, metric) in gm_unit:
            by_group[group].append(metric)

        cards: List[str] = []
        for group in sorted(by_group):
            for metric in sorted(by_group[group]):
                pid += 1
                plot_id = f"p{pid}"
                metric_key = _metrickey(group, metric)
                unit = gm_unit[(group, metric)]
                card_series: List[Dict] = []
                present_sources: List[str] = []
                events_by_source: Dict[str, List] = {}
                for s in sources:
                    sd = entry["sources"].get(s["id"])
                    if not sd or (group, metric) not in sd["metrics"]:
                        continue
                    m_unit, vals = sd["metrics"][(group, metric)]
                    card_series.append({
                        "source_id":   s["id"],
                        "time_unit":   sd["time_unit"],
                        "time_points": sd["time_points"],
                        "unit":        m_unit,
                        "values":      vals,
                    })
                    present_sources.append(s["id"])
                    events_by_source[s["id"]] = [[t, str(name)] for t, name in sd["events"]]

                fig = build_compare_figure(rank, device_id, group, metric, card_series, sources_by_id)
                fig_dict = fig.to_dict()
                unit_label, _ = convert_unit(unit, card_series[0]["values"])
                plots_js.append({
                    "id":             plot_id,
                    "label":          f"{group} — {metric}",
                    "unit":           unit_label,
                    "group":          group,
                    "metric":         metric,
                    "metrickey":      metric_key,
                    "device":         device_id,
                    "devkey":         devkey,
                    "rank":           rank_str,
                    "sources":        present_sources,
                    "eventsBySource": events_by_source,
                    "data":           fig_dict["data"],
                    "layout":         fig_dict["layout"],
                })
                cards.append(
                    f'<div class="plot-card"'
                    f' data-device="{_esc(device_id)}"'
                    f' data-device-label="{_esc(device_id)}"'
                    f' data-devkey="{_esc(devkey)}"'
                    f' data-group="{_esc(group)}"'
                    f' data-metric="{_esc(metric)}"'
                    f' data-metrickey="{_esc(metric_key)}"'
                    f' data-rank="{_esc(rank_str)}">'
                    f'<button class="expand-btn" data-plot-id="{plot_id}"'
                    f' title="Expand plot">{_EXPAND_SVG}</button>'
                    f'<div class="plot-div" id="{plot_id}"></div>'
                    f'</div>'
                )

        if cards:
            content = f'<div class="plots-grid">{"".join(cards)}</div>'
        else:
            content = '<p class="no-ts-msg">No time-series metrics available for this device.</p>'

        sections_html.append(
            f'<section class="sampler-section"'
            f' data-device="{_esc(device_id)}"'
            f' data-devkey="{_esc(devkey)}"'
            f' data-rank="{_esc(rank_str)}"'
            f' data-has-plots="{"true" if cards else "false"}">'
            f'{header}'
            f'{content}'
            f'</section>'
        )

    return sections_html, plots_js, device_entries, group_metrics, all_ranks_with_data


def build_html(
    input_path: str,
    sources: List[Dict[str, Any]],
    title: Optional[str] = None,
    embed_plotly: bool = True,
    views: Optional[List[Dict]] = None,
    custom_plots_path: Optional[str] = None,
) -> str:
    if title is None:
        title = f"hws Report: {os.path.basename(input_path)}"

    compare_mode = len(sources) > 1

    # MPI format: at least one document has a top-level 'rank' key.
    if compare_mode:
        is_mpi = any("rank" in doc for s in sources for doc in s["docs"])
        (sections_html, plots_js, device_entries, group_metrics,
         all_ranks_with_data) = build_compare_sections(sources)
    else:
        docs = sources[0]["docs"]
        is_mpi = any("rank" in doc for doc in docs)
        (sections_html, plots_js, device_entries, group_metrics,
         all_ranks_with_data) = build_single_sections(docs)

    # Filter sidebar. The Device filter is grouped by rank in MPI runs (device
    # ids are not unique across ranks) and a flat list otherwise. The Metric
    # Group filter is a tree: each group expands to its individual metrics.
    device_cbs = _device_filter_items(device_entries, is_mpi)
    group_cbs = _metric_filter_items(group_metrics)

    # Source filter (comparison mode only).
    source_section = ""
    if compare_mode:
        src_cbs = "".join(
            f'<label class="filter-item">'
            f'<input type="checkbox" data-cat="source" value="{_esc(s["id"])}" checked>'
            f'<span class="src-dot" style="background:{s["color"]}"></span>'
            f'<span>{_esc(s["label"])}</span>'
            f'</label>'
            for s in sources
        )
        # Styled as a toggle panel (like the Events control), not a filter group.
        source_section = (
            '<div class="event-control">'
            '<div class="sidebar-heading">Source file</div>'
            f'<div class="filter-items">{src_cbs}</div>'
            '<div class="toggle-row">'
            '<button class="toggle-btn" data-cat="source" data-action="all">all</button>'
            '<button class="toggle-btn" data-cat="source" data-action="none">none</button>'
            '</div>'
            '</div>'
        )

    # Global event-source control. Compare: one checkbox per source, only the
    # base (s0) checked by default. Single-file: a single "Show events" toggle.
    if compare_mode:
        ev_items = "".join(
            f'<label class="filter-item">'
            f'<input type="checkbox" data-cat="eventsrc" value="{_esc(s["id"])}"'
            f'{" checked" if s["id"] == "s0" else ""}>'
            f'<span class="src-dot" style="background:{s["color"]}"></span>'
            f'<span>{_esc(s["label"])}</span>'
            f'</label>'
            for s in sources
        )
        event_control = (
            '<div class="event-control">'
            '<div class="sidebar-heading">Events</div>'
            f'<div class="filter-items">{ev_items}</div>'
            '<div class="toggle-row">'
            '<button class="toggle-btn" data-cat="eventsrc" data-action="all">all</button>'
            '<button class="toggle-btn" data-cat="eventsrc" data-action="none">none</button>'
            '</div>'
            '</div>'
        )
    else:
        event_control = (
            '<div class="event-control">'
            '<div class="sidebar-heading">Events</div>'
            '<div class="filter-items">'
            '<label class="filter-item">'
            '<input type="checkbox" data-cat="eventsrc" value="s0" checked>'
            '<span>Show events</span>'
            '</label>'
            '</div>'
            '</div>'
        )

    sources_json_str = json.dumps(
        [{"id": s["id"], "label": s["label"], "color": s["color"]} for s in sources]
    )

    n_samplers = len(sections_html)
    n_plots = len(plots_js)
    plots_json_str = json.dumps(plots_js)

    if views:
        has_user_all = any(v["name"].lower() == "all" for v in views)
        final_views = ([] if has_user_all else _DEFAULT_VIEWS) + views
    else:
        final_views = _DEFAULT_VIEWS
    has_energy = any(p["group"] == "power" and p["metric"] == "power_total_energy_consumed"
                     for p in plots_js)
    if has_energy:
        final_views = final_views + [{"name": "Energy Dashboard", "energy": True,
                                       "include_metrics": "all", "group_by": ["device"],
                                       "columns": None, "utility": True}]
    final_views = final_views + [{"name": "Custom Plots", "custom": True,
                                   "include_metrics": "all", "group_by": ["device"],
                                   "columns": None, "utility": True}]
    show_view_tabs = len(final_views) > 1
    views_json_str = json.dumps(final_views)

    custom_plots_data: List[Dict] = []
    if custom_plots_path:
        custom_plots_data = load_custom_plots(custom_plots_path, plots_js, sources)

    app_js = (
        _JS_TEMPLATE
        .replace("__VIEWS_JSON__", views_json_str)
        .replace("__EXPAND_SVG_JSON__", json.dumps(_EXPAND_SVG))
        .replace("__CUSTOM_PLOTS_JSON__", json.dumps(custom_plots_data))
        .replace("__SOURCES_JSON__", sources_json_str)
        .replace("__COMPARE_MODE__", "true" if compare_mode else "false")
        .replace("__PLOTS_JSON__", plots_json_str)
    )

    def _tab_btn(i: int, v: dict) -> str:
        spacer = ('<span class="tab-spacer"></span>'
                  if v.get("utility") and (i == 0 or not final_views[i - 1].get("utility"))
                  else "")
        active = " active" if i == 0 else ""
        return f'{spacer}<button class="view-tab{active}" data-view-idx="{i}">{_esc(v["name"])}</button>'

    view_tab_bar = (
        '<div class="view-tabs" id="view-tabs">'
        + "".join(_tab_btn(i, v) for i, v in enumerate(final_views))
        + "</div>\n"
    ) if show_view_tabs else ""

    if embed_plotly:
        plotly_script = f"<script>\n{_get_plotly_js()}\n</script>"
    else:
        plotly_script = (
            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
        )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_esc(title)}</title>\n"
        f"<style>\n{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="app">\n'

        # ── Sidebar
        '<aside class="sidebar">\n'
        '<div class="sidebar-filters">\n'
        '<div class="sidebar-heading">Filters</div>\n'
        '<details class="filter-group" open>\n'
        '<summary>Device</summary>\n'
        f'{device_cbs}\n'
        '<div class="toggle-row">'
        '<button class="toggle-btn" data-cat="device" data-action="all">all</button>'
        '<button class="toggle-btn" data-cat="device" data-action="none">none</button>'
        '</div>\n'
        '</details>\n'
        '<details class="filter-group" open>\n'
        '<summary>Metric Group</summary>\n'
        f'{group_cbs}\n'
        '<div class="toggle-row">'
        '<button class="toggle-btn" data-cat="metric" data-action="all">all</button>'
        '<button class="toggle-btn" data-cat="metric" data-action="none">none</button>'
        '</div>\n'
        '</details>\n'
        f'{source_section}\n'
        f'{event_control}\n'
        '</div>\n'
        f'<div class="sidebar-logo">{_LOGO_SVG}</div>\n'
        '</aside>\n'

        # ── Main
        '<main class="main">\n'
        '<div class="report-header">\n'
        f'<h1 class="report-title">{_esc(title)}</h1>\n'
        f'<p class="report-subtitle">{n_samplers} sampler(s) · {n_plots} plot(s)</p>\n'
        '</div>\n'
        f'{view_tab_bar}'
        f'{"".join(sections_html)}\n'
        '<div id="no-results" class="no-results">No plots match the current filters.</div>\n'
        '</main>\n'

        '</div>\n'
        '<div id="plot-modal" class="modal-overlay" role="dialog" aria-modal="true">\n'
        '<div class="modal-content">\n'
        '<div class="modal-header">\n'
        '<span id="modal-title"></span>\n'
        '<button id="modal-close" title="Close (Esc)">✕</button>\n'
        '</div>\n'
        '<div class="modal-body"><div id="modal-plot"></div></div>\n'
        '</div>\n'
        '</div>\n'
        '<div id="demo-modal" class="modal-overlay" role="dialog" aria-modal="true">\n'
        '<div class="modal-content demo-modal-content">\n'
        '<div class="modal-header">\n'
        '<span id="demo-modal-title">Not available in this demo</span>\n'
        '<button id="demo-modal-close" title="Close (Esc)">✕</button>\n'
        '</div>\n'
        '<div class="modal-body demo-modal-body"><p id="demo-modal-msg"></p></div>\n'
        '</div>\n'
        '</div>\n'
        f'{plotly_script}\n'
        f"<script>\n{app_js}\n</script>\n"
        "</body>\n"
        "</html>\n"
    )


# ── Entry point ────────────────────────────────────────────────────────

_ANSI_YELLOW = "\033[33;1m"
_ANSI_RESET = "\033[0m"


def _print_touchscreen_demo_warning() -> None:
    """Touchscreen-demo branch only: make it obvious this is not the real hws visualizer."""
    banner = (
        "TOUCHSCREEN DEMO BUILD — this is a stripped-down build of hws visualizer "
        "for on-site touchscreen demos.\n"
        "File import/export, plot downloads, and PDF export are disabled. "
        "Use the regular hws visualizer for actual analysis."
    )
    print(f"{_ANSI_YELLOW}{banner}{_ANSI_RESET}", file=sys.stderr)


def main() -> None:
    _print_touchscreen_demo_warning()
    args = parse_args()
    inputs = args.inputs
    for path in inputs:
        if not os.path.isfile(path):
            raise SystemExit(f"File not found: {path}")

    # Build the list of sources. The first file is the base (source s0); when more
    # than one file is given the report runs in comparison mode.
    sources: List[Dict[str, Any]] = []
    used_labels: Dict[str, int] = defaultdict(int)
    for i, path in enumerate(inputs):
        docs = load_documents(path)
        if not docs:
            raise SystemExit(f"No valid YAML documents found in {path}.")
        stem = os.path.splitext(os.path.basename(path))[0]
        used_labels[stem] += 1
        label = stem if used_labels[stem] == 1 else f"{stem} ({used_labels[stem]})"
        sources.append({
            "id":    f"s{i}",
            "label": label,
            "color": _SOURCE_COLORS[i % len(_SOURCE_COLORS)],
            "docs":  docs,
        })

    output = args.output
    if not output:
        base, _ = os.path.splitext(inputs[0])
        output = base + "_report.html"

    view_config_path = args.view_config
    if not view_config_path:
        default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_views.yaml")
        if os.path.exists(default):
            view_config_path = default
    views = load_view_config(view_config_path) if view_config_path else None
    html = build_html(inputs[0], sources, title=args.title, embed_plotly=not args.cdn,
                      views=views, custom_plots_path=args.custom_plots)

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(output) // 1024
    print(f"Report written to: {output}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
