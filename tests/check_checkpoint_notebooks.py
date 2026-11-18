from pathlib import Path
import json, ast, re, tempfile, gc
import numpy as np
import brian2 as b
from sc_checkpoint import StageCache
out=[]
root=Path.cwd()
with tempfile.TemporaryDirectory() as d:
    tested=0
    for p in sorted((root/'01_Original_Colab').rglob('*.ipynb')):
        cells=json.loads(p.read_text())['cells']
        setup=next((''.join(c['source']) for c in cells if c['cell_type']=='code' and 'start_scope()' in ''.join(c['source']) and '_sc_recurrent = StageCache' in ''.join(c['source'])),None)
        if setup is None:continue
        ns={'V_R_MV':0}
        imports=next(''.join(c['source']) for c in cells if 'from brian2 import *' in ''.join(c['source']))
        exec(imports,ns);b.prefs.codegen.target='numpy'
        setup=re.sub(r'N_E\s*=\s*\d+','N_E = 20',setup)
        setup=re.sub(r'N_I\s*=\s*\d+','N_I = 5',setup)
        setup=re.sub(r'epsilon\s*=\s*[\d.]+','epsilon = 0.2',setup)
        setup=re.sub(r'sim_time\s*=\s*\d+\s*\*\s*ms','sim_time = 70 * ms',setup)
        setup=setup.replace("start_scope()",f"_SC_OUTPUT = Path({str(Path(d)/p.stem)!r})\nstart_scope()",1)
        exec(setup,ns)
        for c in cells:
            s=''.join(c['source'])
            if s.startswith(('# Reuse matching','# Automatic load, run')):exec(s,ns)
        expected=ns['spike_mon'].t.copy()
        exec(setup,ns)
        for c in cells:
            s=''.join(c['source'])
            if s.startswith(('# Reuse matching','# Automatic load, run')):exec(s,ns)
        assert np.array_equal(expected,ns['spike_mon'].t),str(p)
        tested+=1
        del ns;gc.collect()
    out.append(f'PASS run and reload in all {tested} original simulation variants')

    # Modern SNN.
    cells=json.loads(Path('02_Brunel_SNN/Brunel_SNN.ipynb').read_text())['cells']
    ns={}
    exec(''.join(cells[3]['source']),ns)
    b.prefs.codegen.target='numpy'
    ns.update(N_E=20,N_I=5,N=25,C_E=4,C_I=2,sim_time=70*b.ms,_SC_OUTPUT=Path(d)/'modern-snn')
    exec(''.join(cells[5]['source']),ns)
    exec(''.join(cells[7]['source']),ns)
    _,r,s,_=ns['run_network']();_,rr,ss,_=ns['run_network']()
    assert np.array_equal(s.t,ss.t)
    out.append('PASS modern Brunel run and cached monitor reload')
    del ns;gc.collect()

    # Sweep function.
    cells=json.loads(Path('01_Original_Colab/G_Comparison_Recurrent_LIF.ipynb').read_text())['cells']
    ns={}
    exec(''.join(cells[3]['source']),ns);b.prefs.codegen.target='numpy'
    ns['_SC_OUTPUT']=Path(d)/'sweep'
    exec(''.join(cells[5]['source']),ns)
    result=ns['run_condition'](4.,n_e=20,n_i=5,c_e=4,c_i=2,duration_ms=70.)
    again=ns['run_condition'](4.,n_e=20,n_i=5,c_e=4,c_i=2,duration_ms=70.)
    assert result==again
    out.append('PASS sweep condition reuses completed results')
    del ns;gc.collect()

Path('/tmp/sc_extra_report.txt').write_text('\n'.join(out)+'\n')
print('\n'.join(out))

