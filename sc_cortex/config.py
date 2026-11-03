from dataclasses import dataclass, asdict, replace
import hashlib
import json

@dataclass(frozen=True)
class Config:
    # Voltages in mV; all times in seconds. Homogeneous fixed in-degree.
    n_e: int = 2000
    n_i: int = 500
    c_e: int = 200
    c_i: int = 50
    tau: float = .020
    threshold: float = 20.
    reset: float = 10.
    refractory: float = .002
    j: float = .1
    g: float = 4.
    delay: float = .0015
    drive: str = 'dc'
    dc_mv: float = 30.
    eta: float = 1.5
    dt: float = .0001
    burn: float = 1.
    duration: float = 2.
    seed: int = 4321
    record_e: int = 160
    record_i: int = 40
    trials: int = 128
    batch: int = 32
    iterations: int = 15
    initial_rate: float = 71.
    mixing: float = 1.
    tolerance: float = .08
    backend: str = 'cython'

    def validate(self):
        for k in ('n_e', 'n_i', 'c_e', 'c_i', 'record_e', 'record_i', 'trials', 'batch', 'iterations'):
            v = getattr(self, k)
            if not isinstance(v, int) or v <= 0:
                raise ValueError(f'{k} must be a positive integer')
        if self.c_e >= self.n_e or self.c_i >= self.n_i:
            raise ValueError('In-degree must leave room to exclude self-connections')
        if self.record_e > self.n_e or self.record_i > self.n_i:
            raise ValueError('Recorded sample exceeds population')
        if self.drive not in ('dc', 'poisson') or self.backend not in ('numpy', 'cython'):
            raise ValueError('Unknown drive/backend')
        if not (0 < self.mixing <= 1 and self.threshold > self.reset):
            raise ValueError('Invalid mixing or voltage thresholds')
        for k in ('dt', 'tau', 'refractory', 'delay', 'duration', 'j', 'initial_rate', 'tolerance'):
            if getattr(self, k) <= 0:
                raise ValueError(f'{k} must be positive')
        if self.burn < 0 or self.g < 0 or self.eta < 0:
            raise ValueError('Invalid burn, g, or eta')
        for k in ('duration', 'burn', 'refractory', 'delay'):
            ratio = getattr(self, k) / self.dt
            if abs(ratio - round(ratio)) > 1e-8:
                raise ValueError(f'{k} must be an integer multiple of dt')
        return self

    @property
    def external_rate(self):
        return self.eta * self.threshold / (self.j * self.c_e * self.tau)

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:12]

    def save(self, path):
        from pathlib import Path
        Path(path).write_text(json.dumps(asdict(self), indent=2) + '\n')

    @classmethod
    def load(cls, path):
        from pathlib import Path
        return cls(**json.loads(Path(path).read_text())).validate()


def preset(name='quick'):
    c = Config()
    if name == 'reference':
        c = replace(c, n_e=20000, n_i=5000, c_e=1000, c_i=250,
                    record_e=800, record_i=200, trials=1024, duration=10.)
    elif name == 'smoke':
        c = replace(c, n_e=160, n_i=40, c_e=16, c_i=4,
                    record_e=16, record_i=4, trials=8, batch=4,
                    burn=.05, duration=.1, iterations=2, backend='numpy')
    elif name != 'quick':
        raise ValueError('Choose quick, reference, or smoke')
    return c.validate()
