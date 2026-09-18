"""블록 순열 — 자기상관이 p 를 부풀렸는가.

Canopy 의 '식재런'(연속 배치를 통째로 옮김)을 시간 차원으로 옮긴 것.
배출 시계열은 이웃 시각이 강하게 상관돼 있어서, 시각을 하나씩 섞으면
자유도를 과대평가하고 p 가 실제보다 작아진다.
블록 단위로 통째로 회전시키면 그 상관을 귀무 쪽에도 남긴다.
"""
import sys, random, datetime, math
from collections import defaultdict
from parse_ieso import local_rows
from nulls import load, excess, mean_profile, OFF, ON, SEED

TRIALS = 2000

def autocorr(profile, lag=1):
    v = [profile[h] for h in range(24)]
    m = sum(v)/24
    num = sum((v[i]-m)*(v[(i+lag) % 24]-m) for i in range(24))
    den = sum((x-m)**2 for x in v)
    return num/den

def circular_shift(days, rng):
    """각 날의 24시간을 통째로 회전. 이웃 상관을 완전히 보존한다."""
    order = {}
    for d in days:
        k = rng.randrange(24)
        order[d] = [(h + k) % 24 for h in range(24)]
    return order

def block_shuffle(days, rng, block):
    """24시간을 block 시간짜리 덩어리로 자르고 덩어리를 섞는다."""
    nb = 24 // block
    order = {}
    for d in days:
        blocks = [list(range(i*block, (i+1)*block)) for i in range(nb)]
        rng.shuffle(blocks)
        order[d] = [h for b in blocks for h in b]
    return order

if __name__ == "__main__":
    days = load(sys.argv[1])
    obs_prof = mean_profile(days)
    obs = excess(obs_prof)
    print(f"  관측 초과 {obs:+.2f} g / 이웃 시각 자기상관(lag1) {autocorr(obs_prof):.3f}")
    print()
    rng = random.Random(SEED)
    for name, gen in (("시각 단위 셔플(기존)", lambda r: {d: r.sample(range(24), 24) for d in days}),
                      ("블록 2시간",  lambda r: block_shuffle(days, r, 2)),
                      ("블록 3시간",  lambda r: block_shuffle(days, r, 3)),
                      ("블록 4시간",  lambda r: block_shuffle(days, r, 4)),
                      ("블록 6시간",  lambda r: block_shuffle(days, r, 6)),
                      ("원형 회전",   lambda r: circular_shift(days, r))):
        rng = random.Random(SEED)
        null = [excess(mean_profile(days, gen(rng))) for _ in range(TRIALS)]
        null.sort()
        mn = sum(null)/len(null)
        sd = math.sqrt(sum((v-mn)**2 for v in null)/(len(null)-1))
        p = (sum(1 for v in null if v >= obs) + 1) / (TRIALS + 1)
        flag = "" if p < 0.05 else "   <- 유의하지 않음"
        print(f"  {name:<16} 귀무 {mn:+6.2f} ± {sd:5.2f}   p = {p:.4f}{flag}")
    print()
    print("  블록이 커질수록 귀무가 관측을 더 잘 흉내 내면 자기상관이 p 를 부풀린 것이다.")
