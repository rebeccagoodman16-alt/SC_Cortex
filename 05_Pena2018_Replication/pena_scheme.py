"""Homogeneous self-consistent scheme of Pena et al. (2018), Sections 2.1-2.4.

Equations implemented (numbering as in the paper):

* Eq. 1/15  LIF:  tau_m dv/dt = -v + mu + RI_ext + RI_G(t), threshold v_th,
            reset v_r after a refractory period tau_ref.
* Eq. 5     S_xx(f) = <|x~(f)|^2> / T   (two-sided, -> nu as f -> inf).
* Eq. 10    K(t) = theta(t) exp(-t/tau_s) / tau_s, so |K~(f)|^2 = 1 / (1 + (2 pi f tau_s)^2).
* Eq. 11    nu_hat_n = mean of the rates of the past n generations.
* Eq. 12    mu = tau_m J (C_E - g C_I) nu   (homogeneous population).
* Eq. 13    S_in(f) = tau_m^2 J^2 |K~(f)|^2 (C_E + g^2 C_I) S_xx(f).
* Eq. 14    RI~_G(f) = sqrt(S_in(f) / (2 df)) (eta_r + i eta_i), then inverse FT.

Units: time in seconds, voltage in mV, rate in Hz (parameter dicts use ms; converted here).
"""

from __future__ import annotations

import numpy as np
from scipy import integrate, special

ZETA_HALF = 1.4603545088095868  # |zeta(1/2)|, Brunel & Sergi (1998)


# --------------------------------------------------------------------------- helpers
def filter_power(f: np.ndarray, tau_s_ms: float) -> np.ndarray:
    """|K~(f)|^2 of the exponential synaptic filter (Eq. 10); 1 for delta synapses."""
    if tau_s_ms <= 0:
        return np.ones_like(f)
    return 1.0 / (1.0 + (2 * np.pi * f * tau_s_ms * 1e-3) ** 2)


def mean_input(nu: float, p: dict) -> float:
    """Total mean drive RI_ext + mu (Eq. 12) in mV."""
    tau = p["tau_m"] * 1e-3
    return p["RI_ext"] + tau * p["J"] * (p["C_E"] - p["g"] * p["C_I"]) * nu


def input_spectrum(f: np.ndarray, S_out: np.ndarray, p: dict) -> np.ndarray:
    """Input-noise spectrum (Eq. 13) in mV^2/Hz from the output spike-train spectrum."""
    tau = p["tau_m"] * 1e-3
    gain = tau**2 * p["J"] ** 2 * (p["C_E"] + p["g"] ** 2 * p["C_I"])
    return gain * filter_power(f, p["tau_s"]) * S_out


def gaussian_noise(S_in_fn, n_trials: int, n_steps: int, dt: float,
                   rng: np.random.Generator) -> np.ndarray:
    """Colored Gaussian noise with two-sided spectrum S_in (Eq. 14), zero mean.

    ``S_in_fn(f)`` returns the spectrum on the rfft grid of the n_steps window.
    The DC bin is zero: the mean input is supplied separately by Eq. 12.
    """
    T = n_steps * dt
    f = np.fft.rfftfreq(n_steps, dt)
    amp = np.sqrt(S_in_fn(f) * T / 2.0) / dt
    X = amp * (rng.standard_normal((n_trials, f.size))
               + 1j * rng.standard_normal((n_trials, f.size)))
    X[:, 0] = 0.0
    if n_steps % 2 == 0:  # Nyquist bin must be real
        X[:, -1] = amp[-1] * np.sqrt(2.0) * rng.standard_normal(n_trials)
    return np.fft.irfft(X, n=n_steps, axis=1)


def simulate_lif(mu_total: float, noise: np.ndarray, p: dict, n_transient: int,
                 rng: np.random.Generator) -> np.ndarray:
    """Euler-integrate LIF trials (rows of ``noise``); return spike counts per bin
    after the transient, shape (n_trials, n_steps - n_transient)."""
    dt = p["dt"] * 1e-3
    tau = p["tau_m"] * 1e-3
    n_trials, n_steps = noise.shape
    ref_steps = int(round(p["tau_ref"] / p["dt"]))
    v = rng.uniform(p["V_r"], p["V_th"], n_trials)
    ref = np.zeros(n_trials, dtype=np.int32)
    out = np.zeros((n_trials, n_steps - n_transient), dtype=np.uint8)
    k = dt / tau
    for t in range(n_steps):
        active = ref == 0
        v = np.where(active, v + k * (-v + mu_total + noise[:, t]), v)
        ref = np.where(active, 0, ref - 1)
        fired = v >= p["V_th"]
        if fired.any():
            v[fired] = p["V_r"]
            ref[fired] = ref_steps
            if t >= n_transient:
                out[fired, t - n_transient] = 1
    return out


