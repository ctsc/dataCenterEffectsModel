"""Plan Step 7.2: real NetLogo interface snapshots of the two demo configurations, plus the SD Modeler diagram.

Compiles analysis/snapshot/Snap.java against NetLogo 7.0.4 and drives the NetLogo GUI through its Controlling API
(a NetLogo window opens for about 20 seconds per snapshot). Snap declines NetLogo 7's first-run usage-statistics
dialog automatically. Writes figures/snapshot_1.png (Sail base case), figures/snapshot_2.png (3,500 MW,
evaporative cooling, drought) and figures/sd_modeler.png. Run: python analysis/snapshots.py
"""
import os
import shutil
import subprocess
import tempfile

import nl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = os.path.join(HERE, "snapshot")
MODEL = os.path.abspath(os.path.join(ROOT, "model", "DataCenterSD.nlogox")).replace("\\", "/")
FIG = os.path.join(ROOT, "figures")
CONFIGS = {"snapshot_1": [], "snapshot_2": ["set size-mw 3500", 'set cooling "evap"', "set drought? true"]}


def main():
    h = nl.NETLOGO_HOME
    cp = h + "/app/*"
    subprocess.run(["javac", "-cp", cp, "Snap.java"], cwd=SRC, check=True)
    base = nl.java_cmd()
    jvm = base[:base.index("-classpath")]
    with tempfile.TemporaryDirectory() as d:
        for name, cmds in CONFIGS.items():
            r = subprocess.run(jvm + ["-cp", cp + os.pathsep + ".", "Snap", MODEL, d, name] + cmds, cwd=SRC,
                               capture_output=True, text=True, timeout=300)
            if "SNAP_DONE" not in r.stdout:
                raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
            shutil.copy(os.path.join(d, name + ".png"), os.path.join(FIG, name + ".png"))
        shutil.copy(os.path.join(d, "snapshot_1_sd_modeler.png"), os.path.join(FIG, "sd_modeler.png"))
    print("wrote figures/snapshot_1.png, snapshot_2.png, sd_modeler.png")


if __name__ == "__main__":
    main()
