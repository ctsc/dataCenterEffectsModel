# ai_use_log.md

Every use of AI tools in this project. Feeds the AI-use disclosure section of the report. Tools: Claude Code (Anthropic Claude) for Steps 0 to mid-5, Devin CLI (Cognition, Claude-based agent) from Step 5.2 on. Carter Tierney defined the topic, scope, goals and proposal; he reviews all deliverables (see manual.md).

| Date | Tool | Step | What the AI did | How it was verified |
|---|---|---|---|---|
| 2026-11-23 | Claude Code | planning | Read project.md and the proposal; drafted plan.md, manual.md, CLAUDE.md, progress.md, decisions.md | Carter reviewed the plan before execution |
| 2026-11-23 | Claude Code | 0 | Installed NetLogo 7.0.4 without admin, wrote the headless launcher | Toy BehaviorSpace run matched the analytic logistic value (D3) |
| 2026-11-23 | Claude Code | 1 | Web research for Project Sail, Coweta County, water, electricity and comparison-county facts; built data/sources.md, parameters.csv, comparison_counties.csv | Each claim has a URL and a Verified/Secondary label; values without a source are labeled ASSUMPTION; derive_eig.py reproduces the EIG fiscal schedule |
| 2026-11-23 | Claude Code | 2 | Wrote notes/model_spec.md, data/units_check.md and the diagram script (causal loop and stock-and-flow figures) | Unit audit of every equation; loops checked against the proposal |
| 2026-11-23 | Claude Code | 3 | Wrote analysis/reference_model.py and test_reference.py | 6 hand-derived behavior tests pass |
| 2026-11-23 | Claude Code | 4 | Wrote model/build_nlogox.py (generates the NetLogo SD model), nl.py and compare_models.py | NetLogo output matches the independent Python model to 5e-12 in 8 scenarios |
| 2026-11-23 | Devin CLI | 5.2-5.3 | Ran and debugged analysis/validate.py (tolerance and a pandas attribute bug), added section-based log writer vlog.py | 10/10 extreme tests pass in NetLogo; dt change 0.40% < 2% |
| 2026-11-23 | Devin CLI | 5.4 | Wrote compare_counties.py comparing model ratios with Douglas, Newton and LBNL figures | Inputs traced to sources.md S16, S17, S21, S23, S24 |
| 2026-11-23 | Devin CLI | 5.5-5.6 | Wrote sensitivity.py (one-at-a-time, Latin hypercube, tornado) and gate.py | 3 NetLogo spot checks agree with the Python sweeps to 4e-15 |
| 2026-11-23 | Devin CLI | 6 | Wrote run_experiments.py (E0-E10 BehaviorSpace setups) and ran them in NetLogo | Row counts and NaN checks per experiment; numbers in findings.md come from the CSVs |
| 2026-11-23 | Devin CLI | 7 | Wrote make_figures.py, the NetLogo GUI snapshot program (Snap.java, snapshots.py) and demo_script.md; regenerated the SD diagram layout | Figures inspected visually; snapshot numbers equal E5 results; compare_models.py PASS after the layout change |
| 2026-11-23 | Devin CLI | 8 | Drafted the report text and wrote build_report.py (numbers read from CSVs at build time) | Page count and fonts checked from the PDF; notes/factcheck.md |
| 2026-11-23 | Devin CLI | 9 | Drafted slides and speaker notes (build_slides.py) | Rendered every slide with PowerPoint and inspected; overflow check |
| 2026-11-23 | Devin CLI | 10 | Wrote package.py, the submission README, final_checklist.md and the manual.md final status | Zip unzipped to a clean folder; tests, one experiment and figures rerun there |