def spike_spectrum(counts: np.ndarray, dt: float):
    """Trial-averaged two-sided spike-train spectrum (Eq. 5) and mean rate."""
    T = counts.shape[1] * dt
    f = np.fft.rfftfreq(counts.shape[1], dt)
    xf = np.fft.rfft(counts.astype(float), axis=1)  # sum of exp(-2 pi i f t_k)
    S = (np.abs(xf) ** 2).mean(axis=0) / T
    rate = counts.sum() / (counts.shape[0] * T)
    S[0] = np.nan  # DC carries the nu^2 T delta peak, not fluctuations
    return f, S, rate


# --------------------------------------------------------------------------- scheme
def run_scheme(p: dict, n_generations: int, n_trials: int, average: int | str | None,
               nu0: float, seed: int = 0, batch: int = 1000, verbose: bool = True):
    """Iterate the homogeneous scheme with the rate-averaging of Section 2.3 (Fig 3).

    Generation 0 is not simulated: it is the starting rate ``nu0`` with a flat
    (Poisson) spectrum S = nu0, i.e. Gaussian white noise. Generation n >= 1 is driven
    with mean input from the averaged rate nu_hat_{n-1} (Eq. 12) and noise built from
    the previous generation's output spectrum (Eqs. 13-14).

    average (how nu_hat_n is formed from the output rates r_0 = nu0, r_1, ..., r_n):
        1        no averaging, nu_hat_n = r_n                       (Fig 3A)
        2        nu_hat_n = (nu_hat_{n-1} + r_n) / 2                 (Fig 3B)
        None     nu_hat_n = mean(r_0, ..., r_n), all past generations (Fig 3C)
        "last2"  nu_hat_n = (r_{n-1} + r_n) / 2  (alternative reading of 3B; it is
                 linearly unstable when d nu_out / d nu_in < -2, as here)
    The paper plots nu_hat_n against n. These conventions reproduce Fig 3A-C
    generation by generation; they are inferred from the published curves.
    Returns per-generation output rates r, averaged rates nu_hat, input rates, spectra.
    """
    rng = np.random.default_rng(seed)
    dt = p["dt"] * 1e-3
    n_win = int(round(p["T_window"] / p["dt"]))
    n_tr = int(round(p["T_transient"] / p["dt"]))
    n_steps = n_win + n_tr

    f_prev = np.array([0.0, 1.0 / dt])
    S_prev = np.array([nu0, nu0])            # generation 0: flat spectrum (white noise)
    rates, nu_hat, nu_inputs, spectra = [nu0], [nu0], [np.nan], []
    for gen in range(1, n_generations + 1):
        nu_in = nu_hat[-1]
        S_in_fn = lambda f, f_prev=f_prev, S_prev=S_prev: input_spectrum(f, np.interp(f, f_prev, S_prev), p)
        mu_total = mean_input(nu_in, p)
        S_acc = None
        spikes = 0
        for b0 in range(0, n_trials, batch):
            nb = min(batch, n_trials - b0)
            noise = gaussian_noise(S_in_fn, nb, n_steps, dt, rng)
            counts = simulate_lif(mu_total, noise, p, n_tr, rng)
            f, S_b, _ = spike_spectrum(counts, dt)
            S_acc = S_b * nb if S_acc is None else S_acc + S_b * nb
            spikes += counts.sum()
        S = S_acc / n_trials
        rate = spikes / (n_trials * n_win * dt)
        rates.append(rate)
        nu_inputs.append(nu_in)
        spectra.append(S)
        if average == 1:
            nu_hat.append(rate)
        elif average == 2:
            nu_hat.append(0.5 * (nu_hat[-1] + rate))
        elif average == "last2":
            nu_hat.append(0.5 * (rates[-2] + rate))
        elif average is None:
            nu_hat.append(float(np.mean(rates)))
        else:
            raise ValueError(f"unknown average={average!r}")
        if verbose:
            print(f"gen {gen:2d}: nu_in = {nu_in:6.2f} Hz -> nu_out = {rate:6.2f} Hz,"
                  f" nu_hat = {nu_hat[-1]:6.2f} Hz")
        S_prev = S.copy()
        S_prev[0] = S_prev[1]
        f_prev = f
    return {"rates": np.array(rates), "nu_hat": np.array(nu_hat),
            "nu_in": np.array(nu_inputs), "f": f, "spectra": np.array(spectra)}


