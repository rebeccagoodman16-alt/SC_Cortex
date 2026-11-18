"""Recurrent LIF networks for the Pena et al. (2018) comparisons (Eqs. 8-10).

A lean NumPy event-driven simulator (fits the 2-CPU / ~2 GB Codespace better than
Brian2 at 10^7 synapses). Conventions match the scheme in ``pena_scheme.py``:
Euler step dt, threshold V_th, reset V_r, voltage clamped at reset during the
refractory period, common transmission delay, delta synapses (v jumps by w) or the
exponential filter of Eq. 10 (charge-preserving: u jumps by tau_m w / tau_s).

Connectivity: fixed in-degree (``K``) or Erdos-Renyi (``p``, binomial in-degree);
presynaptic partners are drawn with replacement (as in the repo's Brunel notebooks).
Weights are fixed or exponentially distributed with the given mean.

Spectra: after ``T_transient`` the run is cut into windows of ``T_window``; each
recorded neuron's |x~(f)|^2 / T (Eq. 5) is averaged over windows.
"""

from __future__ import annotations

import time
import numpy as np


def build_connectivity(pops, conns, rng):
    offsets = np.cumsum([0] + [q["N"] for q in pops])
    index = {q["name"]: i for i, q in enumerate(pops)}
    N = int(offsets[-1])
    pre_l, post_l, w_l = [], [], []
    for c in conns:
        t, s = index[c["target"]], index[c["source"]]
        Nt, Ns = pops[t]["N"], pops[s]["N"]
        K = (np.full(Nt, int(c["K"])) if "K" in c else rng.binomial(Ns, c["p"], Nt))
        post = np.repeat(np.arange(Nt, dtype=np.int32) + np.int32(offsets[t]), K)
        pre = rng.integers(0, Ns, post.size, dtype=np.int32) + np.int32(offsets[s])
        if c.get("dist", "fixed") == "exponential":
            w = (np.sign(c["w"]) * rng.exponential(abs(c["w"]), post.size)).astype(np.float32)
        else:
            w = np.full(post.size, c["w"], dtype=np.float32)
        pre_l.append(pre); post_l.append(post); w_l.append(w)
    pre = np.concatenate(pre_l); post = np.concatenate(post_l); w = np.concatenate(w_l)
    del pre_l, post_l, w_l
    order = np.argsort(pre, kind="stable")
    post = post[order]; w = w[order]
    indptr = np.concatenate([[0], np.cumsum(np.bincount(pre, minlength=N))]).astype(np.int64)
    return offsets, indptr, post, w


