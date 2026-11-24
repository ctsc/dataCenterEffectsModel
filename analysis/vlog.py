"""Write or replace one '## <heading>' section of experiments/validation_log.md, keeping the others."""
import os
import re

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "experiments", "validation_log.md")
HEADER = ("# experiments/validation_log.md\n\nValidation record (plan Step 5). Sections are written by analysis/validate.py (5.2, 5.3), "
          "analysis/compare_counties.py (5.4), analysis/sensitivity.py (5.5) and analysis/gate.py (5.6).\n\n")
ORDER = ["5.2", "5.3", "5.4", "5.5", "5.6"]


def write_section(key, title, body):
    text = open(LOG, encoding="utf-8").read() if os.path.exists(LOG) else HEADER
    parts = re.split(r"(?m)^(?=## )", text)
    head, secs = parts[0], {}
    for s in parts[1:]:
        k = s[3:].split(" ", 1)[0]
        secs[k] = s
    secs[key] = "## %s %s\n\n%s\n\n" % (key, title, body.strip())
    keys = sorted(secs, key=lambda k: ORDER.index(k) if k in ORDER else 99)
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write(HEADER if not head.startswith("# ") else head)
        fh.write("".join(secs[k].rstrip() + "\n\n" for k in keys))
