"""척도스윕 — 몇 시간 창으로 뭉개면 어긋남이 사라지는가.

Canopy 의 발견("효과는 척도의 함수다")을 그대로 가져온다.
여기서는 그것이 제품의 정확도 요구사항이 된다:
6시간 창으로 말하면 조언이 무의미해진다 => "오늘 밤에"가 아니라 "새벽 3시에"라고 말해야 한다.
"""
import sys, datetime
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday

EF_GAS = 490.0
def tou_name(h):                      # h = 0..23 (구간 시작)
    if h >= 19 or h < 7:  return "off"
    if 11 <= h < 17:      return "on"
    return "mid"

acc, n = defaultdict(float), defaultdict(int)
for day, hour, mix in local_rows(sys.argv[1]):
    if not summer_weekday(day): continue
    tot = sum(mix.values())
    if tot <= 0: continue
    acc[hour] += mix.get("GAS",0.0)*EF_GAS/tot; n[hour] += 1
c = {h: acc[h]/n[h] for h in sorted(acc)}

print("  === 척도스윕: 집계 창을 넓히면 어긋남이 어떻게 되는가 ===")
print("   창   최저~최고      비율    최저가 안의 최악  최고가 최악   어긋남 시간수")
rows_out = []
for win in (1, 2, 3, 4, 6, 8, 12):
    # 창 단위로 평균 내고, 창의 TOU 라벨은 그 창의 다수결
    agg = {}
    for start in range(0, 24, win):
        hs = [(start + k) % 24 for k in range(win)]
        val = sum(c[h] for h in hs) / win
        labs = [tou_name(h) for h in hs]
        # 과반이 있어야 그 계층이다. 동수면 "mixed" — align8.py 와 같은 규칙.
        # 앞 판본(`max(set(labs), key=labs.count)`)은 동수를 set 순회 순서로 깼고,
        # 파이썬이 문자열 해시를 프로세스마다 무작위화하므로 **같은 입력에 4가지 답**이 나왔다.
        top = max(sorted(set(labs)), key=labs.count)
        lab = top if labs.count(top) * 2 > len(labs) else "mixed"
        agg[start] = (val, lab)
    vals = [v for v, _ in agg.values()]
    offs = [v for v, l in agg.values() if l == "off"]
    ons  = [v for v, l in agg.values() if l == "on"]
    if not offs or not ons:
        print(f"   {win:>2}h   (요금 구간이 뭉개져 비교 불가)")
        rows_out.append((win, None, None))
        continue
    bad = sum(1 for v, l in agg.values() if l == "off" and v > max(ons)) * win
    rows_out.append((win, max(vals) / min(vals), bad))
    print(f"   {win:>2}h   {min(vals):5.1f}~{max(vals):5.1f}   {max(vals)/min(vals):.3f}x"
          f"      {max(offs):6.1f}        {max(ons):6.1f}       {bad:>2}시간")

# 결론은 표에서 **계산한다.** 손으로 적어 두면 표가 바뀌어도 문장이 남는다 —
# 앞 판본은 "어긋남이 사라진다"고 적혀 있었는데 표의 어긋남 시간수는 3→8로 늘고 있었다.
ok_rows = [(w, r, b) for w, r, b in rows_out if r is not None]
ratios = [r for _, r, _ in ok_rows]
bads   = [b for _, _, b in ok_rows]
mono = lambda xs: all(a >= b for a, b in zip(xs, xs[1:]))
print()
print(f"  비율        {ratios[0]:.3f}x -> {ratios[-1]:.3f}x   "
      f"{'단조 감소한다' if mono(ratios) else '단조가 아니다'}")
print(f"  어긋남 시간  {bads[0]}시간 -> {bads[-1]}시간   "
      f"{'단조 감소한다' if mono(bads) else '단조가 아니다 — 오히려 늘어난다'}")
print()
print("  => 뭉갤수록 사라지는 것은 **비율**뿐이다. 어긋나는 시간 수는 줄지 않는다.")
print("     행동으로 옮길 수 있는 여지가 좁아지는 것이지 현상이 없어지는 게 아니다.")
print("     그래서 제품은 '오늘 밤에'가 아니라 '몇 시에'라고 말해야 한다.")
