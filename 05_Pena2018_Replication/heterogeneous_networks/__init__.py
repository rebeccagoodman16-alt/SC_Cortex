"""Gaussian self-consistent iteration for heterogeneous populations."""

import sys
from pathlib import Path

# model.py imports the shared sc_checkpoint helper from the repository root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .model import (
    HeterogeneousConfig,
    Population,
    run_iteration,
)

__all__ = ["HeterogeneousConfig", "Population", "run_iteration"]
