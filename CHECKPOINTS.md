# Saving and recovery

Run notebooks from the SC_Cortex checkout so they can import `sc_checkpoint.py`.
After restarting a kernel, run the setup and simulation cells in their usual order
(or Run All). A matching completed run loads automatically. Existing run/sweep
switches retain their original values; enabling them allows either cache loading
or simulation when no matching cache exists.

- Original recurrent notebooks, HOLYKALE, Brunel, and the g sweep save raw spikes,
  counts, and population rates immediately after simulation. Plotting and analysis
  work with the restored monitor views.
- Recurrent networks save a complete Brian checkpoint every
  `CHECKPOINT_SECONDS = 1.0` seconds of simulated time, including synapses, delayed
  events, voltages, monitors, and random state. Recovery rebuilds connectivity
  before restoring, so initial network memory is still required.
- Both homogeneous Gaussian variants and the heterogeneous model save every
  completed generation with spectra, histories, rates, and random state. A crash
  during a generation repeats only that unfinished generation.
- Numerical model settings, software versions, notebook code, and the shared
  helper code identify each cache. Changed scientific settings produce a new
  cache. Notebook output changes and operational run/cache switches do not.
- Leave `FORCE_RERUN = False` to reuse work. Set it to True only for a deliberate
  fresh run, then restore False. The heterogeneous API uses `force_rerun=True`
  and optionally `checkpoint_dir=...`.
- Cache files use checksums and atomic replacement, keeping the prior committed
  recovery point. Network snapshot checksums are also checked before restoration.

Notebook caches live under `results_auto/<notebook path>/cache/`; heterogeneous
caches live under `05_Pena2018_Replication/heterogeneous_networks/results/cache/`. Existing exports remain
in their original locations. Older NPZ exports lack complete code/parameter
identity and are not silently imported as validated caches.

Checkpoints persist on the Codespace disk across kernel restarts and Codespace
stops. They are ignored by git; deleting the Codespace also deletes those files
unless copied to durable external storage. Large networks require disk space for
the current and previous full network snapshots.

The notebooks' pre-change working copies are kept in `.checkpoint_backups/`.
Original model parameters, equations, initial guesses, durations, and seeds are
preserved. The 04 comparison notebook already reads saved results and is unchanged.
The pre-existing shell-only maintenance cell in HOLYKALE remains unchanged.

## Validation

From the repository root, with the existing requirements installed:

```bash
PYTHONPATH=. python tests/check_checkpoint_recovery.py
PYTHONPATH=. python tests/check_checkpoint_notebooks.py
```

These checks use temporary directories and small explicit test settings. They
compare interrupted and uninterrupted spikes/spectra, reload every original
simulation variant, and exercise both modern notebooks and the g sweep. They do
not launch the full production networks.
