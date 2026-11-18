# Pena et al. (2018) replication — report

_Generated 2026-11-18 09:12 UTC by `make_report.py`. Open with Ctrl+Shift+V. Compare each figure with the paper page given._


| Fig | Ran | Status |
|---|---|---|
| [3](#figure-3) | ✅ 18 Nov 07:57 | ✓ A–D match the published curves (generations 0–10) |
| [4](#figure-4) | ✅ 18 Nov 08:06 | scaffold |
| [5](#figure-5) | ✅ 18 Nov 08:22 | scaffold |
| [6](#figure-6) | ✅ 18 Nov 08:28 | scaffold |
| [7](#figure-7) | ✅ 18 Nov 08:28 | scaffold |
| [8](#figure-8) | ✅ 18 Nov 08:45 | scaffold |
| [9](#figure-9) | ✅ 18 Nov 09:10 | scaffold |
| [10](#figure-10) | ✅ 18 Nov 09:10 | scaffold |
| [11](#figure-11) | ✅ 18 Nov 09:10 | scaffold |
| [12](#figure-12) | ✅ 18 Nov 09:12 | scaffold |
| [13](#figure-13) | ✅ 18 Nov 09:12 | scaffold |

## Figure 3
`Figure03_Rate_Averaging.ipynb` · paper p. 7 · ✅ 18 Nov 07:57

![Figure 3](figures/figure03_rate_averaging.png)

Data: [figure03_numbers.csv](figures/figure03_numbers.csv) · [figure03_rate_averaging.csv](figures/figure03_rate_averaging.csv)

| gen | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A ours | 13.00 | 2.40 | 46.79 | 0.00 | 62.86 | 0.00 | 62.86 | 0.00 | 62.86 | 0.00 | 62.86 |
| A paper | 13.0 | 2.0 | 51.0 | 0.0 | 63.0 | 0.0 | 63.0 | 0.0 | 63.0 | 0.0 | 63.0 |
| B ours | 13.00 | 7.70 | 8.42 | 9.65 | 8.65 | 9.26 | 9.01 | 9.11 | 9.12 | 9.11 | 9.12 |
| B paper | 13.1 | 7.4 | 8.4 | 9.7 | 8.6 | 9.4 | 9.0 | 9.2 | 9.1 | 9.1 | 9.1 |
| C ours | 13.00 | 7.70 | 8.18 | 9.12 | 9.27 | 9.21 | 9.13 | 9.08 | 9.07 | 9.08 | 9.09 |
| C paper | 13.0 | 7.4 | 8.1 | 9.1 | 9.3 | 9.2 | 9.1 | 9.1 | 9.1 | 9.1 | 9.1 |

<details><summary>Other printed output</summary>

```
A: loaded figure03v2_A_avg1_trials10000_gen10_nu013_seed3.npz
B: loaded figure03v2_B_avg2_trials10000_gen10_nu013_seed3.npz
C: loaded figure03v2_C_avgall_trials10000_gen10_nu013_seed3.npz
fixed point of nu_out(nu_in): 8.72 Hz, slope -2.56 (network: 9.1 Hz)
two-sample averaging (r_(n-1)+r_n)/2 is stable only if slope > -2 -> UNSTABLE
panel B: generations 7-10 mean = 9.12 Hz (network 9.1 Hz)
panel C: generations 7-10 mean = 9.08 Hz (network 9.1 Hz)
```
</details>


## Figure 4
`Figure04_Slow_Fluctuations.ipynb` · paper p. 8 · ✅ 18 Nov 08:06

![Figure 4](figures/figure04_slow_fluctuations.png)

Data: [figure04_numbers.csv](figures/figure04_numbers.csv) · [figure04_slow_fluctuations.csv](figures/figure04_slow_fluctuations.csv)

| J | nu_sch | nu_net | FF_sch | FF_net | tc_sch | tc_net (ms) |
|---|---|---|---|---|---|---|
| 0.1 | 13.58 | 13.83 | 0.25 | 0.24 | 44.77 | 44.89 |
| 0.2 | 11.27 | 11.67 | 0.83 | 0.78 | 10.66 | 12.97 |
| 0.3 | 11.50 | 11.48 | 1.60 | 1.51 | 38.92 | 28.50 |
| 0.4 | 13.55 | 13.29 | 2.77 | 2.75 | 244.66 | 225.67 |
| 0.6 | 24.96 | 23.90 | 7.30 | 8.20 | 1171.14 | 1617.59 |
| 0.8 | 41.07 | 39.64 | 13.42 | 14.68 | 1776.53 | 2316.59 |
| 1.0 | 54.67 | 57.52 | 18.71 | 22.28 | 2067.50 | 2824.48 |

## Figure 5
`Figure05_Synaptic_Filter.ipynb` · paper p. 9 · ✅ 18 Nov 08:22

![Figure 5](figures/figure05_synaptic_filter.png)

Data: [figure05_numbers.csv](figures/figure05_numbers.csv) · [figure05_synaptic_filter.csv](figures/figure05_synaptic_filter.csv)

| tau_s | nu scheme | net |
|---|---|---|
| 0.0 | 11.27 | 11.67 |
| 2.0 | 9.26 | 9.19 |
| 5.0 | 8.34 | 8.31 |
| 10.0 | 7.60 | 7.65 |
| 20.0 | 7.03 | 6.91 |

| J | FF | FF 2 | tau_c | tau_c 2 |
|---|---|---|---|---|
| 0.1 | 0.48 | 0.45 | 40.7 | 41.8 |
| 0.2 | 1.28 | 1.23 | 49.4 | 40.3 |
| 0.3 | 2.10 | 2.02 | 285.4 | 237.4 |
| 0.4 | 3.36 | 3.47 | 931.9 | 859.8 |
| 0.6 | 9.17 | 10.77 | 2640.6 | 3491.5 |
| 0.8 | 17.76 | 19.22 | 3354.4 | 4200.6 |
| 1.0 | 24.90 | 27.01 | 3665.9 | 3919.1 |

## Figure 6
`Figure06_EI_Heterogeneous.ipynb` · paper p. 10 · ✅ 18 Nov 08:28

![Figure 6](figures/figure06_ei_heterogeneous.png)

Data: [figure06_ei_heterogeneous.csv](figures/figure06_ei_heterogeneous.csv) · [figure06_numbers.csv](figures/figure06_numbers.csv)

| case | nuE sch | nuE net | nuE paper | nuI sch | nuI net | nuI paper | rel.err E | rel.err I |
|---|---|---|---|---|---|---|---|---|
| A | 3.78 | 3.20 | 3.2 | 10.26 | 9.77 | 9.7 | 0.026 | 0.002 |
| B | 128.89 | 126.99 | 128.9 | 129.95 | 128.30 | 129.9 | 0.046 | 0.042 |
| C | 0.26 | 0.14 | 0.1 | 7.38 | 7.38 | 7.4 | 0.832 | 0.001 |

## Figure 7
`Figure07_Network_Size.ipynb` · paper p. 11 · ✅ 18 Nov 08:28

![Figure 7](figures/figure07_network_size.png)

Data: [figure07_network_size.csv](figures/figure07_network_size.csv) · [figure07_numbers.csv](figures/figure07_numbers.csv)

| N_E | err E | I | rates | rates 2 |
|---|---|---|---|---|
| 2500 | 0.0409 | 0.0026 | 3.13 | 9.87 |
| 5000 | 0.0368 | 0.0020 | 3.17 | 9.80 |
| 10000 | 0.0264 | 0.0021 | 3.20 | 9.77 |
| 20000 | 0.0282 | 0.0017 | 3.24 | 9.77 |

## Figure 8
`Figure08_Multi_Population.ipynb` · paper p. 12 · ✅ 18 Nov 08:45

![Figure 8](figures/figure08_multi_population.png)

Data: [figure08_multi_population.csv](figures/figure08_multi_population.csv) · [figure08_numbers.csv](figures/figure08_numbers.csv)

| label | rate scheme | network | error |
|---|---|---|---|
| RS | 5.03 | 4.81 | 0.002 |
| LTS | 7.86 | 7.81 | 0.000 |
| FS | 20.36 | 19.70 | 0.002 |
| E1 | 70.43 | 69.67 | 0.013 |
| I1 | 70.43 | 69.88 | 0.012 |
| E2 | 95.86 | 93.11 | 0.002 |
| I2 | 95.94 | 93.44 | 0.002 |

## Figure 9
`Figure09_Rate_Histograms.ipynb` · paper p. 13 · ✅ 18 Nov 09:10

![Figure 9](figures/figure09_rate_histograms.png)

Data: [figure09_numbers.csv](figures/figure09_numbers.csv) · [figure09_rate_histograms.csv](figures/figure09_rate_histograms.csv)

| fixed g | mean | mean 2 | Hz SD | Hz SD 2 |
|---|---|---|---|---|
| 3.5 | 194.95 | 185.89 | 44.54 | 41.19 |
| 4.0 | 71.10 | 61.06 | 36.80 | 30.98 |
| 6.0 | 14.12 | 13.45 | 11.22 | 10.43 |

| exponential g | mean | mean 2 | Hz SD | Hz SD 2 |
|---|---|---|---|---|
| 3.5 | 197.81 | 172.48 | 66.41 | 65.59 |
| 4.0 | 78.46 | 62.30 | 52.02 | 43.21 |
| 6.0 | 16.80 | 14.45 | 15.70 | 13.96 |

## Figure 10
`Figure10_ER_Rates_Spectra.ipynb` · paper p. 14 · ✅ 18 Nov 09:10

![Figure 10](figures/figure10_er_fixed.png)

Data: [figure10_er_fixed.csv](figures/figure10_er_fixed.csv) · [figure10_numbers.csv](figures/figure10_numbers.csv)

| g | M | mean | mean 2 | Hz SD | Hz SD 2 | error of mean spectrum |
|---|---|---|---|---|---|---|
| 3.5 | 10 | 190.48 | 185.89 | 33.72 | 41.19 | 0.008 |
| 3.5 | 50 | 194.95 | 185.89 | 43.70 | 41.19 | 0.045 |
| 3.5 | 100 | 194.81 | 185.89 | 41.11 | 41.19 | 0.030 |
| 4.0 | 10 | 66.37 | 61.06 | 28.60 | 30.98 | 0.020 |
| 4.0 | 50 | 71.10 | 61.06 | 36.21 | 30.98 | 0.036 |
| 4.0 | 100 | 69.43 | 61.06 | 34.87 | 30.98 | 0.028 |
| 6.0 | 10 | 13.42 | 13.45 | 8.19 | 10.43 | 0.018 |
| 6.0 | 50 | 14.12 | 13.45 | 11.02 | 10.43 | 0.005 |
| 6.0 | 100 | 14.01 | 13.45 | 10.88 | 10.43 | 0.000 |

## Figure 11
`Figure11_ER_Exp_Weights.ipynb` · paper p. 15 · ✅ 18 Nov 09:10

![Figure 11](figures/figure11_er_exponential.png)

Data: [figure11_er_exponential.csv](figures/figure11_er_exponential.csv) · [figure11_numbers.csv](figures/figure11_numbers.csv)

| g | M | mean | mean 2 | Hz SD | Hz SD 2 | error of mean spectrum |
|---|---|---|---|---|---|---|
| 3.5 | 10 | 182.66 | 172.48 | 58.53 | 65.59 | 0.009 |
| 3.5 | 50 | 197.81 | 172.48 | 63.89 | 65.59 | 0.138 |
| 3.5 | 100 | 197.45 | 172.48 | 62.98 | 65.59 | 0.088 |
| 4.0 | 10 | 70.87 | 62.30 | 41.84 | 43.21 | 0.016 |
| 4.0 | 50 | 78.46 | 62.30 | 50.95 | 43.21 | 0.025 |
| 4.0 | 100 | 74.61 | 62.30 | 48.63 | 43.21 | 0.009 |
| 6.0 | 10 | 15.86 | 14.45 | 11.57 | 13.96 | 0.068 |
| 6.0 | 50 | 16.80 | 14.45 | 15.31 | 13.96 | 0.014 |
| 6.0 | 100 | 15.69 | 14.45 | 14.01 | 13.96 | 0.026 |

## Figure 12
`Figure12_Non_Gaussianity.ipynb` · paper p. 16 · ✅ 18 Nov 09:12

![Figure 12](figures/figure12_non_gaussianity.png)

Data: [figure12_non_gaussianity.csv](figures/figure12_non_gaussianity.csv) · [figure12_numbers.csv](figures/figure12_numbers.csv)

| g | g 2 | neurons mean error | lower bound |
|---|---|---|---|
| 4.0 | 892 | 0.133 | 0.341 |
| 6.0 | 848 | 0.228 | 0.359 |

## Figure 13
`Figure13_Non_Gaussianity_Rate_Window.ipynb` · paper p. 16 · ✅ 18 Nov 09:12

![Figure 13](figures/figure13_non_gaussianity_20_100Hz.png)

Data: [figure13_non_gaussianity_20_100Hz.csv](figures/figure13_non_gaussianity_20_100Hz.csv) · [figure13_numbers.csv](figures/figure13_numbers.csv)

| g | g 2 | neurons mean error | lower bound |
|---|---|---|---|
| 4.0 | 556 | 0.129 | 0.335 |
| 6.0 | 298 | 0.130 | 0.328 |

