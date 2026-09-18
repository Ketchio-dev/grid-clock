"""Hourly gas share of Ontario's electricity, by season and day type.

Reports gas share, not gCO2/kWh. The headline claim does not need an emission
factor: intensity is gas share times a constant, so every ratio and ordering is
invariant to the factor you pick. Only the axis label changes.

Hours are labelled 0-23, where hour H covers H:00-H+1:00. IESO numbers them
1-24; an earlier version of this file printed the raw IESO index, so the same
hour was called "1" here and "0" in the chart.
"""
import sys, datetime
from collections import defaultdict
from parse_ieso import local_rows

def season(d):
    return "summer" if 5 <= int(d[5:7]) <= 10 else "winter"

by_hour = defaultdict(list)
for day, hour, mix in local_rows(sys.argv[1]):
    tot = sum(mix.values())
    if tot <= 0:
        continue
    dt = datetime.date(int(day[:4]), int(day[5:7]), int(day[8:10]))
    by_hour[(season(day), dt.weekday() < 5, hour)].append(
        mix.get("GAS", 0.0) * 100.0 / tot)

for seas in ("summer", "winter"):
    vals = [(h, sum(v) / len(v)) for h in range(24)
            if (v := by_hour.get((seas, True, h)))]
    if not vals:
        continue
    lo, hi = min(v for _, v in vals), max(v for _, v in vals)
    print(f"\n  === {seas} weekdays — gas share of generation (%) ===")
    for h, m in vals:
        bar = "#" * int((m - lo) / max(hi - lo, 1e-9) * 46)
        print(f"    {h:>2}:00 {m:6.2f}  {bar}")
    lo_h = min(vals, key=lambda x: x[1])[0]
    hi_h = max(vals, key=lambda x: x[1])[0]
    print(f"    lowest {lo:.2f}% at {lo_h}:00 / highest {hi:.2f}% at {hi_h}:00"
          f" / ratio {hi/max(lo,1e-9):.3f}x")
