"""Build REPORT.md: one readable page with every figure, its key numbers and its status.

    python make_report.py          # from 05_Pena2018_Replication/

Reads only the executed notebooks and figures/, so it is safe to run while
run_figures.sh is working. results/ is a cache for resuming runs and is not needed
to read the report. Open REPORT.md in VS Code with Ctrl+Shift+V (Markdown preview).
"""

from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGS = HERE / "figures"
PAPER_PAGE = {3: 7, 4: 8, 5: 9, 6: 10, 7: 11, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16, 13: 16}
NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$|^nan$|^-?inf$")


def roadmap_status() -> dict[int, str]:
    """Status column of the README figure roadmap."""
    out = {}
    for line in (HERE / "README.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0].isdigit():
            out[int(cells[0])] = cells[-1]
    return out


def tables_from_text(text: str):
    """Find printed tables: runs of >= 2 lines ending in the same number (>= 3) of numeric
    values, optionally led by text labels, under a header line. Returns (tables, other)."""
    lines = text.splitlines()

    def n_trailing_numeric(tok):
        k = 0
        for t in reversed(tok):
            if not NUM.match(t):
                break
            k += 1
        return k

    tables, other, i = [], [], 0
    while i < len(lines):
        tok = lines[i].split()
        k = n_trailing_numeric(tok)
        j = i
        while j < len(lines) and len(lines[j].split()) and n_trailing_numeric(lines[j].split()) == k:
            j += 1
        if k >= 3 and j - i >= 2:
            run = [lines[r].split() for r in range(i, j)]
            first_nums = run[0][-k:]
            if all(re.fullmatch(r"-?\d+", t) for t in first_nums) and any(
                    "." in t for r in run[1:] for t in r[-k:]):
                header_tok, run = run[0], run[1:]      # e.g. "gen 0 1 2 ... 10"
            elif other and other[-1].split():
                header_tok = other.pop().split()
            else:
                header_tok = []
            labelled = any(len(r) > k for r in run)
            width = k + (1 if labelled else 0)
            while len(header_tok) > width and header_tok[-1].startswith("("):   # "tc_net (ms)"
                header_tok[-2:] = [" ".join(header_tok[-2:])]
            if len(header_tok) >= k:
                names = header_tok[-k:]
                label = " ".join(header_tok[:len(header_tok) - k])
            else:
                if header_tok:
                    other.append(" ".join(header_tok))
                names, label = [f"c{c + 1}" for c in range(k)], ""
            if labelled:
                head = [label] + names
                rows = [[" ".join(t[:len(t) - k])] + t[-k:] for t in run]
            else:
                head, rows = names, [t[-k:] for t in run]
            tables.append([head] + rows)
            i = j
        else:
            other.append(lines[i]); i += 1
    return tables, other


def md_table(rows) -> str:
    head, body = rows[0], rows[1:]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)


def notebook_summary(nb_path: Path):
    nb = json.loads(nb_path.read_text())
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    ran = sum(1 for c in code if c.get("execution_count"))
    errors, text, images = [], [], []
    for c in code:
        for o in c.get("outputs", []):
            t = o.get("output_type")
            if t == "error":
                errors.append(f"{o.get('ename')}: {o.get('evalue')}")
            elif t == "stream" and o.get("name") == "stdout":
                text.append("".join(o["text"]))
            elif t in ("display_data", "execute_result") and "image/png" in o.get("data", {}):
                images.append(o["data"]["image/png"])
    # drop cache chatter ("loaded x.npz", "saved y.npz (12 s)") and per-generation logs
    keep = [l for l in "".join(text).splitlines()
            if not re.match(r"^(loaded|saved) \S+\.npz|^gen\s+\d+:|^--- ", l.strip())]
    return {"ran": ran, "cells": len(code), "errors": errors, "text": "\n".join(keep),
            "images": images, "mtime": nb_path.stat().st_mtime}


def main():
    status = roadmap_status()
    out = [f"# Pena et al. (2018) replication — report",
           f"_Generated {time.strftime('%Y-%m-%d %H:%M')} UTC by `make_report.py`. "
           "Open with Ctrl+Shift+V. Compare each figure with the paper page given._", ""]
    index = ["| Fig | Ran | Status |", "|---|---|---|"]
    sections = []
    for nb_path in sorted(HERE.glob("Figure[0-9][0-9]_*.ipynb")):
        n = int(nb_path.name[6:8])
        s = notebook_summary(nb_path)
        if s["errors"]:
            run_state = f"❌ error"
        elif s["ran"] == s["cells"]:
            run_state = "✅ " + time.strftime("%d %b %H:%M", time.gmtime(s["mtime"]))
        elif s["ran"]:
            run_state = f"◐ {s['ran']}/{s['cells']} cells"
        else:
            run_state = "— not run"
        index.append(f"| [{n}](#figure-{n}) | {run_state} | {status.get(n, '')} |")

        sec = [f"## Figure {n}", f"`{nb_path.name}` · paper p. {PAPER_PAGE.get(n, '?')} · {run_state}", ""]
        pngs = sorted(FIGS.glob(f"figure{n:02d}_*.png"))
        if not pngs and s["images"]:      # figure only shown inline: export the last one
            p = FIGS / f"figure{n:02d}_notebook.png"
            p.write_bytes(base64.b64decode(s["images"][-1]))
            pngs = [p]
        sec += [f"![Figure {n}](figures/{p.name})" for p in pngs] or ["_No figure yet._"]
        if s["errors"]:
            sec += ["", "**Errors:**", ""] + [f"- `{e}`" for e in s["errors"]]
        tables, other = tables_from_text(s["text"])
        if tables:  # key numbers as CSV: one block per printed table, blank line between
            import csv
            with (FIGS / f"figure{n:02d}_numbers.csv").open("w", newline="") as fh:
                w = csv.writer(fh)
                for k, t in enumerate(tables):
                    if k:
                        w.writerow([])
                    w.writerows(t)
        csvs = sorted(FIGS.glob(f"figure{n:02d}_*.csv"))
        if csvs:
            sec += ["", "Data: " + " · ".join(f"[{p.name}](figures/{p.name})" for p in csvs)]
        for t in tables:
            sec += ["", md_table(t)]
        other = [l for l in other if l.strip()]
        if other:
            sec += ["", "<details><summary>Other printed output</summary>", "", "```",
                    *other[-40:], "```", "</details>", ""]
        sections.append("\n".join(sec) + "\n")
    out += index + [""] + sections
    (HERE / "REPORT.md").write_text("\n\n".join(out[:3]) + "\n" + "\n".join(out[3:]) + "\n")
    print(f"wrote {HERE / 'REPORT.md'}")


if __name__ == "__main__":
    main()
