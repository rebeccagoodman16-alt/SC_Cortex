# SC_Cortex

Updated: November 7, 2026

Readable notebooks based on the supplied `HOLYKALE.ipynb`. The original notebook is preserved unchanged in [`01_Original_Colab/`](./01_Original_Colab/). [`G_Comparison_Recurrent_LIF.ipynb`](./01_Original_Colab/G_Comparison_Recurrent_LIF.ipynb) in that same folder runs the original network across multiple relative inhibitory strengths.

## Notebook order

1. [`02_Brunel_SNN/Brunel_SNN.ipynb`](./02_Brunel_SNN/Brunel_SNN.ipynb) — faithful recurrent SNN, with the original dense spectrum calculation retained and a batched equivalent.
2. [`05_Pena2018_Replication/`](./05_Pena2018_Replication/) — figure-by-figure replication of Pena et al. (2018); see its README for the figure roadmap. Includes the Fig 8A `heterogeneous_networks` package.
3. [`01_Original_Colab/G_Comparison_Recurrent_LIF.ipynb`](./01_Original_Colab/G_Comparison_Recurrent_LIF.ipynb) — opt-in comparison of `g = 3.0, 4.0, 4.5, 6.0`, the relative inhibitory strengths (`-g*J`).

The individual recurrent LIF condition notebooks are organized by inhibitory strength in [`01_Original_Colab/`](./01_Original_Colab/): `3.0/`, `4.0/`, `4.5/`, and `6.0/`. Each notebook saves its outputs under `01_Original_Colab/results/.../`. Notebook root discovery works when launched from the repository root, `01_Original_Colab`, or any condition subfolder.
The Figure 10 notebook [`Figure10_G4.5_CE100_CI25_J1.0.ipynb`](./01_Original_Colab/4.5/Figure10_G4.5_CE100_CI25_J1.0.ipynb) reproduces the larger-amplitude condition with `J = 1 mV`, `C_E = 100`, `C_I = 25`, and `g = 4.5`. Set `V_R_MV = 0` for panel A or `10` for panel B; each run writes to a separate condition directory.
Run the immediate “Save the completed recurrent simulation” cell after the network/FFT cells to persist results before starting the Gaussian analysis. If the kernel has been restarted, in-memory results are gone and the simulation must be rerun.

Additional condition notebooks cover `V_r = 0 mV` for `g = 4.0` and `g = 4.5`, with `J = 0.1 mV` and `J = 1.0 mV`. Their outputs are saved under `01_Original_Colab/results/G..._VR0_J.../`.

Install dependencies with:

```bash
python -m pip install -r requirements.txt
jupyter lab
```

All full simulations are opt-in. The notebooks default to `RUN_SIMULATION = False` so opening or testing them does not launch the 125,000-neuron network.

## Reproducibility and outputs

Each source notebook saves a descriptive run ID, parameters and units, seed, software versions, duration, transient handling, analysis convention, runtime, and numerical arrays. Numeric data use compressed NPZ; metadata use JSON. Figures are written separately and generated outputs are ignored by Git.

The SNN preserves HOLYKALE's 100,000 excitatory and 25,000 inhibitory neurons, fixed incoming counts (`C_E=1000`, `C_I=250`), replacement sampling, duplicate edges, autapses, initialization, seed, Euler step, drive, and 3-second duration.

The branch `backup/pre-holy-kale-reorganization` preserves the repository state and local changes that existed before this reorganization.

## Pena et al. (2018) replication

[`05_Pena2018_Replication/`](./05_Pena2018_Replication/) rebuilds Pena et al., *Self-Consistent
Scheme for Spike-Train Power Spectra in Heterogeneous Sparse Networks* (Frontiers in
Computational Neuroscience 12:9, doi:10.3389/fncom.2018.00009) one notebook per figure.
See its README for the figure roadmap and status.


## Automatic result saving

Simulation notebooks and the heterogeneous model now reuse matching saved runs
and recover interrupted work. See [CHECKPOINTS.md](CHECKPOINTS.md) for controls,
cache locations, restart instructions, and validation commands.
