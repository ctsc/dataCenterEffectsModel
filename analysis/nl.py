"""Run NetLogo 7 BehaviorSpace experiments headless from Python (no .bat, no GUI).

NETLOGO_HOME defaults to C:/dev/nl704 (a copy of the NetLogo 7.0.4 install without spaces in its path; the
shipped netlogo-headless.bat breaks on paths with spaces, see decisions.md D3).
"""
import io
import os
import subprocess
import tempfile

import pandas as pd

NETLOGO_HOME = os.environ.get("NETLOGO_HOME", "C:/dev/nl704")
JAVA = os.environ.get("JAVA_EXE", "java")


def java_cmd():
    h = NETLOGO_HOME
    return [JAVA, "-XX:MaxRAMPercentage=50", "-Dfile.encoding=UTF-8", "-Dnetlogo.docs.dir=" + h,
            "-Dnetlogo.models.dir=" + h + "/models", "-Dnetlogo.extensions.dir=" + h + "/extensions",
            "--add-exports=java.base/java.lang=ALL-UNNAMED", "--add-exports=java.desktop/sun.awt=ALL-UNNAMED",
            "--add-exports=java.desktop/sun.java2d=ALL-UNNAMED", "-classpath", h + "/app/netlogo-7.0.4.jar",
            "org.nlogo.headless.Main"]


def experiment_xml(name, metrics, constants=None, every_step=False, steps=200, setup="setup", go="go", values=None):
    """Build one <experiment>. constants: {var: value} fixed; values: {var: [v1, v2, ...]} swept (cross product)."""
    def q(v):
        return str(v).replace('"', "&quot;")
    cs = "".join('<enumeratedValueSet variable="%s"><value value="%s"/></enumeratedValueSet>' % (k, q(v))
                 for k, v in (constants or {}).items())
    cs += "".join('<enumeratedValueSet variable="%s">%s</enumeratedValueSet>' % (k, "".join('<value value="%s"/>' % q(x) for x in vs))
                  for k, vs in (values or {}).items())
    return ('<experiment name="%s" repetitions="1" sequentialRunOrder="true" runMetricsEveryStep="%s" timeLimit="%d">'
            "<setup>%s</setup><go>%s</go><metrics>%s</metrics><constants>%s</constants></experiment>" % (
                name, str(every_step).lower(), steps, setup, go, "".join("<metric>%s</metric>" % m for m in metrics), cs))


def run_setup(model, setup_xml, experiment, threads=1, keep_xml=None):
    """Run one experiment from a setup-file string; return the BehaviorSpace table as a DataFrame."""
    with tempfile.TemporaryDirectory() as d:
        sf = os.path.join(d, "setup.xml")
        with open(sf, "w", encoding="utf-8") as fh:
            fh.write('<?xml version="1.0" encoding="utf-8"?><experiments>%s</experiments>' % setup_xml)
        if keep_xml:
            with open(keep_xml, "w", encoding="utf-8") as fh:
                fh.write('<?xml version="1.0" encoding="utf-8"?>\n<experiments>\n%s\n</experiments>\n' % setup_xml)
        out = os.path.join(d, "out.csv")
        cmd = java_cmd() + ["--model", os.path.abspath(model).replace("\\", "/"), "--setup-file", sf.replace("\\", "/"),
                            "--experiment", experiment, "--table", out.replace("\\", "/"), "--threads", str(threads)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if not os.path.exists(out):
            raise RuntimeError("NetLogo failed:\n" + r.stdout[-1500:] + r.stderr[-1500:])
        lines = open(out, encoding="utf-8").read().splitlines()
        i = [k for k, l in enumerate(lines) if l.startswith('"[run number]"')][0]
        return pd.read_csv(io.StringIO("\n".join(lines[i:])))
