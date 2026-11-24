"""Checks for analysis/reference_model.py (plan step 3.2). Run: python analysis/test_reference.py"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reference_model as rm

p = rm.load_params()


def test_zero_data_center_is_baseline():
    df = rm.run(size=0)
    assert (df.E == 0).all() and (df.G == 0).all() and (df.C == 0).all()
    assert abs(df.hx).max() < 1e-9
    assert abs(df.O - p["O0"]).max() < 1e-9, "opposition must stay at O0 with no driver"
    assert abs(df.nb).max() < 1e-6 and abs(df.F).max() < 1e-9
    base = p["P0"] * math.exp(p["g_pop"] * 20)
    assert abs(df.P.iloc[-1] / base - 1) < 0.02  # Euler path stays close to the exact exponential


def test_grid_lags_contracted_load():
    # near-instant signing of 900 MW: G follows C with a first-order delay D_grid
    df = rm.run(size=900, t_sign=0.125, links_on=False)
    i = int(round(p["D_grid"] / p["dt"]))
    frac = df.G.iloc[i] / df.C.iloc[i]
    assert abs(frac - (1 - math.exp(-1))) < 0.05, frac


def test_energized_never_exceeds_grid():
    for kw in [dict(), dict(size=3500, t_sign=3), dict(size=2800, drought=True, cooling="evap")]:
        df = rm.run(**kw)
        assert (df.E <= df.G + 1e-9).all() and (df.G <= df.C + 1e-9).all()


def test_tax_calibration_near_100M_at_900MW():
    assert abs(p["rev_per_MW"] * 900 - 100.0) < 2.0
    df = rm.run(abate0=0.0)
    assert 90 < df.rev_net.iloc[-1] < 105, df.rev_net.iloc[-1]


def test_bounds_and_buildout_timing():
    df = rm.run()
    assert (df.O >= 0).all() and (df.O < 1).all()
    assert (df[["E", "G", "C", "W", "P"]] >= 0).all().all()
    assert not df.isna().any().any()
    t90 = df[df.E >= 0.9 * 900].year.min()
    assert 8.0 <= t90 <= 10.0, t90  # EIG: last building online year 9


def test_evaporative_cooling_stresses_water_more():
    a = rm.run(cooling="closed").water_stress.max()
    b = rm.run(cooling="evap").water_stress.max()
    assert b > a + 0.1


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            n += 1
            print("PASS", name)
    print(n, "tests passed")
