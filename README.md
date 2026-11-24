# Data Center Effects Model

A system dynamics model of how data center development affects **Coweta County, Georgia** — built for CSC8840 (System Dynamics Modeling, Georgia State University, Fall 2026).

The model asks a practical question: when a county approves a large data center campus, who benefits and who pays? It tracks electricity, water, county finances, population, housing, and community opposition over 20 years, and tests what happens under different sizes, build-out speeds, cooling technologies, and policy choices.

## Headline result

For the base case — **Project Sail** (Prologis, ~900 MW near Sargent) — the model finds a **modest net benefit of about +$2,800 per household over 20 years**, but only under favorable assumptions about residents' quality-of-life costs, housing impacts, and starting opposition. The sign flips negative under worse policy combinations (e.g., evaporative cooling + ratepayers paying for grid upgrades), and the full analysis is in [`experiments/findings.md`](experiments/findings.md).

## What's in this repo

| Path | Contents |
|---|---|
| `model/` | The NetLogo 7 System Dynamics model (`DataCenterSD.nlogox`) and `build_nlogox.py`, which generates it from the spec — never edit the `.nlogox` by hand |
| `analysis/` | Python reference model (the test oracle), NetLogo-vs-Python comparison, all validation scripts, experiment runner, sensitivity analysis, and figure/report builders |
| `data/` | `parameters.csv` — every constant in the model with value, unit, source, and plausible range. `sources.md` — citations for every sourced fact; anything not publicly verifiable is labeled `ASSUMPTION` |
| `experiments/` | BehaviorSpace experiment definitions (`E0`–`E10`), raw result CSVs, and `findings.md` — the plain-English results writeup |
| `figures/` | All charts, generated from the experiment CSVs (never hand-made) |
| `submission/` | Final deliverables: report PDF/DOCX, slides PPTX, and the code zip |
| `report/`, `slides/` | Deliverable outputs only (build scripts are not published) |

## Tech stack

- **NetLogo 7** — the simulation model itself, using the System Dynamics Modeler and BehaviorSpace for batch runs
- **Python** — everything else: an independent reference implementation of the same equations, the experiment runner, validation, sensitivity analysis, and report/slide/figure generation
- **Java** — only used to launch NetLogo headless (NetLogo is a Java app); no model code is written in Java

## Model at a glance

- **Time:** 1-year steps, dt = 0.125, 20-year runs (year 0 ≈ FY2026–27)
- **Sectors:** electricity/grid, water, county finance, population/housing/opposition
- **Stocks:** energized data center capacity, grid capacity added, water supply capacity, cumulative net fiscal impact, population, community opposition
- **Loops:** one reinforcing (data center tax revenue → property tax relief → lower opposition → faster build-out) and three balancing (opposition slows permitting; grid capacity lags contracted load; water stress triggers delayed expansion)

## Quick start

Requires Python 3.11+ (pandas, numpy, matplotlib, scipy) and NetLogo 7 for the full pipeline. From a neutral directory:

```bash
# Verify the Python reference model
python analysis/test_reference.py

# Regenerate the NetLogo model from spec + parameters
python model/build_nlogox.py

# Confirm NetLogo matches the Python model (should print PASS)
python analysis/compare_models.py

# Run the experiments headless in NetLogo
python analysis/run_experiments.py
```

See `submission/README.md` (inside the code zip) for the full command list.

## Results in one paragraph

Build-out speed matters less than policy: cooling technology, who pays for grid upgrades, and tax abatements determine whether a campus is a net benefit or net cost. Closed-loop cooling keeps water and electricity impacts small even at 3,500 MW; evaporative cooling creates a hard size threshold (~1,458 MW) beyond which water stress outweighs tax revenue. Socializing grid costs on ratepayers shifts the threshold to ~3,687 MW. Opposition delays energization by up to ~3 years but never stalls construction entirely.

## Data honesty

Every parameter is either sourced (see `data/sources.md`, S1–S24) or explicitly labeled `ASSUMPTION` with a plausible range in `data/parameters.csv`. All assumption parameters go through sensitivity analysis; the report states plainly which conclusions are robust and which depend on judgement calls.

## Deliverables

- 📄 Report: [`submission/FinalProject_2026_CTierney.pdf`](submission/FinalProject_2026_CTierney.pdf)
- 🎞️ Slides: [`submission/FinalProject_2026_CTierney.pptx`](submission/FinalProject_2026_CTierney.pptx)
- 💻 Code: [`submission/FinalProject_2026_CTierney.zip`](submission/FinalProject_2026_CTierney.zip)
