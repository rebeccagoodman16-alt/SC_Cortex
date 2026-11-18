"""Shared parameters for the Pena et al. (2018) replication notebooks.

Units: ms, mV, Hz. ``TABLE1`` holds the paper's standard values; ``FIGURES`` holds
only the per-figure overrides stated in the captions. Use ``params_for(n)`` to get
the merged dictionary for figure ``n``. Entries marked VERIFY still need checking
against the published PDF.
"""

from __future__ import annotations

from copy import deepcopy

TABLE1 = {
    # LIF neuron
    "tau_m": 20.0,          # membrane time constant (ms)
    "V_th": 20.0,           # threshold (mV)
    "V_r": 10.0,            # reset (mV)
    "tau_ref": 2.0,         # refractory period (ms)
    "RI_ext": 30.0,         # external drive (mV)
    # Network
    "N_E": 100_000,
    "gamma": 0.25,          # N_I = gamma N_E, C_I = gamma C_E
    "C_E": 1000,
    "J": 0.1,               # EPSP amplitude (mV)
    "g": 5.0,               # relative inhibition; VERIFY Table 1 default
    "tau_D": 1.5,           # synaptic delay (ms)
    "tau_s": 0.0,           # synaptic filter time constant; 0 = delta synapses
    # Scheme / spectral estimation
    "dt": 0.1,              # VERIFY: not in extracted text; repo convention
    "T_window": 2000.0,     # analysis window (ms), df = 1/T
    "T_transient": 1000.0,  # discarded transient (ms)
    "n_trials": 10_000,     # trials per generation
    "n_generations": 30,
    "M_neurons": 50,        # representative neurons per generation (ER scheme)
}

FIGURES = {
    3: {"g": 5.5, "J": 0.2, "tau_s": 10.0, "RI_ext": 30.0,
        "target_network_rate_Hz": 9.1},
    4: {"g": 5.0, "RI_ext": 24.0, "tau_D": 0.55, "tau_ref": 0.5,
        "N_E_values": [8_000, 80_000], "T_long": 100_000.0},
    5: {"g": 5.0, "RI_ext": 24.0, "tau_D": 0.55, "tau_ref": 0.5,  # "as in Figure 4"
        "J": 0.2, "tau_s_panel_BC": 10.0},
    6: {"tau_E": 20.0, "tau_I": 19.0,
        "gE_gI": [(4.2, 4.0), (3.7, 3.7), (4.25, 3.6)],
        "reported_rates_Hz": {"B": (128.9, 129.9), "C": (0.1, 7.4)}},
    7: {"gE": 4.2, "gI": 4.0, "tau_E": 20.0, "tau_I": 19.0},
    8: {"g": 4.0,  # A: RS/LTS/FS, see heterogeneous_networks/; B: two modules
        "tau_RS": 20.0, "tau_LTS": 19.0, "tau_FS": 21.0, "w_E_to_FS": 1.4,
        "module_J": (0.1, 0.27), "module_size": 125_000},
    9: {"M_neurons": 50, "generations_used": (6, 20)},
    10: {"J": 0.1, "tau_D": 2.0, "C_E_mean": 1000, "C_I_mean": 250,
         "trials_per_neuron": 100, "trial_length": 10_000.0},
    11: {"J": 0.1, "tau_D": 2.0, "weights": "exponential"},
    12: {"g_values": [4.0, 6.0], "n_neurons": 1000, "bin_ms": 2.0},
    13: {"g_values": [4.0, 6.0], "n_neurons": 1000, "bin_ms": 2.0,
         "rate_window_Hz": (20.0, 100.0)},
}


def params_for(figure: int) -> dict:
    """Return Table 1 defaults merged with the overrides for ``figure``."""
    p = deepcopy(TABLE1)
    p.update(deepcopy(FIGURES.get(figure, {})))
    p["N_I"] = int(p["gamma"] * p["N_E"])
    p["C_I"] = int(p["gamma"] * p["C_E"])
    p["figure"] = figure
    return p
