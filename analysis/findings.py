"""Plan Step 6.11: summarize E0-E10 and find the net benefit thresholds; writes experiments/findings.md,
experiments/summary_runs.csv and experiments/thresholds.csv.

Summaries come from the NetLogo CSVs. Exact thresholds (roots of 20-year cumulative net benefit) are found with the
Python reference model (decision D14) by a grid scan plus Brent's method, and three thresholds are re-run in NetLogo
to confirm that cumulative net benefit is about zero there. Run: python analysis/findings.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nl  # noqa: E402
import reference_model as rm  # noqa: E402

ROOT = os.path.join(HERE, "..")
EXP = os.path.join(ROOT, "experiments")
P = rm.load_params()
SZ = rm.scenario_sizes(P)
SAIL, ALL4 = SZ["sail"], SZ["sail+bridgeport+pegasus+peach"]
KEYS = ["size-mw", "t-sign", "cooling", "payer", "abate0", "drought?", "links-on?", "case", "param", "level", "param_value"]


def summarize(name):
    d = pd.read_csv(os.path.join(EXP, "%s_results.csv" % name))
    rows = []
    for run, x in d.groupby("[run number]"):
        f = x.iloc[-1]
        E, cum, t = x["energized-mw"].to_numpy(), x["cumulative-nb"].to_numpy(), x.ticks.to_numpy()
        neg = np.where(cum < -1e-6)[0]
        payback = np.nan if cum[-1] <= 0 else (0.0 if len(neg) == 0 else t[neg[-1] + 1])
        row = dict(experiment=name, run=run)
        row.update({k: f[k] for k in KEYS if k in x.columns})
        row.update(E20=f["energized-mw"], t90=t[E >= 0.9 * E[-1]].min() if E[-1] > 0 else np.nan, F20=f["net-fiscal"],
                   rev20=f["rev-net"], RI_max=x["rate-index"].max(), stress_peak=x["water-stress"].max(),
                   hx20=f["housing-excess"], O_peak=x.opposition.max(), O20=f.opposition, m_min=x["permit-factor"].min(),
                   pop20=f.population, nb20=f["net-benefit"], cum_nb=f["cumulative-nb"], cum_nb_min=cum.min(), payback_year=payback)
        rows.append(row)
    return pd.DataFrame(rows)


def cum_nb(**kw):
    return float(rm.run(**kw).iloc[-1].cum_nb)


def root_scan(f, lo, hi, n=60):
    xs = np.linspace(lo, hi, n + 1)
    ys = [f(x) for x in xs]
    roots = [brentq(f, xs[i], xs[i + 1], xtol=1e-6) for i in range(n) if np.sign(ys[i]) != np.sign(ys[i + 1]) and ys[i] != 0]
    return roots, ys


def size_curves(combos):
    """Cumulative net benefit against size for each policy combination (reference model), for the threshold figure."""
    rows = [dict(policy=n, size=s, cum_nb=cum_nb(size=s, **kw)) for n, kw in combos.items() for s in np.arange(0, 6001, 100)]
    pd.DataFrame(rows).to_csv(os.path.join(EXP, "nb_vs_size_policies.csv"), index=False)


def thresholds():
    rows = []
    # size thresholds under each policy combination (cum_nb(0) = 0 by construction, so scan from 50 MW)
    combos = {"base policy": {}, "evaporative": dict(cooling="evap"), "evaporative + drought": dict(cooling="evap", drought=True),
              "ratepayers pay": dict(payer="ratepayer"), "ratepayers pay + evaporative": dict(payer="ratepayer", cooling="evap"),
              "worst (evap, ratepayer, 100% abatement, drought)": dict(cooling="evap", payer="ratepayer", abate0=1.0, drought=True),
              "worst without drought": dict(cooling="evap", payer="ratepayer", abate0=1.0)}
    size_curves(combos)
    for name, kw in combos.items():
        roots, ys = root_scan(lambda s: cum_nb(size=s, **kw), 50, 6050)
        rows.append(dict(kind="size (MW)", condition=name, value=roots[0] if roots else np.nan,
                         note=("net benefit %s below, %s above" % (("positive", "negative") if ys[0] > 0 else ("negative", "positive")))
                         if roots else "no crossing 50-6050 MW; sign %s throughout" % ("positive" if ys[0] > 0 else "negative")))
    # break-even values of the most influential parameters, at Sail and at all four campuses
    tab = pd.read_csv(os.path.join(ROOT, "data", "parameters.csv")).set_index("name")
    for prm, lo, hi in (("ql_cost", 0, 20000), ("k_prox", 0, 0.5), ("O0", 0.01, 0.9), ("svc_cost_per_MW", 0, 0.2), ("rev_per_MW", 0.0, 0.3),
                        ("a_r", 0, 30)):
        for size in (SAIL, ALL4):
            def f(v, prm=prm, size=size):
                o = {prm: v}
                if prm == "O0":
                    o["d_open0"] = v / (1 - v)
                return cum_nb(size=size, overrides=o)
            roots, ys = root_scan(f, lo, hi, n=40)
            rows.append(dict(kind="parameter %s" % prm, condition="%.0f MW, base policy" % size, value=roots[0] if roots else np.nan,
                             note="base value %g (%s); tested range %g-%g" % (P[prm], tab.loc[prm, "source"], tab.loc[prm, "low"], tab.loc[prm, "high"])
                             if roots else "no crossing in [%g, %g]" % (lo, hi)))
    # policy-lever break-evens at all four campuses
    for prm, lo, hi, kw in (("share_ratepayer_pays", 0, 1, dict(payer="ratepayer")), ("wi_evap", 0.0, 0.02, dict(cooling="evap"))):
        for size in (SAIL, ALL4):
            roots, ys = root_scan(lambda v: cum_nb(size=size, overrides={prm: v}, **kw), lo, hi, n=40)
            rows.append(dict(kind="parameter %s" % prm, condition="%.0f MW, %s" % (size, ", ".join("%s=%s" % i for i in kw.items())),
                             value=roots[0] if roots else np.nan,
                             note="base value %g" % P[prm] if roots else "no crossing in [%g, %g]" % (lo, hi)))
    return pd.DataFrame(rows)


def netlogo_check(th):
    model = os.path.join(ROOT, "model", "DataCenterSD.nlogox")
    picks = []
    r = th[(th.kind == "size (MW)") & (th.condition == "evaporative")]
    if r.value.notna().any():
        picks.append(("evaporative at %.0f MW" % r.value.iloc[0], {"size-mw": r.value.iloc[0], "cooling": '"evap"'}))
    for prm in ("ql_cost", "k_prox"):
        r = th[(th.kind == "parameter %s" % prm) & (th.condition.str.startswith("%.0f" % SAIL))]
        if r.value.notna().any():
            picks.append(("%s = %.4g at Sail" % (prm, r.value.iloc[0]), {prm.replace("_", "-").lower(): r.value.iloc[0]}))
    out = []
    for label, c in picks:
        d = nl.run_setup(model, nl.experiment_xml("chk", ["ticks", "cumulative-nb"], constants=c, steps=2000), "chk").iloc[-1]
        out.append((label, float(d["cumulative-nb"])))
    return out


def fmt(x, p=0):
    return ("%%.%df" % p) % x if pd.notna(x) else "n/a"


def main():
    S = pd.concat([summarize(n) for n in ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10"]], ignore_index=True)
    S.to_csv(os.path.join(EXP, "summary_runs.csv"), index=False)
    th = thresholds()
    th.to_csv(os.path.join(EXP, "thresholds.csv"), index=False)
    chk = netlogo_check(th)
    g = lambda e: S[S.experiment == e]  # noqa: E731
    e1 = g("E1").iloc[0]
    L = ["# experiments/findings.md", "", "Answers to the five M&S goals, generated by `analysis/findings.py` from the NetLogo BehaviorSpace results "
         "(`experiments/E*_results.csv`, per-run summary in `summary_runs.csv`) and the thresholds in `thresholds.csv`. "
         "Net benefit is dollars per household relative to the no-data-center baseline (definition in `notes/model_spec.md`); "
         "cumulative values are 20-year undiscounted sums. All results are conditional on the ASSUMPTION parameters in `data/parameters.csv`.", "",
         "## Base case (E1, Project Sail, 900 MW)", "",
         "- 90%% of 900 MW energized by year %.2f; %.0f MW at year 20." % (e1.t90, e1.E20),
         "- Net data center revenue %.1f $M/yr at year 20; cumulative net fiscal impact %.0f $M." % (e1.rev20, e1.F20),
         "- Electricity rate index peaks at %.4f (data centers pay); peak water stress %.3f (baseline %.3f); housing cost %.1f%% above baseline at year 20." % (
             e1.RI_max, e1.stress_peak, g("E0").iloc[0].stress_peak, 100 * e1.hx20),
         "- Opposition peaks at %.2f during construction and settles to %.2f (initial 0.40); permitting factor falls to %.2f." % (e1.O_peak, e1.O20, e1.m_min),
         "- Cumulative net benefit %.0f $/household (low point %.0f during build-out; positive for good from year %.1f); %.0f $/household/yr at year 20." % (
             e1.cum_nb, e1.cum_nb_min, e1.payback_year, e1.nb20), ""]
    # Goal 1
    e2 = g("E2").sort_values("size-mw")
    nz = e2[e2["size-mw"] > 0]
    sl = lambda col: np.polyfit(nz["size-mw"] / 1000, nz[col], 1)[0]  # noqa: E731
    L += ["## Goal 1: effect of build-out size and speed", "", "Size (E2, t-sign = 5):", "",
          "| Size (MW) | 90% energized (yr) | rate index max | peak water stress | housing excess yr 20 | net fiscal yr 20 ($M) | peak opposition | cum. net benefit ($/hh) |",
          "|---|---|---|---|---|---|---|---|"]
    L += ["| %.0f | %s | %.4f | %.3f | %.1f%% | %.0f | %.2f | %.0f |" % (r["size-mw"], fmt(r.t90, 2), r.RI_max, r.stress_peak, 100 * r.hx20, r.F20, r.O_peak, r.cum_nb)
          for _, r in e2.iterrows()]
    L += ["", "- Per 1,000 MW (linear fit, closed-loop, data centers pay): rate index +%.4f, peak water stress +%.4f, housing excess +%.2f points, net fiscal +%.0f $M, cumulative net benefit +%.0f $/household." % (
        sl("RI_max"), sl("stress_peak"), 100 * sl("hx20"), sl("F20"), sl("cum_nb")),
        "- With closed-loop cooling and data centers paying for grid upgrades, rate and water effects are small at every size; finances and housing scale almost linearly.", "",
        "Speed (E3, 900 MW):", "", "| t-sign (yr) | 90% energized (yr) | MW at yr 20 | net fiscal yr 20 ($M) | peak opposition | cum. net benefit ($/hh) |", "|---|---|---|---|---|---|"]
    L += ["| %g | %s | %.0f | %.0f | %.2f | %.0f |" % (r["t-sign"], fmt(r.t90, 2), r.E20, r.F20, r.O_peak, r.cum_nb) for _, r in g("E3").iterrows()]
    e4 = g("E4")
    best = e4.loc[e4.cum_nb.idxmax()]
    L += ["", "- Faster contracting raises peak opposition but brings revenue sooner. Over the E4 grid (7 sizes x 7 speeds) cumulative net benefit is positive "
          "in all %d cells (min %.0f, max %.0f $/household); for each size it peaks at t-sign 3-7.5 years; the overall maximum is %.0f MW at t-sign %g. "
          "Slow build-outs (t-sign 20) leave %.0f-%.0f%% of capacity unbuilt at year 20." % (
              len(e4), e4.cum_nb.min(), e4.cum_nb.max(), best["size-mw"], best["t-sign"],
              100 * (1 - (e4[e4["t-sign"] == 20].E20 / e4[e4["t-sign"] == 20]["size-mw"])).min(),
              100 * (1 - (e4[e4["t-sign"] == 20].E20 / e4[e4["t-sign"] == 20]["size-mw"])).max()), ""]
    # Goal 2
    L += ["## Goal 2: when is development a net benefit or a net cost?", "",
          "Thresholds where 20-year cumulative net benefit crosses zero (Brent root on the reference model; NetLogo confirms below):", "",
          "| Threshold | Condition | Break-even value | Note |", "|---|---|---|---|"]
    L += ["| %s | %s | %s | %s |" % (r.kind, r.condition, ("%.4g" % r.value) if pd.notna(r.value) else "none", r.note) for _, r in th.iterrows()]
    L += ["", "NetLogo check at the thresholds (cumulative net benefit should be about 0 $/household): " +
          "; ".join("%s -> %.2f" % c for c in chk) + ".", ""]
    sz = th[th.kind == "size (MW)"].set_index("condition")
    L += ["Reading:",
          "- Under base assumptions there is no size threshold: every term scales roughly with MW, so net benefit is positive at every size with closed-loop cooling and data-center-paid grid upgrades. Size changes the magnitude, not the sign.",
          "- Evaporative cooling creates a real size threshold (%s MW; %s MW with a drought): above it, water stress exceeds 1 and shortage costs and opposition outweigh tax revenue." % (
              fmt(sz.loc["evaporative"].value), fmt(sz.loc["evaporative + drought"].value)),
          "- Socializing grid costs on ratepayers gives a threshold of %s MW; with evaporative cooling as well, %s MW; the worst policy combination is a net cost above %s MW (%s MW without drought)." % (
              fmt(sz.loc["ratepayers pay"].value), fmt(sz.loc["ratepayers pay + evaporative"].value),
              fmt(sz.loc["worst (evap, ratepayer, 100% abatement, drought)"].value), fmt(sz.loc["worst without drought"].value)),
          "- The judgement parameters decide the sign at any size: see the ql_cost, k_prox and O0 break-evens above. They sit inside their plausible ranges, so the honest answer is that Sail is a modest net benefit only if its quality-of-life and housing costs are at or below the assumed values.", ""]
    # Goal 3
    e5, e6, e7, e8 = g("E5"), g("E6"), g("E7"), g("E8")
    L += ["## Goal 3: policy comparisons", "", "| Experiment | Setting | Size (MW) | peak water stress | rate index max | net fiscal yr 20 ($M) | peak opposition | cum. net benefit ($/hh) |",
          "|---|---|---|---|---|---|---|---|"]
    for _, r in e5.iterrows():
        L.append("| E5 cooling | %s, drought %s | %.0f | %.3f | %.4f | %.0f | %.2f | %.0f |" % (r.cooling, "on" if r["drought?"] else "off", r["size-mw"], r.stress_peak, r.RI_max, r.F20, r.O_peak, r.cum_nb))
    for _, r in e6.iterrows():
        L.append("| E6 payer | %s | %.0f | %.3f | %.4f | %.0f | %.2f | %.0f |" % (r.payer, r["size-mw"], r.stress_peak, r.RI_max, r.F20, r.O_peak, r.cum_nb))
    for _, r in e7.iterrows():
        L.append("| E7 abatement | abate0 = %g | %.0f | %.3f | %.4f | %.0f | %.2f | %.0f |" % (r.abate0, r["size-mw"], r.stress_peak, r.RI_max, r.F20, r.O_peak, r.cum_nb))
    for _, r in e8.iterrows():
        L.append("| E8 combination | %s | %.0f | %.3f | %.4f | %.0f | %.2f | %.0f |" % (r.case, r["size-mw"], r.stress_peak, r.RI_max, r.F20, r.O_peak, r.cum_nb))
    a = lambda s, v: e7[(e7["size-mw"] == s) & (e7.abate0 == v)].iloc[0]  # noqa: E731
    w = lambda c, s: e8[(e8.case == c) & (e8["size-mw"] == s)].iloc[0]  # noqa: E731
    L += ["", "- Cooling matters most at large size: evaporative cooling at %.0f MW lifts peak water stress from %.2f to %.2f (%.2f with drought) and turns net benefit from %.0f to %.0f $/household. At Sail's size it lowers net benefit by %.0f $/household but stays positive." % (
        ALL4, e5[(e5["size-mw"] == ALL4) & (e5.cooling == "closed") & (~e5["drought?"])].stress_peak.iloc[0],
        e5[(e5["size-mw"] == ALL4) & (e5.cooling == "evap") & (~e5["drought?"])].stress_peak.iloc[0],
        e5[(e5["size-mw"] == ALL4) & (e5.cooling == "evap") & (e5["drought?"])].stress_peak.iloc[0],
        e5[(e5["size-mw"] == ALL4) & (e5.cooling == "closed") & (~e5["drought?"])].cum_nb.iloc[0],
        e5[(e5["size-mw"] == ALL4) & (e5.cooling == "evap") & (~e5["drought?"])].cum_nb.iloc[0],
        e5[(e5["size-mw"] == SAIL) & (e5.cooling == "closed") & (~e5["drought?"])].cum_nb.iloc[0] - e5[(e5["size-mw"] == SAIL) & (e5.cooling == "evap") & (~e5["drought?"])].cum_nb.iloc[0]),
        "- Grid payer: socializing upgrades raises the rate index to %.4f at Sail and %.4f at %.0f MW and cuts cumulative net benefit by %.0f and %.0f $/household." % (
            e6[(e6["size-mw"] == SAIL) & (e6.payer == "ratepayer")].RI_max.iloc[0], e6[(e6["size-mw"] == ALL4) & (e6.payer == "ratepayer")].RI_max.iloc[0], ALL4,
            e6[(e6["size-mw"] == SAIL) & (e6.payer == "dc")].cum_nb.iloc[0] - e6[(e6["size-mw"] == SAIL) & (e6.payer == "ratepayer")].cum_nb.iloc[0],
            e6[(e6["size-mw"] == ALL4) & (e6.payer == "dc")].cum_nb.iloc[0] - e6[(e6["size-mw"] == ALL4) & (e6.payer == "ratepayer")].cum_nb.iloc[0]),
        "- Abatement: each 25 points of initial abatement costs about %.0f $/household at Sail (from %.0f with none to %.0f with 100%%) and about %.0f at %.0f MW; abatement never flips the sign on its own." % (
            (a(SAIL, 0).cum_nb - a(SAIL, 1).cum_nb) / 4, a(SAIL, 0).cum_nb, a(SAIL, 1).cum_nb, (a(ALL4, 0).cum_nb - a(ALL4, 1).cum_nb) / 4, ALL4),
        "- Combinations (E8): the best combination gives %.0f (Sail) and %.0f (%.0f MW) $/household; the worst gives %.0f and %.0f. Sail under the worst combination is a net cost; drought alone has little effect with closed-loop cooling." % (
            w("best", SAIL).cum_nb, w("best", ALL4).cum_nb, ALL4, w("worst", SAIL).cum_nb, w("worst", ALL4).cum_nb), ""]
    # Goal 4
    e9 = g("E9")
    on, off = e9[e9["links-on?"] == True].set_index(["size-mw", "t-sign"]), e9[e9["links-on?"] == False].set_index(["size-mw", "t-sign"])  # noqa: E712
    L += ["## Goal 4: how much does cross-sector feedback matter? (E9)", "",
          "| Size (MW) | t-sign | 90% energized on / off (yr) | min permit factor | net fiscal yr 20 on / off ($M) | cum. NB on / off ($/hh) | difference |", "|---|---|---|---|---|---|---|"]
    for k in on.index:
        L.append("| %.0f | %g | %s / %s | %.2f | %.0f / %.0f | %.0f / %.0f | %+.0f |" % (k[0], k[1], fmt(on.loc[k].t90, 2), fmt(off.loc[k].t90, 2), on.loc[k].m_min,
                                                                         on.loc[k].F20, off.loc[k].F20, on.loc[k].cum_nb, off.loc[k].cum_nb, on.loc[k].cum_nb - off.loc[k].cum_nb))
    dt90 = (on.t90 - off.t90)
    dF = (off.F20 - on.F20) / off.F20
    L += ["", "- With feedback on, opposition delays 90%% energization by %.2f to %.2f years and lowers year-20 net fiscal impact by %.1f%% to %.1f%%. The effect grows with size and with slower contracting (longer construction keeps opposition high)." % (
        dt90.min(), dt90.max(), 100 * dF.min(), 100 * dF.max()),
        "- Opposition slows but never stalls build-out in these runs: the lowest permitting factor is %.2f (%.0f MW, t-sign %g), and every run reaches at least %.0f%% of its target by year 20. A stall (permit factor 0) needs opposition above 1/s_perm = %.2f, which only the forced-opposition extreme test reaches; the closest policy case is the worst combination at %.0f MW, where the permit factor falls to %.2f." % (
            on.m_min.min(), on.m_min.idxmin()[0], on.m_min.idxmin()[1], 100 * (on.E20 / np.array([i[0] for i in on.index])).min(), 1 / P["s_perm"], ALL4, w("worst", ALL4).m_min),
        "- The relief loop (R1) pulls opposition below its starting value at large sizes (year-20 opposition %.2f at %.0f MW), which is why bigger campuses can face less opposition after construction ends." % (
            on.loc[(ALL4, 5)].O20, ALL4), ""]
    # Goal 5
    L += ["## Goal 5: validation", "", "See `experiments/validation_log.md`: units audit clean; 10/10 extreme-condition tests pass in NetLogo; year-20 outputs change by at most 0.40% from dt 0.125 to 0.0625; "
          "model revenue share (4.8% of the county budget at year 10, 7.8% at year 20) sits inside Douglas County's observed 3-8%; closed-loop and evaporative water shares bracket Newton County's 10%; "
          "sensitivity ranks k_prox, ql_cost, rev_per_MW and O0 as the most influential parameters; net benefit is positive in about half of a Latin hypercube over the top ASSUMPTION parameters.", ""]
    # E10
    e10 = g("E10")
    L += ["## E10: sign of net benefit by size for the top ASSUMPTION parameters", "", "| Parameter | Level (value) | sizes with positive cum. NB | cum. NB at Sail | cum. NB at %.0f MW |" % ALL4, "|---|---|---|---|---|"]
    for (prm, lev), x in e10.groupby(["param", "level"]):
        x = x[x["size-mw"] > 0]
        pos = x[x.cum_nb > 0]["size-mw"]
        L.append("| %s | %s (%g) | %s | %.0f | %.0f |" % (prm, lev, x.param_value.iloc[0], "all" if len(pos) == len(x) else ("none" if len(pos) == 0 else "%.0f-%.0f MW" % (pos.min(), pos.max())),
                                                       x[x["size-mw"] == SAIL].cum_nb.iloc[0], x[x["size-mw"] == ALL4].cum_nb.iloc[0]))
    L += ["", "- At low or base values of each parameter net benefit is positive at every size; at the high value of k_prox, ql_cost or O0 it is negative at every size. svc_cost_per_MW at its high value makes small campuses a slight net cost and large ones a slight benefit. So the sign is set by the per-MW valuation of local costs, not by campus size."]
    open(os.path.join(EXP, "findings.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
