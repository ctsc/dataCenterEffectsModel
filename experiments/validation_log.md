# experiments/validation_log.md

Validation record (plan Step 5). Sections are written by analysis/validate.py (5.2, 5.3), analysis/compare_counties.py (5.4), analysis/sensitivity.py (5.5) and analysis/gate.py (5.6).

## 5.2 Extreme-condition tests

All runs in NetLogo 7.0.4 headless. Zero-build tolerance is 1e-6 (floating-point noise from the closed-form p-base path is about 1e-11, see D15).

| Test | Expectation | Result | Detail |
|---|---|---|---|
| zero build-out (size-mw = 0) | no energized load, no fiscal impact, no net benefit, opposition stays at O0 | PASS | E=0 F=5.39e-11 nb=3.53e-09 O=0.4000 |
| 10x build-out (9000 MW) | stocks finite and non-negative, E <= G <= C <= size, opposition in [0,1) | PASS | E=8961 G=8980 C=9000 O=0.033 |
| near-zero water capacity (w0 = 0.5 MGD) | stress very high but finite, supply expands toward the permit cap, no NaN | PASS | stress=0.86 W=16.77 O=0.414 |
| abatement 0% | net revenue equals gross rev_per_MW * E at every step | PASS | max /rev-net - gross/ = 1.42e-14 |
| abatement 100% (never fades) | net data center revenue is ~0 for all 20 years | PASS | max rev-net = 2.01e-06 $M/yr |
| opposition driven to 0 | O stays at or near 0 and permitting speeds up to at most m_max | PASS | O_end=0.000 m_max_seen=1.250 |
| opposition driven to 1 | O stays below 1, permitting factor reaches 0 and build-out stalls (contracted << 900 MW) | PASS | O_max=0.9999 m_min=0.000 C_end=22 |
| shortest delays (one time step) | stable (no negative or oscillating stocks), E tracks C within a few steps | PASS | E_end=900.0, E monotone |
| very long delays (1000 years) | almost nothing energized, revenue ~0 | PASS | E_end=0.132 rev=0.0147 |
| zero population growth and zero jobs | population stays at P0 (housing excess only from proximity premium) | PASS | P_end=160240.00 P0=160240 |

## 5.3 Time-step test

Year-20 outputs at dt = 0.5, 0.25, 0.125, 0.0625 for three scenarios (base, 3,500 MW fast, stress case), NetLogo headless. Criterion: change from dt = 0.125 to dt = 0.0625 under 2% for every output.

| dt | scenario | energized-mw | net-fiscal | population | opposition | water-capacity | cumulative-nb | water-stress |
|---|---|---|---|---|---|---|---|---|
| 0.5 | base | 899.9 | 800.5 | 2.063e+05 | 0.3513 | 21 | 2704 | 0.6884 |
| 0.5 | big_fast | 3500 | 3223 | 2.057e+05 | 0.1476 | 21 | 1.21e+04 | 0.7275 |
| 0.5 | stress | 3497 | 2969 | 2.06e+05 | 0.7266 | 26.79 | -2.933e+04 | 1.784 |
| 0.25 | base | 899.7 | 808 | 2.064e+05 | 0.3517 | 21 | 2743 | 0.6887 |
| 0.25 | big_fast | 3499 | 3245 | 2.058e+05 | 0.1496 | 21 | 1.213e+04 | 0.7277 |
| 0.25 | stress | 3496 | 2983 | 2.061e+05 | 0.7271 | 26.78 | -2.888e+04 | 1.784 |
| 0.125 | base | 899.7 | 811.7 | 2.064e+05 | 0.352 | 21 | 2763 | 0.6888 |
| 0.125 | big_fast | 3499 | 3256 | 2.058e+05 | 0.1507 | 21 | 1.216e+04 | 0.7279 |
| 0.125 | stress | 3494 | 2991 | 2.061e+05 | 0.7274 | 26.77 | -2.868e+04 | 1.784 |
| 0.0625 | base | 899.6 | 813.6 | 2.064e+05 | 0.3521 | 21 | 2773 | 0.6889 |
| 0.0625 | big_fast | 3499 | 3262 | 2.059e+05 | 0.1513 | 21 | 1.218e+04 | 0.7279 |
| 0.0625 | stress | 3494 | 2995 | 2.061e+05 | 0.7275 | 26.77 | -2.858e+04 | 1.784 |

Largest relative change between dt = 0.125 and dt = 0.0625: 0.403% -> PASS

