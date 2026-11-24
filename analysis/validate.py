"""Validation tests 5.2 (extreme conditions) and 5.3 (time step), run in NetLogo headless.
Writes experiments/validation_extreme.csv, experiments/validation_timestep.csv and experiments/validation_log.md
(sections for 5.2 and 5.3; other sections are added by their own scripts). Run: python analysis/validate.py"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nl  # noqa: E402
import reference_model as rm  # noqa: E402
import vlog  # noqa: E402

ROOT = os.path.join(HERE, "..")
MODEL = os.path.join(ROOT, "model", "DataCenterSD.nlogox")
EXP = os.path.join(ROOT, "experiments")
os.makedirs(EXP, exist_ok=True)

P = rm.load_params()
METRICS = ["ticks", "energized-mw", "grid-mw", "contracted-mw", "water-capacity", "net-fiscal", "population",
           "opposition", "cumulative-nb", "water-stress", "rate-index", "housing-index", "permit-factor", "rev-net",
           "net-benefit"]


def run(name, consts, model=MODEL, steps=2000, every=False):
    return nl.run_setup(model, nl.experiment_xml(name, METRICS, constants=consts, every_step=every, steps=steps), name)


def ok(cond):
    return "PASS" if cond else "FAIL"


def extreme():
    rows = []

    def add(test, expectation, passed, detail):
        rows.append(dict(test=test, expectation=expectation, result=ok(passed), detail=detail))

    base = run("base", {})
    b = base.iloc[-1]
    # 1. zero build-out equals the no-data-center baseline
    z = run("zero", {"size-mw": 0}).iloc[-1]
    add("zero build-out (size-mw = 0)", "no energized load, no fiscal impact, no net benefit, opposition stays at O0",
        z["energized-mw"] == 0 and abs(z["net-fiscal"]) < 1e-6 and abs(z["cumulative-nb"]) < 1e-6 and abs(z["opposition"] - P["O0"]) < 1e-9,
        "E=%.3g F=%.3g nb=%.3g O=%.4f" % (z["energized-mw"], z["net-fiscal"], z["cumulative-nb"], z["opposition"]))
    # 2. 10x build-out (9,000 MW), stocks bounded
    big = run("tenx", {"size-mw": 9000, "t-sign": 5}).iloc[-1]
    vals = big[["energized-mw", "grid-mw", "contracted-mw", "water-capacity", "population", "opposition"]].astype(float)
    add("10x build-out (9000 MW)", "stocks finite and non-negative, E <= G <= C <= size, opposition in [0,1)",
        np.isfinite(vals).all() and (vals >= 0).all() and big["energized-mw"] <= big["grid-mw"] + 1e-6 <= big["contracted-mw"] + 1e-6
        <= 9000 + 1e-6 and 0 <= big["opposition"] < 1,
        "E=%.0f G=%.0f C=%.0f O=%.3f" % (big["energized-mw"], big["grid-mw"], big["contracted-mw"], big["opposition"]))
    # 3. tiny water capacity
    w = run("lowwater", {"w0": 0.5}).iloc[-1]
    add("near-zero water capacity (w0 = 0.5 MGD)", "stress very high but finite, supply expands toward the permit cap, no NaN",
        np.isfinite(w["water-stress"]) and w["water-capacity"] > 0.5 and w["water-capacity"] <= P["water_cap"] + 1e-6 and 0 <= w["opposition"] < 1,
        "stress=%.2f W=%.2f O=%.3f" % (w["water-stress"], w["water-capacity"], w["opposition"]))
    # 4. abatement 0 and 100%
    a0 = run("abate0", {"abate0": 0.0}, every=True)
    a1 = run("abate1", {"abate0": 1.0, "t-abate": 1e9}, every=True)
    add("abatement 0%", "net revenue equals gross rev_per_MW * E at every step",
        np.allclose(a0["rev-net"], P["rev_per_MW"] * a0["energized-mw"], rtol=1e-9, atol=1e-9),
        "max |rev-net - gross| = %.2e" % np.abs(a0["rev-net"] - P["rev_per_MW"] * a0["energized-mw"]).max())
    add("abatement 100% (never fades)", "net data center revenue is ~0 for all 20 years",
        a1["rev-net"].max() < 1e-3, "max rev-net = %.2e $M/yr" % a1["rev-net"].max())
    # 5. opposition forced low and high through its driver
    lo = run("opplow", {"d-open0": 0.0, "tau-o": 0.125}, every=True)
    hi = run("opphigh", {"d-open0": 1e4, "tau-o": 0.125}, every=True)
    add("opposition driven to 0", "O stays at or near 0 and permitting speeds up to at most m_max",
        lo["opposition"].iloc[-1] < 0.05 and lo["permit-factor"].max() <= P["m_max"] + 1e-9,
        "O_end=%.3f m_max_seen=%.3f" % (lo["opposition"].iloc[-1], lo["permit-factor"].max()))
    add("opposition driven to 1", "O stays below 1, permitting factor reaches 0 and build-out stalls (contracted << 900 MW)",
        hi["opposition"].max() < 1 and hi["permit-factor"].min() == 0 and hi["contracted-mw"].iloc[-1] < 450,
        "O_max=%.4f m_min=%.3f C_end=%.0f" % (hi["opposition"].max(), hi["permit-factor"].min(), hi["contracted-mw"].iloc[-1]))
    # 6. shortest delays (one time step) and very long delays
    sd = run("shortdelay", {"d-grid": P["dt"], "tau-energize": P["dt"]}, every=True)
    add("shortest delays (one time step)", "stable (no negative or oscillating stocks), E tracks C within a few steps",
        (sd["energized-mw"].diff().dropna() >= -1e-9).all() and sd["energized-mw"].iloc[-1] > 850,
        "E_end=%.1f, E monotone" % sd["energized-mw"].iloc[-1])
    ld = run("longdelay", {"d-grid": 1000, "tau-energize": 1000}).iloc[-1]
    add("very long delays (1000 years)", "almost nothing energized, revenue ~0",
        ld["energized-mw"] < 5 and ld["rev-net"] < 1,
        "E_end=%.3f rev=%.4f" % (ld["energized-mw"], ld["rev-net"]))
    # 7. no population growth and no jobs: population stays constant and no data center residents
    pop = run("pop0", {"g-pop": 0, "jobs-per-mw": 0}).iloc[-1]
    add("zero population growth and zero jobs", "population stays at P0 (housing excess only from proximity premium)",
        abs(pop["population"] - P["P0"]) < 1e-6, "P_end=%.2f P0=%.0f" % (pop["population"], P["P0"]))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(EXP, "validation_extreme.csv"), index=False)
    return df


def build_dt_model(dt, out):
    subprocess.run([sys.executable, os.path.join(ROOT, "model", "build_nlogox.py"), "--dt", str(dt), "--out", out],
                   check=True, capture_output=True)
    return out


def timestep():
    import tempfile
    rows = []
    scenarios = {"base": {}, "big_fast": {"size-mw": 3500, "t-sign": 3},
                 "stress": {"size-mw": 3500, "payer": '"ratepayer"', "cooling": '"evap"', "drought?": "true"}}
    outs = ["energized-mw", "net-fiscal", "population", "opposition", "water-capacity", "cumulative-nb", "water-stress"]
    with tempfile.TemporaryDirectory() as d:
        for dt in (0.5, 0.25, 0.125, 0.0625):
            m = build_dt_model(dt, os.path.join(d, "m_%s.nlogox" % dt))
            for sc, consts in scenarios.items():
                r = run("dt", consts, model=m, steps=int(20 / dt) + 50).iloc[-1]
                row = dict(dt=dt, scenario=sc)
                row.update({k: float(r[k]) for k in outs})
                rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(EXP, "validation_timestep.csv"), index=False)
    return df, outs


def write_log(ex, ts, chg, outs):
    worst = chg.change_0125_vs_00625.max()
    ts_pass = worst < 0.02
    b = ["All runs in NetLogo 7.0.4 headless. Zero-build tolerance is 1e-6 (floating-point noise from the closed-form p-base path is about 1e-11, see D15).",
         "", "| Test | Expectation | Result | Detail |", "|---|---|---|---|"]
    b += ["| %s | %s | %s | %s |" % (r.test, r.expectation, r.result, str(r.detail).replace("|", "/")) for _, r in ex.iterrows()]
    vlog.write_section("5.2", "Extreme-condition tests", "\n".join(b))
    b = ["Year-20 outputs at dt = 0.5, 0.25, 0.125, 0.0625 for three scenarios (base, 3,500 MW fast, stress case), NetLogo headless. "
         "Criterion: change from dt = 0.125 to dt = 0.0625 under 2% for every output.", "",
         "| dt | scenario | " + " | ".join(outs) + " |", "|---|---|" + "---|" * len(outs)]
    b += ["| %s | %s | " % (r["dt"], r["scenario"]) + " | ".join("%.4g" % r[k] for k in outs) + " |" for _, r in ts.iterrows()]
    b += ["", "Largest relative change between dt = 0.125 and dt = 0.0625: %.3f%% -> %s" % (100 * worst, ok(ts_pass)), "",
          "| scenario | output | change 0.125 vs 0.0625 | change 0.25 vs 0.125 |", "|---|---|---|---|"]
    b += ["| %s | %s | %.3f%% | %.3f%% |" % (r.scenario, r.output, 100 * r.change_0125_vs_00625, 100 * r.change_025_vs_0125) for _, r in chg.iterrows()]
    vlog.write_section("5.3", "Time-step test", "\n".join(b))
    return ts_pass


def main():
    if "--log-only" in sys.argv:
        ts = pd.read_csv(os.path.join(EXP, "validation_timestep.csv"))
        outs = [c for c in ts.columns if c not in ("dt", "scenario")]
        write_log(pd.read_csv(os.path.join(EXP, "validation_extreme.csv")), ts,
                  pd.read_csv(os.path.join(EXP, "validation_timestep_change.csv")), outs)
        return 0
    ex = extreme()
    print(ex.to_string(index=False))
    ts, outs = timestep()
    chg = []
    for sc, g in ts.groupby("scenario"):
        a = g[g.dt == 0.125].iloc[0]
        b = g[g.dt == 0.0625].iloc[0]
        c = g[g.dt == 0.25].iloc[0]
        for k in outs:
            ref = abs(b[k]) if abs(b[k]) > 1e-9 else 1.0
            chg.append(dict(scenario=sc, output=k, change_0125_vs_00625=abs(a[k] - b[k]) / ref, change_025_vs_0125=abs(c[k] - a[k]) / ref))
    chg = pd.DataFrame(chg)
    chg.to_csv(os.path.join(EXP, "validation_timestep_change.csv"), index=False)
    print(ts.round(4).to_string(index=False))
    print(chg.round(5).to_string(index=False))
    worst = chg.change_0125_vs_00625.max()
    ts_pass = write_log(ex, ts, chg, outs)
    fails = (ex.result == "FAIL").sum()
    print("\nextreme-condition failures: %d; time-step worst change %.3f%% (%s)" % (fails, 100 * worst, ok(ts_pass)))
    return 0 if fails == 0 and ts_pass else 1


if __name__ == "__main__":
    sys.exit(main())
