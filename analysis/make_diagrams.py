"""Draw the causal loop diagram and the stock-and-flow diagram (plan step 2.2) with Graphviz.
Outputs figures/causal_loop.png and figures/stock_flow.png.
Needs the Graphviz `dot` executable: set GRAPHVIZ_DOT or put dot on PATH
(portable copy used here: C:/dev/graphviz/Graphviz-12.2.1-win64/bin/dot.exe)."""
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
DOT = os.environ.get("GRAPHVIZ_DOT") or shutil.which("dot") or "C:/dev/graphviz/Graphviz-12.2.1-win64/bin/dot.exe"

INK, BLUE, ORANGE, GREEN, GREY = "#1f2933", "#1b6ca8", "#d1601f", "#2e7d4f", "#6b7785"
FONT = 'fontname="Helvetica" fontsize=11'


def render(src, out):
    p = subprocess.run([DOT, "-Tpng", "-Gdpi=170", "-o", out], input=src.encode("utf-8"), capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode())


def causal_loop():
    src = f'''digraph G {{
  rankdir=LR; splines=true; nodesep=0.45; ranksep=0.7; bgcolor=white; pad=0.3;
  label="Causal loop diagram: data center development in Coweta County\\nR1 reinforcing (green): tax revenue funds relief, lowering opposition and speeding build-out.  B1 (blue): grid follows contracted load after a delay.  B2 (blue): water stress triggers supply expansion.  B3 (orange): construction, water stress, rates and housing raise opposition, which slows permitting.";
  labelloc=t; labeljust=l; fontname="Helvetica-Bold" fontsize=12; fontcolor="{INK}";
  node [shape=box style="rounded,filled" fillcolor=white color="{INK}" {FONT} margin="0.15,0.08"];
  edge [{FONT} penwidth=1.8 arrowsize=0.9];
  perm [label="Permitting speed m\\n(signing rate)"];
  C [label="Contracted load C"]; G [label="Grid capacity G"]; E [label="Energized capacity E"];
  rev [label="Data center tax revenue\\n(net of abatement)"]; relief [label="Property tax relief"];
  O [label="Community opposition O" fillcolor="#fdf0e6"];
  wd [label="Water demand"]; ws [label="Water stress"]; W [label="Water supply capacity W"];
  ri [label="Electricity rate index"]; hx [label="Housing cost excess"]; con [label="Construction\\nC - E"];
  perm -> C [label="+" color="{BLUE}" fontcolor="{BLUE}"];
  C -> G [label="+  (delay)" color="{BLUE}" fontcolor="{BLUE}"];
  G -> E [label="+  (E <= G)" color="{BLUE}" fontcolor="{BLUE}"];
  E -> rev [label="+" color="{GREEN}" fontcolor="{GREEN}"];
  rev -> relief [label="+" color="{GREEN}" fontcolor="{GREEN}"];
  relief -> O [label="\−" color="{GREEN}" fontcolor="{GREEN}"];
  O -> perm [label="\−" color="{ORANGE}" fontcolor="{ORANGE}"];
  C -> con [label="+" color="{ORANGE}" fontcolor="{ORANGE}"];
  E -> con [label="\−" color="{ORANGE}" fontcolor="{ORANGE}"];
  con -> O [label="+" color="{ORANGE}" fontcolor="{ORANGE}"];
  G -> ri [label="+" color="{ORANGE}" fontcolor="{ORANGE}"]; ri -> O [label="+" color="{ORANGE}" fontcolor="{ORANGE}"];
  E -> hx [label="+" color="{ORANGE}" fontcolor="{ORANGE}"]; hx -> O [label="+" color="{ORANGE}" fontcolor="{ORANGE}"];
  E -> wd [label="+" color="{BLUE}" fontcolor="{BLUE}"]; wd -> ws [label="+" color="{BLUE}" fontcolor="{BLUE}"];
  ws -> W [label="+  (delay)" color="{BLUE}" fontcolor="{BLUE}"]; W -> ws [label="\−" color="{BLUE}" fontcolor="{BLUE}"];
  ws -> O [label="+" color="{ORANGE}" fontcolor="{ORANGE}"];
}}'''
    render(src, os.path.join(FIG, "causal_loop.png"))


def stock_flow():
    src = f'''digraph G {{
  rankdir=TB; splines=true; nodesep=0.3; ranksep=0.55; ratio=0.75; bgcolor=white; pad=0.3;
  label="Stock-and-flow structure (seven stocks; C is the supporting stock, decision D5)\\nBoxes: stocks.  Blue arrows: flows.  Text: converters.  Grey dashed: information links.";
  labelloc=t; labeljust=l; fontname="Helvetica-Bold" fontsize=12; fontcolor="{INK}";
  node [{FONT}]; edge [{FONT}];
  node [shape=box style="filled,bold" fillcolor="#eef3f8" color="{INK}" penwidth=2 margin="0.2,0.12"];
  C [label="C\\ncontracted load (MW)"]; G [label="G\\ngrid capacity added (MW)"]; E [label="E\\nenergized capacity (MW)"];
  W [label="W\\nwater supply capacity (MGD)"]; F [label="F\\ncumulative net fiscal impact ($M)"];
  P [label="P\\npopulation"]; O [label="O\\ncommunity opposition (0-1)" fillcolor="#fdf0e6"];
  node [shape=plaintext style="" penwidth=1 margin="0.02"];
  src_C [label=""]; src_W [label=""]; src_F [label=""]; src_P [label=""];
  edge [color="{BLUE}" penwidth=3 fontcolor="{BLUE}"];
  src_C -> C [label="sign_rate"]; C -> G [label="(C-G)/D_grid"]; G -> E [label="(G-E)/tau"];
  src_W -> W [label="expansion"]; src_F -> F [label="net revenue - relief\\n- service costs"]; src_P -> P [label="growth + in-migration"];
  node [shape=box style="rounded" color="{GREY}" fontcolor="{INK}" margin="0.1,0.05"];
  m [label="permitting factor m"]; RI [label="rate index RI"]; demand [label="water demand"]; stress [label="water stress"];
  drought [label="drought"]; H [label="housing index H, excess hx"]; abate [label="abatement(t)"]; relief [label="relief index R"];
  nb [label="net benefit nb" color="{GREEN}"]; D [label="opposition drivers D"]; constr [label="construction (C-E)/1000"];
  edge [color="{GREY}" penwidth=1.1 style=dashed fontcolor="{GREY}" arrowsize=0.7];
  O -> m; m -> C; G -> RI; E -> demand; P -> demand; demand -> stress; W -> stress; drought -> stress;
  stress -> W; E -> F; abate -> F; F -> relief; E -> relief; relief -> D; RI -> D; stress -> D; H -> D; constr -> D; D -> O;
  C -> constr; E -> constr; P -> H; E -> H; H -> P; E -> P;
  E -> nb; F -> nb; RI -> nb; H -> nb; stress -> nb; O -> nb;
}}'''
    render(src, os.path.join(FIG, "stock_flow.png"))


if __name__ == "__main__":
    causal_loop()
    stock_flow()
    print("wrote causal_loop.png and stock_flow.png")
