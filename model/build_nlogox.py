"""Generate model/DataCenterSD.nlogox (NetLogo 7 System Dynamics Modeler) from notes/model_spec.md.

Usage: python model/build_nlogox.py [--dt 0.125] [--out model/DataCenterSD.nlogox]

All constants come from data/parameters.csv and become interface sliders (so BehaviorSpace can vary
them). The equations below mirror analysis/reference_model.py one to one.
"""
import argparse
import math
import os
import re
import xml.sax.saxutils as xs

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
TEMPLATE = os.path.join(os.environ.get("NETLOGO_HOME", "C:/dev/nl704"), "models", "Sample Models", "System Dynamics",
                        "Logistic Growth.nlogox")  # for shape definitions only

# ---- parameters that are not sliders (handled by the structure) -------------------------------------------
NOT_SLIDERS = {"dt", "horizon", "E0", "G0", "C0", "F0"}
CHOOSERS = {"cooling": ["closed", "evap"], "payer": ["dc", "ratepayer"]}


def hy(name):
    return name.replace("_", "-")


# ---- stocks: name -> (initial expression, allowNegative, x, y) ----------------------------------------------
STOCKS = [
    ("contracted-mw", "0", False, 130, 60),
    ("grid-mw", "0", False, 430, 60),
    ("energized-mw", "0", False, 730, 60),
    ("water-capacity", "w0", False, 130, 380),
    ("net-fiscal", "0", True, 130, 580),
    ("population", "p0", False, 1270, 300),
    ("opposition", "o0", False, 1270, 540),
    ("cumulative-nb", "0", True, 130, 790),
]

# ---- rates: name -> (formula, source/sink reservoir side, target stock, bivalent) ----------------------------
RATES = [
    ("sign-rate", "mn (size-mw / t-sign * permit-factor) ((mx 0 (size-mw - contracted-mw)) / dt-step)", "contracted-mw", False),
    ("grid-build", "(contracted-mw - grid-mw) / d-grid", "grid-mw", False),
    ("energize", "energize-rate", "energized-mw", False),
    ("water-expansion", "ifelse-value (stress-struct > ws-trigger and water-capacity < water-cap) "
                        "[(mn (mx 0 (water-target - water-capacity)) (water-cap - water-capacity)) / d-water] [0]",
     "water-capacity", False),
    ("fiscal-flow", "rev-net - relief-cash - cost-svc - cost-pop", "net-fiscal", True),
    ("pop-growth", "population * g-pop * (mx 0 (1 - s-hm * housing-excess)) + persons-per-mw * energize-rate",
     "population", False),
    ("opp-flow", "(opp-target - opposition) / tau-o", "opposition", True),
    ("nb-flow", "net-benefit", "cumulative-nb", True),
]

