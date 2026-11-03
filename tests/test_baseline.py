import unittest
from dataclasses import replace
import tempfile
import numpy as np
from scipy.fft import rfft, rfftfreq
from sc_cortex.config import preset
from sc_cortex.spectra import spike_spectrum, gaussian_kicks
from sc_cortex.models import run_network, run_iteration
from sc_cortex.results import save_result, load_result, compare

class BaselineTests(unittest.TestCase):
    def test_poisson_normalization(self):
        rng = np.random.default_rng(4)
        n, duration, dt, rate = 128, 4., .001, 50.
        counts = rng.poisson(rate*dt, (n, round(duration/dt)))
        row, col = np.nonzero(counts)
        multiplicity = counts[row,col]
        f, s, rates = spike_spectrum(np.repeat(row,multiplicity),
            np.repeat(col,multiplicity)*dt,n,duration,dt)
        self.assertAlmostEqual(s[1:-1].mean()/rate,1.,delta=.025)
        self.assertAlmostEqual(rates.mean()/rate,1.,delta=.025)

    def test_gaussian_scaling(self):
        dt, steps, coefficient, rate = .001, 8192, 4., 50.
        f = rfftfreq(steps,dt)
        target = np.full_like(f,rate)
        x = gaussian_kicks(f,target,coefficient,steps,dt,64,np.random.default_rng(7))
        self.assertAlmostEqual(x.var()/(coefficient*rate*dt),1.,delta=.02)

    def test_colored_shape(self):
        dt, steps = .001, 8192
        f = rfftfreq(steps,dt)
        target = 1 + 9*np.exp(-((f-50)/15)**2)
        x = gaussian_kicks(f,target,1.,steps,dt,128,np.random.default_rng(8))
        observed = (np.abs(rfft(x,axis=0))**2).mean(axis=1)/(steps*dt)
        for low,high in ((35,65),(150,250)):
            band = (f>low)&(f<high)
            self.assertAlmostEqual(observed[band].mean()/target[band].mean(),1.,delta=.08)

    def test_smoke_and_io(self):
        c = preset('smoke')
        n = run_network(c)
        a = run_iteration(c)
        self.assertTrue(np.isfinite(n['psd']).all())
        self.assertTrue(np.isfinite(a['psd']).all())
        self.assertGreater(n['mean_rate'],0)
        self.assertFalse(a['converged'])
        self.assertEqual(a['history'].shape,(2,5))
        with tempfile.TemporaryDirectory() as d:
            save_result('network',c,n,d)
            save_result('approximation',c,a,d)
            metrics=compare(load_result('network',c,d),load_result('approximation',c,d))
            self.assertIn('relative_spectral_l2_error',metrics)

    def test_poisson_mode(self):
        c=replace(preset('smoke'),drive='poisson',iterations=1)
        self.assertTrue(np.isfinite(run_network(c)['psd']).all())
        self.assertTrue(np.isfinite(run_iteration(c)['psd']).all())

if __name__ == '__main__':
    unittest.main()
