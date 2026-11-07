"""Gaussian self-consistent iteration for heterogeneous populations."""

from .model import (
    HeterogeneousConfig,
    Population,
    run_iteration,
)

__all__ = ["HeterogeneousConfig", "Population", "run_iteration"]