# --------------------------------------------------------------------------- panel D
def brunel_sergi_rate(mu: float, sigma: float, p: dict) -> float:
    """LIF rate for synaptically filtered white noise (Brunel & Sergi 1998):
    1/nu = tau_ref + tau_m sqrt(pi) int_{y_r}^{y_th} e^{u^2}(1+erf u) du,
    with boundaries shifted by (|zeta(1/2)|/sqrt 2) sqrt(tau_s/tau_m)."""
    tau = p["tau_m"] * 1e-3
    shift = ZETA_HALF / np.sqrt(2.0) * np.sqrt(max(p["tau_s"], 0.0) / p["tau_m"])
    y_th = (p["V_th"] - mu) / sigma + shift
    y_r = (p["V_r"] - mu) / sigma + shift
    val, _ = integrate.quad(lambda u: special.erfcx(-u), y_r, y_th, limit=200)
    return 1.0 / (p["tau_ref"] * 1e-3 + tau * np.sqrt(np.pi) * val)


def nu_out_white(nu_in: float, p: dict) -> float:
    """Output rate for a neuron receiving recurrent input at rate nu_in
    (diffusion approximation: sigma^2 = tau J^2 (C_E + g^2 C_I) nu_in)."""
    tau = p["tau_m"] * 1e-3
    mu = mean_input(nu_in, p)
    sigma = np.sqrt(tau * p["J"] ** 2 * (p["C_E"] + p["g"] ** 2 * p["C_I"]) * nu_in)
    return brunel_sergi_rate(mu, sigma, p)


def averaged_map(nu_in: float, i: int, p: dict) -> float:
    """nu_out,i(nu_in): output after i rounds of the averaging procedure.

    r_0 = nu_in, r_{k+1} = nu_out(mean(r_0..r_k)); returns r_{i+1}. This gives
    nu_out,0 = nu_out(nu_in) and nu_out,1 = nu_out((nu_in + nu_out(nu_in))/2),
    as written in Section 2.3.
    """
    r = [nu_in]
    for _ in range(i + 1):
        r.append(nu_out_white(float(np.mean(r)), p))
    return r[-1]


# =========================================================================== general engine
# Used by Figures 4-13. A "unit" is one representative neuron of the scheme: one per
# population (Sections 2.3-2.4) or one of the M sampled neurons (Section 2.5).

def window_grid(p: dict):
    """Steps of the analysis window / transient and the window's frequency grid (Hz)."""
    n_win = int(round(p["T_window"] / p["dt"]))
    n_tr = int(round(p["T_transient"] / p["dt"]))
    return n_win, n_tr, np.fft.rfftfreq(n_win, p["dt"] * 1e-3)


def noise_rows(S_rows: np.ndarray, n_steps: int, dt: float,
               rng: np.random.Generator) -> np.ndarray:
    """Eq. 14 for many rows at once; ``S_rows`` (rows, nf) on the rfft grid of n_steps."""
    T = n_steps * dt
    amp = np.sqrt(np.maximum(S_rows, 0.0) * T / 2.0) / dt
    rows, nf = amp.shape
    X = amp * (rng.standard_normal((rows, nf)) + 1j * rng.standard_normal((rows, nf)))
    X[:, 0] = 0.0
    if n_steps % 2 == 0:
        X[:, -1] = amp[:, -1] * np.sqrt(2.0) * rng.standard_normal(rows)
    return np.fft.irfft(X, n=n_steps, axis=1)


