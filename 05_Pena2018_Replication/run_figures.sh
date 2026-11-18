#!/usr/bin/env bash
# Execute the Pena (2018) figure notebooks one at a time with the project .venv.
#
#   ./run_figures.sh            # all figures 3-13, in order
#   ./run_figures.sh 3 4 7      # selected figures
#
# Runs are sequential on purpose: the Codespace has 2 CPUs / 8 GB and no swap, and
# several notebooks running at once starve each other and get Pylance killed.
# Every notebook caches its results in results/, so a rerun after an interruption
# reloads finished runs instead of recomputing them. Logs go to logs/.
#
# To keep it running after you close the terminal:
#   nohup ./run_figures.sh > logs/run_all.log 2>&1 &
set -u
cd "$(dirname "$0")"
PY="$(cd .. && pwd)/.venv/bin/python"
[ -x "$PY" ] || { echo "missing ../.venv — run: python -m venv .venv && .venv/bin/pip install -r requirements.txt"; exit 1; }
mkdir -p logs

figs=("$@")
[ ${#figs[@]} -eq 0 ] && figs=(3 4 5 6 7 8 9 10 11 12 13)

for n in "${figs[@]}"; do
  nb=$(ls Figure$(printf %02d "$n")_*.ipynb 2>/dev/null | head -1)
  [ -n "$nb" ] || { echo "no notebook for figure $n"; continue; }
  echo "[$(date +%H:%M:%S)] figure $n: $nb"
  start=$(date +%s)
  if "$PY" -m nbconvert --to notebook --execute --inplace \
       --ExecutePreprocessor.kernel_name=sc-cortex \
       --ExecutePreprocessor.timeout=-1 "$nb" > "logs/${nb%.ipynb}.log" 2>&1; then
    echo "    done in $(( $(date +%s) - start )) s"
  else
    echo "    FAILED after $(( $(date +%s) - start )) s — see logs/${nb%.ipynb}.log"
  fi
done
