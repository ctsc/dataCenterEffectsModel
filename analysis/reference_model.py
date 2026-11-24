"""Reference implementation of the Coweta data center system dynamics model.

Follows notes/model_spec.md exactly. Euler integration; all constants come from
data/parameters.csv (no constants are hard-coded here). Used as the test oracle for the
NetLogo model and for fast cross-checks of experiments.
"""
import math
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PARAM_CSV = os.path.join(HERE, "..", "data", "parameters.csv")

SIZES = {
    "none": 0.0,
    "half_sail": 450.0,
    "sail": None,  # size_sail
    "double_sail": 1800.0,
}


def load_params(path=PARAM_CSV):
    df = pd.read_csv(path)
    return {r["name"]: float(r["value"]) for _, r in df.iterrows()}


def scenario_sizes(p):
    """Named campus sizes (MW) used in experiments."""
    sail = p["size_sail"]
    return {
        "sail": sail,
        "sail+bridgeport+pegasus": sail + p["size_bridgeport"] + p["size_pegasus"],
        "sail+bridgeport+pegasus+peach": sail + p["size_bridgeport"] + p["size_pegasus"] + p["size_peach"],
    }


def run(size=None, t_sign=None, cooling="closed", payer="dc", abate0=None, drought=False,
        links_on=True, params=None, overrides=None, dt=None, horizon=None, record_every=None):
    """Run one simulation and return a DataFrame with one row per recorded step.

    size: target campus MW (default size_sail). overrides: dict of parameter overrides.
    """
    p = dict(params if params is not None else load_params())
    if overrides:
        p.update(overrides)
    S = p["size_sail"] if size is None else float(size)
    t_sign = p["t_sign"] if t_sign is None else float(t_sign)
    abate0 = p["abate0"] if abate0 is None else float(abate0)
    dt = p["dt"] if dt is None else float(dt)
    horizon = p["horizon"] if horizon is None else float(horizon)
    wi = p["wi_evap"] if cooling == "evap" else p["wi_closed"]
    share = p["share_ratepayer_pays"] if payer == "ratepayer" else p["share_dc_pays"]

    E, G, C, W, F, P, O = p["E0"], p["G0"], p["C0"], p["W0"], p["F0"], p["P0"], p["O0"]
    nsteps = int(round(horizon / dt))
    rec = max(1, int(round((record_every or 1.0) / dt))) if record_every else 1
    rows = []
    cum_nb = 0.0
    for k in range(nsteps + 1):
        t = k * dt
        # ---- auxiliaries
        P_base = p["P0"] * (1.0 + p["g_pop"] * dt) ** k   # Euler baseline path (matches discrete model)
        H_ref = (P_base / p["P0"]) ** p["hou_elast"]
        constr = (C - E) / 1000.0
        if links_on:
            m = (1.0 - p["s_perm"] * O) / (1.0 - p["s_perm"] * p["O0"])
            m = min(max(m, 0.0), p["m_max"])
        else:
            m = 1.0
        sign_rate = min(S / t_sign * m, max(0.0, S - C) / dt)
        E_flow = (G - E) / p["tau_energize"]
        capex_annual = G * p["cost_per_MW"] * p["carry_charge"]
        RI = 1.0 + share * capex_annual / p["resid_rev_base"]
        demand_base = p["water_base0"] * P / p["P0"]
        demand = demand_base + E * wi
        drought_on = 1.0 if (drought and p["drought_start"] <= t < p["drought_start"] + p["drought_duration"]) else 0.0
        W_eff = W * (1.0 - p["drought_severity"] * drought_on)
        stress = demand / W_eff
        stress_struct = demand / W
        W_target = demand / p["ws_target"]
        if stress_struct > p["ws_trigger"] and W < p["water_cap"]:
            dW = min(max(0.0, W_target - W), p["water_cap"] - W) / p["D_water"]
        else:
            dW = 0.0
        H = (P / p["P0"]) ** p["hou_elast"] * (1.0 + p["k_prox"] * E / 1000.0)
        hx = H / H_ref - 1.0
        persons_per_MW = p["jobs_per_MW"] * (1.0 + p["job_multiplier"]) * p["newhh_per_job"] * p["hh_size"]
        dP = P * p["g_pop"] * max(0.0, 1.0 - p["s_hm"] * hx) + persons_per_MW * E_flow
        abate = abate0 * max(0.0, 1.0 - t / p["T_abate"])
        rev_net = p["rev_per_MW"] * E * (1.0 - abate)
        relief_cash = p["relief_share"] * rev_net
        R = relief_cash / p["levy_base"]
        cost_svc = p["svc_cost_per_MW"] * E
        pop_dc = P - P_base
        cost_pop = p["percap_cost"] * pop_dc / 1e6
        dF = rev_net - relief_cash - cost_svc - cost_pop
        D = (p["d_open0"] + p["a_c"] * constr + p["a_w"] * max(0.0, stress - p["ws_opp"])
             + p["a_e"] * (RI - 1.0) / 0.1 + p["a_h"] * hx - p["a_r"] * R)
        O_star = max(0.0, D) / (1.0 + max(0.0, D))
        dO = (O_star - O) / p["tau_O"]
        # ---- net benefit (spec: scenario minus no-data-center baseline)
        HH = P / p["hh_size"]
        fiscal_hh = 1e6 * (rev_net - cost_svc - cost_pop) / HH
        elec_hh = (RI - 1.0) * p["elec_price"] / 100.0 * p["hh_kwh"]
        house_hh = hx * p["house_cost_base"]
        stress_base_eff = p["water_base0"] * P_base / p["P0"] / (
            p["W0"] * (1.0 - p["drought_severity"] * drought_on))
        water_hh = p["shortage_cost"] * (max(0.0, stress - 1.0) - max(0.0, stress_base_eff - 1.0))
        ql_hh = p["ql_cost"] * (E / 1000.0) * O
        nb = fiscal_hh - elec_hh - house_hh - water_hh - ql_hh
        if k % rec == 0:
            rows.append(dict(year=t, E=E, G=G, C=C, W=W, F=F, P=P, O=O, water_stress=stress,
                             RI=RI, H=H, hx=hx, m=m, rev_net=rev_net, relief_cash=relief_cash,
                             cost_svc=cost_svc, cost_pop=cost_pop, nb=nb, cum_nb=cum_nb,
                             demand=demand, W_eff=W_eff, D=D, O_star=O_star))
        # ---- update stocks (every derivative uses values computed at time t)
        dG = (C - G) / p["D_grid"]
        C += sign_rate * dt
        G += dG * dt
        E += E_flow * dt
        W += dW * dt
        F += dF * dt
        P += dP * dt
        O += dO * dt
        cum_nb += nb * dt
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = run()
    print(df.iloc[[0, 40, 80, 120, 160]][["year", "E", "G", "C", "W", "F", "P", "O", "water_stress", "RI", "H", "m", "nb", "cum_nb"]].round(3).to_string())
