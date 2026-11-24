"""Compare the NetLogo model against the Python reference model (plan steps 4.1-4.2).

Runs scenarios headless in NetLogo and with reference_model.py and reports the relative difference of
every stock at year 20 (and of the full time series for the first scenario). Passing criterion: all
stock differences under 1% (the plan's threshold).

Usage: python analysis/compare_models.py [--model model/DataCenterSD.nlogox]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nl  # noqa: E402
import reference_model as rm  # noqa: E402

MODEL = os.path.join(HERE, "..", "model", "DataCenterSD.nlogox")

STOCKS = {"energized-mw": "E", "grid-mw": "G", "contracted-mw": "C", "water-capacity": "W",
          "net-fiscal": "F", "population": "P", "opposition": "O", "cumulative-nb": "cum_nb"}
CONV = {"water-stress": "water_stress", "rate-index": "RI", "housing-index": "H", "permit-factor": "m",
        "net-benefit": "nb", "rev-net": "rev_net"}

p = rm.load_params()
SC = rm.scenario_sizes(p)
SCENARIOS = {
    "base": dict(),
    "links_off": dict(links_on=False),
    "evap_drought": dict(cooling="evap", drought=True),
    "ratepayer": dict(payer="ratepayer"),
    "abate1": dict(abate0=1.0),
    "big_fast": dict(size=SC["sail+bridgeport+pegasus+peach"], t_sign=3.0),
    "big_ratepayer_evap": dict(size=SC["sail+bridgeport+pegasus+peach"], payer="ratepayer", cooling="evap", drought=True),
    "zero": dict(size=0.0),
}


def to_constants(kw):
    c = {}
    if "size" in kw:
        c["size-mw"] = kw["size"]
    if "t_sign" in kw:
        c["t-sign"] = kw["t_sign"]
    if "cooling" in kw:
        c["cooling"] = '"%s"' % kw["cooling"]
    if "payer" in kw:
        c["payer"] = '"%s"' % kw["payer"]
    if "abate0" in kw:
        c["abate0"] = kw["abate0"]
    if "drought" in kw:
        c["drought?"] = "true" if kw["drought"] else "false"
    if "links_on" in kw:
        c["links-on?"] = "true" if kw["links_on"] else "false"
    return c


def run_netlogo(model, name, consts, every_step=False):
    metrics = ["ticks"] + list(STOCKS) + (list(CONV) if every_step else [])
    return nl.run_setup(model, nl.experiment_xml(name, metrics, constants=consts, every_step=every_step), name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL)
    a = ap.parse_args()
    worst = 0.0
    rows = []
    for name, kw in SCENARIOS.items():
        nl = run_netlogo(a.model, name, to_constants(kw)).iloc[-1]
        ref = rm.run(**kw).iloc[-1]
        for k, v in STOCKS.items():
            r, n = float(ref[v]), float(nl[k])
            rel = abs(n - r) / max(abs(r), 1e-9) if abs(r) > 1e-6 else abs(n - r)
            worst = max(worst, rel)
            rows.append((name, k, r, n, rel))
    df = pd.DataFrame(rows, columns=["scenario", "stock", "reference", "netlogo", "rel_diff"])
    pd.set_option("display.width", 160)
    print(df.round(6).to_string(index=False))
    print("\nworst relative difference over all stocks and scenarios: %.3e" % worst)
    # time-series check for the base scenario
    nl = run_netlogo(a.model, "ts", {}, every_step=True)
    ref = rm.run()
    nl = nl.iloc[1:].reset_index(drop=True) if len(nl) == len(ref) + 0 else nl
    n = min(len(nl), len(ref))
    print("time series rows: netlogo=%d reference=%d" % (len(nl), len(ref)))
    for k, v in {**STOCKS, **CONV}.items():
        x, y = nl[k].to_numpy(float)[-n:], ref[v].to_numpy(float)[-n:]
        scale = max(np.abs(y).max(), 1e-9)
        print("  series %-16s max abs diff / scale = %.2e" % (k, np.abs(x - y).max() / scale))
    ok = worst < 0.01
    print("PASS (<1%)" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
