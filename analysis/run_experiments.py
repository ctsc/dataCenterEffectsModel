"""Plan Step 6: run experiments E0-E10 in NetLogo 7.0.4 headless (BehaviorSpace).

Each experiment's setup is saved as experiments/E*.xml and its table as experiments/E*_results.csv (every step,
so one row per run per dt). The model is deterministic, so there is one run per setting.
Run: python analysis/run_experiments.py [E2 E4 ...]   (default: all)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nl  # noqa: E402
import reference_model as rm  # noqa: E402

ROOT = os.path.join(HERE, "..")
MODEL = os.path.join(ROOT, "model", "DataCenterSD.nlogox")
EXP = os.path.join(ROOT, "experiments")
METRICS = ["ticks", "energized-mw", "grid-mw", "contracted-mw", "water-capacity", "net-fiscal", "population", "opposition",
           "cumulative-nb", "water-stress", "rate-index", "housing-index", "housing-excess", "permit-factor", "rev-net",
           "net-benefit"]

P = rm.load_params()
SZ = rm.scenario_sizes(P)
SAIL, SBP, ALL4 = SZ["sail"], SZ["sail+bridgeport+pegasus"], SZ["sail+bridgeport+pegasus+peach"]
STEPS = int(round(P["horizon"] / P["dt"]))
Q = lambda s: '"%s"' % s  # noqa: E731

# name -> (description, constants, swept values)
EXPERIMENTS = {
    "E0": ("baseline, no data centers", {"size-mw": 0}, {}),
    "E1": ("base case, Project Sail only", {"size-mw": SAIL}, {}),
    "E2": ("build-out size", {}, {"size-mw": [0, 450, SAIL, 1800, SBP, ALL4]}),
    "E3": ("build-out speed (contracting period t-sign)", {"size-mw": SAIL}, {"t-sign": [3, 5, 10, 15, 20]}),
    "E4": ("size x speed grid", {}, {"size-mw": [450, SAIL, 1350, 1800, 2250, SBP, ALL4], "t-sign": [3, 5, 7.5, 10, 12.5, 15, 20]}),
    "E5": ("cooling type with and without drought", {}, {"size-mw": [SAIL, ALL4], "cooling": [Q("closed"), Q("evap")], "drought?": ["false", "true"]}),
    "E6": ("grid upgrade payer", {}, {"size-mw": [SAIL, ALL4], "payer": [Q("dc"), Q("ratepayer")]}),
    "E7": ("tax abatement level", {}, {"size-mw": [SAIL, ALL4], "abate0": [0, 0.25, 0.5, 0.75, 1.0]}),
    "E8": ("policy combinations", {}, None),  # filled in below (best and worst case)
    "E9": ("feedback strength: opposition links on vs off", {}, {"size-mw": [SAIL, 1800, SBP, ALL4], "t-sign": [3, 5, 10], "links-on?": ["true", "false"]}),
}
E8_RUNS = {
    "best": {"cooling": Q("closed"), "payer": Q("dc"), "abate0": 0, "drought?": "false"},
    "best_drought": {"cooling": Q("closed"), "payer": Q("dc"), "abate0": 0, "drought?": "true"},
    "worst": {"cooling": Q("evap"), "payer": Q("ratepayer"), "abate0": 1.0, "drought?": "true"},
    "worst_no_drought": {"cooling": Q("evap"), "payer": Q("ratepayer"), "abate0": 1.0, "drought?": "false"},
}
# E10: net benefit sign versus size for the top ASSUMPTION parameters (from sensitivity 5.5) at low, base and high
E10_PARAMS = ["k_prox", "ql_cost", "O0", "svc_cost_per_MW"]
E10_SIZES = [0, 250, 500, 750, SAIL, 1250, 1500, 1750, 2000, 2500, SBP, 3000, ALL4, 4000]


def nlname(p):
    return p.replace("_", "-").lower()


def run_one(name, consts, values, tag=None):
    tag = tag or name
    xml = nl.experiment_xml(tag, METRICS, constants=consts, values=values, every_step=True, steps=STEPS + 10)
    df = nl.run_setup(MODEL, xml, tag, keep_xml=os.path.join(EXP, "%s.xml" % tag))
    nruns = int(np.prod([len(v) for v in (values or {}).values()])) if values else 1
    return df, nruns


def check(df, nruns, name):
    rows = nruns * (STEPS + 1)
    assert len(df) == rows, "%s: %d rows, expected %d" % (name, len(df), rows)
    assert not df[METRICS].isna().any().any(), "%s has NaN" % name


def main(which):
    import pandas as pd
    for name in which:
        if name == "E8":
            parts = []
            for i, (case, c) in enumerate(E8_RUNS.items()):
                df, n = run_one(name, c, {"size-mw": [SAIL, ALL4]}, tag="E8_%s" % case)
                df["case"] = case
                df["[run number]"] += 2 * i
                parts.append(df)
            df, n = pd.concat(parts, ignore_index=True), 2 * len(E8_RUNS)
        elif name == "E10":
            parts = []
            for i, prm in enumerate(E10_PARAMS):
                v = P[prm]
                t = pd.read_csv(os.path.join(ROOT, "data", "parameters.csv")).set_index("name").loc[prm]
                levels = [float(t.low), v, float(t.high)]
                consts = {}
                vals = {"size-mw": E10_SIZES, nlname(prm): levels}
                if prm == "O0":
                    vals = {"size-mw": E10_SIZES}
                    sub = []
                    for j, lv in enumerate(levels):
                        d, _ = run_one(name, {"o0": lv, "d-open0": lv / (1 - lv)}, vals, tag="E10_O0_%d" % j)
                        d["o0"] = lv
                        d["[run number]"] += j * len(E10_SIZES)
                        sub.append(d)
                    d = pd.concat(sub, ignore_index=True)
                else:
                    d, _ = run_one(name, consts, vals, tag="E10_%s" % prm)
                d["param"] = prm
                d["param_value"] = d[nlname(prm)]
                d["level"] = d["param_value"].map({levels[0]: "low", v: "base", levels[2]: "high"})
                d["[run number]"] += 1000 * i
                parts.append(d)
            df = pd.concat(parts, ignore_index=True)
            n = len(E10_PARAMS) * 3 * len(E10_SIZES)
        else:
            desc, consts, values = EXPERIMENTS[name]
            df, n = run_one(name, consts, values)
        check(df, n, name)
        df.to_csv(os.path.join(EXP, "%s_results.csv" % name), index=False)
        print("%s: %d runs, %d rows OK" % (name, n, len(df)), flush=True)


if __name__ == "__main__":
    args = sys.argv[1:] or ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10"]
    main(args)
