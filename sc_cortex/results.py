from dataclasses import asdict
from pathlib import Path
import json
import platform
import numpy as np
import scipy
import brian2


def save_result(kind, config, result, directory='results'):
    root = Path(directory)/config.fingerprint
    root.mkdir(parents=True, exist_ok=True)
    metadata = dict(config=asdict(config), kind=kind, fingerprint=config.fingerprint,
                    python=platform.python_version(), numpy=np.__version__,
                    scipy=scipy.__version__, brian2=brian2.__version__,
                    spectrum='two-sided PSD at nonnegative frequencies; DC removed; Hz')
    path = root/f'{kind}.npz'
    np.savez_compressed(path, metadata=json.dumps(metadata), **result)
    return path


def load_result(kind, config, directory='results'):
    path = Path(directory)/config.fingerprint/f'{kind}.npz'
    with np.load(path, allow_pickle=False) as data:
        result = {k: data[k] for k in data.files if k != 'metadata'}
        metadata = json.loads(str(data['metadata']))
    if metadata['config'] != asdict(config) or metadata['kind'] != kind:
        raise ValueError('Result/configuration mismatch; rerun the corresponding notebook')
    return result


def compare(network, approximation):
    if not np.array_equal(network['freq'], approximation['freq']):
        raise ValueError('Frequency grids differ')
    mask = (network['freq'] > 0) & (network['freq'] <= 300)
    a, b = network['psd'][mask], approximation['psd'][mask]
    return dict(network_rate_hz=float(network['mean_rate']),
                approximation_rate_hz=float(approximation['mean_rate']),
                relative_rate_error=float(abs(network['mean_rate']-approximation['mean_rate'])/max(network['mean_rate'],1e-12)),
                relative_spectral_l2_error=float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-12)),
                network_mean_cv=float(np.nanmean(network['cv'])) if np.isfinite(network['cv']).any() else float('nan'),
                approximation_mean_cv=float(np.nanmean(approximation['cv'])) if np.isfinite(approximation['cv']).any() else float('nan'),
                iteration_converged=bool(approximation['converged']))
