"""Two Ontario tariffs against the measured gas share.

TOU is the DEFAULT plan. ULO is opt-in. That asymmetry is the whole point: it is not
that the two tariffs contradict each other -- they are separate products and nobody is
on both -- it is that the one you get by default prices the evening as its cheapest
hours, and the opt-in one does not.

Toronto Hydro published rates, verified 2026-09-15:
  Summer TOU (May 1 - Oct 31): off 19:00-07:00 9.8c / mid 07-11,17-19 15.7c
                               / on 11:00-17:00 20.3c
  ULO (Nov 1 2025 - Oct 31 2026): ultra-low 23:00-07:00 3.9c
                               / on 16:00-21:00 39.1c / mid otherwise 15.7c
Hours are 0-23; hour H covers H:00-H+1:00.
"""
import sys, datetime
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday

def tou(h):
    if h >= 19 or h < 7:  return "off-peak", 9.8
    if 11 <= h < 17:      return "ON-PEAK", 20.3
    return "mid-peak", 15.7

def ulo(h):
    if h >= 23 or h < 7:  return "ultra-low", 3.9
    if 16 <= h < 21:      return "ON-PEAK", 39.1
    return "mid-peak", 15.7

acc, n = defaultdict(float), defaultdict(int)
for day, hour, mix in local_rows(sys.argv[1]):
    if not summer_weekday(day):
        continue
    tot = sum(mix.values())
    if tot <= 0:
        continue
    acc[hour] += mix.get("GAS", 0.0) * 100.0 / tot
    n[hour] += 1
g = {h: acc[h] / n[h] for h in sorted(acc)}

print("  === Summer weekdays: what each tariff says, against measured gas share ===")
print("   hour      TOU                  ULO                gas share")
for h in range(24):
    tn, tp = tou(h); un, up = ulo(h)
    print(f"   {h:>2}:00   {tp:5.1f}c {tn:<10}  {up:5.1f}c {un:<10}   {g[h]:6.2f} %")

off = [(h, g[h]) for h in range(24) if tou(h)[0] == "off-peak"]
on  = [(h, g[h]) for h in range(24) if tou(h)[0] == "ON-PEAK"]
wh, wv = max(off, key=lambda x: x[1])
bh, bv = min(off, key=lambda x: x[1])
onh, onv = max(on, key=lambda x: x[1])
print()
print(f"  Inside the single cheapest price (9.8c, twelve hours):")
print(f"    dirtiest {wh}:00 at {wv:.2f}% gas / cleanest {bh}:00 at {bv:.2f}% / {wv/bv:.3f}x")
print(f"  The most expensive bracket (20.3c) peaks at {onh}:00, {onv:.2f}% gas.")
print(f"  Crossover margin: {wv:.2f} - {onv:.2f} = {wv-onv:+.2f} pp"
      f"  (the thinnest claim here; shrink the contrast ~{100*(wv-onv)/(wv-bv):.0f}% and it goes)")
# 섭동 모형을 말로만 적으면 그 수도 손으로 계산한 게 된다. 두 경우를 다 찍는다.
SCALE = 0.7
print(f"    perturbation A — hold {bv:.2f} and {onv:.2f} fixed, shrink only the {wv-bv:.2f} pp"
      f" off-peak spread: crossover gone at ~{100*(wv-onv)/(wv-bv):.0f}%")
print(f"    perturbation B — scale every hour by {SCALE} about a common baseline:"
      f" ordering unchanged, margin {SCALE*(wv-onv):.2f} pp")
print(f"  So the worst hour in the CHEAPEST bracket beats every hour in the most expensive one"
      if wv > onv else "  No misalignment in this season.")
print()
ulo_on = [g[h] for h in range(24) if ulo(h)[0] == "ON-PEAK"]
print(f"  ULO prices those same evening hours at 39.1c and averages {sum(ulo_on)/len(ulo_on):.2f}% gas.")
print(f"  Same hours, opposite prices -- but these are separate products, not a contradiction.")
print(f"  What matters is which one you get without asking: TOU is Ontario's default, ULO is")
print(f"  opt-in. So the utility already knows how to price the evening ramp. It just is not")
print(f"  what lands on your bill unless you go looking. See baseline.py for what that is worth.")
