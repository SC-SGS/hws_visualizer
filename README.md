# hws Visualizer

A single-file Python CLI that converts [hws](https://github.com/SC-SGS/hardware_sampling) (Hardware Sampling library) YAML output into a self-contained interactive HTML report. It uses [Plotly](https://plotly.com/) to render one time-series chart per discovered metric, with a sidebar for filtering, an expand modal for individual plots,
optional named views for focused layouts an interactive custom plot builder, and various export options for plots and data.


## Requirements

- Python 3.12+
- `plotly >= 6.8.0`
- `PyYAML >= 6.0.3`

Install dependencies into a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install plotly pyyaml 
```

---

## Usage

```bash
python hws-report.py hardware_samples.yaml                           # output: hardware_samples_report.html
python hws-report.py hardware_samples.yaml -o out.html               # custom output path
python hws-report.py hardware_samples.yaml --title "My Run"          # custom title
python hws-report.py hardware_samples.yaml --cdn                     # load Plotly from CDN
python hws-report.py hardware_samples.yaml --view-config views.yaml  # use custom views config
python hws-report.py hardware_samples.yaml --custom-plots plots.json # pre-load custom plots
python hws-report.py before.yaml after.yaml                          # comparison mode (overlay both runs)
```

| Argument | Description |
|---|---|
| `input` | Path(s) to the `hws` YAML file(s) (one required). Pass **two or more** files to enable [comparison mode](#comparison-mode-multiple-files). |
| `-o`, `--output` | Output HTML path (default: `<input>_report.html`) |
| `--title` | Title shown in the browser tab and page header |
| `--cdn` | Load Plotly.js from CDN instead of embedding it (requires internet to view) |
| `--view-config FILE` | YAML file defining named views |
| `--custom-plots FILE` | JSON file of custom plot configs to pre-load in the Custom Plots tab |

---

## Input formats

The tool handles both `hws` output layouts automatically.

**Non-MPI** — each `---`-separated document is one sampler:

```yaml
device_identification: "gpu_nvidia_device_0"
time_points: {unit: s, values: [0.0, 0.1, ...]}
power:
  power_usage: {unit: W, values: [120.5, ...]}
---
device_identification: "gpu_nvidia_device_1"
...
```

**MPI** — each document has a `rank` key and one or more `sampler_N` sub-keys:

```yaml
rank: 0
sampler_0:
  device_identification: "gpu_nvidia_device_0"
  time_points: ...
---
rank: 1
sampler_0: ...
```

A **Rank** filter appears in the sidebar automatically when 2+ ranks have data.

---

## The generated report

The output is a fully self-contained HTML file. Open it in any modern browser.

**Sidebar filters** — Device, Rank (MPI only), and Metric Group checkboxes with all/none toggles. All filters stack: a plot is visible only when all its filters are checked.

In MPI runs the **Device** filter is grouped by rank, with one expandable sub-section per rank. This is necessary because device identifications are not unique across ranks — every node reports a `cpu_device`, and GPUs can share a bus id on different nodes. Each rank's devices are filtered independently, so toggling (say) rank 0's GPU never affects the same-named GPU on another rank. Non-MPI runs keep a flat device list.

The **Metric Group** filter is a tree: each group expands to its individual metrics, which are discovered from the data (no metric names are hardcoded, so new sample types work automatically). Toggle a whole group with its parent checkbox — it reflects the combined state of its metrics (checked, unchecked, or indeterminate) — or check/uncheck individual metrics. These filters apply everywhere, including the metrics and sources selectable in the Custom Plots builder.

**Events control** — below the filters, an **Events** panel toggles event markers. In single-file mode it is a single *Show events* checkbox; in comparison mode it has one checkbox per file (so you choose which file's events to overlay). Events added via `hws`'s `add_event()` appear as labelled vertical dotted lines.

**Plot controls** — hover for exact values, drag to zoom, double-click to reset. Each card has an **expand** button for a full-screen view and a **download** button for PNG, SVG, PDF, and machine-readable data export.

---

## Comparison mode (multiple files)

Pass two or more YAML files to compare runs — for example a *before* and *after* a change to the sampled application:

```bash
python hws-report.py before.yaml after.yaml
python hws-report.py baseline.yaml run_a.yaml run_b.yaml   # any number of files
```

In comparison mode **every plot becomes an overlay**: for each metric of each device/rank, one series is drawn per file. Series are matched across files by `(device, rank, group, metric)` — a metric present in only some files is overlaid for just those files.

- **Colors are per file.** Each file gets one fixed color, used for its trace in every plot and for its event lines.
- **Source file toggle.** A *Source file* panel below the filters shows/hides the series of each file across all plots.
- **Events per file.** The *Events* panel lets you pick which file(s)' event markers to show; by default only the base file's events are shown.
- **Custom plots across files.** In the [Custom Plots tab](#custom-plots-tab) the series picker lets you choose the file for each series, so you can freely overlay curves from different files (subject to the shared-unit rule). The chosen file is shown in the series label.

---

## Named views

Views define **tabs** that rearrange and filter the plots client-side. If `default_views.yaml` is present next to the script, it is loaded automatically. Pass `--view-config` to use a different file.

```yaml
# views.yaml
views:
  - name: "Power"
    include_metrics: [power.power_usage, power.power_management_limit]
    group_by: group
    columns: 2

  - name: "Clock & Temp"
    include_metrics: [clock, temperature]
    group_by: [rank, device]
```

A built-in **All** tab (all metrics, grouped by device) is always prepended unless you define your own `"All"` entry. A **Custom Plots** tab is always appended (see below).

### `include_metrics`

Accepts `all` (default) or a list of metric specifiers:

| Specifier | Meaning |
|---|---|
| `all` | Every metric |
| `"groupname"` | All metrics in that group, e.g. `power` |
| `"groupname.metricname"` | One specific metric, e.g. `power.power_usage` |

The exact group and metric names for your data are shown in the sidebar's **Metric Group** filter.

```yaml
include_metrics: [power, temperature.temperature, clock.clock_frequency]
```

### `group_by`

Controls how plots are sectioned. Accepts a single string or a list for nested grouping.

| Value | Sections |
|---|---|
| `device` (default) | One section per sampler/device |
| `group` | One section per metric group — all devices side by side |
| `rank` | One section per MPI rank |

List syntax creates nested collapsible sections (up to three levels):

```yaml
group_by: [rank, device]        # rank → device
group_by: [rank, group]         # rank → metric group
group_by: [rank, device, group] # three levels
```

### `columns`

Fixed column count for the plot grid (default: auto-fill):

```yaml
columns: 3
```

### Default views

`default_views.yaml` ships with the repo and is auto-loaded when no `--view-config` is given. It provides Clock, Memory, Energy and Power, and Temperature tabs with the most commonly useful metrics. Copy and modify it as a starting point for your own config.

---

## Custom Plots tab

The **Custom Plots** tab (always present, last in the tab bar) lets you build overlay charts interactively in the browser.

### Building a chart

1. Click **+ New Plot** to create a chart card.
2. Click **+ Add Series** to open the series picker:
   - Select a **metric** from the dropdown (only compatible units are enabled once the first series is added).
   - Hover over a **source** (device sampler) in the list to see a live preview of that curve.
   - Click a source to select it, then **Add**.
3. Repeat to overlay more series.

### Options per chart

- **Title** — editable text field at the top of the card.
- **Events** — checkbox list of series that have events. Select any combination to overlay their event markers (vertical lines + labels, colored per series, staggered to avoid overlap).
- **Expand** — opens the chart full-screen with the horizontal legend below.
- **Delete** — removes the card.

All charts persist when switching to another tab and back.

### Saving and restoring custom plots

Use the **Export** and **Import** buttons in the toolbar to persist your custom plot configuration across sessions as a `custom_plots.json` file.

- **Export** — downloads a JSON file describing all current charts (metric, device, rank, color, title, event overlays). Disabled when no charts exist.
- **Import** — opens a file picker; the loaded charts are appended to any existing ones. Series that don't exist in the current data are silently skipped.

To share a report with custom plots pre-loaded, pass the JSON to the CLI at build time:

```bash
python hws-report.py data.yaml --custom-plots custom_plots.json -o report.html
```

The recipient opens a single self-contained HTML with the charts already populated.

### Constraints

All series in one chart must share the same Y-axis unit (enforced by the picker). X-axis time ranges may differ between devices and ranks — Plotly renders all series on a shared time axis, which works correctly since all samplers share a common time origin.

---

## Plot export and data post-processing

Every plot — whether in the overview, an expanded modal, or the Custom Plots tab — has a download button in its toolbar. It offers four formats:

| Format | Description |
|---|---|
| **PNG** | Raster image|
| **SVG** | Vector image |
| **PDF** | Opens the browser's print dialog; use *Save as PDF* to download. Page size matches the plot exactly, with no margins |
| **Data (JSON)** | Machine-readable export of the plot data for post-processing |

### Data export for post-processing

The **Data (JSON)** option is different in nature from the **Export** button in the Custom Plots toolbar. The Custom Plots export saves a *configuration* (which series to overlay, colors, titles) so you can restore the same view in a future session — it contains no raw measurement values. The data export contains the actual time-series values, axis labels, units, event markers, and device/rank metadata needed to reproduce or extend the plot in your own scripts.

The exported file has two shapes depending on the plot type:

**Single metric** (any regular plot):
```json
{
  "format_version": "1.0",
  "type": "single",
  "title": "power — power_usage",
  "meta": {"device": "gpu_nvidia_device_0", "rank": "none", "group": "power", "metric": "power_usage"},
  "x_axis": {"label": "Time [s]"},
  "y_axis": {"label": "power_usage [W]"},
  "data": {"x": [...], "y": [...]},
  "events": [{"x": 12.5, "label": "kernel_start"}],
  "view": {"x_range": null, "y_range": null, "zoomed": false}
}
```

**Custom overlay** (Custom Plots tab):
```json
{
  "format_version": "1.0",
  "type": "overlay",
  "title": "GPU Clock Comparison",
  "x_axis": {"label": "Time [s]"},
  "y_axis": {"label": "MHz"},
  "series": [
    {
      "label": "gpu_device_0 · clock_frequency",
      "meta": {"device": "gpu_nvidia_device_0", "rank": "none", "group": "clock", "metric": "clock_frequency"},
      "data": {"x": [...], "y": [...]},
      "events": []
    }
  ],
  "view": {"x_range": null, "y_range": null, "zoomed": false}
}
```

### Zoom-based data subsetting

The data export respects the current zoom state. If you have zoomed into a region of interest before exporting as JSON, only the data points visible in that window are included and `view.x_range` / `view.y_range` record the bounds. This makes it easy to extract a specific time window or amplitude range for further analysis without manual filtering in your script.

### Example: plotting with matplotlib

A minimal script that reads an exported JSON file and reproduces the plot with matplotlib:

```python
"""Quick matplotlib viewer for hws-report data exports (plot_data.json)."""
import json
import sys
import matplotlib.pyplot as plt

if len(sys.argv) < 2:
    print("Usage: python plot_from_json.py <export.json>")
    sys.exit(1)

with open(sys.argv[1]) as f:
    d = json.load(f)

fig, ax = plt.subplots(figsize=(10, 4))

trans = ax.get_xaxis_transform()  # x: data coords, y: axes fraction (0=bottom, 1=top)

def draw_event(x, label, color="gray"):
    ax.axvline(x, linestyle=":", color=color, alpha=0.7)
    ax.text(x, 1.0, label, fontsize=7, rotation=90, va="top", ha="right",
            transform=trans, color=color)

if d["type"] == "single":
    ax.plot(d["data"]["x"], d["data"]["y"], label=d["title"])
    for ev in d.get("events", []):
        draw_event(ev["x"], ev["label"])
    m = d.get("meta", {})
    info = f"{m.get('device', '')}  rank={m.get('rank', 'none')}  {m.get('group', '')}.{m.get('metric', '')}"
    ax.set_title(info, fontsize=9)

elif d["type"] == "overlay":
    for s in d["series"]:
        line, = ax.plot(s["data"]["x"], s["data"]["y"], label=s["label"])
        for ev in s.get("events", []):
            draw_event(ev["x"], ev["label"], color=line.get_color())
    ax.set_title(d.get("title", "Custom overlay"), fontsize=9)
    ax.legend(fontsize=8)

ax.set_xlabel(d.get("x_axis", {}).get("label", "Time"))
ax.set_ylabel(d.get("y_axis", {}).get("label", ""))

view = d.get("view", {})
if view.get("x_range"):
    ax.set_xlim(*view["x_range"])
if view.get("y_range"):
    ax.set_ylim(*view["y_range"])

fig.tight_layout()
plt.show()
```

Use this as a starting point for applying your own plot style, computing statistics over the exported arrays, or feeding the data into further analysis pipelines.

---

## AI Use Disclaimer

This project was developed with assistance from [Claude](https://claude.ai) (Anthropic). AI-generated content may contain errors. Please review and test before relying on it.


## License

See [LICENSE](LICENSE).