def simulate_rows(mu, tau_ms, noise: np.ndarray, p: dict, n_transient: int,
                  rng: np.random.Generator) -> np.ndarray:
    """LIF (Eq. 15) for independent rows with their own mean drive and time constant.
    During the refractory period the voltage is clamped at reset (input ignored)."""
    rows, n_steps = noise.shape
    noise_t = np.ascontiguousarray(noise.T)
    k = (p["dt"] / np.broadcast_to(np.asarray(tau_ms, float), (rows,))).copy()
    mu = np.broadcast_to(np.asarray(mu, float), (rows,)).copy()
    ref_steps = int(round(p["tau_ref"] / p["dt"]))
    V_th, V_r = p["V_th"], p["V_r"]
    v = rng.uniform(V_r, V_th, rows)
    ref = np.zeros(rows, dtype=np.int32)
    out = np.zeros((rows, n_steps - n_transient), dtype=np.uint8)
    for t in range(n_steps):
        active = ref == 0
        v = np.where(active, v + k * (mu - v + noise_t[t]), V_r)
        ref = np.where(active, 0, ref - 1)
        fired = v >= V_th
        if fired.any():
            v[fired] = V_r
            ref[fired] = ref_steps
            if t >= n_transient:
                out[fired, t - n_transient] = 1
    return out


def row_spectra(counts: np.ndarray, dt: float) -> np.ndarray:
    """Eq. 5 for each row (single trial): |x~(f)|^2 / T on the rfft grid."""
    T = counts.shape[1] * dt
    xf = np.fft.rfft(counts.astype(np.float32), axis=1)
    return (xf.real ** 2 + xf.imag ** 2) / T


def simulate_units(mu_u, tau_u, S_in_u, f_win, n_trials: int, p: dict,
                   rng: np.random.Generator, batch_rows: int = 500):
    """Drive each unit with its own Gaussian input (mean mu_u, spectrum S_in_u on f_win)
    for n_trials trials. Returns rates (U,), mean spectra (U, nf) and the variance of
    that mean (U, nf)."""
    dt = p["dt"] * 1e-3
    n_win, n_tr, _ = window_grid(p)
    n_steps = n_win + n_tr
    U = len(mu_u)
    f_tot = np.fft.rfftfreq(n_steps, dt)
    S_tot = np.array([np.interp(f_tot, f_win, S_in_u[u]) for u in range(U)])
    nf = n_win // 2 + 1
    S_sum = np.zeros((U, nf)); S_sq = np.zeros((U, nf)); spikes = np.zeros(U)
    row_unit = np.repeat(np.arange(U), n_trials)
    mu_u = np.asarray(mu_u, float); tau_u = np.broadcast_to(np.asarray(tau_u, float), (U,))
    for b0 in range(0, row_unit.size, batch_rows):
        ru = row_unit[b0:b0 + batch_rows]
        noise = noise_rows(S_tot[ru], n_steps, dt, rng)
        counts = simulate_rows(mu_u[ru], tau_u[ru], noise, p, n_tr, rng)
        del noise
        S = row_spectra(counts, dt)
        for u in np.unique(ru):
            m = ru == u
            S_sum[u] += S[m].sum(0); S_sq[u] += (S[m].astype(float) ** 2).sum(0)
            spikes[u] += counts[m].sum()
    S_mean = S_sum / n_trials
    S_var = np.maximum(S_sq / n_trials - S_mean ** 2, 0) / max(n_trials - 1, 1)
    S_mean[:, 0] = np.nan
    return spikes / (n_trials * n_win * dt), S_mean, S_var


# --------------------------------------------------------------------------- statistics
def fano_factor(f, S, nu, n_bins: int = 2) -> float:
    """Eq. 6: S(f -> 0) / nu, using the lowest n_bins non-zero frequencies."""
    return float(np.nanmean(S[1:1 + n_bins]) / nu) if nu > 0 else np.nan


def correlation_time(f, S, nu, S_var=None) -> float:
    """Eq. 7 (two-sided integral), with the estimator variance subtracted so the
    finite-sample noise in S does not bias tau_c upward. Returns seconds."""
    if not nu > 0:
        return np.nan
    df = f[1] - f[0]
    d = (S[1:] - nu) ** 2
    if S_var is not None:
        d = d - S_var[1:]
    return float(2 * np.nansum(d) * df / nu ** 4)


def relative_error(f, S_net, S_sch, f_cut) -> float:
    """Eq. 19, integrated over 0 < f <= f_cut."""
    m = (f > 0) & (f <= f_cut)
    return float(np.nansum((S_net[m] - S_sch[m]) ** 2) / np.nansum(S_net[m] ** 2))


