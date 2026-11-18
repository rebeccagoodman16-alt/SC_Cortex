import sys
from pathlib import Path
import tempfile, json, numpy as np, gc, contextlib
import brian2 as b
from sc_checkpoint import StageCache, run_recurrent, restore_monitors
b.prefs.codegen.target='numpy'
out=[]
def check(label, condition):
    assert condition, label
    out.append("PASS "+label)
def build():
    b.start_scope(); b.defaultclock.dt=.1*b.ms;b.seed(4321)
    ns=dict(tau=20*b.ms,RI=30*b.mV,theta=20*b.mV,V_r=10*b.mV,tau_rp=2*b.ms,J=.1*b.mV,g=4.,D=1.5*b.ms)
    n=b.NeuronGroup(25,"dv/dt=(-v+RI)/tau : volt (unless refractory)",threshold="v>theta",reset="v=V_r",refractory=ns['tau_rp'],method='euler',name='sc_neurons')
    n.v="rand()*mV"
    e=b.Synapses(n[:20],n,on_pre="v+=J",delay=ns['D'],name='sc_exc')
    i=b.Synapses(n[20:],n,on_pre="v-=g*J",delay=ns['D'],name='sc_inh')
    e.connect(i=np.random.randint(0,20,25*4),j=np.repeat(np.arange(25),4))
    i.connect(i=np.random.randint(0,5,25*2),j=np.repeat(np.arange(25),2))
    return n,e,i,ns
with tempfile.TemporaryDirectory() as d:
    cache=StageCache(d,'atomic',{'g':4})
    cache.save({'value':1});cache.save({'value':2})
    check('atomic round trip',cache.load()['value']==2)
    cache.path.write_bytes(b'broken')
    check('corrupt current falls back to prior checkpoint',cache.load()['value']==1)
    cache.save({'value':3})
    cache.path.write_bytes(b'broken again')
    check('repair retains the valid prior checkpoint',cache.load()['value']==1)
    check('parameter change produces cache miss',StageCache(d,'atomic',{'g':4.5}).load() is None)
    check('force rerun bypasses cache',StageCache(d,'atomic',{'g':4},force=True).load() is None)
    cache=StageCache(d,'network',{'case':'complete'})
    n,e,i,ns=build()
    rates,spikes=run_recurrent(cache,n,e,i,.07*b.second,ns,.02)
    expected=cache.load()
    rr,ss=restore_monitors(expected)
    check('restored monitor units and counts',np.array_equal(ss.count,spikes.count) and b.have_same_dimensions(rr.rate,b.Hz))
    del n,e,i,rates,spikes;gc.collect()
    # A corrupt external Brian snapshot must fall back to the prior one.
    pointer = StageCache(cache.directory, "brian-network", cache.identity)
    pointer.load()
    import pickle
    state = pickle.loads(pointer.path.read_bytes().split(b"\n",1)[1])
    Path(state['filename']).write_bytes(b'test corruption')
    n,e,i,ns=build()
    run_recurrent(cache,n,e,i,.07*b.second,ns,.02)
    repaired=cache.load()
    check('corrupt network snapshot falls back without changing spikes',
          np.array_equal(expected['spike_t_s'],repaired['spike_t_s']))
    del n,e,i;gc.collect()
    # Compare the original uninterrupted Brian run with checkpointed execution.
    n,e,i,ns=build();r=b.PopulationRateMonitor(n,name='sc_rate');s=b.SpikeMonitor(n,name='sc_spikes')
    net=b.Network(n,e,i,r,s);net.run(.07*b.second,namespace=ns)
    check('chunked run preserves original spike train',np.array_equal(np.asarray(s.t/b.second),expected['spike_t_s']) and np.array_equal(np.asarray(s.i),expected['spike_i']))
    del n,e,i,r,s,net;gc.collect()
    interrupted=StageCache(d,'network',{'case':'interrupted'})
    original_save=StageCache.save
    def interrupt_after_commit(self,state):
        original_save(self,state)
        if self.identity['stage']=='brian-network': raise RuntimeError('test interruption')
    StageCache.save=interrupt_after_commit
    n,e,i,ns=build()
    try:run_recurrent(interrupted,n,e,i,.07*b.second,ns,.02)
    except RuntimeError:pass
    finally:StageCache.save=original_save
    del n,e,i;gc.collect()
    n,e,i,ns=build()
    run_recurrent(interrupted,n,e,i,.07*b.second,ns,.02)
    actual=interrupted.load()
    check('network recovery preserves spikes and delay queue',np.array_equal(expected['spike_i'],actual['spike_i']) and np.array_equal(expected['spike_t_s'],actual['spike_t_s']))
    check('network recovery preserves population rates',np.array_equal(expected['rate_hz'],actual['rate_hz']))
    del n,e,i;gc.collect()

