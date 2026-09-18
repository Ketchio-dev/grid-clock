"""web/ 용 데이터 추출 — 페이지에 수를 손으로 적지 않기 위한 다리.

`web/page.html` 은 **템플릿이고 숫자가 하나도 없다.** 이 스크립트가 분석에서 읽은 값을
`web/data.json` 으로 쓰고, 그것을 템플릿의 표시 자리에 **주입해** `web/index.html` 을 만든다.
그래서 index.html 은 서버 없이 파일로 열어도 동작하고(fetch 가 file:// 에서 막힌다),
분석이 바뀌면 다시 돌리지 않는 한 **페이지가 낡은 채로 남지 않는다** — 검사가 그걸 잡는다.

    python3 src/export_web.py data/fuel2026.xml

문서·그림·영상과 같은 규율이다: 수는 한 곳(스크립트 출력)에서만 나온다.
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_ieso import local_rows
from ontario import summer_weekday, winter_weekday, TOU_HOLIDAYS_2026

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
MARK_OPEN, MARK_CLOSE = "/*DATA_START*/", "/*DATA_END*/"

EF_GAS = 490.0                       # g CO2 per kWh of gas generation (표시용 환산에만 쓴다)
APPLIANCES = {"dryer": 3.0, "dishwasher": 1.5, "washer": 0.9, "EV charge": 7.0}


def tou(h):
    if h >= 19 or h < 7:  return "off-peak", 9.8
    if 11 <= h < 17:      return "on-peak", 20.3
    return "mid-peak", 15.7


def ulo(h):
    if h >= 23 or h < 7:  return "ultra-low", 3.9
    if 16 <= h < 21:      return "on-peak", 39.1
    return "mid-peak", 15.7


def season_profile(path, keep):
    """시간별 가스 비중(%) 과 밤별 원자료. 평균만 내고 끝내지 않는다 —
    페이지가 '밤마다 이득이 나는가'를 말하려면 밤별이 필요하다."""
    acc, n = defaultdict(float), defaultdict(int)
    nights = defaultdict(dict)
    days = set()
    for day, hour, mix in local_rows(path):
        if not keep(day):
            continue
        tot = sum(mix.values())
        if tot <= 0:
            continue
        h = hour
        share = mix.get("GAS", 0.0) * 100.0 / tot
        acc[h] += share
        n[h] += 1
        nights[day][h] = share
        days.add(day)
    prof = {h: acc[h] / n[h] for h in sorted(acc) if n[h]}
    return prof, nights, sorted(days)


def quantile(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    i = q * (len(s) - 1)
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("사용법: python3 src/export_web.py data/fuel2026.xml")
    path = sys.argv[1]

    summer, s_nights, s_days = season_profile(path, summer_weekday)
    winter, _w_nights, w_days = season_profile(path, winter_weekday)
    if not summer:
        raise SystemExit("여름 평일 데이터가 없다")

    cheap = [h for h in summer if tou(h)[0] == "off-peak"]
    hi_h = max(cheap, key=lambda h: summer[h])
    lo_h = min(cheap, key=lambda h: summer[h])
    peak_hours = [h for h in summer if tou(h)[0] == "on-peak"]
    peak_h = max(peak_hours, key=lambda h: summer[h])

    # 밤별: 저녁(19시)에 돌리기 vs 가장 깨끗한 off-peak 시각에 돌리기
    gains = []
    for day in s_days:
        v = s_nights[day]
        if 19 in v and lo_h in v:
            gains.append(v[19] - v[lo_h])
    wins = sum(1 for g in gains if g > 0)

    data = {
        "source": {
            "dataset": "IESO Generator Output by Fuel Type Hourly",
            "url": "https://reports-public.ieso.ca/public/GenOutputbyFuelHourly/",
            "note": "gas share of generation. no emission factor is used for the ordering.",
            "ef_gas_g_per_kwh": EF_GAS,
            "holidays_excluded": [str(d) for d in sorted(TOU_HOLIDAYS_2026)],
        },
        "population": {
            "summer_weekdays": len(s_days),
            "winter_weekdays": len(w_days),
            "first_day": s_days[0] if s_days else None,
            "last_day": s_days[-1] if s_days else None,
        },
        "hours": [
            {
                "hour": h,
                "summer_gas_pct": round(summer[h], 4),
                "winter_gas_pct": round(winter[h], 4) if h in winter else None,
                "tou": tou(h)[0], "tou_cents": tou(h)[1],
                "ulo": ulo(h)[0], "ulo_cents": ulo(h)[1],
            }
            for h in range(24) if h in summer
        ],
        "headline": {
            "cheap_bracket": "9.8c off-peak",
            "cheap_hours": len(cheap),
            "dirtiest_cheap_hour": hi_h,
            "dirtiest_cheap_pct": round(summer[hi_h], 4),
            "cleanest_cheap_hour": lo_h,
            "cleanest_cheap_pct": round(summer[lo_h], 4),
            "ratio": round(summer[hi_h] / summer[lo_h], 4),
            "spread_pp": round(summer[hi_h] - summer[lo_h], 4),
            "dearest_bracket_peak_hour": peak_h,
            "dearest_bracket_peak_pct": round(summer[peak_h], 4),
            "crossover_pp": round(summer[hi_h] - summer[peak_h], 4),
        },
        "per_night": {
            "n": len(gains),
            "wins": wins,
            "win_pct": round(wins * 100.0 / len(gains), 2) if gains else None,
            "worst_pp": round(min(gains), 2) if gains else None,
            "p10_pp": round(quantile(gains, 0.10), 2) if gains else None,
            "median_pp": round(quantile(gains, 0.50), 2) if gains else None,
            "p90_pp": round(quantile(gains, 0.90), 2) if gains else None,
            "best_pp": round(max(gains), 2) if gains else None,
        },
        "appliances": APPLIANCES,
        "honesty": {
            # 제품 안에 들어가는 반박. README 에만 두면 아무도 안 읽는다.
            "timer": f"A plug-in timer set to {lo_h}:00 gets you the same hour. "
                     f"This page is the reason to set one, not a replacement for it.",
            "resolution": "Dropping four statutory holidays moved our best hour by one. "
                          "We recommend a window, not a clock reading.",
            "metric": "Gas share, measured. Not emissions, not marginal emissions.",
        },
    }

    os.makedirs(WEB, exist_ok=True)
    json.dump(data, open(os.path.join(WEB, "data.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    tpl_path = os.path.join(WEB, "page.html")
    if not os.path.exists(tpl_path):
        print(f"  web/data.json 작성 ({len(data['hours'])}시간). 템플릿이 없어 index.html 은 건너뛴다")
        return
    tpl = open(tpl_path, encoding="utf-8").read()
    if MARK_OPEN not in tpl or MARK_CLOSE not in tpl:
        raise SystemExit(f"템플릿에 {MARK_OPEN} ... {MARK_CLOSE} 표시가 없다")
    head, rest = tpl.split(MARK_OPEN, 1)
    _old, tail = rest.split(MARK_CLOSE, 1)
    out = head + MARK_OPEN + "\nconst DATA = " + json.dumps(data, ensure_ascii=False) + ";\n" + MARK_CLOSE + tail
    open(os.path.join(WEB, "index.html"), "w", encoding="utf-8").write(out)
    print(f"  web/data.json + web/index.html 작성 "
          f"({len(data['hours'])}시간 · 여름 평일 {len(s_days)}일 · "
          f"밤별 {wins}/{len(gains)})")


if __name__ == "__main__":
    main()
