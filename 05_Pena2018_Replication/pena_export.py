"""Save the data behind a matplotlib figure as one tidy CSV.

    import pena_export
    pena_export.figure_csv(fig, FIGURES / "figure05_synaptic_filter.csv")

Columns: panel, series, kind, x, y, value
  panel  - the panel letter or title of the axes (A, B, ... if untitled)
  series - the legend label of the line/points/bars (or kind_#)
  kind   - line, points, bar, or image
  x, y   - data coordinates; value is the colour value for coloured points/images
Opens directly in Excel, Google Sheets or pandas (pd.read_csv).
"""

from __future__ import annotations

import csv
import string
from pathlib import Path

import numpy as np


def _panel_name(ax, i):
    if ax.get_gid():  # explicit name: ax.set_gid("D (nu_out,0)")
        return str(ax.get_gid())
    for t in (ax.get_title(loc="left"), ax.get_title(), ax.get_title(loc="right")):
        if t:
            return t.strip()
    for txt in ax.texts:  # bold panel letters placed with ax.text(...)
        s = txt.get_text().strip()
        if len(s) == 1 and s.isalpha():
            return s
    return string.ascii_uppercase[i] if i < 26 else f"panel_{i}"


def _label(artist, kind, n):
    lab = artist.get_label() or ""
    return lab if lab and not lab.startswith("_") else f"{kind}_{n}"


def figure_rows(fig):
    rows = []
    axes = [ax for ax in fig.get_axes() if ax.get_label() != "<colorbar>"]
    for i, ax in enumerate(axes):
        panel = _panel_name(ax, i)
        for n, line in enumerate(ax.get_lines()):
            x = np.asarray(line.get_xdata(), float); y = np.asarray(line.get_ydata(), float)
            if x.size == 2 and y.size == 2 and (x[0] == x[1] or y[0] == y[1]) and \
                    _label(line, "line", n).startswith("line_"):
                continue  # unlabelled axhline/axvline/guide segments
            s = _label(line, "line", n)
            rows += [(panel, s, "line", a, b, "") for a, b in zip(x, y)]
        for n, coll in enumerate(ax.collections):
            off = np.asarray(coll.get_offsets(), float)
            if off.ndim != 2 or off.shape[0] == 0 or off.shape[1] != 2:
                continue
            arr = coll.get_array()
            vals = np.asarray(arr, float).ravel() if arr is not None and np.size(arr) == off.shape[0] else None
            s = _label(coll, "points", n)
            rows += [(panel, s, "points", a, b, "" if vals is None else vals[k])
                     for k, (a, b) in enumerate(off)]
        for n, cont in enumerate(ax.containers):
            s = _label(cont, "bar", n)
            for p in cont.patches if hasattr(cont, "patches") else cont:
                if hasattr(p, "get_x"):
                    rows.append((panel, s, "bar", p.get_x() + p.get_width() / 2, p.get_height(), ""))
        if not ax.containers:  # plt.hist adds patches without a container in some versions
            from matplotlib.patches import Rectangle
            bars = [p for p in ax.patches if isinstance(p, Rectangle) and p.get_height() != 0]
            rows += [(panel, "hist", "bar", p.get_x() + p.get_width() / 2, p.get_height(), "")
                     for p in bars]
        for n, im in enumerate(ax.images):
            a = np.asarray(im.get_array(), float)
            if a.ndim != 2 or a.size > 200_000:
                continue
            x0, x1, y0, y1 = im.get_extent()
            xs = np.linspace(x0, x1, a.shape[1]); ys = np.linspace(y0, y1, a.shape[0])
            rows += [(panel, _label(im, "image", n), "image", xs[c], ys[r], a[r, c])
                     for r in range(a.shape[0]) for c in range(a.shape[1])]
    return rows


def figure_csv(fig, path) -> Path:
    path = Path(path).with_suffix(".csv")
    rows = figure_rows(fig)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["panel", "series", "kind", "x", "y", "value"])
        for r in rows:
            w.writerow([r[0], r[1], r[2]] + [f"{v:.6g}" if isinstance(v, (float, np.floating)) else v
                                              for v in r[3:]])
    print(f"saved {path.name} ({len(rows)} data points)")
    return path