# --------------------------------------------------------------------------- populations
def run_populations(tau_ms, RI_ext, C, W, p: dict, n_generations: int, n_trials: int,
                    average: int | None = 1, nu0: float = 10.0, seed: int = 0,
                    n_final: int = 5, f_keep: float = 1000.0, verbose: bool = True,
                    coefs=None):
    """Self-consistent scheme with one neuron per population (Eqs. 12-15).

    coefs: optional (A_mu, A_var) replacing C*W and C*W**2, e.g. a single unit
    standing for a homogeneous E/I network: ([[(C_E - g C_I) J]], [[(C_E + g^2 C_I) J^2]]).

    C[a, b]: number of inputs a neuron of population a receives from population b.
    W[a, b]: signed weight (mV), e.g. J or -g J.
    average: generations averaged for the next input rate (Eq. 11); None = all.
    nu0: rate(s) of the white-noise generation 0 (scalar or one per population);
         ``mean_field_rates`` gives a good choice.
    The final spectrum is the mean over the last n_final generations.
    """
    rng = np.random.default_rng(seed)
    tau_ms = np.asarray(tau_ms, float); tau = tau_ms * 1e-3
    RI_ext = np.broadcast_to(np.asarray(RI_ext, float), tau.shape)
    A_mu, A_var = (np.asarray(coefs[0], float), np.asarray(coefs[1], float)) if coefs else \
        (np.asarray(C, float) * np.asarray(W, float), np.asarray(C, float) * np.asarray(W, float) ** 2)
    P = tau.size
    _, _, f = window_grid(p)
    K2 = filter_power(f, p.get("tau_s", 0.0))
    nu_hat = np.broadcast_to(np.asarray(nu0, float), (P,)).copy()
    S_prev = np.repeat(nu_hat[:, None], f.size, axis=1)
    rates, nu_in, kept = [], [], []
    S_fin = np.zeros((P, f.size)); V_fin = np.zeros((P, f.size)); n_fin = 0
    keep = f <= f_keep
    for gen in range(n_generations + 1):
        mu = RI_ext + tau * (A_mu @ nu_hat)
        S_in = tau[:, None] ** 2 * K2[None] * (A_var @ S_prev)
        r, S, V = simulate_units(mu, tau_ms, S_in, f, n_trials, p, rng)
        rates.append(r); nu_in.append(nu_hat.copy()); kept.append(S[:, keep].astype(np.float32))
        if gen > n_generations - n_final:
            S_fin += S; V_fin += V; n_fin += 1
        if verbose:
            print(f"gen {gen:2d}: " + "  ".join(f"{nu_hat[a]:7.2f}->{r[a]:7.2f} Hz" for a in range(P)))
        S_prev = S.copy(); S_prev[:, 0] = S_prev[:, 1]
        past = rates[1:] if gen > 0 else rates
        window = past if average is None else past[-average:]
        nu_hat = np.mean(window, axis=0)
    rates = np.array(rates)
    S_fin /= n_fin; V_fin /= n_fin ** 2
    nu_fin = rates[-n_final:].mean(0)
    return {"f": f[keep], "rates": rates, "nu_in": np.array(nu_in),
            "spectra": np.array(kept), "S_final": S_fin[:, keep], "nu_final": nu_fin,
            "FF": np.array([fano_factor(f, S_fin[a], nu_fin[a]) for a in range(P)]),
            "tau_c": np.array([correlation_time(f, S_fin[a], nu_fin[a], V_fin[a]) for a in range(P)])}


