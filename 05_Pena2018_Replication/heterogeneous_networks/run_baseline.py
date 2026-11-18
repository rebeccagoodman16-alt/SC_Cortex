"""Run and plot the Figure 8A three-population Gaussian baseline."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .model import run_iteration


def main() -> None:
    result = run_iteration(trial_s=1.0, generations=2, seed=4321)
    names = result["populations"]
    rates = result["rates_hz"]
    frequencies = result["frequencies_hz"]
    spectra = result["spectra"]

    output_root = Path(__file__).parent
    figures = output_root / "figures"
    results = output_root / "results"
    figures.mkdir(exist_ok=True)
    results.mkdir(exist_ok=True)

    output_stem = results / "figure_8a_baseline"
    np.savez_compressed(
        output_stem.with_suffix(".npz"),
        rates_hz=rates,
        frequencies_hz=np.stack(frequencies),
        spectra=np.stack(spectra[-1]),
    )
    with output_stem.with_suffix(".json").open("w", encoding="utf-8") as file:
        json.dump(
            {
                "populations": names,
                "history": result["history"],
                "runtime_s": result["runtime_s"],
            },
            file,
            indent=2,
        )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for index, name in enumerate(names):
        axes[0].plot(np.arange(1, rates.shape[0] + 1), rates[:, index], "o-", label=name)
        axes[1].semilogy(frequencies[index], spectra[-1][index], label=name)
    axes[0].set(xlabel="Generation", ylabel="Firing rate (Hz)")
    axes[1].set(xlabel="Frequency (Hz)", ylabel="One-sided PSD")
    axes[0].legend()
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(figures / "figure_8a_baseline.png", dpi=150)
    print("Final rates (Hz):", dict(zip(names, rates[-1])))


if __name__ == "__main__":
    main()