| scenario | output | change 0.125 vs 0.0625 | change 0.25 vs 0.125 |
|---|---|---|---|
| base | energized-mw | 0.005% | 0.009% |
| base | net-fiscal | 0.230% | 0.461% |
| base | population | 0.010% | 0.019% |
| base | opposition | 0.038% | 0.073% |
| base | water-capacity | 0.000% | 0.000% |
| base | cumulative-nb | 0.369% | 0.733% |
| base | water-stress | 0.009% | 0.018% |
| big_fast | energized-mw | 0.003% | 0.006% |
| big_fast | net-fiscal | 0.174% | 0.347% |
| big_fast | population | 0.009% | 0.018% |
| big_fast | opposition | 0.403% | 0.756% |
| big_fast | water-capacity | 0.000% | 0.000% |
| big_fast | cumulative-nb | 0.132% | 0.236% |
| big_fast | water-stress | 0.008% | 0.017% |
| stress | energized-mw | 0.018% | 0.032% |
| stress | net-fiscal | 0.130% | 0.261% |
| stress | population | 0.009% | 0.019% |
| stress | opposition | 0.018% | 0.033% |
| stress | water-capacity | 0.013% | 0.022% |
| stress | cumulative-nb | 0.326% | 0.718% |
| stress | water-stress | 0.003% | 0.005% |

## 5.4 Comparison with metro Atlanta counties

Model-implied Sail ratios (base case unless noted, Python reference model) against observed values for counties that already host data centers. These checks are thin: only Douglas (revenue share) and Newton (water share) publish comparable numbers, both from secondary news sources, and no county publishes rate or housing effects attributable to data centers.

| Metric | Model | Observed | Verdict | Note |
|---|---|---|---|---|
| county share of DC revenue / county budget, year 10 | 4.8% | Douglas 3-8% (avg 5%, S23) | inside | county government share (0.331) of net DC revenue 61.5 $M/yr over $428M budget |
| county share of DC revenue / county budget, year 20 | 7.8% | Douglas 3-8% (avg 5%, S23) | inside | county government share (0.331) of net DC revenue 100.3 $M/yr over $428M budget |
| net DC revenue / county + school budgets, year 20 | 13.3% | no comparable county figure | n/a | 100.3 $M/yr over $753M; Sail calibration target is about $100M/yr (S5, S7) |
| DC share of county water demand, year 20 (closed-loop) | 2.1% | Newton (Meta) about 10% (S24) | below | 0.30 MGD of 14.5 MGD |
| DC share of county water demand, year 20 (evaporative) | 37.9% | Newton (Meta) about 10% (S24) | above | 8.65 MGD of 22.8 MGD |
| water per energized MW (MGD/MW) | closed 0.00033 / evap 0.00962 | LBNL fleet average 0.00228 (S21, at full load) | bracketed | 0.36 L/kWh x 24,000 kWh/day per MW; Sail closed-loop is a low-water design, the 2025 plan was evaporative |
| residential bill change, year 20 (DC pays (base)) | 2 $/hh/yr | no county-level data; GA Power June 2026 change about -$50/yr (S19) | n/a | rate index 1.0012; scale check only |
| residential bill change, year 20 (ratepayers pay) | 25 $/hh/yr | no county-level data; GA Power June 2026 change about -$50/yr (S19) | n/a | rate index 1.0144; scale check only |
| housing cost index excess vs no-DC baseline, year 20 | 1.7% | no local study found (sources.md) | n/a | driven by ASSUMPTION k_prox and hou_elast; covered by sensitivity |

Reading: the revenue share at full build-out sits inside the Douglas range, so `rev_per_MW` (from the EIG analysis) is plausible. The closed-loop water share is well below Newton's Meta and the evaporative design well above it, which brackets the observation as expected for a low-water and a high-water design. Water per MW brackets the LBNL fleet average. Rate and housing effects cannot be checked against data, so they rest on ASSUMPTION parameters that are tested in 5.5. No parameters were adjusted.

## 5.5 Sensitivity analysis

One-at-a-time sweeps of all 55 parameters with a low/high range (Python reference model, decision D14), Sail base case. Base case: cumulative net benefit 2763 $/household, peak water stress 0.689, final opposition 0.352, year-20 net fiscal impact 812 $M. Ranked by the swing in cumulative net benefit. Full table: `experiments/sensitivity_results.csv`; chart: `figures/tornado.png`.