# --------------------------------------------------------------------------- Erdos-Renyi
def run_er_scheme(p: dict, M: int, n_generations: int, n_trials: int,
                  weights: str = "fixed", stabilize: bool = False, nu0: float = 10.0,
                  seed: int = 0, f_keep: float = 1000.0, verbose: bool = True):
    """Section 2.5: M representative neurons per generation with binomial in-degrees
    (Eqs. 16-17) and optionally exponential weights; Eq. 18 rate shift if stabilize."""
    rng = np.random.default_rng(seed)
    tau = p["tau_m"] * 1e-3
    J, g = p["J"], p["g"]
    N_E, N_I, C_E, C_I = p["N_E"], p["N_I"], p["C_E"], p["C_I"]
    _, _, f = window_grid(p)
    keep = f <= f_keep
    nu_hat = np.full(M, nu0); S_prev = np.full((M, f.size), nu0)
    rates, kept, mean_hist = [], [], []

    def summed(counts):
        """Per (alpha, k): sum of weights and of squared weights for counts[alpha, k]."""
        if weights == "fixed":
            return counts * J, counts * J ** 2
        flat = counts.ravel()
        w = rng.exponential(J, flat.sum())
        owner = np.repeat(np.arange(flat.size), flat)
        s1 = np.bincount(owner, w, minlength=flat.size).reshape(counts.shape)
        s2 = np.bincount(owner, w ** 2, minlength=flat.size).reshape(counts.shape)
        return s1, s2

    for gen in range(n_generations + 1):
        CE = rng.binomial(N_E // M, C_E / N_E, (M, M))
        CI = rng.binomial(N_I // M, C_I / N_I, (M, M))
        sE, sE2 = summed(CE); sI, sI2 = summed(CI)
        mu = p["RI_ext"] + tau * ((sE - g * sI) @ nu_hat)
        S_in = tau ** 2 * ((sE2 + g ** 2 * sI2) @ S_prev)
        r, S, _ = simulate_units(mu, np.full(M, p["tau_m"]), S_in, f, n_trials, p, rng)
        rates.append(r); kept.append(S[:, keep].astype(np.float32))
        if gen > 0:
            mean_hist.append(r.mean())
        if verbose:
            print(f"gen {gen:2d}: mean rate {r.mean():7.2f} Hz, SD {r.std():6.2f} Hz")
        S_prev = S.copy(); S_prev[:, 0] = S_prev[:, 1]
        nu_hat = r.copy()
        if stabilize and mean_hist:  # Eq. 18
            nu_hat = r - r.mean() + np.mean(mean_hist)
        nu_hat = np.maximum(nu_hat, 0.0)
    return {"f": f[keep], "rates": np.array(rates), "spectra": np.array(kept)}


# --------------------------------------------------------------------------- caching
def cached(name: str, params: dict, fn, results_dir, force: bool = False) -> dict:
    """Run ``fn()`` (returning a dict of arrays) once per parameter set; reload after."""
    import hashlib, json
    from pathlib import Path
    key = hashlib.sha1(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()[:10]
    path = Path(results_dir) / f"{name}_{key}.npz"
    if path.exists() and not force:
        print(f"loaded {path.name}")
        return dict(np.load(path))
    import time
    t0 = time.time()
    out = fn()
    np.savez_compressed(path, **out)
    path.with_suffix(".json").write_text(json.dumps(
        {"name": name, "params": params, "runtime_s": time.time() - t0}, indent=2, default=str))
    print(f"saved {path.name} ({time.time() - t0:.0f} s)")
    return out


# --------------------------------------------------------------------------- initial guess
def mean_field_rates(tau_ms, RI_ext, C, W, p: dict, guess=5.0, coefs=None):
    """Diffusion-approximation fixed point (Siegert / Brunel-Sergi rate for each
    population). Used only as the starting rate nu0 of generation 0; the paper does not
    specify its initial condition."""
    from scipy.optimize import least_squares
    tau_ms = np.asarray(tau_ms, float); tau = tau_ms * 1e-3
    RI_ext = np.broadcast_to(np.asarray(RI_ext, float), tau.shape)
    A_mu, A_var = (np.asarray(coefs[0], float), np.asarray(coefs[1], float)) if coefs else \
        (np.asarray(C, float) * np.asarray(W, float), np.asarray(C, float) * np.asarray(W, float) ** 2)

    def out_rates(nu):
        mu = RI_ext + tau * (A_mu @ nu)
        sig = np.sqrt(np.maximum(tau * (A_var @ nu), 1e-9))
        return np.array([brunel_sergi_rate(mu[a], sig[a], {**p, "tau_m": tau_ms[a]})
                         for a in range(tau.size)])

    best = None
    for g0 in (guess, 1.0, 20.0, 80.0):  # several starts; keep the best residual
        sol = least_squares(lambda x: out_rates(np.exp(x)) - np.exp(x),
                            np.log(np.full(tau.size, g0)), bounds=(-10, 6.5))
        if best is None or sol.cost < best.cost:
            best = sol
    return np.exp(best.x)
