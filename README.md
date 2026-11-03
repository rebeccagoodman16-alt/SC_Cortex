# SC_Cortex

A readable, memory-conscious Brunel-based SNN and iterative Gaussian approximation, with a separate comparison notebook. This is a new baseline, not yet a validated reproduction of a specific Dummer figure.

## Run

```bash
python -m pip install -r requirements.txt
jupyter lab
```

Open notebooks from the repository root, in order:

1. `01_Brunel_SNN.ipynb`: full recurrent network.
2. `02_Iterative_Approximation.ipynb`: independent representative-neuron trials.
3. `03_Comparison.ipynb`: load saved results and compare.

Edit **config.json** once for all notebooks. Outputs go into `results/<configuration hash>/`. A changed configuration creates a different result directory. Results include configuration, software versions, spectrum convention, iteration history, and convergence status. Do not compare output from different configurations by renaming files.

For a tiny installation test, or a larger baseline:

```python
from sc_cortex.config import preset
preset('smoke').save('config.json')      # tiny execution check, not scientific validation
preset('quick').save('config.json')      # default development configuration
preset('reference').save('config.json')  # larger Dummer-like baseline, not an exact figure preset
```

The reference preset is 20,000 E + 5,000 I neurons, fixed C_E=1,000/C_I=250, 10 seconds of measurement, and 1,024 approximation trials. Inspect memory and runtime before increasing sizes: this has 31.25 million recurrent synapses. Quick runs reduce both size and in-degree and therefore change the model's fluctuation strength, not just runtime.

## Model choices

- LIF: tau=20 ms, threshold=20 mV, reset=10 mV, absolute refractory=2 ms; voltage is relative to zero leak reversal.
- Euler dt=0.1 ms, excitatory voltage jump J=0.1 mV, inhibitory jump -gJ, delay=1.5 ms. Refractory voltage is clamped and incoming events during refractoriness are discarded by both implementations. Reset is immediate at threshold in Brian2.
- Fixed E/I in-degree, random sampling without duplicate edges; autapses allowed. This replaces the uploaded notebooks' Bernoulli connectivity, which has variable in-degree. This is an explicit scientific change to provide a homogeneous baseline for the closure.
- Default **constant external drive**, RI=30 mV, follows the supplied notebooks. `drive='poisson'` switches to independent Brian2 PoissonInput in BOTH methods, with eta = nu_ext/nu_thr and nu_thr = threshold/(J C_E tau). Brian2 may approximate its binomial input draw by a normal distribution when appropriate; this is its efficient aggregated Poisson-input mechanism.
- `g` is a synaptic weight ratio, not a conductance. `eta` is ignored in DC mode; `dc_mv` is ignored in Poisson mode.

## Gaussian self-consistency

For homogeneous independent presynaptic statistics:

- Mean recurrent voltage increment per second: J(C_E - g C_I) r.
- Two-sided fluctuation spectrum: J²(C_E + g² C_I) S(f).

SciPy FFTs synthesize Gaussian voltage increments. Brian2 applies the increments to batches of independent LIF trials, with matching external drive, numerical integrator, threshold, and refractory convention. Each output rate and spectrum becomes the next generation's input. The first generation uses independent Poisson recurrent streams at the initial rate; later generations use Gaussian input shaped by the preceding output spectrum. The iteration is independently initialized; it does not fit to the simulated network.

No renewal approximation is included. `mixing=1` gives direct updates; lower mixing is optional damping, not the particular stabilization procedure of Pena et al. 2018. Rate/spectrum residuals must both satisfy tolerance for three successive generations. Exhausting the iteration budget reports `converged=False`.

The closure ignores presynaptic cross-correlations and assumes asynchronous activity. A synchronized network cannot be expected to match. A common synaptic delay cancels out of individual input auto-spectra under these assumptions, but can change synchrony in the full network.

## Spectral convention

Spectra are averages of **individual-neuron spike-train spectra**, not spectra of the population-average rate. Use |FFT(spike counts)|² / duration in seconds, with no positive-frequency doubling. A Poisson process has a flat spectrum equal to its rate. DC is removed. FFT bins are calculated from dt and duration; repeated spikes in a bin accumulate rather than overwrite.

Both methods use the same dt and spectral routine. Finite bins introduce high-frequency discretization effects; inspect frequencies well below Nyquist and test dt sensitivity. Feedback approximates the unmeasured near-zero spectrum using the first positive bin. Generated Gaussian records are twice the required length and cropped to reduce periodic-wrap effects. No hidden smoothing is used in comparison errors.

