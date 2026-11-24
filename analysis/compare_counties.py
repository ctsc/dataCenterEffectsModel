"""Validation 5.4: compare model-implied Sail ratios with metro Atlanta counties that already host data centers.

Uses the Python reference model (identical to NetLogo to 5e-12, see compare_models.py). Observed values come
from data/comparison_counties.csv and data/sources.md. Writes experiments/validation_counties.csv and the 5.4
section of experiments/validation_log.md. Run: python analysis/compare_counties.py
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reference_model as rm  # noqa: E402
import vlog  # noqa: E402

ROOT = os.path.join(HERE, "..")
COUNTY_GF = 428.0     # $M, Coweta FY2027 tentative budget (S16, secondary)
SCHOOL_GF = 324.8     # $M, Coweta schools FY2027 tentative general fund (S17, secondary)
LBNL_WUE = 0.36       # L/kWh site water use effectiveness (S21)
L_PER_GAL = 3.78541


def at(df, year):
    return df.iloc[(df.year - year).abs().idxmin()]


def main():
    p = rm.load_params()
    obs = pd.read_csv(os.path.join(ROOT, "data", "comparison_counties.csv"))
    base, evap, rp = rm.run(), rm.run(cooling="evap"), rm.run(payer="ratepayer")
    rows = []

    def add(metric, model, observed, verdict, note):
        rows.append(dict(metric=metric, model=model, observed=observed, verdict=verdict, note=note))

    douglas = obs[(obs.county == "Douglas GA") & (obs.metric.str.startswith("data center share"))].value.iloc[0]
    for yr in (10, 20):
        r = at(base, yr)
        cshare = p["county_share"] * r.rev_net / COUNTY_GF
        add("county share of DC revenue / county budget, year %d" % yr, "%.1f%%" % (100 * cshare),
            "Douglas 3-8%% (avg %.0f%%, S23)" % (100 * douglas), "inside" if 0.03 <= cshare <= 0.08 else "outside",
            "county government share (%.3f) of net DC revenue %.1f $M/yr over $%.0fM budget" % (p["county_share"], r.rev_net, COUNTY_GF))
    r = at(base, 20)
    tot = r.rev_net / (COUNTY_GF + SCHOOL_GF)
    add("net DC revenue / county + school budgets, year 20", "%.1f%%" % (100 * tot), "no comparable county figure", "n/a",
        "%.1f $M/yr over $%.0fM; Sail calibration target is about $100M/yr (S5, S7)" % (r.rev_net, COUNTY_GF + SCHOOL_GF))
    for name, df, wi in (("closed-loop", base, p["wi_closed"]), ("evaporative", evap, p["wi_evap"])):
        r = at(df, 20)
        share = r.E * wi / r.demand
        add("DC share of county water demand, year 20 (%s)" % name, "%.1f%%" % (100 * share), "Newton (Meta) about 10% (S24)",
            "below" if share < 0.10 else "above", "%.2f MGD of %.1f MGD" % (r.E * wi, r.demand))
    lbnl = LBNL_WUE * 1000 * 24 / L_PER_GAL / 1e6
    add("water per energized MW (MGD/MW)", "closed %.5f / evap %.5f" % (p["wi_closed"], p["wi_evap"]),
        "LBNL fleet average %.5f (S21, at full load)" % lbnl, "bracketed" if p["wi_closed"] < lbnl < p["wi_evap"] else "outside",
        "0.36 L/kWh x 24,000 kWh/day per MW; Sail closed-loop is a low-water design, the 2025 plan was evaporative")
    for name, df in (("DC pays (base)", base), ("ratepayers pay", rp)):
        r = at(df, 20)
        add("residential bill change, year 20 (%s)" % name, "%.0f $/hh/yr" % ((r.RI - 1) * p["elec_price"] / 100 * p["hh_kwh"]),
            "no county-level data; GA Power June 2026 change about -$50/yr (S19)", "n/a",
            "rate index %.4f; scale check only" % r.RI)
    r = at(base, 20)
    add("housing cost index excess vs no-DC baseline, year 20", "%.1f%%" % (100 * r.hx), "no local study found (sources.md)", "n/a",
        "driven by ASSUMPTION k_prox and hou_elast; covered by sensitivity")
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(ROOT, "experiments", "validation_counties.csv"), index=False)
    b = ["Model-implied Sail ratios (base case unless noted, Python reference model) against observed values for counties that already host data centers. "
         "These checks are thin: only Douglas (revenue share) and Newton (water share) publish comparable numbers, both from secondary news sources, "
         "and no county publishes rate or housing effects attributable to data centers.", "",
         "| Metric | Model | Observed | Verdict | Note |", "|---|---|---|---|---|"]
    b += ["| %s | %s | %s | %s | %s |" % tuple(r) for r in df.itertuples(index=False)]
    b += ["", "Reading: the revenue share at full build-out sits inside the Douglas range, so `rev_per_MW` (from the EIG analysis) is plausible. "
          "The closed-loop water share is well below Newton's Meta and the evaporative design well above it, which brackets the observation "
          "as expected for a low-water and a high-water design. Water per MW brackets the LBNL fleet average. Rate and housing effects cannot be checked "
          "against data, so they rest on ASSUMPTION parameters that are tested in 5.5. No parameters were adjusted."]
    vlog.write_section("5.4", "Comparison with metro Atlanta counties", "\n".join(b))
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
