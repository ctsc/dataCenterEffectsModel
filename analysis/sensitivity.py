"""Validation 5.5: one-at-a-time sensitivity, a Latin hypercube over the top parameters, and NetLogo spot checks.

Sweeps use the Python reference model (decision D14: it matches NetLogo to 5e-12); three settings are re-run in
NetLogo headless and must agree to 1e-6 relative. Every parameter in data/parameters.csv with low != high is swept
(except dt and horizon, covered by 5.3, and d_open0, which is derived from O0) on the base case (Sail, 900 MW). When O0 moves, d_open0 = O0/(1-O0) moves with it
so the no-data-center opposition stays at O0.

Outputs: experiments/sensitivity_results.csv, experiments/sensitivity_lhs.csv, figures/tornado.png and the 5.5 section of
experiments/validation_log.md. Run: python analysis/sensitivity.py [--no-netlogo]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import qmc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reference_model as rm  # noqa: E402
import vlog  # noqa: E402

ROOT = os.path.join(HERE, "..")
EXP = os.path.join(ROOT, "experiments")
FIG = os.path.join(ROOT, "figures")
OUTS = {"cum_nb": "cumulative net benefit ($/household, 20 yr)", "peak_stress": "peak water stress",
        "O_end": "opposition at year 20", "F_end": "cumulative net fiscal impact, year 20 ($M)"}
SKIP = {"dt", "horizon", "d_open0"}  # d_open0 is derived from O0 and moves with it
N_LHS, TOP_K = 400, 8


def overrides_for(name, value):
    o = {name: value}
    if name == "O0":
        o["d_open0"] = value / (1 - value)
    return o


def summarize(df):
    r = df.iloc[-1]
    return dict(cum_nb=float(r.cum_nb), peak_stress=float(df.water_stress.max()), O_end=float(r.O), F_end=float(r.F))


def oat(params, table):
    base = summarize(rm.run(params=params))
    rows = []
    for _, t in table.iterrows():
        n = t["name"]
        if n in SKIP or float(t.low) == float(t.high):
            continue
        res = {lv: summarize(rm.run(params=params, overrides=overrides_for(n, float(t[lv])))) for lv in ("low", "high")}
        row = dict(parameter=n, source=t.source, assumption="ASSUMPTION" in str(t.source), base_value=float(t.value),
                   low=float(t.low), high=float(t.high))
        for k in OUTS:
            row["%s_low" % k], row["%s_high" % k] = res["low"][k], res["high"][k]
            row["%s_swing" % k] = abs(res["high"][k] - res["low"][k])
        row["cum_nb_sign_flip"] = (res["low"]["cum_nb"] > 0) != (res["high"]["cum_nb"] > 0) or (res["low"]["cum_nb"] > 0) != (base["cum_nb"] > 0)
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("cum_nb_swing", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", np.arange(1, len(df) + 1))
    return base, df


def lhs(params, table, top):
    t = table.set_index("name").loc[top]
    u = qmc.LatinHypercube(d=len(top), seed=42).random(N_LHS)
    vals = t.low.astype(float).to_numpy() + u * (t.high.astype(float) - t.low.astype(float)).to_numpy()
    rows = []
    for v in vals:
        o = {}
        for n, x in zip(top, v):
            o.update(overrides_for(n, float(x)))
        row = dict(zip(top, v))
        row.update(summarize(rm.run(params=params, overrides=o)))
        rows.append(row)
    return pd.DataFrame(rows)


def tornado(base, df, path, k=15):
    d = df.head(k).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6.2))
    y = np.arange(len(d))
    lo, hi = d.cum_nb_low - base["cum_nb"], d.cum_nb_high - base["cum_nb"]
    ax.barh(y, lo, color="#0072B2", label="parameter at low value")
    ax.barh(y, hi, color="#E69F00", label="parameter at high value")
    ax.axvline(0, color="#222222", lw=1)
    ax.axvline(-base["cum_nb"], color="#D55E00", lw=1.4, ls="--", label="net benefit = 0 (break-even)")
    ax.set_yticks(y, ["%s%s" % (p, " *" if a else "") for p, a in zip(d.parameter, d.assumption)], fontsize=11)
    ax.set_xlabel("change in 20-year cumulative net benefit from base case ($ per household)", fontsize=11)
    ax.set_title("Sensitivity of cumulative net benefit, Sail base case (base = %.0f $/household)\n* = ASSUMPTION parameter"
                 % base["cum_nb"], fontsize=12)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.1), ncol=3, fontsize=10, frameon=False)
    ax.grid(axis="x", color="#dddddd")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def netlogo_spot(params, table, df):
    import nl
    model = os.path.join(ROOT, "model", "DataCenterSD.nlogox")
    metrics = ["ticks", "cumulative-nb", "opposition", "net-fiscal"]
    rows = []
    for _, r in df.head(3).iterrows():
        o = overrides_for(r.parameter, r.high)
        consts = {k.replace("_", "-").lower(): v for k, v in o.items()}
        n = nl.run_setup(model, nl.experiment_xml("spot", metrics, constants=consts, steps=2000), "spot").iloc[-1]
        ref = rm.run(params=params, overrides=o).iloc[-1]
        diff = max(abs(float(n["cumulative-nb"]) - ref.cum_nb) / max(abs(ref.cum_nb), 1e-9),
                   abs(float(n["opposition"]) - ref.O) / max(abs(ref.O), 1e-9),
                   abs(float(n["net-fiscal"]) - ref.F) / max(abs(ref.F), 1e-9))
        rows.append(dict(setting="%s = %g" % (r.parameter, r.high), netlogo_cum_nb=float(n["cumulative-nb"]),
                         reference_cum_nb=float(ref.cum_nb), worst_rel_diff=diff))
    return pd.DataFrame(rows)


def main():
    params = rm.load_params()
    table = pd.read_csv(os.path.join(ROOT, "data", "parameters.csv"))
    base, df = oat(params, table)
    df.to_csv(os.path.join(EXP, "sensitivity_results.csv"), index=False)
    tornado(base, df, os.path.join(FIG, "tornado.png"))
    top = list(df[df.assumption].parameter.head(TOP_K))  # uncertainty only: policy levers and sourced values excluded
    L = lhs(params, table, top)
    L.to_csv(os.path.join(EXP, "sensitivity_lhs.csv"), index=False)
    spot = None if "--no-netlogo" in sys.argv else netlogo_spot(params, table, df)
    if spot is not None:
        spot.to_csv(os.path.join(EXP, "sensitivity_netlogo_spot.csv"), index=False)

    b = ["One-at-a-time sweeps of all %d parameters with a low/high range (Python reference model, decision D14), Sail base case. "
         "Base case: cumulative net benefit %.0f $/household, peak water stress %.3f, final opposition %.3f, year-20 net fiscal impact %.0f $M. "
         "Ranked by the swing in cumulative net benefit. Full table: `experiments/sensitivity_results.csv`; chart: `figures/tornado.png`."
         % (len(df), base["cum_nb"], base["peak_stress"], base["O_end"], base["F_end"]), "",
         "| Rank | Parameter | Type | Low / high | cum. NB at low | cum. NB at high | swing | sign flips? | final O low / high |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in df.head(15).itertuples():
        b.append("| %d | %s | %s | %g / %g | %.0f | %.0f | %.0f | %s | %.3f / %.3f |" % (
            r.rank, r.parameter, "ASSUMPTION" if r.assumption else "sourced", r.low, r.high, r.cum_nb_low, r.cum_nb_high,
            r.cum_nb_swing, "yes" if r.cum_nb_sign_flip else "no", r.O_end_low, r.O_end_high))
    flips = df[df.cum_nb_sign_flip].parameter.tolist()
    pos = (L.cum_nb > 0).mean()
    b += ["", "Parameters whose low or high value alone flips the sign of cumulative net benefit: %s." % (", ".join(flips) or "none"),
          "", "Latin hypercube (%d samples, seed 42) over the top %d ASSUMPTION parameters jointly (%s; sourced values and policy levers held at base): cumulative net benefit is positive in %.0f%% of samples "
          "(median %.0f, 5th-95th percentile %.0f to %.0f $/household). Peak water stress stays below %.3f in every sample."
          % (N_LHS, TOP_K, ", ".join(top), 100 * pos, L.cum_nb.median(), L.cum_nb.quantile(0.05), L.cum_nb.quantile(0.95), L.peak_stress.max()),
          "", "Honest reading: the sign of net benefit for Sail is not robust. It is driven mostly by judgement parameters (ASSUMPTION) "
          "that no public data pins down, so the report presents net benefit as conditional on these values, not as a forecast."]
    if spot is not None:
        b += ["", "NetLogo spot checks (top 3 parameters at their high value, NetLogo 7.0.4 headless vs reference):", "",
              "| Setting | NetLogo cum. NB | Reference cum. NB | worst rel. diff (cum NB, O, F) |", "|---|---|---|---|"]
        b += ["| %s | %.3f | %.3f | %.1e |" % tuple(r) for r in spot.itertuples(index=False)]
        b.append("\nSpot checks %s (criterion 1e-6)." % ("PASS" if spot.worst_rel_diff.max() < 1e-6 else "FAIL"))
    vlog.write_section("5.5", "Sensitivity analysis", "\n".join(b))
    print(df[["rank", "parameter", "assumption", "cum_nb_low", "cum_nb_high", "cum_nb_swing", "cum_nb_sign_flip"]].head(20).to_string(index=False))
    print("base", base)
    print("LHS positive share %.3f" % pos)
    if spot is not None:
        print(spot.to_string(index=False))


if __name__ == "__main__":
    main()
