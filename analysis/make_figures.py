"""Plan Step 7.1: regenerate every results figure in figures/ from the CSVs in experiments/.

Colorblind-safe Okabe-Ito palette, labeled axes with units, sized for slides and the report.
Run: python analysis/make_figures.py   (diagrams: make_diagrams.py; NetLogo snapshots: snapshots.py)
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sensitivity  # noqa: E402

ROOT = os.path.join(HERE, "..")
EXP = os.path.join(ROOT, "experiments")
FIG = os.path.join(ROOT, "figures")
OI = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00", "purple": "#CC79A7", "sky": "#56B4E9",
      "yellow": "#F0E442", "black": "#000000", "grey": "#777777"}
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "legend.fontsize": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e5e5e5", "savefig.dpi": 170})


def load(name):
    return pd.read_csv(os.path.join(EXP, "%s_results.csv" % name))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name))
    plt.close(fig)
    print("wrote figures/%s" % name)


def base_timeseries():
    e1, e0 = load("E1"), load("E0")
    t = e1.ticks
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    a = ax[0, 0]
    a.plot(t, e1["contracted-mw"], color=OI["grey"], label="contracted load C")
    a.plot(t, e1["grid-mw"], color=OI["orange"], label="grid capacity G")
    a.plot(t, e1["energized-mw"], color=OI["blue"], lw=2.2, label="energized E")
    a.set(title="(a) Grid and load", xlabel="year", ylabel="MW")
    a.legend(loc="center right", frameon=False)
    a.text(19.5, 120, "electricity rate index tracks G and peaks at %.4f\n(about +$%.0f per household per year)" % (
        e1["rate-index"].max(), (e1["rate-index"].max() - 1) * 15.5 / 100 * 11000), ha="right", fontsize=9, color=OI["red"])
    a = ax[0, 1]
    a.plot(t, e0["water-stress"], color=OI["grey"], label="no data centers (E0)")
    a.plot(t, e1["water-stress"], color=OI["blue"], lw=2.2, label="Sail, closed-loop (E1)")
    e5 = load("E5")
    ev = e5[(e5["size-mw"] == 900) & (e5.cooling == "evap") & (~e5["drought?"])]
    a.plot(ev.ticks, ev["water-stress"], color=OI["orange"], label="Sail, evaporative (E5)")
    a.axhline(1, color=OI["red"], lw=1, ls=":")
    a.set(title="(b) Water stress (demand / capacity)", xlabel="year", ylabel="water stress", ylim=(0.4, 1.05))
    a.legend(frameon=False, loc="lower right")
    a = ax[1, 0]
    a.plot(t, e1["net-fiscal"], color=OI["green"], lw=2.2, label="cumulative net fiscal impact")
    a.set(title="(c) County and school finances", xlabel="year", ylabel="$ million (cumulative)")
    b = a.twinx()
    b.plot(t, e1["rev-net"], color=OI["blue"], ls="--", label="net DC tax revenue (right)")
    b.set_ylabel("$ million per year")
    b.spines["right"].set_visible(True)
    b.grid(False)
    h1, l1 = a.get_legend_handles_labels()
    h2, l2 = b.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)
    a = ax[1, 1]
    a.plot(t, e1.opposition, color=OI["red"], lw=2.2, label="opposition O (0-1)")
    a.plot(t, e1["permit-factor"], color=OI["sky"], label="permitting speed factor m")
    a.plot(t, 10 * e1["housing-excess"], color=OI["purple"], ls="--", label="housing cost excess x 10")
    a.set(title="(d) Opposition, permitting and housing", xlabel="year", ylabel="index", ylim=(0, 1.3))
    a.legend(frameon=False, loc="upper left", ncol=2, fontsize=9)
    fig.suptitle("Base case: Project Sail, 900 MW, closed-loop cooling, data centers pay for grid upgrades (NetLogo E1)", fontsize=13)
    save(fig, "base_timeseries.png")


def nb_heatmap():
    e4 = load("E4")
    f = e4.groupby("[run number]").last()
    pv = f.pivot(index="size-mw", columns="t-sign", values="cumulative-nb")
    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(pv.values / 1000, origin="lower", cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(pv.columns)), ["%g" % c for c in pv.columns])
    ax.set_yticks(range(len(pv.index)), ["%.0f" % i for i in pv.index])
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]):
            v = pv.values[i, j] / 1000
            ax.text(j, i, "%.1f" % v, ha="center", va="center", color="white" if v < 0.6 * np.nanmax(pv.values) / 1000 else "black", fontsize=10)
    ax.set(xlabel="contracting period t-sign (years; larger = slower build-out)", ylabel="campus size (MW)",
           title="20-year cumulative net benefit, $ thousand per household (E4)\nPositive in every cell: no break-even line inside this grid")
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="$ thousand per household")
    save(fig, "nb_heatmap.png")


def threshold_curves():
    c = pd.read_csv(os.path.join(EXP, "nb_vs_size_policies.csv"))
    th = pd.read_csv(os.path.join(EXP, "thresholds.csv"))
    th = th[th.kind == "size (MW)"].set_index("condition")
    colors = [OI["blue"], OI["orange"], OI["red"], OI["sky"], OI["purple"], OI["black"], OI["green"]]
    styles = ["-", "-", "--", "-", "-.", "-", ":"]
    fig, ax = plt.subplots(figsize=(10, 6))
    k = 0
    for (name, g), col, ls in zip(c.groupby("policy", sort=False), colors, styles):
        v = th.loc[name].value if name in th.index else np.nan
        ax.plot(g["size"], g.cum_nb / 1000, color=col, ls=ls, lw=2, label=name + ("  (break-even %.0f MW)" % v if pd.notna(v) else ""))
        if pd.notna(v):
            ax.plot([v], [0], "o", color=col, ms=7)
            ax.annotate("%.0f" % v, (v, 0), textcoords="offset points", xytext=(6, 10 + 13 * k), color=col, fontsize=9,
                        arrowprops=dict(arrowstyle="-", color=col, lw=0.6))
            k += 1
    ax.axhline(0, color="#222222", lw=1)
    for s, lab in ((900, "Sail"), (2800, "+Bridgeport+Pegasus"), (3500, "+Peach")):
        ax.axvline(s, color=OI["grey"], lw=0.8, ls=":")
        ax.text(s, ax.get_ylim()[1], lab, rotation=90, va="top", ha="right", fontsize=9, color=OI["grey"])
    ax.set(xlabel="campus size (MW)", ylabel="20-year cumulative net benefit ($ thousand per household)",
           title="Net benefit against size by policy; dots mark break-even sizes (Python reference model, NetLogo-checked)")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    save(fig, "threshold_curves.png")


def policy_comparison():
    s = pd.read_csv(os.path.join(EXP, "summary_runs.csv"))
    rows = []
    for size in (900, 3500):
        q = s[s["size-mw"] == size]
        pick = lambda e, **kw: q[(q.experiment == e) & np.logical_and.reduce([q[k] == v for k, v in kw.items()])].cum_nb.iloc[0]  # noqa: E731
        rows += [(size, "closed-loop (base)", pick("E5", cooling="closed", **{"drought?": False})),
                 (size, "closed-loop + drought", pick("E5", cooling="closed", **{"drought?": True})),
                 (size, "evaporative", pick("E5", cooling="evap", **{"drought?": False})),
                 (size, "evaporative + drought", pick("E5", cooling="evap", **{"drought?": True})),
                 (size, "ratepayers pay grid", pick("E6", payer="ratepayer")),
                 (size, "no abatement", pick("E7", abate0=0.0)),
                 (size, "100% abatement", pick("E7", abate0=1.0)),
                 (size, "best combination", pick("E8", case="best")),
                 (size, "worst combination", pick("E8", case="worst"))]
    d = pd.DataFrame(rows, columns=["size", "policy", "cum_nb"])
    fig, ax = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
    for a, size, col in zip(ax, (900, 3500), (OI["blue"], OI["orange"])):
        x = d[d["size"] == size].iloc[::-1]
        colors = [OI["red"] if v < 0 else col for v in x.cum_nb]
        a.barh(x.policy, x.cum_nb / 1000, color=colors)
        for yv, v in enumerate(x.cum_nb):
            a.text(v / 1000, yv, " %.1f " % (v / 1000), va="center", ha="left" if v >= 0 else "right", fontsize=9)
        a.axvline(0, color="#222222", lw=1)
        a.set(title="%s (%.0f MW)" % ("Sail only" if size == 900 else "all four campuses", size), xlabel="cumulative net benefit ($ thousand per household)")
        a.grid(axis="y", visible=False)
        lo, hi = (x.cum_nb / 1000).min(), (x.cum_nb / 1000).max()
        a.set_xlim(min(0, lo) * 1.35 - 1, hi * 1.3 + 1)
    fig.suptitle("Policy experiments E5-E8: one setting changed from the base case at a time (red = net cost)", fontsize=13)
    save(fig, "policy_comparison.png")


def feedback():
    e9 = load("E9")
    s = pd.read_csv(os.path.join(EXP, "summary_runs.csv"))
    s = s[s.experiment == "E9"]
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    a = ax[0]
    for ts, col in ((5, OI["blue"]), (10, OI["orange"])):
        for on, ls in ((True, "-"), (False, "--")):
            x = e9[(e9["size-mw"] == 3500) & (e9["t-sign"] == ts) & (e9["links-on?"] == on)]
            a.plot(x.ticks, x["energized-mw"], color=col, ls=ls, lw=2, label="t-sign %d, feedback %s" % (ts, "on" if on else "off"))
    a.set(title="(a) Energized capacity, 3,500 MW", xlabel="year", ylabel="MW")
    a.legend(frameon=False, loc="lower right")
    a = ax[1]
    for ts, col in ((3, OI["green"]), (5, OI["blue"]), (10, OI["orange"])):
        on = s[(s["t-sign"] == ts) & (s["links-on?"] == True)].set_index("size-mw")  # noqa: E712
        off = s[(s["t-sign"] == ts) & (s["links-on?"] == False)].set_index("size-mw")  # noqa: E712
        a.plot(on.index, on.t90 - off.t90, "o-", color=col, lw=2, label="t-sign %d" % ts)
    a.set(title="(b) Delay in reaching 90% energized caused by opposition", xlabel="campus size (MW)", ylabel="years (feedback on minus off)")
    a.legend(frameon=False)
    fig.suptitle("Goal 4: opposition feedback slows build-out but never stalls it (E9)", fontsize=13)
    save(fig, "feedback.png")


def tornado():
    s = pd.read_csv(os.path.join(EXP, "summary_runs.csv"))
    base = dict(cum_nb=float(s[s.experiment == "E1"].cum_nb.iloc[0]))
    sensitivity.tornado(base, pd.read_csv(os.path.join(EXP, "sensitivity_results.csv")), os.path.join(FIG, "tornado.png"))
    print("wrote figures/tornado.png")


def timestep():
    ts = pd.read_csv(os.path.join(EXP, "validation_timestep.csv"))
    outs = ["cumulative-nb", "net-fiscal", "opposition", "energized-mw"]
    fig, ax = plt.subplots(figsize=(9, 5))
    cols = [OI["blue"], OI["orange"], OI["green"], OI["purple"]]
    for sc, mk in (("base", "o"), ("big_fast", "s"), ("stress", "^")):
        g = ts[ts.scenario == sc].sort_values("dt")
        ref = g[g.dt == 0.0625].iloc[0]
        for o, c in zip(outs, cols):
            ax.plot(g.dt, 100 * (g[o] - ref[o]).abs() / abs(ref[o]), marker=mk, color=c, lw=1.2,
                    label="%s" % o if sc == "base" else None)
    ax.axhline(2, color=OI["red"], ls="--", lw=1)
    ax.text(0.2, 2.07, "2% criterion (applied between 0.125 and 0.0625)", color=OI["red"], fontsize=9)
    ax.set_xscale("log", base=2)
    ax.set_xticks([0.0625, 0.125, 0.25, 0.5], ["0.0625", "0.125", "0.25", "0.5"])
    ax.set(xlabel="time step dt (years)", ylabel="% difference from dt = 0.0625 at year 20",
           title="Time-step test (NetLogo): markers o base, s 3,500 MW fast, ^ stress case")
    ax.legend(frameon=False, loc="upper left")
    save(fig, "timestep.png")


def e10_sign():
    e10 = load("E10")
    f = e10.groupby("[run number]").last()
    fig, ax = plt.subplots(1, 4, figsize=(15, 4.3), sharey=True)
    for a, prm in zip(ax, ["k_prox", "ql_cost", "O0", "svc_cost_per_MW"]):
        x = f[f.param == prm]
        for lev, col in (("low", OI["blue"]), ("base", OI["black"]), ("high", OI["red"])):
            y = x[x.level == lev].sort_values("size-mw")
            a.plot(y["size-mw"], y["cumulative-nb"] / 1000, color=col, lw=2, label="%s = %g" % (lev, y.param_value.iloc[0]))
        a.axhline(0, color="#222222", lw=1)
        a.set(title=prm, xlabel="campus size (MW)")
        a.legend(frameon=False, fontsize=9)
    ax[0].set_ylabel("cum. net benefit ($ thousand / household)")
    fig.suptitle("E10: the sign of net benefit is set by judgement parameters, not by campus size (NetLogo)", fontsize=13)
    save(fig, "e10_sign.png")


def main():
    base_timeseries()
    nb_heatmap()
    threshold_curves()
    policy_comparison()
    feedback()
    tornado()
    timestep()
    e10_sign()


if __name__ == "__main__":
    main()
