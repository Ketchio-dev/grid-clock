"""귀무모형 — 어긋남이 우연인가. Canopy 의 라벨셔플·층화·블록순열을 이식한다.

검정할 것: "최저가 구간(off-peak) 안의 최악 시각이 최고가 구간(on-peak)의 어떤 시각보다
더럽다"가 시간대 구조 때문인가, 아니면 off-peak 가 12시간이고 on-peak 가 6시간이라
표본이 많아서 생기는 것인가.

귀무모형은 **날짜 안에서 시각 라벨을 섞는다**(층화 = 날짜). 각 날의 배출값 분포는 그대로 두고
시간대 구조만 파괴한다. 구간 크기 비대칭은 귀무 쪽에도 똑같이 적용되므로 자동으로 보정된다.
"""
import sys, random, datetime, math
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday

EF_GAS = 490.0
SEED = 20260915
TRIALS = 2000
OFF = set(list(range(19,24)) + list(range(0,7)))
ON  = set(range(11,17))

def load(path):
    days = defaultdict(dict)
    for day, hour, mix in local_rows(path):
        if not summer_weekday(day): continue
        tot = sum(mix.values())
        if tot <= 0: continue
        days[day][hour] = mix.get("GAS",0.0)*EF_GAS/tot
    return {d: v for d, v in days.items() if len(v) == 24}

def excess(profile):
    return max(profile[h] for h in OFF) - max(profile[h] for h in ON)

def mean_profile(days, order=None):
    """order[d] = 시각 순열. None 이면 관측 그대로."""
    acc = defaultdict(float)
    for d, hv in days.items():
        perm = order[d] if order else list(range(24))
        for slot, h in enumerate(perm):
            acc[slot] += hv[h]
    n = len(days)
    return {h: acc[h]/n for h in range(24)}

def se(v):
    n=len(v); m=sum(v)/n
    return math.sqrt(sum((x-m)**2 for x in v)/(n-1)/n)

def run_null(days, obs, gen, trials, seed=SEED):
    """귀무 루프 하나. 자기검정도 이 함수를 쓴다 — 별도 루프를 만들면 안 된다."""
    rng = random.Random(seed)
    null = [excess(mean_profile(days, gen(rng))) for _ in range(trials)]
    p = (sum(1 for v in null if v >= obs) + 1) / (trials + 1)
    return null, p


def synth(spikes):
    """손계산 가능한 합성 데이터. 기본 100, 지정한 시각만 다른 값."""
    d = {f"d{i}": {h: 100.0 for h in range(24)} for i in range(3)}
    for k in d:
        for h, v in spikes.items():
            d[k][h] = v
    return d


if __name__ == "__main__":
    days = load(sys.argv[1])
    print(f"  여름 평일 완전한 날: {len(days)}일")
    obs_prof = mean_profile(days)
    obs = excess(obs_prof)
    print(f"  관측 초과: {obs:+.2f} g  (off 최악 {max(obs_prof[h] for h in OFF):.1f} "
          f"- on 최악 {max(obs_prof[h] for h in ON):.1f})")

    shuffle_gen = lambda r: {d: r.sample(range(24), 24) for d in days}
    null, p = run_null(days, obs, shuffle_gen, TRIALS)
    null_sorted = sorted(null)
    mean_null = sum(null) / len(null)
    sd = math.sqrt(sum((v - mean_null) ** 2 for v in null) / (len(null) - 1))
    p_se = math.sqrt(p * (1 - p) / TRIALS)
    print(f"  귀무 평균 초과: {mean_null:+.2f} g ± {se(null):.3f}  (구간 크기 비대칭만으로 생기는 값)")
    print(f"  귀무 5~95 %: {null_sorted[int(.05*TRIALS)]:+.2f} ~ {null_sorted[int(.95*TRIALS)]:+.2f} g")
    print(f"  p = {p:.3f} ± {p_se:.3f}   ({TRIALS}회 순열, 몬테카를로 표준오차)")
    print()

    # A' 라운드트립 — 아는 답이 있는 비항등 순열로 실제 코드 경로를 지난다.
    # 앞 판본은 sorted(집합)==sorted(집합) 이라 순열이기만 하면 항상 참이었고
    # mean_profile 도 excess 도 호출하지 않았다.
    rev = {d: list(range(23, -1, -1)) for d in days}
    rp = mean_profile(days, rev)
    okA = (all(abs(rp[h] - obs_prof[23 - h]) < 1e-9 for h in range(24))
           and any(abs(rp[h] - obs_prof[h]) > 1e-9 for h in range(24)))
    print(f"  자기검정 A — 역순 순열이 프로파일을 정확히 뒤집는가: {'통과' if okA else '실패'}")

    # B' 기지답 두 건 — 경계를 양쪽에서 친다. 한 건만 쓰면 OFF 누출과 ON 누출이
    # 서로 상쇄돼 정답이 그대로 나온다.
    b1 = excess(mean_profile(synth({20: 130.0, 13: 110.0, 18: 200.0})))
    b2 = excess(mean_profile(synth({20: 130.0, 13: 110.0, 10: 125.0})))
    okB = abs(b1 - 20.0) < 1e-9 and abs(b2 - 20.0) < 1e-9
    print(f"  자기검정 B — 합성 데이터에서 구간 정의가 맞는가: {'통과' if okB else '실패'}"
          f"  (기대 20.0 / 20.0, 실제 {b1:.1f} / {b2:.1f})")

    # C 귀무 분포가 퍼져 있는가 — 셔플이 실제로 일어나야 한다
    print(f"  자기검정 C — 귀무 분포가 퍼져 있는가: {'통과' if sd > 0.1 else '실패'}"
          f"  (표준편차 {sd:.3f})")

    # D' 진짜 사보타주 — **같은 run_null 을** 항등 순열로 돌린다.
    # 앞 판본은 별도 루프를 만들어서, 진짜 귀무가 망가져도 자기 루프만 보고 통과했다.
    _, p_ident = run_null(days, obs, lambda r: {d: list(range(24)) for d in days}, 400)
    _, p_real = run_null(days, obs, shuffle_gen, 400)
    okD = p_real < 0.05 < p_ident
    print(f"  자기검정 D — 셔플을 지우면 검정이 붕괴하는가: {'통과' if okD else '실패'}"
          f"  (실제 {p_real:.4f} / 항등 {p_ident:.4f})")
