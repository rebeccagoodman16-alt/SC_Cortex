"""Three-population Gaussian self-consistent iteration.

The homogeneous Dummer--Lindner--Brunel scheme is generalized by replacing
the scalar population rate and spectrum with one value per population. Each
postsynaptic population receives independent Poisson or colored Gaussian
inputs from all three presynaptic populations.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.signal import welch


@dataclass(frozen=True)
class Population:
    """Parameters for one population and its LIF membrane."""

    name: str
    size: int
    tau_s: float
    inhibitory: bool


@dataclass(frozen=True)
class HeterogeneousConfig:
    """Parameters for the Figure 8A baseline."""

    populations: tuple[Population, ...] = (
        Population("RS", 100_000, 0.020, False),
        Population("LTS", 25_000, 0.019, True),
        Population("FS", 5_000, 0.021, True),
    )
    g: float = 4.0
    ce: int = 1_000
    j_v: float = 0.0001
    ri_v: float = 0.030
    threshold_v: float = 0.020
    reset_v: float = 0.010
    refractory_s: float = 0.002
    dt_s: float = 0.0001
    initial_rate_hz: float = 15.0
    rs_to_fs_weight_multiplier: float = 1.4

    @property
    def n_populations(self) -> int:
        return len(self.populations)

    @property
    def connection_counts(self) -> np.ndarray:
        """Return postsynaptic-by-presynaptic in-degree counts."""
        return np.array(
            [
                [self.ce, 0.25 * self.ce, 0.05 * self.ce],
                [self.ce, 0.25 * self.ce, 0.05 * self.ce],
                [0.25 * self.ce, 0.25 * self.ce, 0.05 * self.ce],
            ],
            dtype=float,
        )

    @property
    def signed_weights(self) -> np.ndarray:
        """Return postsynaptic-by-presynaptic synaptic weights in volts."""
        inhibitory = np.array([False, True, True])
        weights = np.tile(
            np.where(inhibitory, -self.g * self.j_v, self.j_v),
            (self.n_populations, 1),
        )
        weights[2, 0] *= self.rs_to_fs_weight_multiplier
        return weights


def _validate_config(config: HeterogeneousConfig, trial_s: float) -> None:
    names = tuple(pop.name for pop in config.populations)
    if names != ("RS", "LTS", "FS"):
        raise ValueError(f"Expected populations ('RS', 'LTS', 'FS'), got {names}")
    if config.dt_s <= 0 or trial_s <= 0:
        raise ValueError("dt_s and trial_s must be positive")
    if _trial_steps(config, trial_s) < 2:
        raise ValueError("trial_s must contain at least two time steps")


def _trial_steps(config: HeterogeneousConfig, trial_s: float) -> int:
    return int(round(trial_s / config.dt_s))


def _simulate_lif(
    input_v: np.ndarray,
    *,
    tau_s: float,
    dt_s: float,
    threshold_v: float,
    reset_v: float,
    refractory_s: float,
) -> np.ndarray:
    voltage = reset_v
    refractory_steps = 0
    spikes: list[int] = []
    ref_limit = int(round(refractory_s / dt_s))
    for index, drive_v in enumerate(input_v):
        if refractory_steps:
            refractory_steps -= 1
            voltage = reset_v
            continue
        voltage += (-voltage + drive_v) * dt_s / tau_s
        if voltage >= threshold_v:
            spikes.append(index)
            voltage = reset_v
            refractory_steps = ref_limit
    return np.asarray(spikes, dtype=int)


def _spike_spectrum(
    spike_indices: np.ndarray,
    *,
    n_steps: int,
    dt_s: float,
    nperseg: int,
) -> tuple[np.ndarray, np.ndarray]:
    signal = np.zeros(n_steps)
    signal[spike_indices] = 1.0 / dt_s
    return welch(
        signal,
        fs=1.0 / dt_s,
        nperseg=min(n_steps, nperseg),
        window="hann",
    )


def _poisson_input(
    rates_hz: np.ndarray,
    *,
    post_index: int,
    config: HeterogeneousConfig,
    rng: np.random.Generator,
    n_steps: int,
) -> np.ndarray:
    counts = config.connection_counts[post_index]
    weights = config.signed_weights[post_index]
    total = np.zeros(n_steps)
    for pre_index, (count, rate_hz, weight) in enumerate(
        zip(counts, rates_hz, weights)
    ):
        del pre_index
        total += weight * rng.poisson(count * rate_hz * config.dt_s, n_steps)
    return config.ri_v + total * config.populations[post_index].tau_s / config.dt_s


def _colored_input(
    rates_hz: np.ndarray,
    frequencies: tuple[np.ndarray, ...],
    spectra: tuple[np.ndarray, ...],
    *,
    post_index: int,
    config: HeterogeneousConfig,
    rng: np.random.Generator,
    n_steps: int,
) -> np.ndarray:
    post_tau = config.populations[post_index].tau_s
    frequency_grid = np.fft.rfftfreq(n_steps, d=config.dt_s)
    input_spectrum = np.zeros(frequency_grid.size)
    counts = config.connection_counts[post_index]
    weights = config.signed_weights[post_index]
    for pre_index, (count, weight) in enumerate(zip(counts, weights)):
        previous = np.interp(
            frequency_grid,
            frequencies[pre_index],
            spectra[pre_index],
            left=spectra[pre_index][0],
            right=spectra[pre_index][-1],
        )
        input_spectrum += count * weight**2 * previous
    input_spectrum *= post_tau**2
    amplitudes = np.sqrt(np.maximum(input_spectrum, 0.0) * n_steps / (2.0 * config.dt_s))
    phases = rng.uniform(0.0, 2.0 * np.pi, frequency_grid.size)
    transform = amplitudes * np.exp(1j * phases)
    transform[0] = 0.0
    noise = np.fft.irfft(transform, n=n_steps)
    mean_v = config.ri_v + post_tau * np.dot(
        config.connection_counts[post_index] * config.signed_weights[post_index],
        rates_hz,
    )
    return mean_v + noise


def run_iteration(
    *,
    config: HeterogeneousConfig | None = None,
    trial_s: float = 1.0,
    generations: int = 2,
    seed: int = 4321,
    nperseg: int = 8192,
    average_rate_generations: bool = True,
) -> dict[str, object]:
    """Run the coupled population iteration and return rates and spectra."""
    config = config or HeterogeneousConfig()
    _validate_config(config, trial_s)
    n_steps = _trial_steps(config, trial_s)
    if generations < 1:
        raise ValueError("generations must be positive")
    if n_steps < 2:
        raise ValueError("trial_s must contain at least two time steps")

    rng = np.random.default_rng(seed)
    rates = np.full(config.n_populations, config.initial_rate_hz, dtype=float)
    history: list[dict[str, object]] = []
    frequencies: tuple[np.ndarray, ...] | None = None
    spectra: tuple[np.ndarray, ...] | None = None
    all_rates: list[np.ndarray] = []
    all_spectra: list[tuple[np.ndarray, ...]] = []
    started = perf_counter()

    for generation in range(1, generations + 1):
        inputs = []
        for post_index in range(config.n_populations):
            if generation == 1:
                drive = _poisson_input(
                    rates,
                    post_index=post_index,
                    config=config,
                    rng=rng,
                    n_steps=n_steps,
                )
            else:
                assert frequencies is not None and spectra is not None
                drive_rates = (
                    np.mean(np.asarray(all_rates), axis=0)
                    if average_rate_generations
                    else rates
                )
                drive = _colored_input(
                    drive_rates,
                    frequencies,
                    spectra,
                    post_index=post_index,
                    config=config,
                    rng=rng,
                    n_steps=n_steps,
                )
            inputs.append(drive)

        generation_spectra = []
        generation_frequencies = []
        generation_rates = []
        cvs = []
        for post_index, population in enumerate(config.populations):
            spikes = _simulate_lif(
                inputs[post_index],
                tau_s=population.tau_s,
                dt_s=config.dt_s,
                threshold_v=config.threshold_v,
                reset_v=config.reset_v,
                refractory_s=config.refractory_s,
            )
            frequency, spectrum = _spike_spectrum(
                spikes,
                n_steps=n_steps,
                dt_s=config.dt_s,
                nperseg=nperseg,
            )
            isi = np.diff(spikes) * config.dt_s
            cv = float(np.std(isi) / np.mean(isi)) if isi.size else float("nan")
            generation_rates.append(spikes.size / trial_s)
            generation_frequencies.append(frequency)
            generation_spectra.append(spectrum)
            cvs.append(cv)

        rates = np.asarray(generation_rates)
        frequencies = tuple(generation_frequencies)
        spectra = tuple(generation_spectra)
        all_rates.append(rates.copy())
        all_spectra.append(spectra)
        history.append(
            {
                "generation": generation,
                "rates_hz": rates.tolist(),
                "cvs": cvs,
                "drive_rates_hz": (
                    [config.initial_rate_hz] * config.n_populations
                    if generation == 1
                    else (
                        np.mean(np.asarray(all_rates[:-1]), axis=0).tolist()
                        if average_rate_generations
                        else rates.tolist()
                    )
                ),
            }
        )

    return {
        "populations": tuple(pop.name for pop in config.populations),
        "rates_hz": np.asarray(all_rates),
        "frequencies_hz": frequencies,
        "spectra": all_spectra,
        "history": history,
        "runtime_s": perf_counter() - started,
    }
