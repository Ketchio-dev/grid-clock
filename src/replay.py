"""밤별 재생 — 평균이 아니라 **분포**를 본다.

외부 심사자(GPT-6 Pro, 2026-09-15)의 지적:
  "The highest-value remaining evidence is whether the broad message corresponds to a
   repeatable, feasible opportunity across actual nights and complete cycles."

맞는 말이다. 우리가 지금까지 보고한 건 전부 **92밤을 평균 낸 프로파일 하나**였다.
평균이 6.06 pp 라는 것과, 그 이득이 **밤마다 실제로 생긴다**는 것은 다른 주장이다.
여기서는 각 밤을 따로 재생해서 세 가지를 묻는다:

  1. "저녁 말고 야간" 이 **몇 밤에서 참인가** (넓은 메시지의 재현성)
  2. 그 이득의 **분포** — 최악의 밤은 어떤가
  3. 사이클 전체(1·2·3시간)로 평가해도 같은가

주의: 이것도 **가스 비중**이지 배출량이 아니다. 어느 밤에 이겼다는 것은
그 밤에 가스 비중이 낮았다는 뜻이고, 그만큼 배출이 줄었다는 뜻이 아니다.
"""
import sys, statistics
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday

TOU_OFF = [h for h in range(24) if h >= 19 or h < 7]
ADVICE_H = 19          # "7시 넘어서 돌려" — 사람들이 듣는 조언
TIMER_H = 2            # $12 콘센트 타이머가 맞춰지는 시각. **사람의 습관이지 우리 권고가 아니다.**
# 앞 판본은 여기에 "(= 우리 권고와 같다)"고 적어 뒀다. 두 값이 우연히 같았기 때문이다.
# 시계 정렬을 고치자 권고가 3시로 옮겨가면서 그 주석이 거짓이 됐다.
# **값이 같다고 개념을 합치면, 값이 갈릴 때 조용히 틀린 말이 된다.** 이제 권고는 데이터에서 구한다.

def nights(path):
    """{날짜: {시각: 가스비중%}} — 저렴 구간이 온전한 밤만."""
    d = defaultdict(dict)
    for day, hour, mix in local_rows(path):
        if not summer_weekday(day):
            continue
        tot = sum(mix.values())
        if tot > 0:
            d[day][hour] = mix.get("GAS", 0.0) * 100.0 / tot
    need = set(TOU_OFF) | {ADVICE_H}
    return {k: v for k, v in d.items() if need <= set(v)}

def q(xs, p):
    """분위수 하나. **표와 분포가 같은 추정량을 써야 한다.**

    앞 판본은 표 행에 `statistics.median`(짝수면 가운데 둘의 평균)을,
    세 줄 아래 분포에는 `xs[int(p*n)]`(최근접 순위)을 썼다. 같은 데이터의 같은 통계인데
    **+5.05 와 +5.15 로 서로 다르게 찍혔고**, 영상은 앞의 중앙값과 뒤의 10·90 분위를
    **섞어서** 인용했다. 추정량이 다르면 같은 이름으로 부르지 않는다.
    """
    if not xs:
        return float("nan")
    s = sorted(xs)
    i = p * (len(s) - 1)
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def cycle_mean(hrs, start, length):
    return sum(hrs[(start + k) % 24] for k in range(length)) / length

def legal_starts(length):
    """사이클이 저렴 구간 안에서 **끝나야** 한다. 시작만 off-peak 인 건 부족하다."""
    return [h for h in range(24) if all((h + k) % 24 in TOU_OFF for k in range(length))]

data = nights(sys.argv[1])
N = len(data)

def ours_hour(d):
    """우리 권고 시각 = 저렴 구간 안에서 평균 가스 비중이 가장 낮은 시각. **박아 두지 않는다.**"""
    acc = {h: [] for h in TOU_OFF}
    for hrs in d.values():
        for h in TOU_OFF:
            acc[h].append(hrs[h])
    return min(TOU_OFF, key=lambda h: statistics.mean(acc[h]))

OURS_H = ours_hour(data)
print(f"\n  === 밤별 재생: {N}밤, 각 밤을 따로 채점한다 ===")
print("  (평균 프로파일 하나가 아니라, 밤마다 실제로 이득이 생기는지를 센다)\n")
print("  사이클   야간이 저녁을 이긴 밤     이득 중앙값   최악의 밤   완벽예보 대비 손해")

for L in (1, 2, 3):
    starts = legal_starts(L)
    pick = OURS_H if OURS_H in starts else min(starts)
    gaps, regrets = [], []
    for hrs in data.values():
        evening = cycle_mean(hrs, ADVICE_H, L)      # 조언대로 19시에 시작
        ours = cycle_mean(hrs, pick, L)             # 우리 권고 시각
        best = min(cycle_mean(hrs, s, L) for s in starts)
        gaps.append(evening - ours)                 # +면 야간이 이겼다
        regrets.append(ours - best)                 # 완벽한 예보 대비 손해
    won = sum(1 for g in gaps if g > 0)
    print(f"   {L}h      {won:>3}/{N}  ({won*100/N:5.1f} %)"
          f"      {q(gaps, .5):+6.2f} pp"
          f"    {min(gaps):+6.2f} pp"
          f"     {statistics.mean(regrets):+5.2f} pp")

print()
L = 1
starts = legal_starts(L)
gaps = sorted(cycle_mean(h, ADVICE_H, L) - cycle_mean(h, OURS_H, L) for h in data.values())
print(f"  1시간 작업의 이득 분포 ({ADVICE_H}시 대비 {OURS_H}시, 가스 비중 pp):")
print(f"    최악 {gaps[0]:+.2f}   10% {q(gaps, .10):+.2f}   중앙 {q(gaps, .50):+.2f}"
      f"   90% {q(gaps, .90):+.2f}   최고 {gaps[-1]:+.2f}")
lost = sum(1 for g in gaps if g <= 0)
print(f"    야간이 **진** 밤: {lost}/{N} ({lost*100/N:.1f} %)")
print()
print(f"  읽는 법: 평균 이득이 양수라는 것과 **밤마다 이득이 난다**는 것은 다른 주장이다.")
print(f"  위 승률이 그 둘을 가른다. 그리고 이것은 여전히 가스 비중이지 배출량이 아니다 —")
print(f"  어느 밤에 이겼다는 것은 그 밤 가스 비중이 낮았다는 뜻일 뿐이다.")
