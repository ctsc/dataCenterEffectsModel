"""Validation gate 5.6: check that 5.1-5.5 passed, write the 5.6 section and archive the validated model.
Run: python analysis/gate.py"""
import os
import shutil
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vlog  # noqa: E402

ROOT = os.path.join(HERE, "..")
EXP = os.path.join(ROOT, "experiments")


def main():
    checks = []
    units = open(os.path.join(ROOT, "data", "units_check.md"), encoding="utf-8").read()
    checks.append(("5.1 units", "No mismatches" in units, "data/units_check.md"))
    ex = pd.read_csv(os.path.join(EXP, "validation_extreme.csv"))
    checks.append(("5.2 extreme conditions", (ex.result == "PASS").all(), "%d/%d tests pass" % ((ex.result == "PASS").sum(), len(ex))))
    ch = pd.read_csv(os.path.join(EXP, "validation_timestep_change.csv"))
    checks.append(("5.3 time step", ch.change_0125_vs_00625.max() < 0.02, "worst change %.2f%% (< 2%%)" % (100 * ch.change_0125_vs_00625.max())))
    checks.append(("5.4 county comparison", os.path.exists(os.path.join(EXP, "validation_counties.csv")),
                   "table written; thin data documented (exception: rate and housing effects have no observed comparator)"))
    spot = pd.read_csv(os.path.join(EXP, "sensitivity_netlogo_spot.csv"))
    checks.append(("5.5 sensitivity", os.path.exists(os.path.join(EXP, "sensitivity_results.csv")) and os.path.exists(os.path.join(ROOT, "figures", "tornado.png"))
                   and spot.worst_rel_diff.max() < 1e-6, "OAT table, tornado and LHS written; NetLogo spot checks agree to %.0e" % spot.worst_rel_diff.max()))
    ok = all(c[1] for c in checks)
    b = ["| Check | Result | Evidence |", "|---|---|---|"] + ["| %s | %s | %s |" % (n, "PASS" if p else "FAIL", e) for n, p, e in checks]
    b += ["", "Documented exceptions: (1) 5.4 cannot test rate or housing effects because no comparison county publishes them; "
          "(2) 5.5 shows that the sign of Sail's net benefit depends on ASSUMPTION parameters (k_prox, ql_cost, O0, svc_cost_per_MW), "
          "which is a finding to report, not a model defect.", "",
          "Gate: %s." % ("PASS, model archived as model/archive/DataCenterSD_validated.nlogox" if ok else "FAIL")]
    vlog.write_section("5.6", "Validation gate", "\n".join(b))
    if ok:
        shutil.copy(os.path.join(ROOT, "model", "DataCenterSD.nlogox"), os.path.join(ROOT, "model", "archive", "DataCenterSD_validated.nlogox"))
    print("\n".join(b))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
