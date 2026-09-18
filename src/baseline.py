"""What does Grid Clock add over the obvious alternatives?

GPT-6 Pro's objection (2026-09-15): "compare with a simple overnight timer, and
note that ULO already incentivizes overnight shifting." Both are fair. A tool is
worth only what it adds over the next-best thing a person would actually do, and
the next-best thing here is a $12 plug-in timer.

So we measure the alternatives instead of asserting we beat them. The answer is
not flattering and it is in the README.

Strategies are scored on mean gas share (%) at the hour they pick; lower is better.
No emission factor: gas share is measured, so every gap below is invariant to it.
"""
import sys, datetime, statistics
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday, to_date, is_holiday

TOU_OFF = [h for h in range(24) if h >= 19 or h < 7]   # 19:00-07:00  9.8c
ULO_LOW = [h for h in range(24) if h >= 23 or h < 7]   # 23:00-07:00  3.9c

def summer_weekday_hours(path):
    """{day: {hour0_23: gas share %}} for Ontario summer weekdays."""
    out = defaultdict(dict)
    for day, hour, mix in local_rows(path):
        if not summer_weekday(day):
            continue
        tot = sum(mix.values())
        if tot > 0:
            out[day][hour] = mix.get("GAS", 0.0) * 100.0 / tot
    return out

day_hr = summer_weekday_hours(sys.argv[1])
TOU_HOL_IN_RANGE = sorted(d for d in __import__("ontario").TOU_HOLIDAYS_2026
                          if d.month in (5, 6, 7, 8, 9, 10) and d.weekday() < 5
                          and f"{d}" <= max(day_hr))
acc, n = defaultdict(float), defaultdict(int)
for hrs in day_hr.values():
    for h, v in hrs.items():
        acc[h] += v; n[h] += 1
g = {h: acc[h] / n[h] for h in sorted(acc)}

avg  = lambda hs: sum(g[h] for h in hs) / len(hs)
best = lambda hs: min(hs, key=lambda h: g[h])

print("  === 1. What Grid Clock adds over the next-best thing ===")
print("   strategy                      hour   gas share    what it is")
for name, h, v, note in [
    ("no plan / run at dinner",   20, g[20],        "20:00, when people actually run things"),
    ("common advice: after 7pm",  19, g[19],        "19:00, the hour off-peak opens"),
    ("simple overnight timer",  None, avg(ULO_LOW), "set once, fires anywhere 23:00-07:00"),
    ("timer set to 2 a.m.",        2, g[2],         "the hour people pick when they pick one"),
    ("Grid Clock, TOU customer", best(TOU_OFF), g[best(TOU_OFF)], "cleanest hour inside 9.8c"),
    ("Grid Clock, ULO customer", best(ULO_LOW), g[best(ULO_LOW)], "cleanest hour inside 3.9c"),
    ("oracle, mean profile",   best(range(24)), g[best(range(24))], "upper bound on a STATIC pick"),
]:
    hs = f"{h:>2}:00" if isinstance(h, int) else "  any"
    print(f"   {name:<27} {hs}   {v:6.2f} %    {note}")

tou_gain = g[19] - g[best(TOU_OFF)]
timer_gain = g[2] - g[best(ULO_LOW)]
print()
print(f"  headline gap, dirtiest vs cleanest hour in the 9.8c bracket:"
      f" {g[20]:.2f} -> {g[best(TOU_OFF)]:.2f} %  ({g[20]-g[best(TOU_OFF)]:+.2f} pp)")
print(f"  vs the advice a TOU customer is given today: {g[19]:.2f} -> {g[best(TOU_OFF)]:.2f} %"
      f"  ({tou_gain:+.2f} pp)")
print(f"  vs a 2 a.m. timer:                          {g[2]:.2f} -> {g[best(ULO_LOW)]:.2f} %"
      f"  ({timer_gain:+.2f} pp)")
print(f"  A timer already captures {100*(1 - timer_gain/tou_gain):.1f} % of what we offer.")

# --- 2. is the static pick even right on a given night? ---------------------
full = {d: h for d, h in day_hr.items() if all(x in h for x in ULO_LOW)}
fixed2 = [h[2] for h in full.values()]
static = [h[g_best] for h in full.values()] if (g_best := best(ULO_LOW)) is not None else []
oracle, wins = [], defaultdict(int)
for hrs in full.values():
    w = {h: hrs[h] for h in ULO_LOW}
    b = min(w, key=w.get); wins[b] += 1; oracle.append(w[b])
N = len(full)

print()
print(f"  === 2. Is our static {g_best}:00 pick right on any given night? ({N} nights) ===")
print(f"   fixed 2 a.m. timer       mean {statistics.mean(fixed2):6.2f} %  sd {statistics.stdev(fixed2):5.2f}")
print(f"   our static {g_best}:00 pick     mean {statistics.mean(static):6.2f} %  sd {statistics.stdev(static):5.2f}")
print(f"   per-night oracle         mean {statistics.mean(oracle):6.2f} %  sd {statistics.stdev(oracle):5.2f}")
print()
print("   cleanest hour, counted night by night:")
for h, c in sorted(wins.items(), key=lambda x: -x[1]):
    mark = "  <- what we recommend" if h == g_best else ""
    print(f"     {h:>2}:00  {c:>3} nights  {c*100/N:5.1f} %{mark}")
