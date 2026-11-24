"""Derive tax-revenue and abatement parameters from the Economic Impact Group (Sept 2025)
fiscal impact analysis of Project Sail (972 MW, 9 buildings). All inputs are $ thousands, years 0-20.
Source: assets.foleon.com ... project_sail_fiscal_impact_analysis_-_21_years_-_final (see data/sources.md S7)."""
import numpy as np

county_benefits = [8968.9,7525.9,14536.4,10690.4,24999.8,19270.3,31594.6,22899.7,38059.6,27970.1,36515.5,25370.7,40570.2,29379.0,39210.4,26710.8,44054.0,31463.9,42690.6,28774.4,48339.8]
county_support  = [8094.9,5975.6,11885.3,7603.6,17817.2,11581.8,20571.8,12754.1,18560.2,10499.3,12162.6,6322.7,7388.8,3631.9,3281.7,1195.2,1179.8,477.1,0,0,0]
county_costs_total = [8108.9,6004.9,11945.4,7681.4,17928.9,11713.7,20741.2,12946.5,18785.0,10740.3,12420.2,6588.1,7662.2,3913.4,3571.7,1493.9,1487.5,794.0,326.4,336.2,346.3]
school_benefits = [18169.2,15230.9,29409.4,21588.5,50589.4,38940.9,63905.9,46232.7,76963.8,56459.6,73799.5,51155.6,82012.2,59273.3,79227.6,53830.9,89039.8,63458.5,86245.0,57969.9,97690.1]
school_support  = [16439.4,12135.4,24137.1,15441.7,36183.8,23520.7,41778.0,25901.6,37692.8,21322.4,24700.2,12840.3,15005.5,7375.7,6664.6,2427.3,2396.1,968.9,0,0,0]
school_costs_total = [16464.1,12187.0,24242.7,15578.3,36380.1,23752.3,42075.6,26239.4,38087.7,21745.7,25152.8,13306.5,15485.6,7870.3,7174.0,2952.0,2936.4,1525.5,573.3,590.5,608.2]
MW = 972.0
cb, cs, ct = map(np.array, (county_benefits, county_support, county_costs_total))
sb, ss, st = map(np.array, (school_benefits, school_support, school_costs_total))
gross = (cb + sb) / 1000.0                       # $M/yr, county + schools, before incentives
support = (cs + ss) / 1000.0
opcost = ((ct - cs) + (st - ss)) / 1000.0        # operating service costs excluding incentive
full = slice(10, 21)                             # years 10-20 = after last building online (year 9)
print("gross revenue $M/yr, mean yrs 10-20:", gross[full].mean().round(2))
print("gross revenue per MW $M/MW/yr:", (gross[full].mean() / MW).round(4))
print("gross revenue at 900 MW $M/yr:", (gross[full].mean() / MW * 900).round(1))
print("county share of gross (yrs 10-20):", (cb[full].sum() / (cb[full].sum() + sb[full].sum())).round(3))
print("incentive / gross over 21 yrs:", (support.sum() / gross.sum()).round(3))
print("operating service cost $M/yr, mean yrs 10-20:", opcost[full].mean().round(3), " per MW:", (opcost[full].mean() / MW).round(5))
ratio = support / gross
print("abatement share by year:", np.round(ratio, 2).tolist())
t = np.arange(21)
m = t <= 17
slope, icpt = np.polyfit(t[m], ratio[m], 1)
print("linear fit abatement share: a0=%.3f, zero at t=%.1f" % (icpt, -icpt / slope))
# revenue-weighted check: apply a(t)=a0*max(0,1-t/T) to gross revenue
for a0, T in [(0.85, 17.5), (icpt, -icpt / slope)]:
    a = a0 * np.maximum(0, 1 - t / T)
    print("a0=%.3f T=%.1f -> incentive/gross over 21 yrs = %.3f" % (a0, T, (a * gross).sum() / gross.sum()))
print("jobs/MW:", round(270 / MW, 4), " new households per job:", round(75 / 270, 3), " students per new hh:", round(49 / 75, 2))
print("payroll per job $k:", round(23000 / 270, 1))
