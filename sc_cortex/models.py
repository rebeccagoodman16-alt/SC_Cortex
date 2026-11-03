import numpy as np
import brian2 as b2
from scipy.fft import rfftfreq
from .spectra import spike_spectrum, gaussian_kicks, spike_cv


def setup(c, seed):
    c.validate()
    b2.start_scope()
    b2.prefs.codegen.target = c.backend
    b2.defaultclock.dt = c.dt * b2.second
    b2.seed(seed)


def cells(c, n):
    ns = dict(tau=c.tau*b2.second, theta=c.threshold*b2.mV,
              vr=c.reset*b2.mV, ref=c.refractory*b2.second,
              drive=(c.dc_mv if c.drive == 'dc' else 0.)*b2.mV)
    group = b2.NeuronGroup(n, 'dv/dt = (drive-v)/tau : volt (unless refractory)',
                          threshold='v > theta', reset='v = vr',
                          refractory='ref', method='euler', namespace=ns)
    group.v = 'rand()*theta'
    return group


def external(c, group):
    if c.drive == 'poisson':
        return [b2.PoissonInput(group, 'v', c.c_e, c.external_rate*b2.Hz,
                                c.j*b2.mV)]
    return []


def run_network(c):
    """Fixed in-degree, autapses allowed, no duplicate edges; sparse Brian2 synapses.

Incoming generator sampling avoids a dense N×N adjacency matrix. All cells
have identical intrinsic parameters and exactly C_E/C_I incoming contacts.
"""
    setup(c, c.seed)
    group = cells(c, c.n_e+c.n_i)
    exc = b2.Synapses(group[:c.n_e], group, on_pre='v_post += jump',
                     delay=c.delay*b2.second, namespace={'jump':c.j*b2.mV})
    inh = b2.Synapses(group[c.n_e:], group, on_pre='v_post += jump',
                     delay=c.delay*b2.second, namespace={'jump':-c.g*c.j*b2.mV})
    exc.connect(i=f'k for k in sample(N_pre, size={c.c_e})')
    inh.connect(i=f'k for k in sample(N_pre, size={c.c_i})')
    objects = [group, exc, inh] + external(c, group)
    net = b2.Network(objects)
    net.run(c.burn*b2.second)
    # Record only representative cells, rather than every network spike.
    em = b2.SpikeMonitor(group[:c.record_e])
    im = b2.SpikeMonitor(group[c.n_e:c.n_e+c.record_i])
    rate = b2.PopulationRateMonitor(group)
    net.add(em, im, rate)
    net.run(c.duration*b2.second)
    i = np.concatenate((np.asarray(em.i), np.asarray(im.i)+c.record_e))
    t = np.concatenate((np.asarray(em.t/b2.second), np.asarray(im.t/b2.second)))-c.burn
    f, s, rates = spike_spectrum(i, t, c.record_e+c.record_i, c.duration, c.dt, c.batch)
    return dict(freq=f, psd=s, rates=rates, mean_rate=float(rates.mean()),
                cv=spike_cv(i, t, c.record_e+c.record_i),
                population_mean_rate=float(np.mean(rate.rate/b2.Hz)),
                spike_i=i, spike_t=t, population_t=np.asarray(rate.t/b2.second)-c.burn,
                population_rate=np.asarray(rate.rate/b2.Hz))


def gaussian_trials(c, freq, psd, rate, iteration):
    total_psd = np.zeros_like(psd)
    rates_all, cv_all = [], []
    steps = round((c.burn+c.duration)/c.dt)
    coefficient = c.j**2*(c.c_e+c.g**2*c.c_i)
    mean_kick = c.j*(c.c_e-c.g*c.c_i)*rate*c.dt
    for start in range(0, c.trials, c.batch):
        n = min(c.batch, c.trials-start)
        seed = c.seed + 100000 + iteration*10000 + start
        setup(c, seed)
        rng = np.random.default_rng(seed)
        if iteration == 0:
            # Dummer/Colab initialization: independent Poisson recurrent streams.
            exc_counts = rng.poisson(c.c_e*rate*c.dt, (steps,n))
            inh_counts = rng.poisson(c.c_i*rate*c.dt, (steps,n))
            kicks = c.j*(exc_counts-c.g*inh_counts)-mean_kick
        else:
            kicks = gaussian_kicks(freq, psd, coefficient, steps, c.dt, n, rng)
        noise = b2.TimedArray(kicks, dt=c.dt*b2.second)
        group = cells(c, n)
        group.namespace.update(noise=noise, mean_kick=mean_kick)
        # Same event slot and refractory gating as voltage-jump synapses.
        update = group.run_regularly('v += int(not_refractory)*(mean_kick + noise(t, i))*mV',
                                     when='synapses')
        net = b2.Network(group, update, *external(c, group))
        net.run(c.burn*b2.second)
        monitor = b2.SpikeMonitor(group)
        net.add(monitor)
        net.run(c.duration*b2.second)
        _, output, rates = spike_spectrum(np.asarray(monitor.i),
            np.asarray(monitor.t/b2.second)-c.burn, n, c.duration, c.dt, c.batch)
        total_psd += n*output
        rates_all.extend(rates)
        cv_all.extend(spike_cv(np.asarray(monitor.i), np.asarray(monitor.t/b2.second), n))
    return total_psd/c.trials, np.asarray(rates_all), np.asarray(cv_all)


def run_iteration(c):
    c.validate()
    f = rfftfreq(round(c.duration/c.dt), c.dt)
    state = np.full_like(f, c.initial_rate)
    rate = c.initial_rate
    history, spectra, stable = [], [], 0
    converged = False
    for generation in range(c.iterations):
        output, rates, cv = gaussian_trials(c, f, state, rate, generation)
        new_rate = float(rates.mean())
        band = (f > 0) & (f <= min(300., .5/c.dt))
        spectral_error = np.linalg.norm(output[band]-state[band]) / max(np.linalg.norm(state[band]), 1e-12)
        rate_error = abs(new_rate-rate)/max(abs(rate), 1e-12)
        history.append([generation+1, rate, new_rate, rate_error, spectral_error])
        spectra.append(output.copy())
        print(f'Iteration {generation+1}: {new_rate:.2f} Hz; rate residual {rate_error:.3f}; spectrum residual {spectral_error:.3f}')
        stable = stable+1 if max(rate_error,spectral_error) < c.tolerance else 0
        if stable >= 3:
            converged = True
            break
        state = (1-c.mixing)*state + c.mixing*output
        state[0] = state[1]
        rate = (1-c.mixing)*rate + c.mixing*new_rate
    return dict(freq=f, psd=output, rates=rates, mean_rate=new_rate,
                history=np.asarray(history), spectra=np.asarray(spectra),
                converged=converged, cv=cv)