## Efficiency and readability

- Sparse Brian2 connections; no dense adjacency matrix.
- Cython backend by default (initial compilation costs time); NumPy fallback via `backend='numpy'`.
- Sampled E/I spike monitoring and full population rate; no full voltage traces.
- Batched SciPy real FFTs and Gaussian trials bound working memory.
- Saved compressed outputs; comparison never reruns simulations.
- Short notebook sections with shared implementation in `sc_cortex/`.

Performance is workload-dependent. This has not been benchmarked against the original notebooks, so no speedup factor is claimed.

## What changed from the originals

`Copy of MAIN:DUMMER (1).ipynb` has the more compact baseline (reset 10 mV), but includes an undefined final `run_and_plot_spectrum` call. `Another copy of MAIN:DUMMER 2.ipynb` adds g sweeps, redefines a simulation function, and switches reset from 0 to 10 mV later. Neither of these two older uploads contains the iterative Gaussian implementation. The subsequently supplied HOLYKALE.ipynb does contain it and is the more complete scientific reference. Both record all network spikes, use hard-coded frequency spacing, and normalize the individual and averaged spectra differently. This implementation makes those choices explicit and consistent. It does not claim numerical equivalence to the originals: connectivity and initialization are changed, burn-in is added, and spectral processing is corrected.

## Checks

```bash
python -m unittest discover -s tests -v
```

Tests cover Poisson PSD normalization, Gaussian variance and colored spectral shape, network/iteration execution, both drive modes, and saved-result comparison. Passing these tests verifies mechanics, not agreement with the papers. Before presenting a reproduction: specify a figure, match its connectivity and parameters, verify asynchronous activity, check numerical time-step sensitivity, repeat seeds, and quantify spectral and firing-rate differences.

## References

- Brunel (2000), *Dynamics of Sparsely Connected Networks of Excitatory and Inhibitory Spiking Neurons*: https://doi.org/10.1023/A:1008925309027
- Brian2 Brunel example: https://brian2.readthedocs.io/en/stable/examples/frompapers.Brunel_2000.html
- Dummer, Wieland & Lindner (2014): https://doi.org/10.3389/fncom.2014.00104
- Pena et al. (2018): https://doi.org/10.3389/fncom.2018.00009

## Latest reference: HOLYKALE.ipynb

Source: https://colab.research.google.com/drive/1aI3R5MbxPIZkWlHIYDf2zDR4EYCMPv7P

This is the most complete supplied notebook: network, Gaussian iteration, rate/CV comparisons, and additional diagnostics. Its saved outputs report network 70.59 Hz/CV 0.197 and iteration 70.46 Hz/CV 0.190 (not rerun here). It explicitly targets Dummer Figure 8B.

Key audit findings and intentional changes:

- Its actual population is 100,000 E + 25,000 I, not the 2,500 I stated in a comment. With C_E=1,000/C_I=250 this is 156.25 million synapses. The smaller `reference` preset here has 20,000 E + 5,000 I with the same in-degrees; it is not a size-matched rerun.
- Its sampling with `randint` permits duplicate edges. This version samples without replacement; autapses remain allowed. That is a topology difference to assess, not merely a speed optimization.
- Its N×3,000 dense spike matrix alone uses approximately 3 GB, before FFT arrays. This version processes only sampled neurons in bounded batches.
- Network spectrum division by 2 is inconsistent with a 3-second record. Its Gaussian estimator is a one-sided Welch PSD; overlaying these directly is not consistently normalized. Both outputs here use one shared two-sided periodogram convention and the same frequency grid.
- Its function named `simulate_lif_vectorized` actually loops through five million Python time steps per 500-second trial. Here Brian2 runs independent trials in compiled batches. Several short trials are not identical to a single 500-second realization; long-time correlations need a longer `duration` and convergence checks.
- Its fixed spectral amplitudes/random phases are replaced with filtered Gaussian samples. Variance and spectral-shape tests check this new generator.
- Its first-generation recurrent Poisson input and selectable initial rate (15 or 71 Hz) are retained. Optional burn-in and common Brian2 event/refractory handling make comparisons consistent; exact equivalence to the original scalar loop is not asserted.
- CV is retained per recorded neuron/trial; means exclude traces with fewer than three spikes. No frequency-axis smoothing is performed.
