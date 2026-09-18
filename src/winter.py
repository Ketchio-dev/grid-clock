"""겨울 프로파일 — 여름과 요금 구간이 다르다. 발견이 계절을 넘는가."""
import sys, datetime
from collections import defaultdict
from parse_ieso import local_rows
from ontario import to_date, is_holiday

# Toronto Hydro 겨울(11/1~4/30): on 07-11 & 17-19 / mid 11-17 / off 19-07
def tou_w(h):
    if h >= 19 or h < 7:          return "off", 9.8
    if (7 <= h < 11) or (17 <= h < 19): return "on", 20.3
    return "mid", 15.7
def tou_s(h):
    if h >= 19 or h < 7:  return "off", 9.8
    if 11 <= h < 17:      return "on", 20.3
    return "mid", 15.7

def prof(path, months, label):
    acc, n = defaultdict(float), defaultdict(int)
    for day, hour, mix in local_rows(path):
        d = to_date(day)
        if d.month not in months or d.weekday() >= 5 or is_holiday(d): continue
        t = sum(mix.values())
        if t <= 0: continue
        acc[hour] += mix.get("GAS", 0.0)*100.0/t; n[hour] += 1
    return {h: acc[h]/n[h] for h in sorted(acc)}, label

if __name__ == "__main__":
    for months, label, tou in ((set([5,6,7,8,9,10]), "여름 (5~10월)", tou_s),
                               (set([1,2,3,4]),     "겨울 (1~4월)", tou_w)):
        c, lab = prof(sys.argv[1], months, label)
        if not c: continue
        w, b = max(c, key=c.get), min(c, key=c.get)
        offs = [(h, v) for h, v in c.items() if tou(h)[0] == "off"]
        ons  = [(h, v) for h, v in c.items() if tou(h)[0] == "on"]
        onmax_h, onmax = max(ons, key=lambda x: x[1])
        bad = [h for h, v in offs if v > onmax]
        print(f"\n  === {lab} ===")
        print(f"    최고 {w}시 {c[w]:.2f}%  /  최저 {b}시 {c[b]:.2f}%  /  비율 {c[w]/c[b]:.3f}배")
        print(f"    최고가 구간(on-peak) 최악: {onmax_h}시 {onmax:.2f}%")
        print(f"    최저가인데 on-peak 최악보다 가스 비중이 높은 시각: {bad if bad else '없음'}")
        if bad:
            print(f"    → 어긋남 있음 ({len(bad)}시간)")
        else:
            print(f"    → 어긋남 없음. 겨울 요금제는 아침·저녁 양쪽을 on-peak 로 잡아서 봉우리를 덮는다")
