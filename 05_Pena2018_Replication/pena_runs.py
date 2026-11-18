"""Cached, figure-level runs shared by the Figure 4-13 notebooks.

Every function returns a dict of arrays and stores it in ``results/`` keyed by a hash
of its parameters, so a notebook re-run (or another figure using the same run) loads
it instead of recomputing. Network sizes are scaled down by default (see README).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

import pena_network as pn
import pena_scheme as ps
from pena2018_params import params_for

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)


def net_common(p: dict, dt: float | None = None) -> dict:
    return {"dt": dt or p["dt"], "V_th": p["V_th"], "V_r": p["V_r"], "tau_ref": p["tau_ref"],
            "delay": p["tau_D"], "tau_s": p.get("tau_s", 0.0),
            "T_window": p["T_window"], "T_transient": p["T_transient"]}


def _scheme_p(p):
    return {k: p[k] for k in ("dt", "V_th", "V_r", "tau_ref", "tau_s", "T_window", "T_transient")}


# --------------------------------------------------------------------------- homogeneous
def homogeneous_scheme(p: dict, n_generations=40, n_trials=1000, average=None, seed=0,
                       force=False, rescale=None):
    """One unit for a homogeneous E/I network (E and I cells identical)."""
    A = ([[(p["C_E"] - p["g"] * p["C_I"]) * p["J"]]], [[(p["C_E"] + p["g"] ** 2 * p["C_I"]) * p["J"] ** 2]])
    key = {"kind": "homogeneous", **_scheme_p(p), "tau_m": p["tau_m"], "RI_ext": p["RI_ext"],
           "C_E": p["C_E"], "C_I": p["C_I"], "J": p["J"], "g": p["g"],
           "n_generations": n_generations, "n_trials": n_trials, "average": average, "seed": seed}
    rescale = (average != 1) if rescale is None else rescale
    if rescale:  # key added only when on, so non-averaged runs keep their cache
        key["rescale_spectrum"] = True
    def run():
        nu0 = ps.mean_field_rates([p["tau_m"]], p["RI_ext"], None, None, p, coefs=A)
        out = ps.run_populations([p["tau_m"]], p["RI_ext"], None, None, p, n_generations,
                                 n_trials, average=average, nu0=nu0, seed=seed,
                                 n_final=10, coefs=A, rescale_spectrum=rescale)
        out["nu0"] = nu0
        return out
    return ps.cached("scheme_homog", key, run, RESULTS, force)


def homogeneous_network(p: dict, N_E: int, n_windows=10, dt=None, seed=1, record=500,
                        force=False):
    pops, conns = pn.brunel_network(N_E, p["gamma"], p["C_E"], p["J"], p["g"],
                                    tau_m=p["tau_m"], RI_ext=p["RI_ext"])
    common = net_common(p, dt)
    key = {"kind": "homogeneous_net", "N_E": N_E, "n_windows": n_windows, "seed": seed,
           "record": record, **common, "J": p["J"], "g": p["g"], "C_E": p["C_E"],
           "gamma": p["gamma"], "tau_m": p["tau_m"], "RI_ext": p["RI_ext"]}
    return ps.cached("net_homog", key, lambda: pn.simulate_network(
        pops, conns, common, n_windows, record={"E": record, "I": 0}, seed=seed), RESULTS, force)


# --------------------------------------------------------------------------- populations
def population_scheme(name, tau_ms, RI_ext, C, W, p, n_generations=40, n_trials=1000,
                      average=None, seed=0, force=False, rescale=None):
    C = np.asarray(C, float); W = np.asarray(W, float)
    key = {"kind": name, **_scheme_p(p), "tau": list(map(float, tau_ms)), "RI_ext": RI_ext,
           "C": C.tolist(), "W": W.tolist(), "n_generations": n_generations,
           "n_trials": n_trials, "average": average, "seed": seed}
    rescale = (average != 1) if rescale is None else rescale
    if rescale:
        key["rescale_spectrum"] = True
    def run():
        nu0 = ps.mean_field_rates(tau_ms, RI_ext, C, W, p)
        out = ps.run_populations(tau_ms, RI_ext, C, W, p, n_generations, n_trials,
                                 average=average, nu0=nu0, seed=seed, n_final=10,
                                 rescale_spectrum=rescale)
        out["nu0"] = nu0
        return out
    return ps.cached(f"scheme_{name}", key, run, RESULTS, force)


def two_pop(gE, gI, p, N_E=None, n_windows=10, scheme_kw=None, seed=1, force=False):
    """Figure 6/7 setup: tau_E = 20 ms, tau_I = 19 ms, separate g for E and I targets."""
    J, CE, CI = p["J"], p["C_E"], p["C_I"]
    C = [[CE, CI], [CE, CI]]
    W = [[J, -gE * J], [J, -gI * J]]
    out = {}
    if N_E is None:  # scheme only
        avg = 1 if max(gE, gI) < 4 else None
        return population_scheme(f"twopop_gE{gE}_gI{gI}", [p["tau_E"], p["tau_I"]], p["RI_ext"],
                                 C, W, p, average=avg, **(scheme_kw or {}), force=force)
    pops, conns = pn.brunel_network(N_E, p["gamma"], CE, J, gE, tau_m=p["tau_E"],
                                    RI_ext=p["RI_ext"], tau_I=p["tau_I"], g_I=gI)
    common = net_common(p)
    key = {"kind": "twopop_net", "gE": gE, "gI": gI, "N_E": N_E, "n_windows": n_windows,
           "seed": seed, **common, "J": J, "C_E": CE, "tau_E": p["tau_E"], "tau_I": p["tau_I"]}
    return ps.cached("net_twopop", key, lambda: pn.simulate_network(
        pops, conns, common, n_windows, seed=seed), RESULTS, force)


# --------------------------------------------------------------------------- Figure 8
def three_pop_spec(p, N_E):
    J, g, CE = p["J"], p["g"], p["C_E"]
    names = ["RS", "LTS", "FS"]
    taus = [p["tau_RS"], p["tau_LTS"], p["tau_FS"]]
    sizes = [N_E, int(0.25 * N_E), int(0.05 * N_E)]
    Cin = [CE, int(0.25 * CE), int(0.05 * CE)]
    w_src = {"RS": J, "LTS": -g * J, "FS": -g * J}
    C = np.zeros((3, 3)); W = np.zeros((3, 3))
    for a, tgt in enumerate(names):
        for b, src in enumerate(names):
            C[a, b] = Cin[b]
            W[a, b] = w_src[src] * (p["w_E_to_FS"] if (src == "RS" and tgt == "FS") else 1.0)
    pops = [{"name": n, "N": s, "tau_m": t, "RI_ext": p["RI_ext"]} for n, s, t in zip(names, sizes, taus)]
    conns = [{"target": names[a], "source": names[b], "K": int(C[a, b]), "w": float(W[a, b])}
             for a in range(3) for b in range(3)]
    return names, taus, C, W, pops, conns


def module_spec(p, N_E):
    """Two modules (E1, I1, E2, I2). Module 2 takes half its E and I inputs from module 1.
    Weights are set by the target module (J1 into module 1, J2 into module 2)."""
    J1, J2 = p["module_J"]; g = p["g"]; CE, CI = p["C_E"], p["C_I"]
    names = ["E1", "I1", "E2", "I2"]
    sizes = [N_E, int(p["gamma"] * N_E)] * 2
    C = np.zeros((4, 4)); W = np.zeros((4, 4))
    for a, tgt in enumerate(names):
        J = J1 if tgt.endswith("1") else J2
        for b, src in enumerate(names):
            K = CE if src.startswith("E") else CI
            if tgt.endswith("1"):
                C[a, b] = K if src.endswith("1") else 0
            else:
                C[a, b] = K // 2
            W[a, b] = J if src.startswith("E") else -g * J
    pops = [{"name": n, "N": s, "tau_m": p["tau_m"], "RI_ext": p["RI_ext"]} for n, s in zip(names, sizes)]
    conns = [{"target": names[a], "source": names[b], "K": int(C[a, b]), "w": float(W[a, b])}
             for a in range(4) for b in range(4) if C[a, b] > 0]
    return names, [p["tau_m"]] * 4, C, W, pops, conns


def multi_network(name, pops, conns, p, n_windows=10, seed=1, force=False):
    common = net_common(p)
    key = {"kind": name, "pops": pops, "conns": conns, "n_windows": n_windows, "seed": seed, **common}
    return ps.cached(f"net_{name}", key, lambda: pn.simulate_network(
        pops, conns, common, n_windows, seed=seed), RESULTS, force)


# --------------------------------------------------------------------------- Erdos-Renyi
def er_params(g, weights="fixed"):
    p = params_for(10)
    p.update({"g": g, "weights": weights})
    return p


def er_scheme(g, weights="fixed", M=50, n_generations=20, n_trials=40, seed=0, force=False):
    p = er_params(g, weights)
    stabilize = g > 5
    key = {"kind": "er_scheme", **_scheme_p(p), "g": g, "weights": weights, "M": M,
           "n_generations": n_generations, "n_trials": n_trials, "seed": seed,
           "J": p["J"], "C_E": p["C_E"], "N_E": p["N_E"], "RI_ext": p["RI_ext"],
           "stabilize": stabilize}
    def run():
        A = ([[(p["C_E"] - g * p["C_I"]) * p["J"]]], [[(p["C_E"] + g ** 2 * p["C_I"]) * p["J"] ** 2]])
        nu0 = float(ps.mean_field_rates([p["tau_m"]], p["RI_ext"], None, None, p, coefs=A)[0])
        out = ps.run_er_scheme(p, M, n_generations, n_trials, weights=weights,
                               stabilize=stabilize, nu0=nu0, seed=seed)
        out["nu0"] = np.array(nu0)
        return out
    return ps.cached("scheme_er", key, run, RESULTS, force)


def er_network(g, weights="fixed", N_E=10_000, n_windows=20, record_input=True, seed=1,
               force=False):
    """ER network (connection probability C/N). With exponential weights the input
    currents of 1,000 E cells are also recorded (Figures 12-13)."""
    p = er_params(g, weights)
    pops, conns = pn.brunel_network(N_E, p["gamma"], p["C_E"], p["J"], g, tau_m=p["tau_m"],
                                    RI_ext=p["RI_ext"], er=True, weights=weights)
    common = net_common(p)
    rin = ("E", 1000) if (record_input and weights == "exponential") else None
    key = {"kind": "er_net", "g": g, "weights": weights, "N_E": N_E, "n_windows": n_windows,
           "seed": seed, "record_input": rin, **common, "J": p["J"], "C_E": p["C_E"]}
    return ps.cached("net_er", key, lambda: pn.simulate_network(
        pops, conns, common, n_windows, record={"E": 1000, "I": 0}, record_input=rin,
        seed=seed), RESULTS, force)


def gaussian_surrogate(g, net, n_trials=20, seed=2, force=False):
    """Figure 12: drive an isolated LIF with Gaussian noise that has the same mean and
    spectrum as each recorded network neuron's input current."""
    p = er_params(g, "exponential")
    key = {"kind": "surrogate", "g": g, "n_trials": n_trials, "seed": seed,
           "net_runtime": float(net["runtime_s"]), **_scheme_p(p)}
    def run():
        rng = np.random.default_rng(seed)
        mu = p["RI_ext"] + net["in_mean"]
        r, S, _ = ps.simulate_units(mu, np.full(mu.size, p["tau_m"]), net["in_S"].astype(float),
                                    net["f_full"], n_trials, p, rng)
        keep = net["f_full"] <= net["f"][-1] + 1e-9
        return {"rates": r, "S": S[:, keep].astype(np.float32)}
    return ps.cached("surrogate", key, run, RESULTS, force)
