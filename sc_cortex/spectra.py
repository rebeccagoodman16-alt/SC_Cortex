"""Two-sided PSD evaluated at nonnegative frequencies, in spikes²/s (Hz).

No factor of two: a Poisson spike train has a flat spectrum equal to its rate.
The DC mean is removed; this does not estimate the zero-frequency limit.
"""
import numpy as np
from scipy.fft import rfft, irfft, rfftfreq


def spike_spectrum(indices, times, n, duration, dt, batch=32):
    steps = round(duration / dt)
    indices, times = np.asarray(indices), np.asarray(times)
    valid = (times >= 0) & (times < duration)
    indices, bins = indices[valid], np.floor(times[valid] / dt + 1e-7).astype(int)
    keep = bins < steps
    indices, bins = indices[keep], bins[keep]
    total = np.zeros(steps // 2 + 1)
    for lo in range(0, n, batch):
        hi = min(lo + batch, n)
        counts = np.zeros((hi - lo, steps), dtype=np.float64)
        mask = (indices >= lo) & (indices < hi)
        np.add.at(counts, (indices[mask] - lo, bins[mask]), 1.)
        counts -= counts.mean(axis=1, keepdims=True)
        total += (np.abs(rfft(counts, axis=1))**2).sum(axis=0) / duration
    rates = np.bincount(indices, minlength=n) / duration
    return rfftfreq(steps, dt), total / n, rates


def gaussian_kicks(freq, spike_psd, coefficient, steps, dt, trials, rng):
    """mV increments with two-sided input-current PSD coefficient * spike_psd.

coefficient = J²(C_E + g² C_I). Filtering unit white samples by sqrt(S*dt)
produces increments with variance S*dt for a flat target S. Generate twice
as long and crop to reduce periodic-boundary effects. DC uses the first
positive estimate, an explicit low-frequency approximation.
"""
    size = 2 * steps
    grid = rfftfreq(size, dt)
    target = np.interp(grid, freq[1:], spike_psd[1:])
    if np.any(target < 0) or not np.all(np.isfinite(target)):
        raise ValueError('Spectrum must be finite and nonnegative')
    white = rng.standard_normal((trials, size))
    transformed = rfft(white, axis=1, overwrite_x=True)
    transformed *= np.sqrt(coefficient * target * dt)[None, :]
    return np.ascontiguousarray(irfft(transformed, n=size, axis=1)[:, :steps].T)


def spike_cv(indices, times, n):
    """Per-neuron ISI CV; NaN where fewer than three spikes are observed."""
    indices, times = np.asarray(indices), np.asarray(times)
    order = np.lexsort((times, indices))
    ids, ts = indices[order], times[order]
    boundaries = np.searchsorted(ids, np.arange(n+1))
    cv = np.full(n, np.nan)
    for k in range(n):
        intervals = np.diff(ts[boundaries[k]:boundaries[k+1]])
        if len(intervals) >= 2 and intervals.mean() > 0:
            cv[k] = intervals.std()/intervals.mean()
    return cv