def _spectra_chunks(buf, dt, chunk=250):
    T = buf.shape[1] * dt
    out = np.empty((buf.shape[0], buf.shape[1] // 2 + 1), dtype=np.float32)
    for a in range(0, buf.shape[0], chunk):
        xf = np.fft.rfft(buf[a:a + chunk].astype(np.float32), axis=1)
        out[a:a + chunk] = (xf.real ** 2 + xf.imag ** 2) / T
    return out


def simulate_network(pops, conns, common, n_windows, record=None, record_input=None,
                     raster_n=100, seed=0, f_keep=1000.0, verbose=True):
    """Simulate and return rates and window-averaged spike-train spectra.

    pops:   [{name, N, tau_m (ms), RI_ext (mV)}]
    conns:  [{target, source, K | p, w (mV, signed), dist: fixed|exponential}]
    common: {dt, V_th, V_r, tau_ref, delay, tau_s, T_window, T_transient} (ms, mV)
    record: {pop_name: n} neurons per population whose spectra are measured
            (default 500 per population).
    record_input: (pop_name, n) neurons whose recurrent input current is recorded
            (Figure 12); they are also spike-recorded.
    """
    rng = np.random.default_rng(seed)
    t0 = time.time()
    offsets, indptr, post, w = build_connectivity(pops, conns, rng)
    N = int(offsets[-1])
    if verbose:
        print(f"built {N} neurons, {post.size/1e6:.1f} M synapses in {time.time()-t0:.1f} s")
    dt_ms = common["dt"]; dt = dt_ms * 1e-3
    tau_m = np.concatenate([np.full(q["N"], q["tau_m"], float) for q in pops])
    RI = np.concatenate([np.full(q["N"], q["RI_ext"], float) for q in pops])
    k = dt_ms / tau_m
    V_th, V_r = common["V_th"], common["V_r"]
    ref_steps = int(round(common["tau_ref"] / dt_ms))
    D = max(int(round(common["delay"] / dt_ms)), 1)
    L = D + 1
    tau_s = common.get("tau_s", 0.0)
    ring = np.zeros((L, N), dtype=np.float32)
    u = np.zeros(N) if tau_s > 0 else None
    u_decay = np.exp(-dt_ms / tau_s) if tau_s > 0 else 0.0
    u_jump = tau_m / tau_s if tau_s > 0 else None

    # recorded neurons
    record = record or {q["name"]: 500 for q in pops}
    rec_idx, rec_pop = [], []
    in_idx = np.array([], dtype=np.int64)
    for i, q in enumerate(pops):
        n = min(record.get(q["name"], 0), q["N"])
        if record_input and record_input[0] == q["name"]:
            n = max(n, record_input[1])
        sel = np.sort(rng.choice(q["N"], n, replace=False)) + offsets[i]
        rec_idx.append(sel); rec_pop.append(np.full(n, i))
        if record_input and record_input[0] == q["name"]:
            in_idx = sel[:record_input[1]]
    rec_idx = np.concatenate(rec_idx); rec_pop = np.concatenate(rec_pop)
    rec_pos = np.full(N, -1, dtype=np.int64); rec_pos[rec_idx] = np.arange(rec_idx.size)
    in_pos = np.full(N, -1, dtype=np.int64); in_pos[in_idx] = np.arange(in_idx.size)

    n_win = int(round(common["T_window"] / dt_ms))
    n_tr = int(round(common["T_transient"] / dt_ms))
    n_total = n_tr + n_windows * n_win
    nf = n_win // 2 + 1
    f = np.fft.rfftfreq(n_win, dt)
    keep = f <= f_keep
    buf = np.zeros((rec_idx.size, n_win), dtype=np.uint8)
    S_sum = np.zeros((rec_idx.size, nf)); S_sq = np.zeros((rec_idx.size, nf))
    halves = np.zeros((2, in_idx.size, keep.sum()))
    if in_idx.size:
        inbuf = np.zeros((in_idx.size, n_win), dtype=np.float32)
        in_S = np.zeros((in_idx.size, nf)); in_sum = np.zeros(in_idx.size)
        bin_steps = int(round(2.0 / dt_ms))
        mom = np.zeros((4, in_idx.size)); n_bins_tot = 0
    counts = np.zeros(N, dtype=np.int32)
    ras_i, ras_t = [], []
    raster_set = rec_idx[:raster_n]
    raster_mask = np.zeros(N, bool); raster_mask[raster_set] = True

    v = rng.uniform(V_r, V_th, N)
    ref = np.zeros(N, dtype=np.int32)
    t1 = time.time()
    for t in range(n_total):
        slot = t % L
        arr = ring[slot]
        active = ref == 0
        if u is not None:
            u = u * u_decay + arr * u_jump
            v = np.where(active, v + k * (RI - v + u), V_r)
        else:
            v = np.where(active, v + k * (RI - v) + arr, V_r)
        if in_idx.size and t >= n_tr:
            inbuf[:, (t - n_tr) % n_win] = arr[in_idx]
        ring[slot] = 0.0
        ref = np.where(active, 0, ref - 1)
        sp = np.flatnonzero(v >= V_th)
        if sp.size:
            v[sp] = V_r; ref[sp] = ref_steps
            starts = indptr[sp]; lens = indptr[sp + 1] - starts
            tot = int(lens.sum())
            if tot:
                idx = np.repeat(starts - np.concatenate([[0], np.cumsum(lens)[:-1]]), lens) + np.arange(tot)
                ring[(t + D) % L] += np.bincount(post[idx], weights=w[idx], minlength=N).astype(np.float32)
            if t >= n_tr:
                counts[sp] += 1
                r = rec_pos[sp]; r = r[r >= 0]
                buf[r, (t - n_tr) % n_win] = 1
                rs = sp[raster_mask[sp]]
                if rs.size:
                    ras_i.append(rs); ras_t.append(np.full(rs.size, (t - n_tr) * dt))
        if t >= n_tr and (t - n_tr) % n_win == n_win - 1:
            wnum = (t - n_tr) // n_win
            S = _spectra_chunks(buf, dt)
            S_sum += S; S_sq += S.astype(float) ** 2
            if in_idx.size:
                halves[wnum % 2] += S[rec_pos[in_idx]][:, keep]
                x = tau_m[in_idx, None] * 1e-3 * inbuf / dt          # RI_loc(t) in mV
                in_sum += x.mean(1)
                xc = x - x.mean(1, keepdims=True)
                in_S += _spectra_chunks(xc, dt).astype(float) * dt * dt  # |dt sum x e^..|^2 / T
                b = x[:, : (n_win // bin_steps) * bin_steps].reshape(in_idx.size, -1, bin_steps).sum(2) * dt
                for m_ in range(4):
                    mom[m_] += (b ** (m_ + 1)).sum(1)
                n_bins_tot += b.shape[1]
            buf[:] = 0
            if verbose:
                el = time.time() - t1
                print(f"  window {wnum + 1}/{n_windows} done ({el:.0f} s, "
                      f"mean rate {counts.sum() / (N * (t - n_tr + 1) * dt):.2f} Hz)")
    T_rec = n_windows * n_win * dt
    rates = counts / T_rec
    S_mean = S_sum / n_windows
    out = {"f": f[keep], "rates": rates.astype(np.float32), "offsets": offsets,
           "rec_idx": rec_idx, "rec_pop": rec_pop, "rec_rates": rates[rec_idx],
           "rec_S": S_mean[:, keep].astype(np.float32),
           "raster_i": np.concatenate(ras_i) if ras_i else np.array([], int),
           "raster_t": np.concatenate(ras_t) if ras_t else np.array([]),
           "runtime_s": np.array(time.time() - t0)}
    # population averages: mean over recorded neurons and windows
    from pena_scheme import fano_factor, correlation_time
    for i, q in enumerate(pops):
        m = rec_pop == i
        if not m.any():
            continue
        cnt = m.sum() * n_windows
        S_pop = S_sum[m].sum(0) / cnt
        V_pop = np.maximum(S_sq[m].sum(0) / cnt - S_pop ** 2, 0) / max(cnt - 1, 1)
        nu = rates[offsets[i]:offsets[i + 1]].mean()
        nu_rec = rates[rec_idx[m]].mean()
        S_pop[0] = np.nan
        out[f"S_{q['name']}"] = S_pop[keep]
        out[f"nu_{q['name']}"] = np.array(nu)
        out[f"FF_{q['name']}"] = np.array(fano_factor(f, S_pop, nu_rec))
        out[f"tau_c_{q['name']}"] = np.array(correlation_time(f, S_pop, nu_rec, V_pop))
    if in_idx.size:
        nb = n_bins_tot
        m1, m2, m3, m4 = mom / nb
        var = m2 - m1 ** 2
        out.update({
            "in_idx": in_idx, "in_rates": rates[in_idx],
            "in_mean": in_sum / n_windows,                 # mean recurrent input (mV)
            "in_S": (in_S / n_windows).astype(np.float32),  # two-sided spectrum, full grid
            "f_full": f,
            "in_skew": (m3 - 3 * m1 * m2 + 2 * m1 ** 3) / var ** 1.5,
            "in_kurt": (m4 - 4 * m1 * m3 + 6 * m1 ** 2 * m2 - 3 * m1 ** 4) / var ** 2 - 3,
            "in_S_spk": S_mean[rec_pos[in_idx]][:, keep].astype(np.float32),
            "half0": (halves[0] / max(n_windows // 2 + n_windows % 2, 1)).astype(np.float32),
            "half1": (halves[1] / max(n_windows // 2, 1)).astype(np.float32),
        })
    if verbose:
        print(f"simulated {n_total * dt:.1f} s in {time.time() - t1:.0f} s")
    return out


def brunel_network(N_E, gamma, C_E, J, g, tau_m=20.0, RI_ext=30.0, er=False,
                   weights="fixed", tau_I=None, g_I=None):
    """Two-population E/I network (Brunel model B / Erdos-Renyi variant).

    g is applied to inhibitory inputs of E cells; g_I (default g) to those of I cells.
    """
    N_I = int(gamma * N_E); C_I = int(gamma * C_E)
    g_I = g if g_I is None else g_I
    pops = [{"name": "E", "N": N_E, "tau_m": tau_m, "RI_ext": RI_ext},
            {"name": "I", "N": N_I, "tau_m": tau_I or tau_m, "RI_ext": RI_ext}]
    def deg(K, Ns):
        return {"p": K / Ns} if er else {"K": K}
    conns = []
    for tgt, gg in (("E", g), ("I", g_I)):
        conns.append({"target": tgt, "source": "E", "w": J, "dist": weights, **deg(C_E, N_E)})
        conns.append({"target": tgt, "source": "I", "w": -gg * J, "dist": weights, **deg(C_I, N_I)})
    return pops, conns
