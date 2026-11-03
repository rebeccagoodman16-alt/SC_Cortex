# Roadmap for understanding and extending the baseline

| Review topic | Code to trace | Question to explain to Rodrigo |
|---|---|---|
| LIF equation and units | config.py; models.cells | How do drive, leak, reset, and refractory time set firing? |
| Recurrent E/I network | models.run_network | What do J, g, C_E, C_I, delay, and topology control? |
| External drive | models.external | Why is DC drive different from matched-mean Poisson input? |
| Homogeneity | fixed in-degree construction | Why did variable in-degree in the originals introduce heterogeneity? |
| Spike-train spectra | spectra.spike_spectrum | Why does a Poisson spectrum approach the firing rate? |
| Gaussian approximation | spectra.gaussian_kicks | How does a target spectrum become temporally correlated noise? |
| Self-consistency | models.run_iteration | Which input statistics are updated from the output? |
| Validation | 03_Comparison.ipynb | Are differences sampling error, numerical error, or failure of the approximation? |
| Heterogeneity | future extension | Which neuron classes and connectivity distributions should be added first? |

## First meeting deliverables

- Run all three notebooks from fresh kernels with the same config.json.
- Choose a Dummer figure/reset with Rodrigo; document all parameter differences.
- Bring raster, population rate, mean single-neuron spectrum, and iteration residuals.
- Explain the constant-drive convention and the change to fixed in-degree.
- Report nonconvergence honestly; increasing iteration count does not fix an unstable map.
- Keep AI/ML, plasticity, and biological-data integration as later steps after baseline validation.

## Subsequent validation

1. Repeat across network seeds; save each configuration and its results.
2. Increase measurement duration and trial count to assess Monte Carlo noise.
3. Halve dt with all physical parameters fixed.
4. Inspect population activity and cross-correlations before assuming asynchrony.
5. Compare g and reset sweeps to the selected paper figures.
6. Extend to heterogeneous populations using the 2018 framework.
