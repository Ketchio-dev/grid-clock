"""오늘 밤 카드 — 차트가 아니라 결정 한 장. 의존성 0.

ASTRA 가 지적한 것: 19개 후보 중 대부분이 그림 한 장으로 끝나는데,
만질 수 있는 산출물(파일·카드·규칙)이 Completion 지각에서 유리하다.
그래서 카드가 앞이고 차트는 근거로 뒤에 둔다.
"""
import os, sys, datetime
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday

FIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures', 'card.svg')
EF_GAS = 490.0
APPLIANCES = {"dryer": 3.0, "dishwasher": 1.5, "washer": 0.9}
def tou(h):
    if h >= 19 or h < 7:  return "off-peak", 9.8
    if 11 <= h < 17:      return "on-peak", 20.3
    return "mid-peak", 15.7
def ulo(h):
    if h >= 23 or h < 7:  return "ultra-low", 3.9
    if 16 <= h < 21:      return "on-peak", 39.1
    return "mid-peak", 15.7

N_DAYS = 0   # profile() 이 채운다. 그림에 박아 두면 방법론이 바뀔 때 그림만 낡는다 —
             # 공휴일 4일을 뺀 뒤에도 카드가 "96 nights" 라고 말하고 있었다.

def profile(path):
    global N_DAYS
    acc, n = defaultdict(float), defaultdict(int)
    days = set()
    for day, hour, mix in local_rows(path):
        if not summer_weekday(day): continue
        tot = sum(mix.values())
        if tot <= 0: continue
        days.add(day)
        acc[hour] += mix.get("GAS",0.0)*EF_GAS/tot; n[hour] += 1
    N_DAYS = len(days)
    return {h: acc[h]/n[h] for h in sorted(acc)}

def card(c, now_h, appliance, out):
    kwh = APPLIANCES[appliance]
    # 앞으로 24시간 중 지금보다 나은 시각. 없으면 "지금이 최선"이라고 말한다.
    # 앞 판본은 창을 다음날 07시로 끊어서, 새벽 3~6시에는 남은 시각이 전부
    # 지금보다 더러운데도 그중 최저를 권고했다 — 절감량이 음수가 되었다.
    ahead = [(now_h + k) % 24 for k in range(1, 25)]
    ahead = [h for h in ahead if h in c]
    better = [h for h in ahead if c[h] < c[now_h]]
    best = min(better, key=lambda h: c[h]) if better else now_h
    now_g, best_g = c[now_h]*kwh, c[best]*kwh
    tn, tp = tou(now_h); bn, bp = tou(best)
    un, up = ulo(now_h); ub, ubp = ulo(best)
    W,H = 620,356
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="system-ui,-apple-system,sans-serif">',
       f'<rect width="{W}" height="{H}" rx="14" fill="#111"/>',
       f'<text x="34" y="52" font-size="15" fill="#9aa">typical summer weeknight · one {appliance} load ({kwh} kWh)</text>',
       (f'<text x="34" y="106" font-size="40" font-weight="700" fill="#fff">run it now</text>'
        if best == now_h else
        f'<text x="34" y="106" font-size="40" font-weight="700" fill="#fff">run it at {best}:00</text>'),
       (f'<text x="34" y="140" font-size="16" fill="#8fd18f">cleanest hour in the next 24</text>'
        if best == now_h else
        f'<text x="34" y="140" font-size="16" fill="#8fd18f">{now_g-best_g:.0f} g CO₂ less than now ({now_h}:00)</text>'),
       f'<line x1="34" y1="166" x2="{W-34}" y2="166" stroke="#333"/>']
    rowsd=[("now, " + str(now_h) + ":00", f"{now_g:.0f} g", f"TOU {tp}¢ · ULO {up}¢", "#d86a6a"),
           (f"{best}:00",                 f"{best_g:.0f} g", f"TOU {bp}¢ · ULO {ubp}¢", "#8fd18f")]
    y=200
    for lab, g, price, col in rowsd:
        s.append(f'<text x="34" y="{y}" font-size="17" fill="#ccc">{lab}</text>')
        s.append(f'<text x="210" y="{y}" font-size="21" font-weight="700" fill="{col}">{g}</text>')
        s.append(f'<text x="330" y="{y}" font-size="15" fill="#999">{price}</text>')
        y += 38
    s.append(f'<text x="34" y="{H-70}" font-size="13" fill="#7a7a7a">'
             f'Both hours sit in the same TOU bracket, so price says nothing about this.</text>')
    s.append(f'<text x="34" y="{H-48}" font-size="13" fill="#7a7a7a">'
             f'Average-emissions basis. We do not claim a saving; on a marginal basis it is larger.</text>')
    # 표본 일수는 세어서 넣는다. 손으로 적으면 방법론이 바뀔 때 그림만 낡는다.
    s.append(f'<text x="34" y="{H-26}" font-size="13" fill="#7a7a7a">'
             f'Mean of {N_DAYS} summer weeknights (holidays excluded), not a forecast for tonight.</text>')
    s.append('</svg>')
    open(out,"w",encoding="utf-8").write("\n".join(s))
    return best, now_g, best_g, tp, bp

if __name__ == "__main__":
    c = profile(sys.argv[1])
    now = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    # 세 번째 인자로 출력 경로를 받는다. 검사의 시각 스윕이 **제출용 카드를 덮어쓰면 안 된다** —
    # 스윕의 마지막이 23시라 저장소에 남는 카드가 늘 23시(차이 38 g)가 됐다.
    # 제출용은 20시(차이 91 g)여야 한다. 검사는 임시 파일에 그린다.
    out = sys.argv[3] if len(sys.argv) > 3 else FIG
    b, ng, bg, tp, bp = card(c, now, "dryer", out)
    print(f"  now={now}시 → 권고 {b}시")
    print(f"  {now}시 {ng:.0f} g (TOU {tp}¢) → {b}시 {bg:.0f} g (TOU {bp}¢)")
    print(f"  차이 {ng-bg:.0f} g. 요금은 {'같다' if tp==bp else '다르다'} — 그래서 가격은 이걸 말해주지 않는다")
    print(f"  {os.path.basename(out)} 작성")