# ---- converters: name -> (formula-or-constant, x, y) ---------------------------------------------------------
CONVERTERS = [
    # layout: electricity rows y 60-270, water y 380-470, finance y 580-660, population/opposition x >= 1100,
    # net benefit y 790-880 (columns 170 px apart so labels do not overlap in the SD Modeler)
    ("time-year", "ticks", 1100, 60),
    ("p-base", "p0 * (1 + g-pop * dt-step) ^ (time-year / dt-step)", 1270, 60),
    ("h-ref", "(p-base / p0) ^ hou-elast", 1440, 60),
    ("construction-gw", "(contracted-mw - energized-mw) / 1000", 400, 190),
    ("permit-factor", "ifelse-value links-on? [clip ((1 - s-perm * opposition) / (1 - s-perm * o0)) 0 m-max] [1]", 60, 190),
    ("energize-rate", "(grid-mw - energized-mw) / tau-energize", 910, 190),
    ("wi", "ifelse-value (cooling = \"evap\") [wi-evap] [wi-closed]", 570, 380),
    ("ratepayer-share", "ifelse-value (payer = \"ratepayer\") [share-ratepayer-pays] [share-dc-pays]", 230, 270),
    ("capex-annual", "grid-mw * cost-per-mw * carry-charge", 400, 270),
    ("rate-index", "1 + ratepayer-share * capex-annual / resid-rev-base", 570, 270),
    ("water-demand-base", "water-base0 * population / p0", 740, 380),
    ("water-demand", "water-demand-base + energized-mw * wi", 910, 380),
    ("drought-on", "ifelse-value (drought? and time-year >= drought-start and time-year < drought-start + drought-duration) [1] [0]", 60, 470),
    ("effective-capacity", "water-capacity * (1 - drought-severity * drought-on)", 230, 470),
    ("water-stress", "water-demand / effective-capacity", 400, 470),
    ("stress-struct", "water-demand / water-capacity", 570, 470),
    ("water-target", "water-demand / ws-target", 740, 470),
    ("housing-index", "(population / p0) ^ hou-elast * (1 + k-prox * energized-mw / 1000)", 1100, 190),
    ("housing-excess", "housing-index / h-ref - 1", 1270, 190),
    ("persons-per-mw", "jobs-per-mw * (1 + job-multiplier) * newhh-per-job * hh-size", 1440, 190),
    ("abatement", "abate0 * (mx 0 (1 - time-year / t-abate))", 400, 580),
    ("rev-net", "rev-per-mw * energized-mw * (1 - abatement)", 570, 580),
    ("relief-cash", "relief-share * rev-net", 740, 580),
    ("relief-index", "relief-cash / levy-base", 910, 580),
    ("cost-svc", "svc-cost-per-mw * energized-mw", 400, 660),
    ("pop-dc", "population - p-base", 570, 660),
    ("cost-pop", "percap-cost * pop-dc / 1000000", 740, 660),
    ("opp-driver", "d-open0 + a-c * construction-gw + a-w * (mx 0 (water-stress - ws-opp)) + a-e * (rate-index - 1) / 0.1 "
                   "+ a-h * housing-excess - a-r * relief-index", 1100, 660),
    ("opp-target", "(mx 0 opp-driver) / (1 + (mx 0 opp-driver))", 1270, 660),
    ("households", "population / hh-size", 1440, 330),
    ("fiscal-hh", "1000000 * (rev-net - cost-svc - cost-pop) / households", 400, 790),
    ("elec-hh", "(rate-index - 1) * elec-price / 100 * hh-kwh", 570, 790),
    ("house-hh", "housing-excess * house-cost-base", 740, 790),
    ("stress-base-eff", "water-base0 * p-base / p0 / (w0 * (1 - drought-severity * drought-on))", 910, 880),
    ("water-hh", "shortage-cost * ((mx 0 (water-stress - 1)) - (mx 0 (stress-base-eff - 1)))", 910, 790),
    ("ql-hh", "ql-cost * (energized-mw / 1000) * opposition", 1100, 790),
    ("net-benefit", "fiscal-hh - elec-hh - house-hh - water-hh - ql-hh", 230, 880),
]

HELPERS = """to-report mx [a b]
  report ifelse-value (a > b) [a] [b]
end

to-report mn [a b]
  report ifelse-value (a < b) [a] [b]
end

to-report clip [x lo hi]
  report mx lo (mn x hi)
end

to presets-sail
  set size-mw size-sail
end

to presets-sail-bridgeport-pegasus
  set size-mw size-sail + size-bridgeport + size-pegasus
end

to presets-all-four
  set size-mw size-sail + size-bridgeport + size-pegasus + size-peach
end
"""