print()
print(f"   So {g_best}:00 is the best hour on only {wins[g_best]*100/N:.1f} % of nights. It wins on the")
print(f"   average and not much else. A perfect forecast would beat a 2 a.m. timer by")
print(f"   {statistics.mean(fixed2)-statistics.mean(oracle):+.2f} pp -- real, but {tou_gain/(statistics.mean(fixed2)-statistics.mean(oracle)):.1f}x smaller than the"
      f" {tou_gain:+.2f} pp")
print(f"   available from not running in the evening at all. We do not ship a forecast,")
print(f"   so we do not claim that {statistics.mean(fixed2)-statistics.mean(oracle):+.2f} pp.")

# --- 3. 이 시각 선택이 얼마나 단단한가 -------------------------------------
# 공휴일을 평일로 섞느냐 빼느냐 하나로 최선 시각이 뒤집힌다.
# 온타리오 TOU 는 공휴일에 하루 종일 off-peak 로 과금하므로 빼는 쪽이 맞지만,
# 중요한 건 어느 쪽이 맞느냐가 아니라 **그 결정이 답을 바꾼다**는 사실이다.
def profile_including_holidays(path):
    a, m = defaultdict(float), defaultdict(int)
    for day, hour, mix in local_rows(path):
        d = to_date(day)
        if d.month not in (5, 6, 7, 8, 9, 10) or d.weekday() >= 5:
            continue
        tot = sum(mix.values())
        if tot > 0:
            a[hour] += mix.get("GAS", 0.0) * 100.0 / tot
            m[hour] += 1
    return {h: a[h] / m[h] for h in sorted(a)}

g_inc = profile_including_holidays(sys.argv[1])
b_inc = min(TOU_OFF, key=lambda h: g_inc[h])
b_exc = best(TOU_OFF)
print()
print("  === 3. Is that hour a robust pick? (sensitivity to holiday handling) ===")
print(f"   holidays excluded (OEB rule, our build)  best {b_exc}:00  {g[b_exc]:.3f} %"
      f"   2am {g[2]:.3f} / 3am {g[3]:.3f}")
print(f"   holidays left in (our first version)     best {b_inc}:00  {g_inc[b_inc]:.3f} %"
      f"   2am {g_inc[2]:.3f} / 3am {g_inc[3]:.3f}")
print()
if b_exc != b_inc:
    print(f"   Dropping {len(TOU_HOL_IN_RANGE)} statutory holidays flips the best hour "
          f"{b_inc}:00 -> {b_exc}:00.")
else:
    print(f"   The best hour is {b_exc}:00 either way.")
print(f"   2 a.m. and 3 a.m. differ by {abs(g[2]-g[3]):.3f} pp. That is the resolution of our"
      f" hour-picking.")
print(f"   So we do not say '{b_exc} a.m. is best'. We say 'overnight, not evening'.")

# --- 4. 한 시간짜리 일이 아니면? ------------------------------------------
# "A multi-hour task should be evaluated using the electricity consumed throughout its
# cycle, not just its start hour." (GPT-6 Pro, 2026-09-15) 맞는 지적이라 재 본다.
# 카드는 시작 시각만 본다. 사이클 길이를 늘리면 최선 시작 시각이 움직이는가?
print()
print("  === 4. Multi-hour cycles: does the best START hour move? ===")
print("   cycle   best start   mean over cycle   vs 1h pick")
one_h, costs = None, {}
for L in (1, 2, 3):
    cyc = {h: sum(g[(h + k) % 24] for k in range(L)) / L for h in range(24)}
    # 사이클이 저렴 구간 안에서 **끝나야** 한다 — 시작만 off-peak 인 것으로는 부족하다.
    ok_start = [h for h in range(24) if all((h + k) % 24 in TOU_OFF for k in range(L))]
    bh = min(ok_start, key=lambda h: cyc[h])
    if one_h is None:
        one_h = bh
    # 1시간 기준으로 고른 시각을 이 사이클 길이로 평가했을 때 얼마나 손해인가 — 계산한다, 주장하지 않는다.
    penalty = cyc[one_h] - cyc[bh] if one_h in ok_start else None
    pen = f"+{penalty:.3f} pp worse" if penalty is not None else "1h pick is not a legal start"
    costs[L] = penalty
    print(f"   {L}h      {bh:>2}:00        {cyc[bh]:6.3f} %"
          f"        {'same' if bh == one_h else f'{one_h}:00 -> {bh}:00, {pen}'}")
print()
print(f"   A longer cycle must also *finish* inside the cheap window, which removes late starts.")
worst = max((v for v in costs.values() if v is not None), default=0.0)
sep = abs(g[2] - g[3])
print(f"   Sticking with the 1-hour pick costs at most {worst:.3f} pp across these cycle lengths,")
print(f"   versus the {sep:.3f} pp that separates 2 a.m. from 3 a.m. at all — so cycle length"
      f" {'matters more' if worst > sep else 'matters less'} than")
print(f"   the hour we print. The card reports a start hour and does not model cycle length;")
print(f"   that is a real limitation of the card, and it is in the README.")
