# SC_Cortex

Readable notebooks based on the supplied `HOLYKALE.ipynb`. The original notebook is preserved unchanged in [`01_Original_Colab/`](./01_Original_Colab/). [`G_Comparison_Recurrent_LIF.ipynb`](./01_Original_Colab/G_Comparison_Recurrent_LIF.ipynb) in that same folder runs the original network across multiple relative inhibitory strengths.

## Notebook order

1. [`02_Brunel_SNN/Brunel_SNN.ipynb`](./02_Brunel_SNN/Brunel_SNN.ipynb) — faithful recurrent SNN, with the original dense spectrum calculation retained and a batched equivalent.
2. [`03_Gaussian_Approximation/Gaussian_Approximation.ipynb`](./03_Gaussian_Approximation/Gaussian_Approximation.ipynb) — readable 15-generation Gaussian iteration, selectable at 15 or 71 Hz.
3. [`04_Comparison/Comparison.ipynb`](./04_Comparison/Comparison.ipynb) — loads saved NPZ/JSON results and never reruns simulations.
4. [`01_Original_Colab/G_Comparison_Recurrent_LIF.ipynb`](./01_Original_Colab/G_Comparison_Recurrent_LIF.ipynb) — opt-in comparison of `g = 3.0, 4.0, 4.5, 6.0`, the relative inhibitory strengths (`-g*J`).

The individual recurrent LIF condition notebooks are organized by inhibitory strength in [`01_Original_Colab/`](./01_Original_Colab/): `3.0/`, `4.0/`, `4.5/`, and `6.0/`. Each notebook saves its outputs under `01_Original_Colab/results/.../`. Notebook root discovery works when launched from the repository root, `01_Original_Colab`, or any condition subfolder.
Run the immediate “Save the completed recurrent simulation” cell after the network/FFT cells to persist results before starting the Gaussian analysis. If the kernel has been restarted, in-memory results are gone and the simulation must be rerun.

Additional condition notebooks cover `V_r = 0 mV` for `g = 4.0` and `g = 4.5`, with `J = 0.1 mV` and `J = 1.0 mV`. Their outputs are saved under `01_Original_Colab/results/G..._VR0_J.../`.

Install dependencies with:

```bash
python -m pip install -r requirements.txt
jupyter lab
```

All full simulations are opt-in. The notebooks default to `RUN_SIMULATION = False` so opening or testing them does not launch the 125,000-neuron network or 500-second approximation.

## Reproducibility and outputs

Each source notebook saves a descriptive run ID, parameters and units, seed, software versions, duration, transient handling, analysis convention, runtime, and numerical arrays. Numeric data use compressed NPZ; metadata use JSON. Figures are written separately and generated outputs are ignored by Git.

The SNN preserves HOLYKALE's 100,000 excitatory and 25,000 inhibitory neurons, fixed incoming counts (`C_E=1000`, `C_I=250`), replacement sampling, duplicate edges, autapses, initialization, seed, Euler step, drive, and 3-second duration. The Gaussian notebook preserves the original 500-second trial, 0.1 ms step, 15 generations, first-generation Poisson input, later colored-noise construction, LIF timing, and Welch settings.

The comparison reports original conventions separately from a clearly labeled corrected view. The original SNN divides FFT power by two; Welch is one-sided; and the two measurements have different durations and frequency grids. No smoothing is used for numerical errors.

The branch `backup/pre-holy-kale-reorganization` preserves the repository state and local changes that existed before this reorganization.

## Pena et al. (2018) replication

The Gaussian notebook is the replication entry point for Pena et al., *Self-Consistent
Scheme for Spike-Train Power Spectra in Heterogeneous Sparse Networks* (Frontiers in
Computational Neuroscience 12:9, doi:10.3389/fncom.2018.00009). Its
`AVERAGE_RATE_GENERATIONS` control implements the stabilizing rate average described
by Equation 11 and Figure 3 of that paper, and the saved metadata records the
replication target. The Gaussian replication is enabled by default. Set `RUN_SIMULATION = False` in
[`Gaussian_Approximation.ipynb`](03_Gaussian_Approximation/Gaussian_Approximation.ipynb)
to skip the 500-second iteration. The large recurrent SNN remains opt-in.

This is the homogeneous fixed-in-degree case. The paper's heterogeneous
subpopulation and Erdős-Rényi extensions are not silently claimed as reproduced.