INFO = """## WHAT IS IT?

A system dynamics model of how data center development affects Coweta County, Georgia over 20 years (CSC8840 final project, Option 2). The base case is Project Sail (900 MW, nine buildings, closed-loop cooling). Four linked sectors: electricity and grid, water, county finances, and population / housing / community opposition.

## HOW IT WORKS

Stocks: contracted-mw (supporting stock), grid-mw, energized-mw, water-capacity, net-fiscal, population, opposition (plus an accounting stock, cumulative-nb).
Loops: R1 (tax revenue funds property tax relief, lowering opposition and speeding build-out), B1 (grid capacity follows contracted load after a delay and caps energization), B2 (water stress triggers supply expansion after a delay), B3 (construction disruption, water stress, rates and housing raise opposition, which slows permitting).
Time unit is one year; dt is set when the model is generated (default 0.125). Equations are in notes/model_spec.md; every constant is a slider whose default is in data/parameters.csv with its source or ASSUMPTION label.

## HOW TO USE IT

1. Choose scenario controls on the left: size-mw (or press a preset button), t-sign (speed), cooling, payer, abate0 (abatement level), drought?, and links-on? (opposition feedback).
2. Press setup, then go (stops at year 20).
3. Watch the plots and monitors. net-benefit is dollars per household per year relative to the no-data-center baseline, and cumulative-nb is its running total.

## THINGS TO TRY

- Compare links-on? on and off for a 3500 MW campus with t-sign = 3.
- Set cooling = evap with drought? on and compare water-stress.
- Set payer = ratepayer and watch rate-index.
- Set abate0 to 0 and to 1 and watch net-fiscal.

## CREDITS AND REFERENCES

Parameters come from public data listed in data/sources.md (Project Sail fiscal impact analysis by Economic Impact Group, Chattahoochee Riverkeeper fact sheets, Census, EPD permit notices, LBNL 2024 report). Parameters without public data are labeled ASSUMPTION and tested in the sensitivity analysis. Generated by model/build_nlogox.py. Built with AI assistance (see the project report's disclosure).
"""


def slider_xml(name, default, low, high, x, y, step=None):
    lo = min(low, default)
    hi = max(high, default)
    lo = 0 if (lo >= 0 and lo < abs(hi)) else lo
    hi = hi * 2 if hi > 0 else 1
    if step is None:  # a round power of ten so the slider shows a short number (e.g. 0.001, not 0.000110...)
        step = 10.0 ** math.floor(math.log10(max((hi - lo) / 1000.0, 1e-9)))
        step = min(step, 10.0 ** math.floor(math.log10(abs(default)) - 2)) if default else step
    return ('    <slider x="%d" step="%s" y="%d" max="%s" width="200" display="%s" height="45" min="%s" '
            'direction="Horizontal" default="%s" variable="%s"></slider>' % (x, repr(step), y, repr(float(hi)), name, repr(float(lo)),
                                                                            repr(float(default)), name))


def plot_xml(x, y, w, h, title, pens, ytitle=""):
    out = ['    <plot x="%d" autoPlotX="true" yMax="1.0" autoPlotY="true" yAxis="%s" y="%d" xMin="0.0" height="%d" legend="true" '
           'xMax="20.0" yMin="0.0" width="%d" xAxis="year" display="%s">' % (x, ytitle, y, h, w, title), "      <setup></setup>", "      <update></update>"]
    for name, color, expr in pens:
        out.append('      <pen interval="1.0" mode="0" display="%s" color="%d" legend="true">\n        <setup></setup>\n'
                   '        <update>plotxy ticks %s</update>\n      </pen>' % (name, color, expr))
    out.append("    </plot>")
    return "\n".join(out)


