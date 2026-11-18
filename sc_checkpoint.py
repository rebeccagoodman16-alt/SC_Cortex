"""Shared local result caching and recovery for SC_Cortex.

Only load checkpoints created by this project: payloads use Python pickle.
Cache identity includes model code, runtime parameters, and software versions.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import pickle
import re
import sys
import uuid
import warnings
import numpy as np

def _canonical(value):
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, np.ndarray):
        return {"dtype": str(value.dtype), "shape": value.shape, "sha256": hashlib.sha256(value.tobytes()).hexdigest()}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return repr(value)

def notebook_code(path, fallback=""):
    """Hash saved code, excluding operational cache/run switches and outputs."""
    path = Path(path)
    if not path.exists():
        return fallback
    sources = [
        re.sub(r"(?m)^(?:FORCE_RERUN|CHECKPOINT_SECONDS|RUN_SIMULATION|RUN_SWEEP|SAVE_RESULTS|SAVE_FIGURES|SAVE_FIGURE)\s*=.*$", "", "".join(cell["source"]))
        for cell in json.loads(path.read_text())["cells"]
        if cell["cell_type"] == "code"
    ]
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()

def versions():
    result = {"python": sys.version.split()[0]}
    for name in ("numpy", "scipy", "brian2"):
        try: result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: pass
    return result

class StageCache:
    """Atomic, checksummed writes with a previous committed recovery point."""
    def __init__(self, root, stage, parameters, code="", force=False):
        identity = _canonical({"schema": 1, "stage": stage, "parameters": parameters,
                               "code": code, "software": versions(),
                               "checkpoint_code": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
        raw = json.dumps(identity, sort_keys=True).encode()
        self.directory = Path(root) / "cache" / hashlib.sha256(raw).hexdigest()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "state.pkl"
        self._last_valid_path = None
        self.force = force
        self.identity = identity
        (self.directory / "identity.json").write_text(json.dumps(identity, indent=2))

    def load(self, validate=None):
        if self.force:
            return None
        for path in (self.path, self.path.with_suffix(".previous")):
            if not path.exists(): continue
            try:
                raw = path.read_bytes()
                checksum, payload = raw.split(b"\n", 1)
                if hashlib.sha256(payload).hexdigest().encode() != checksum:
                    raise ValueError("checksum mismatch")
                value = pickle.loads(payload)
                if validate is not None and not validate(value):
                    raise ValueError("checkpoint data file is missing or corrupt")
                self._last_valid_path = path
                print(f"Loaded {self.identity['stage']}: {path}")
                return value
            except (OSError, ValueError, EOFError, pickle.UnpicklingError) as exc:
                warnings.warn(f"Cannot read {path}: {exc}; trying previous checkpoint")
        return None

    def save(self, state):
        payload = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        temporary = self.directory / (uuid.uuid4().hex + ".tmp")
        try:
            with temporary.open("wb") as stream:
                stream.write(hashlib.sha256(payload).hexdigest().encode() + b"\n" + payload)
                stream.flush()
                os.fsync(stream.fileno())
            if self.path.exists() and self._last_valid_path != self.path.with_suffix(".previous"):
                os.replace(self.path, self.path.with_suffix(".previous"))
            os.replace(temporary, self.path)
            self._last_valid_path = self.path
            descriptor = os.open(self.directory, os.O_RDONLY)
            try: os.fsync(descriptor)
            finally: os.close(descriptor)
        finally:
            temporary.unlink(missing_ok=True)

def parameters(namespace):
    """Runtime values used by the existing homogeneous notebook models."""
    names = ("N_E N_I N C_E C_I epsilon gamma tau theta V_r tau_rp J g D RI "
             "T_trial dt_sec N_steps tau_val vT_val vR_val tau_ref_val J_val g_val RI_val "
             "SEED initial_rate_hz n_gen average_rate_generations DT_MS TAU_MS THETA_MV "
             "V_RESET_MV REFRACTORY_MS J_MV DELAY_MS EXTERNAL_INPUT_MV").split()
    values = {name: namespace[name] for name in names if name in namespace}
    # Brian quantities must retain dimensions as well as numerical SI values.
    return {key: {"value": np.asarray(value).tolist(), "dimensions": str(getattr(value, "dim", ""))}
            for key, value in values.items()}

class SavedSpikes:
    def __init__(self, data):
        from brian2 import second
        self.i = data["spike_i"]
        self.t = data["spike_t_s"] * second
        self.count = data["counts"]
    def spike_trains(self):
        return {i: self.t[self.i == i] for i in range(len(self.count))}

class SavedRates:
    def __init__(self, data):
        from brian2 import second, Hz
        self.t = data["rate_t_s"] * second
        self.rate = data["rate_hz"] * Hz

def restore_monitors(data):
    np.random.set_state(data["numpy_rng"])
    return SavedRates(data), SavedSpikes(data)

def _file_digest(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def run_recurrent(cache, neurons, excitatory, inhibitory, duration, namespace,
                  checkpoint_seconds=1.0):
    """Preserve voltages, synapses, delay queues, monitor data, and Brian RNG."""
    from brian2 import Network, PopulationRateMonitor, SpikeMonitor, second, Hz
    if checkpoint_seconds <= 0:
        raise ValueError("checkpoint_seconds must be positive")
    rate = PopulationRateMonitor(neurons, name="sc_rate")
    spikes = SpikeMonitor(neurons, name="sc_spikes")
    net = Network(neurons, excitatory, inhibitory, rate, spikes)
    pointer = StageCache(cache.directory, "brian-network", cache.identity, force=cache.force)
    previous = pointer.load(validate=lambda value:
        Path(value['filename']).is_file()
        and _file_digest(value['filename']) == value['sha256'])
    if previous is not None:
        net.restore("checkpoint", filename=previous["filename"], restore_random_state=True)
        print(f"Resuming recurrent network at {float(net.t / second):g} s")
    target = float(duration / second)
    while float(net.t / second) < target - 1e-12:
        amount = min(checkpoint_seconds, target - float(net.t / second))
        net.run(amount * second, namespace=namespace)
        filename = str(pointer.directory / (uuid.uuid4().hex + ".brian"))
        net.store("checkpoint", filename=filename)
        with open(filename, "rb") as stream: os.fsync(stream.fileno())
        pointer.save({"filename": filename, "sha256": _file_digest(filename),
                      "time_s": float(net.t / second)})
        # Keep the current and previous network snapshots; only delete older ones.
        keep = {filename}
        old = pointer.path.with_suffix(".previous")
        if old.exists():
            raw = old.read_bytes().split(b"\n", 1)[1]
            keep.add(pickle.loads(raw)["filename"])
        for path in pointer.directory.glob("*.brian"):
            if str(path) not in keep: path.unlink()
        print(f"Checkpoint: recurrent {float(net.t/second):g}/{target:g} s")
    data = {"spike_i": np.asarray(spikes.i[:]), "spike_t_s": np.asarray(spikes.t[:] / second),
            "counts": np.asarray(spikes.count[:]), "rate_t_s": np.asarray(rate.t[:] / second),
            "rate_hz": np.asarray(rate.rate[:] / Hz), "numpy_rng": np.random.get_state()}
    cache.save(data)
    return restore_monitors(data)

