# Checkpoint validation

Completed: November 8, 2026

20 recovery checks passed. All 17 notebook scientific-settings comparisons passed.
All 14 original simulation variants passed run-and-reload checks.

Validated: atomic saves, corrupt-checkpoint fallback, parameter invalidation,
cached monitor units, delayed-event recovery, random-state recovery,
exact interrupted/uninterrupted spikes and spectra, both modern notebooks,
the inhibition sweep, and the heterogeneous model.

Production networks were not launched. Test settings were temporary.
Code is saved in this Codespace; changes have not been committed or pushed.

## Check results

- atomic round trip
- corrupt current falls back to prior checkpoint
- repair retains the valid prior checkpoint
- parameter change produces cache miss
- force rerun bypasses cache
- restored monitor units and counts
- corrupt network snapshot falls back without changing spikes
- chunked run preserves original spike train
- network recovery preserves spikes and delay queue
- network recovery preserves population rates
- heterogeneous generation recovery matches uninterrupted rates
- heterogeneous recovery matches spectra
- completed heterogeneous run reuses results
- original notebook reload restores monitor data
- original Gaussian completed run reloads
- original Gaussian generation recovery matches uninterrupted spectrum
- run and reload in all 14 original simulation variants
- modern Brunel run and cached monitor reload
- sweep condition reuses completed results
- averaged Gaussian recovery matches rates and spectra