def build(dt, out_path):
    params = pd.read_csv(os.path.join(ROOT, "data", "parameters.csv"))
    P = {r["name"]: r for _, r in params.iterrows()}
    slider_params = [n for n in params["name"] if n not in NOT_SLIDERS]

    # names of everything that is a variable
    stock_names = [s[0] for s in STOCKS]
    rate_names = [r[0] for r in RATES]
    conv_names = [c[0] for c in CONVERTERS] + ["dt-step"]

    # ----- widgets -----
    w = []
    w.append('    <view x="1010" wrappingAllowedX="true" y="10" frameRate="30.0" minPycor="0" height="12" showTickCounter="true" '
             'patchSize="4.0" fontSize="10" wrappingAllowedY="true" width="164" tickCounterLabel="year" maxPycor="0" updateMode="1" '
             'maxPxcor="39" minPxcor="0"></view>')
    w.append('    <button x="10" y="10" height="35" disableUntilTicks="false" forever="false" kind="Observer" width="90">setup</button>')
    w.append('    <button x="105" y="10" height="35" disableUntilTicks="true" forever="true" kind="Observer" width="90">go</button>')
    w.append('    <button x="10" y="50" height="30" disableUntilTicks="false" forever="false" kind="Observer" width="190" display="Sail only">presets-sail</button>')
    w.append('    <button x="10" y="84" height="30" disableUntilTicks="false" forever="false" kind="Observer" width="190" display="Sail + Bridgeport + Pegasus">presets-sail-bridgeport-pegasus</button>')
    w.append('    <button x="10" y="118" height="30" disableUntilTicks="false" forever="false" kind="Observer" width="190" display="+ Peach (all four)">presets-all-four</button>')
    # scenario controls
    y = 155
    w.append('    <slider x="10" step="50.0" y="%d" max="4000.0" width="200" display="size-mw" height="45" min="0.0" direction="Horizontal" default="%s" variable="size-mw"></slider>' % (y, repr(float(P["size_sail"]["value"]))))
    y += 50
    w.append(slider_xml("t-sign", float(P["t_sign"]["value"]), 1.0, 20.0, 10, y, step=0.5))
    y += 50
    w.append(slider_xml("abate0", float(P["abate0"]["value"]), 0.0, 1.0, 10, y))
    y += 50
    for var, choices in CHOOSERS.items():
        w.append('    <chooser x="10" y="%d" height="45" variable="%s" current="0" width="200" display="%s">\n%s\n    </chooser>' % (
            y, var, var, "\n".join('      <choice type="string" value="%s"></choice>' % c for c in choices)))
        y += 50
    w.append('    <switch x="10" y="%d" height="35" on="false" variable="drought?" width="95" display="drought?"></switch>' % y)
    w.append('    <switch x="110" y="%d" height="35" on="true" variable="links-on?" width="100" display="links-on?"></switch>' % y)
    y += 45
    # monitors
    mons = [("year", "ticks"), ("energized MW", "energized-mw"), ("grid MW", "grid-mw"), ("water stress", "water-stress"),
            ("rate index", "rate-index"), ("housing index", "housing-index"), ("net fiscal $M", "net-fiscal"),
            ("opposition", "opposition"), ("permit factor", "permit-factor"), ("population", "population"),
            ("net benefit $/hh/yr", "net-benefit"), ("cumulative nb $/hh", "cumulative-nb")]
    for i, (lab, expr) in enumerate(mons):
        w.append('    <monitor x="%d" precision="3" y="%d" height="45" fontSize="11" width="110" display="%s">%s</monitor>' % (
            220 + (i % 3) * 115, 10 + (i // 3) * 50, lab, expr))
    # plots
    px, py, pw, ph = 220, 215, 395, 200
    w.append(plot_xml(px, py, pw, ph, "Load (MW)", [("contracted", -7500403, "contracted-mw"), ("grid", -955883, "grid-mw"), ("energized", -13345367, "energized-mw")], "MW"))
    w.append(plot_xml(px + pw + 5, py, pw, ph, "Water stress", [("stress", -2674135, "water-stress"), ("structural", -13791810, "stress-struct")], "demand / capacity"))
    w.append(plot_xml(px, py + ph + 5, pw, ph, "Rate and housing index", [("rate index", -955883, "rate-index"), ("housing index", -10899396, "housing-index")], "index"))
    w.append(plot_xml(px + pw + 5, py + ph + 5, pw, ph, "Net fiscal impact ($M)", [("net fiscal", -13345367, "net-fiscal")], "$ million"))
    w.append(plot_xml(px, py + 2 * (ph + 5), pw, ph, "Opposition and permitting", [("opposition", -2674135, "opposition"), ("permit factor", -13791810, "permit-factor")], "0-1+"))
    w.append(plot_xml(px + pw + 5, py + 2 * (ph + 5), pw, ph, "Net benefit ($/household/yr)", [("net benefit", -10899396, "net-benefit")], "$/hh/yr"))
    # parameter sliders (all remaining parameters)
    skip = {"t_sign", "abate0", "size_sail"} | set()
    col, row = 0, 0
    sx0, sy0 = 1010, 40
    for n in slider_params:
        if n in skip or n in ("cooling", "payer"):
            continue
        r = P[n]
        w.append(slider_xml(hy(n), float(r["value"]), float(r["low"]), float(r["high"]), sx0 + col * 205, sy0 + row * 47))
        row += 1
        if row >= 28:
            row = 0
            col += 1
    # size_sail slider (also used by presets)
    w.append(slider_xml("size-sail", float(P["size_sail"]["value"]), float(P["size_sail"]["low"]), float(P["size_sail"]["high"]), sx0 + col * 205, sy0 + row * 47))

    # ----- experiments are loaded from experiments/*.xml via --setup-file (see experiments/README) -----
    code = ("; Generated by model/build_nlogox.py from notes/model_spec.md. Do not edit by hand; edit the generator.\n\n"
            "to setup\n  clear-all\n  system-dynamics-setup\n  update-plots\nend\n\n"
            "to go\n  if ticks >= %s [ stop ]\n  system-dynamics-go\n  update-plots\nend\n\n" % int(float(P["horizon"]["value"]))
            + HELPERS)

    # ----- system dynamics block -----
    figs = []  # (kind, name)
    sd = []
    for name, init, neg, x, yy in STOCKS:
        sd.append('    <stock name="%s" allowNegative="%s" x="%d" y="%d">%s</stock>' % (name, str(neg).lower(), x, yy, xs.escape(init)))
        figs.append(("stock", name))
    reservoirs = []
    for i, (name, f, tgt, biv) in enumerate(RATES):
        t = [s for s in STOCKS if s[0] == tgt][0]
        rx, ry = t[3] - 90, t[4] + 70
        reservoirs.append((rx, ry))
        sd.append('    <reservoir x="%d" y="%d"></reservoir>' % (rx, ry))
        figs.append(("reservoir", "res-%d" % i))
    idx = {}
    for i, (k, n) in enumerate(figs):
        idx[n] = i
    nstock_res = len(figs)
    for i, (name, f, tgt, biv) in enumerate(RATES):
        idx[name] = len(figs)
        figs.append(("rate", name))
    for name, f, x, yy in CONVERTERS:
        idx[name] = len(figs)
        figs.append(("converter", name))
    idx["dt-step"] = len(figs)
    figs.append(("converter", "dt-step"))

    for i, (name, f, tgt, biv) in enumerate(RATES):
        start = idx["res-%d" % i]
        end = idx[tgt]
        a, b = (start, end)
        sd.append('    <rate name="%s" bivalent="%s" startFigure="%d" endFigure="%d">%s</rate>' % (name, str(biv).lower(), a, b, xs.escape(f)))
    for name, f, x, yy in CONVERTERS:
        sd.append('    <converter name="%s" x="%d" y="%d">%s</converter>' % (name, x, yy, xs.escape(f)))
    sd.append('    <converter name="dt-step" x="1440" y="130">%s</converter>' % repr(float(dt)))

    # bindings: reference -> consumer
    known = set(stock_names) | set(rate_names) | set(conv_names)
    token = re.compile(r"[a-z][a-z0-9\-\?]*")
    formulas = [(n, f) for n, f, *_ in RATES] + [(n, f) for n, f, *_ in CONVERTERS]
    bindings = []
    for consumer, f in formulas:
        refs = {t for t in token.findall(f) if t in known and t != consumer}
        # rate names are not referenced by formulas; flows depend on stocks and converters only
        for r in sorted(refs):
            if r in rate_names:
                continue
            bindings.append((idx[r], idx[consumer]))
    for a, b in bindings:
        sd.append('    <binding startFigure="%d" endFigure="%d"></binding>' % (a, b))

    # ----- assemble from template for shape definitions -----
    tpl = open(TEMPLATE, encoding="utf-8").read()
    shapes = tpl[tpl.index("  <turtleShapes>"): tpl.index("  <systemDynamics")]
    xml = ['<?xml version="1.0" encoding="utf-8"?>', '<model version="NetLogo 7.0.4" snapToGrid="false">',
           "  <code>" + xs.escape(code) + "</code>", "  <widgets>"] + w + ["  </widgets>",
           "  <info><![CDATA[" + INFO + "]]></info>", shapes.rstrip(), '  <systemDynamics dt="%s">' % repr(float(dt))] + sd + [
        "  </systemDynamics>", "  <previewCommands>need-to-manually-make-preview-for-this-model</previewCommands>", "</model>", ""]
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(xml))
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dt", type=float, default=0.125)
    ap.add_argument("--out", default=os.path.join(HERE, "DataCenterSD.nlogox"))
    a = ap.parse_args()
    print("wrote", build(a.dt, a.out))
