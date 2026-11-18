# Pena et al. (2018) — figure-by-figure replication

Pena, Vellmer, Bernardi, Roque & Lindner, *Self-Consistent Scheme for Spike-Train
Power Spectra in Heterogeneous Sparse Networks*, Front. Comput. Neurosci. 12:9 (2018),
doi:[10.3389/fncom.2018.00009](https://doi.org/10.3389/fncom.2018.00009).

One notebook per data figure (3–13); Figures 1–2 are schematic drawings and are not
reproduced. Outputs go to `results/` (NPZ + JSON, reused on rerun) and `figures/`
(both git-ignored).

## Running

Use the project environment (`/workspaces/SC_Cortex/.venv`, Jupyter kernel **SC_Cortex (.venv)**).
Exact versions are pinned in [`../requirements-lock.txt`](../requirements-lock.txt).

```bash
./run_figures.sh            # all figures, one at a time, logs in logs/
./run_figures.sh 3 4        # selected figures
nohup ./run_figures.sh > logs/run_all.log 2>&1 &   # keep running after closing the terminal
```

Run one notebook at a time. With 2 CPUs and 8 GB of RAM, parallel kernels run each other out of memory.
Results are cached in `results/`, so an interrupted run resumes.

## Code

| File | Contents |
|---|---|
| [`pena2018_params.py`](pena2018_params.py) | Table 1 defaults and per-figure overrides (`params_for(n)`) |
| [`pena_scheme.py`](pena_scheme.py) | Self-consistent scheme: Eqs. 5–7 statistics, Eq. 11 averaging, multi-population scheme (Eqs. 12–15), Erdős–Rényi scheme (Eqs. 16–18), Eq. 19 error, Brunel–Sergi rate map, mean-field start |
| [`pena_network.py`](pena_network.py) | NumPy recurrent LIF network (Eqs. 8–10): fixed in-degree or ER, fixed/exponential weights, delay, exponential synapses, per-window spectra, input-current recording |
| [`pena_runs.py`](pena_runs.py) | Cached figure-level runs shared by the notebooks |

The scheme follows Dummer, Wieland & Lindner (2014) as extended by Pena et al.: one LIF
neuron per population driven by Gaussian noise whose mean (Eq. 12) and spectrum
(Eq. 13) are built from the previous generation's rates and spike-train spectra (Eq. 14).

### Deviations from the paper (all recorded in the notebooks)

- **Network size:** default N_E = 10,000 (8,000/20,000 in Fig 4) instead of 100,000;
  the Codespace has 2 CPUs and ~2 GB free RAM. Fig 7 shows how the scheme–network
  agreement depends on N_E, so smaller networks are expected to deviate more.
- **Trials:** 1,000 trials per generation (paper 10,000); ER scheme 40 trials × 2 s per
  neuron (paper 100 × 10 s).
- **Unstated details:** dt = 0.1 ms (0.05 ms in Fig 4/5 networks so τD = 0.55 ms is
  exact); generation 0 starts at the mean-field rate; voltage clamped during refractoriness;
  presynaptic partners drawn with replacement.
- **Not reproduced:** Fig 4A exponential-IF inset; Fig 12A distribution inset.

## Figure roadmap

| Fig | Content | Needs | Notebook | Status |
|----|---------|-------|----------|--------|
| 1 | Schematic: heterogeneous E/I network → one representative neuron per population, iterated over generations | Diagram only | — | skipped (schematic) |
| 2 | Schematic: Erdős–Rényi network (distributed in-degrees/weights) → M representative neurons | Diagram only | — | skipped (schematic) |
| 3 | Rate stabilization by averaging (g = 5.5, J = 0.2 mV, τs = 10 ms, RI = 30 mV; network rate 9.1 Hz). A: no averaging, B: 2-generation average, C: all-past average, D: input→output rate map | Scheme | [`Figure03_Rate_Averaging.ipynb`](Figure03_Rate_Averaging.ipynb) | ✓ A–D match the published curves (generations 0–10) |
| 4 | Slow-fluctuation state, homogeneous net (g = 5, RI = 24 mV, τD = 0.55 ms, τR = 0.5 ms). A: spectra vs J (N_E = 8k, 80k; EIF inset), B–C: rasters J = 0.2, 0.8 mV, D–F: rate, τ_corr, Fano vs J | Network + scheme | [`Figure04_Slow_Fluctuations.ipynb`](Figure04_Slow_Fluctuations.ipynb) | ran 18 Nov — rate/FF match network at all J; τ_c 25–30% short at J ≥ 0.6 |
| 5 | Synaptic filtering (J = 0.2 mV). A: spectra vs τs, B–C: Fano and τ_corr vs J (τs = 10 ms) | Scheme (+ network) | [`Figure05_Synaptic_Filter.ipynb`](Figure05_Synaptic_Filter.ipynb) | ran 18 Nov — rates within 0.4 Hz; FF within ~15% |
| 6 | Two populations with different parameters (τE = 20, τI = 19 ms); (gE, gI) = (4.2, 4.0), (3.7, 3.7), (4.25, 3.6) | Network + scheme | [`Figure06_EI_Heterogeneous.ipynb`](Figure06_EI_Heterogeneous.ipynb) | ran 18 Nov — B matches; A, C scheme not fully converged (E rate high) |
| 7 | Scheme accuracy vs network size (gE = 4.2, gI = 4.0): relative error, Fano, τ_corr vs N_E | Network sweep | [`Figure07_Network_Size.ipynb`](Figure07_Network_Size.ipynb) | ran 18 Nov — E error 4.1% → 2.8% with N_E (paper < 1% at 20k) |
| 8 | >2 populations. A: RS/LTS/FS (g = 4) — baseline exists in [`heterogeneous_networks/`](heterogeneous_networks/). B: two modules of 1.25×10⁵ cells, J = 0.1 / 0.27 mV (~80 Hz hump) | Network + scheme | [`Figure08_Multi_Population.ipynb`](Figure08_Multi_Population.ipynb) | ran 18 Nov — 3-pop and modules within 3%, errors ≤ 0.013 |
| 9 | Rate histograms, scheme (M = 50, generations 6–20) vs network. A: binomial in-degrees, B: + exponential weights | ER scheme + network | [`Figure09_Rate_Histograms.ipynb`](Figure09_Rate_Histograms.ipynb) | ran 18 Nov — shapes match; scheme mean rate 5–25% high |
| 10 | ER net: rate mean/SD across generations vs g (⟨CE⟩ = 1000, ⟨CI⟩ = 250, J = 0.1 mV, τD = 2 ms). C–D: rate-binned and averaged spectra | ER scheme + network | [`Figure10_ER_Rates_Spectra.ipynb`](Figure10_ER_Rates_Spectra.ipynb) | ran 18 Nov — mean-spectrum error ≤ 4.5%; mean rate high at g = 4 |
| 11 | As Fig 10 with exponentially distributed weights | ER scheme + network | [`Figure11_ER_Exp_Weights.ipynb`](Figure11_ER_Exp_Weights.ipynb) | ran 18 Nov — errors mostly < 5% (g = 3.5: 9–14%) |
| 12 | Relative spectral error vs input skewness (A) and excess kurtosis (B), g = 4 and 6, 1000 neurons, 2 ms bins | Network analysis | [`Figure12_Non_Gaussianity.ipynb`](Figure12_Non_Gaussianity.ipynb) | ran 18 Nov — lower bound (0.34) above errors: needs longer measurements |
| 13 | As Fig 12, restricted to neurons firing 20–100 Hz | Network analysis | [`Figure13_Non_Gaussianity_Rate_Window.ipynb`](Figure13_Non_Gaussianity_Rate_Window.ipynb) | ran 18 Nov — same lower-bound issue as Fig 12 |

Note: `01_Original_Colab/4.5/Figure10_G4.5_CE100_CI25_J1.0.ipynb` is a different "Figure 10"
(C_E = 100, V_r = 0/10 mV) and is **not** Pena Fig 10.

## Open items to verify against the PDF

Results for every figure: open `REPORT.md` (Ctrl+Shift+V); data are in `figures/*.csv`.

- Fig 6/7: all-past rate averaging keeps early transients; try no averaging near balance,
  two-generation smoothing, or a burn-in before averaging.
- Fig 9–11: scheme mean rate 5–25% above the network (worst at g = 4); check with a larger network.
- Fig 12/13: the two-measurement lower bound exceeds the errors; use longer recordings.
- Fig 4/5: τ_c shorter than the network at strong coupling (network size?).

- Integration step `dt` (not stated in the paper; we use 0.1 ms).
- Fig 3 conventions are inferred from the published curves, not stated in the text: generation 0 is
  13 Hz with a white spectrum, B uses ν̂ₙ = (ν̂ₙ₋₁ + rₙ)/2, and C averages r₀…rₙ. The literal
  (rₙ₋₁ + rₙ)/2 reading of B is linearly unstable here (rate-map slope −2.56 < −2).
- Table 1 values marked `# VERIFY` in `pena2018_params.py`.
