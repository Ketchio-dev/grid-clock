"""8시간 창의 +4.4 g 튐이 정렬 인공물인가. 시작점만 옮겨 한 번 본다."""
import sys, datetime
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday
EF_GAS = 490.0
def tou(h):
    if h >= 19 or h < 7: return "off"
    if 11 <= h < 17:     return "on"
    return "mid"
acc, n = defaultdict(float), defaultdict(int)
for day, hour, mix in local_rows(sys.argv[1]):
    if not summer_weekday(day): continue
    t = sum(mix.values())
    if t <= 0: continue
    acc[hour] += mix.get("GAS",0.0)*EF_GAS/t; n[hour] += 1
c = {h: acc[h]/n[h] for h in sorted(acc)}

print("  === 8시간 창, 시작점을 바꿔가며 ===")
print("   시작   창 구성                     최저가 최악  최고가 최악   초과")
for start in (0, 7, 11, 17, 19):
    agg = []
    for i in range(3):
        hs = [(start + i*8 + k) % 24 for k in range(8)]
        val = sum(c[h] for h in hs)/8
        labs = [tou(h) for h in hs]
        # 과반이 있어야 그 계층이라고 부른다. 동수면 "mixed" 로 두고 비교에서 뺀다.
        #
        # 앞 판본은 `max(set(labs), key=labs.count)` 였다. start=7 의 창은 mid 4 / on 4 로
        # **정확히 동수**이고, 동수의 승자는 set 순회 순서가 정했다 — 파이썬이 문자열 해시를
        # 프로세스마다 무작위화하므로 **같은 입력에 같은 답이 나오지 않았다.**
        # 실행마다 그 줄이 `+7.0 g` 였다가 `비교 불가` 였다가 했고, README·Devpost·영상 대본이
        # 인용한 범위가 실행마다 달랐다. 검증 스크립트가 재현되지 않으면 검증이 아니다.
        best = max(sorted(set(labs)), key=labs.count)
        lab = best if labs.count(best) * 2 > len(labs) else "mixed"
        agg.append((hs[0], val, lab, labs.count("off"), labs.count("on")))
    offs = [v for _,v,l,_,_ in agg if l=="off"]
    ons  = [v for _,v,l,_,_ in agg if l=="on"]
    desc = " ".join(f"{h}시({l[:3]})" for h,_,l,_,_ in agg)
    if offs and ons:
        print(f"   {start:>2}시   {desc:<28} {max(offs):6.1f}      {max(ons):6.1f}    {max(offs)-max(ons):+5.1f} g")
    else:
        print(f"   {start:>2}시   {desc:<28} (off 또는 on 계층이 비어 비교 불가)")
print()
print("  참고 — 1h 창 초과 +3.7 g / 4h +0.1 g / 6h +0.8 g")
