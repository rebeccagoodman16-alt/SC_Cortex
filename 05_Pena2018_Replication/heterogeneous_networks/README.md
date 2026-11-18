# Heterogeneous networks

This project is the first three-population baseline for Figure 8A of Pena et
al. (2018). It contains only the Gaussian self-consistent iteration; it does
not construct the full recurrent network.

The implementation reuses the existing Dummer--Lindner--Brunel conventions:

- Euler LIF integration with `dt = 0.1 ms`, threshold `20 mV`, reset `10 mV`,
  refractory period `2 ms`, and baseline input `R_I = 30 mV`.
- The first generation uses independent Poisson population inputs.
- Later generations use random-phase colored Gaussian inputs from the previous
  spike-train spectra and Welch one-sided PSD estimates.
- Completed-generation population rates are averaged for the next drive, as in
  the existing Pena et al. stabilization.

It generalizes the homogeneous scalar equations to a population matrix. For
postsynaptic population `i` and presynaptic population `j`,

`mu_i = R_I + tau_i * sum_j(C_ij w_ij nu_j)`

and

`S_eta,i(f) = tau_i^2 * sum_j(C_ij w_ij^2 S_x,j(f))`.

The baseline uses `g = 4`, `tau_RS = 20 ms`, `tau_LTS = 19 ms`,
`tau_FS = 21 ms`, `C_LTS = 0.25 C_E`, `C_FS = 0.05 C_E`, and a `1.4`
RS-to-FS excitatory weight multiplier. Population sizes are recorded in the
configuration for the Figure 8A setup; the Gaussian calculation uses one
representative LIF neuron per population.

Run the small baseline from `05_Pena2018_Replication/`:

```bash
python -m heterogeneous_networks.run_baseline
```

The script writes the figure to
`05_Pena2018_Replication/heterogeneous_networks/figures/figure_8a_baseline.png` and the compressed
arrays and metadata to
`05_Pena2018_Replication/heterogeneous_networks/results/figure_8a_baseline.npz` and
`05_Pena2018_Replication/heterogeneous_networks/results/figure_8a_baseline.json`.
