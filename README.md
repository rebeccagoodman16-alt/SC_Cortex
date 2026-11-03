# SC_Cortex

Readable notebooks based on the supplied `HOLYKALE.ipynb`. The original notebook is preserved unchanged in [`01_Original_Colab/`](./01_Original_Colab/).

## Notebook order

1. [`02_Brunel_SNN/Brunel_SNN.ipynb`](./02_Brunel_SNN/Brunel_SNN.ipynb) — faithful recurrent SNN, with the original dense spectrum calculation retained and a batched equivalent.
2. [`03_Gaussian_Approximation/Gaussian_Approximation.ipynb`](./03_Gaussian_Approximation/Gaussian_Approximation.ipynb) — readable 15-generation Gaussian iteration, selectable at 15 or 71 Hz.
3. [`04_Comparison/Comparison.ipynb`](./04_Comparison/Comparison.ipynb) — loads saved NPZ/JSON results and never reruns simulations.

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