# Three-population iteration exact recovery, including the Generator state.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '05_Pena2018_Replication'))
from heterogeneous_networks.model import run_iteration
with tempfile.TemporaryDirectory() as d:
    reference=run_iteration(trial_s=.05,generations=3,checkpoint_dir=Path(d)/'ref')
    interrupted=Path(d)/'resume'
    calls=[0]
    def interrupt_generation(self,state):
        original_save(self,state)
        if self.identity['stage']=='heterogeneous-iteration':
            calls[0]+=1
            if calls[0]==1:raise RuntimeError('test interruption')
    StageCache.save=interrupt_generation
    try:run_iteration(trial_s=.05,generations=3,checkpoint_dir=interrupted)
    except RuntimeError:pass
    finally:StageCache.save=original_save
    resumed=run_iteration(trial_s=.05,generations=3,checkpoint_dir=interrupted)
    check('heterogeneous generation recovery matches uninterrupted rates',np.array_equal(reference['rates_hz'],resumed['rates_hz']))
    check('heterogeneous recovery matches spectra',np.array_equal(np.asarray(reference['spectra']),np.asarray(resumed['spectra'])))
    again=run_iteration(trial_s=.05,generations=3,checkpoint_dir=interrupted)
    check('completed heterogeneous run reuses results',np.array_equal(again['rates_hz'],reference['rates_hz']))

# Original notebook uses its existing functions and generation updates.
p=Path('01_Original_Colab/4.5/Figure10_G4.5_CE100_CI25_J1.0.ipynb')
cells=json.loads(p.read_text())['cells']
ns={"V_R_MV":0}
for c in cells:
    src=''.join(c['source'])
    if 'from brian2 import *' in src:exec(src,ns)
b.prefs.codegen.target='numpy'
setup=next(''.join(c['source']) for c in cells if 'start_scope()' in ''.join(c['source']) and c['cell_type']=='code')
setup=setup.replace('N_E      = 1000','N_E      = 20').replace('N_I      = 250','N_I      = 5').replace('epsilon  = 0.01','epsilon  = 0.2').replace('sim_time = 3000 * ms','sim_time = 70 * ms')
with tempfile.TemporaryDirectory() as d:
    # Isolate all generated smoke-test data from the real result directories.
    setup=setup.replace("start_scope()",f"_SC_OUTPUT = Path({d!r})\nstart_scope()",1)
    exec(setup,ns)
    for c in cells:
        src=''.join(c['source'])
        if src.startswith('# Reuse matching') or src.startswith('# Automatic load, run'):
            exec(src,ns)
    spike_t=ns['spike_mon'].t.copy()
    exec(setup,ns)
    for c in cells:
        src=''.join(c['source'])
        if src.startswith('# Reuse matching') or src.startswith('# Automatic load, run'):
            exec(src,ns)
    check('original notebook reload restores monitor data',np.array_equal(spike_t,ns['spike_mon'].t))
    for c in cells:
        src=''.join(c['source'])
        if src.startswith('# Numerical/Iterative Constraints'):
            exec(src.replace('T_trial = 500.0','T_trial = 0.05'),ns)
        if src.startswith('def mu_D_stats'):exec(src,ns)
    gen=next(''.join(c['source']) for c in cells if ''.join(c['source']).startswith('print("Executing Gaussian'))
    gen=gen.replace('n_gen = 15','n_gen = 3')
    np.random.seed(9);exec(gen,ns)
    expected=ns['S_cur'].copy()
    exec(gen,ns)
    check('original Gaussian completed run reloads',np.array_equal(expected,ns['S_cur']))
    # Delete only temporary test state, then inject a crash after generation 1.
    import shutil
    for path in Path(d).glob('cache/*'):
        if json.loads((path/'identity.json').read_text())['stage'].startswith('gaussian'):
            shutil.rmtree(path)
    np.random.seed(9)
    def stop_original(self,state):
        original_save(self,state)
        if self.identity['stage'].startswith('gaussian'):raise RuntimeError('test interruption')
    StageCache.save=stop_original
    try:exec(gen,ns)
    except RuntimeError:pass
    finally:StageCache.save=original_save
    exec(gen,ns)
    check('original Gaussian generation recovery matches uninterrupted spectrum',np.array_equal(expected,ns['S_cur']))
Path('/tmp/sc_test_report.txt').write_text('\n'.join(out)+'\n')
print('\n'.join(out))