| Rank | Parameter | Type | Low / high | cum. NB at low | cum. NB at high | swing | sign flips? | final O low / high |
|---|---|---|---|---|---|---|---|---|
| 1 | k_prox | ASSUMPTION | 0 / 0.1 | 6351 | -11365 | 17715 | yes | 0.340 / 0.396 |
| 2 | ql_cost | ASSUMPTION | 0 / 3000 | 10667 | -5142 | 15809 | yes | 0.352 / 0.352 |
| 3 | rev_per_MW | sourced | 0.08 / 0.14 | -2025 | 7105 | 9130 | yes | 0.372 / 0.333 |
| 4 | O0 | ASSUMPTION | 0.2 / 0.6 | 6492 | -989 | 7481 | yes | 0.112 / 0.579 |
| 5 | abate0 | sourced | 0 / 1 | 8107 | 2216 | 5891 | no | 0.351 / 0.352 |
| 6 | T_abate | sourced | 10 / 20 | 6181 | 336 | 5845 | no | 0.351 / 0.357 |
| 7 | svc_cost_per_MW | ASSUMPTION | 0.00085 / 0.02 | 3556 | -103 | 3658 | yes | 0.352 / 0.352 |
| 8 | a_r | ASSUMPTION | 1 / 6 | 2508 | 6040 | 3533 | no | 0.375 / 0.022 |
| 9 | house_cost_base | ASSUMPTION | 10000 / 20000 | 4424 | 1655 | 2769 | no | 0.352 / 0.352 |
| 10 | g_pop | sourced | 0.005 / 0.025 | 3874 | 1162 | 2712 | no | 0.354 / 0.378 |
| 11 | s_hm | ASSUMPTION | 0 / 3 | 1854 | 4142 | 2287 | no | 0.356 / 0.347 |
| 12 | relief_share | ASSUMPTION | 0 / 0.5 | 2039 | 4134 | 2095 | no | 0.417 / 0.221 |
| 13 | hh_size | ASSUMPTION | 2.6 / 3 | 1765 | 3758 | 1993 | no | 0.352 / 0.352 |
| 14 | newhh_per_job | sourced | 0.15 / 0.6 | 3307 | 1396 | 1910 | no | 0.351 / 0.355 |
| 15 | jobs_per_MW | sourced | 0.15 / 0.5 | 3306 | 1819 | 1487 | no | 0.351 / 0.354 |

Parameters whose low or high value alone flips the sign of cumulative net benefit: k_prox, ql_cost, rev_per_MW, O0, svc_cost_per_MW.

Latin hypercube (400 samples, seed 42) over the top 8 ASSUMPTION parameters jointly (k_prox, ql_cost, O0, svc_cost_per_MW, a_r, house_cost_base, s_hm, relief_share; sourced values and policy levers held at base): cumulative net benefit is positive in 50% of samples (median -128, 5th-95th percentile -13601 to 10033 $/household). Peak water stress stays below 0.691 in every sample.

Honest reading: the sign of net benefit for Sail is not robust. It is driven mostly by judgement parameters (ASSUMPTION) that no public data pins down, so the report presents net benefit as conditional on these values, not as a forecast.

NetLogo spot checks (top 3 parameters at their high value, NetLogo 7.0.4 headless vs reference):

| Setting | NetLogo cum. NB | Reference cum. NB | worst rel. diff (cum NB, O, F) |
|---|---|---|---|
| k_prox = 0.1 | -11364.789 | -11364.789 | 3.8e-15 |
| ql_cost = 3000 | -5141.672 | -5141.672 | 3.5e-16 |
| rev_per_MW = 0.14 | 7104.764 | 7104.764 | 0.0e+00 |

Spot checks PASS (criterion 1e-6).

## 5.6 Validation gate

| Check | Result | Evidence |
|---|---|---|
| 5.1 units | PASS | data/units_check.md |
| 5.2 extreme conditions | PASS | 10/10 tests pass |
| 5.3 time step | PASS | worst change 0.40% (< 2%) |
| 5.4 county comparison | PASS | table written; thin data documented (exception: rate and housing effects have no observed comparator) |
| 5.5 sensitivity | PASS | OAT table, tornado and LHS written; NetLogo spot checks agree to 4e-15 |

Documented exceptions: (1) 5.4 cannot test rate or housing effects because no comparison county publishes them; (2) 5.5 shows that the sign of Sail's net benefit depends on ASSUMPTION parameters (k_prox, ql_cost, O0, svc_cost_per_MW), which is a finding to report, not a model defect.

Gate: PASS, model archived as model/archive/DataCenterSD_validated.nlogox.

