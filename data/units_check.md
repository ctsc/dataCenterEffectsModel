# data/units_check.md

Dimensional audit of every equation in `notes/model_spec.md`. Time is years, so every flow must be (stock unit)/year. Dimensionless ratios are marked [1].

| Equation | Left side | Right side units | OK |
|---|---|---|---|
| P_base = P0 (1+g dt)^(t/dt) | people | people * [1] | yes |
| H_ref = (P_base/P0)^e | [1] | ([1])^[1] | yes |
| constr = (C-E)/1000 | GW | MW / (MW/GW) | yes |
| m = clip((1 - s O)/(1 - s O0)) | [1] | [1] | yes |
| sign_rate = min(S/t_sign * m, (S-C)/dt) | MW/yr | MW/yr, MW/yr | yes |
| dC/dt = sign_rate | MW/yr | MW/yr | yes |
| dG/dt = (C-G)/D_grid | MW/yr | MW / yr | yes |
| E_flow = (G-E)/tau_energize | MW/yr | MW / yr | yes |
| capex_annual = G * cost_per_MW * carry_charge | $M/yr | MW * ($M/MW) * (1/yr) | yes |
| RI = 1 + share * capex_annual / resid_rev_base | [1] | [1] * ($M/yr) / ($M/yr) | yes |
| demand_base = water_base0 * P/P0 | MGD | MGD * [1] | yes |
| demand = demand_base + E * wi | MGD | MGD + MW * (MGD/MW) | yes |
| W_eff = W (1 - sev * on) | MGD | MGD * [1] | yes |
| water_stress = demand / W_eff | [1] | MGD / MGD | yes |
| dW/dt = min(max(0, W_target - W), cap - W) / D_water | MGD/yr | MGD / yr | yes |
| H = (P/P0)^e (1 + k_prox E/1000) | [1] | [1] * (1 + (1/GW) * GW) | yes |
| persons_per_MW = jobs_per_MW (1+mult) newhh_per_job hh_size | people/MW | (jobs/MW) * [1] * (hh/job) * (people/hh) | yes |
| dP/dt = P g (1 - s hx) + persons_per_MW * E_flow | people/yr | people * (1/yr) + (people/MW)*(MW/yr) | yes |
| abate(t) = abate0 * max(0, 1 - t/T_abate) | [1] | [1] * [1] (t and T_abate in yr) | yes |
| rev_net = rev_per_MW * E * (1 - abate) | $M/yr | ($M/MW/yr) * MW | yes |
| relief_cash = relief_share * rev_net | $M/yr | [1] * $M/yr | yes |
| R = relief_cash / levy_base | [1] | ($M/yr) / ($M/yr) | yes |
| cost_svc = svc_cost_per_MW * E | $M/yr | ($M/MW/yr) * MW | yes |
| cost_pop = percap_cost * (P - P_base) / 1e6 | $M/yr | ($/person/yr) * people / ($/$M) | yes |
| dF/dt = rev_net - relief_cash - cost_svc - cost_pop | $M/yr | $M/yr | yes |
| D = d0 + a_c constr + a_w max(0, stress-ws_opp) + a_e (RI-1)/0.1 + a_h hx - a_r R | [1] | each coefficient is per-unit of a dimensionless or GW driver; all terms [1] | yes (a_c per GW) |
| O_star = max(0,D)/(1+max(0,D)) | [1] | [1] | yes |
| dO/dt = (O_star - O)/tau_O | 1/yr | [1] / yr | yes |
| fiscal_hh = 1e6 (rev_net - cost_svc - cost_pop)/HH | $/hh/yr | ($M/yr) * ($/$M) / households | yes |
| elec_hh = (RI-1) * elec_price/100 * hh_kwh | $/hh/yr | [1] * ($/kWh) * kWh/hh/yr | yes (cents to $) |
| house_hh = hx * house_cost_base | $/hh/yr | [1] * $/hh/yr | yes |
| water_hh = shortage_cost * (...) | $/hh/yr | ($/hh/yr per unit stress) * [1] | yes |
| ql_hh = ql_cost * E/1000 * O | $/hh/yr | ($/hh/yr per GW per unit O) * GW * [1] | yes |
| cum_nb = sum nb * dt | $/hh | ($/hh/yr) * yr | yes |

No mismatches. The only mixed-unit points are the 1e6 conversion ($M to $), the /1000 conversion (MW to GW) and the /100 conversion (cents to dollars), all explicit in the equations.
