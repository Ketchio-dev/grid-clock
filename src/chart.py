"""24시간 스트립 SVG — 의존성 0. 회색 띠=요금, 빨간 선=탄소, 노랑=어긋남."""
import os, sys, datetime
from collections import defaultdict
from parse_ieso import local_rows
from ontario import summer_weekday

FIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures', 'chart.svg')
EF_GAS = 490.0
TOU = {**{h: ("off-peak", 9.8, "#e8e8e8") for h in list(range(19,24))+list(range(0,7))},
       **{h: ("mid-peak", 15.7, "#c0c0c0") for h in [7,8,9,10,17,18]},
       **{h: ("on-peak", 20.3, "#8f8f8f") for h in range(11,17)}}

def carbon(path):
    """가스 비중(%). 배출계수를 곱하지 않는다 — 발견이 계수와 무관하기 때문이다."""
    acc, n = defaultdict(float), defaultdict(int)
    for day, hour, mix in local_rows(path):
        if not summer_weekday(day): continue
        tot = sum(mix.values())
        if tot <= 0: continue
        acc[hour] += mix.get("GAS",0.0)*100.0/tot; n[hour] += 1
    return {h: acc[h]/n[h] for h in sorted(acc)}

def svg(c, out):
    W,H = 980,420; L,R,T,B = 64,24,52,64
    pw,ph = W-L-R, H-T-B
    lo,hi = 17.5, 26.5
    x = lambda h: L + pw*h/24
    y = lambda v: T + ph*(hi-v)/(hi-lo)
    onmax = max(v for h,v in c.items() if TOU[h][0]=="on-peak")
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="system-ui,-apple-system,Helvetica,sans-serif">',
       f'<rect width="{W}" height="{H}" fill="#fff"/>']
    # 요금 띠
    for h in range(24):
        s.append(f'<rect x="{x(h):.1f}" y="{T}" width="{pw/24:.1f}" height="{ph}" fill="{TOU[h][2]}"/>')
    # 어긋남: off-peak(최저가)인데 on-peak 최고보다 더러운 시간
    bad=[h for h in range(24) if TOU[h][0]=="off-peak" and c.get(h,0) > onmax]
    for h in bad:
        s.append(f'<rect x="{x(h):.1f}" y="{T}" width="{pw/24:.1f}" height="{ph}" fill="#ffd400" opacity="0.62"/>')
    # 격자
    for v in (18,20,22,24,26):
        s.append(f'<line x1="{L}" y1="{y(v):.1f}" x2="{W-R}" y2="{y(v):.1f}" stroke="#fff" stroke-width="1"/>')
        s.append(f'<text x="{L-10}" y="{y(v)+4:.1f}" font-size="12" fill="#666" text-anchor="end">{v}</text>')
    # 탄소 선
    pts=" ".join(f"{x(h)+pw/48:.1f},{y(c[h]):.1f}" for h in sorted(c))
    s.append(f'<polyline points="{pts}" fill="none" stroke="#d32020" stroke-width="3.2"/>')
    for h in sorted(c):
        s.append(f'<circle cx="{x(h)+pw/48:.1f}" cy="{y(c[h]):.1f}" r="2.6" fill="#d32020"/>')
    # 축
    for h in range(0,25,3):
        s.append(f'<text x="{x(h):.1f}" y="{H-B+20}" font-size="12" fill="#555" text-anchor="middle">{h}:00</text>')
    s.append(f'<text x="18" y="{T+ph/2:.0f}" font-size="12" fill="#555" '
             f'transform="rotate(-90 18 {T+ph/2:.0f})" text-anchor="middle">'
             f'gas share of generation (%)</text>')
    # 주석 두 개
    worst=max(c,key=c.get); best=min(c,key=c.get)
    for h,lab,dy in ((worst,f"{worst}:00 · {c[worst]:.1f}% gas · 9.8c, cheapest",-16),
                     (best,f"{best}:00 · {c[best]:.1f}% gas · 9.8c, same price",26)):
        s.append(f'<circle cx="{x(h)+pw/48:.1f}" cy="{y(c[h]):.1f}" r="6" fill="none" stroke="#111" stroke-width="2"/>')
        anc = "start" if h < 12 else "end"
        ox = 12 if h < 12 else -12
        s.append(f'<text x="{x(h)+pw/48+ox:.1f}" y="{y(c[h])+dy:.1f}" font-size="14" font-weight="600" fill="#111" text-anchor="{anc}">{lab}</text>')
    # 제목·범례
    s.append(f'<text x="{L}" y="26" font-size="17" font-weight="700" fill="#111">'
             f'One price, 9.8c. Gas share inside it varies {c[worst]/c[best]:.3f}x.</text>')
    s.append(f'<text x="{L}" y="44" font-size="13" fill="#555">'
             f'darker grey = dearer  ·  yellow = cheapest price, yet more gas than any hour of the dearest bracket</text>')
    s.append(f'<text x="{L}" y="{H-14}" font-size="12" fill="#777">'
             f'Ontario summer weekdays, statutory holidays excluded  ·  IESO hourly fuel mix 2026-01-01 to 09-13  ·  Toronto Hydro summer TOU  ·  no emission factor assumed</text>')
    s.append('</svg>')
    open(out,"w",encoding="utf-8").write("\n".join(s))
    return bad, worst, best, onmax

if __name__ == "__main__":
    c = carbon(sys.argv[1])
    bad, w, b, onmax = svg(c, FIG)
    print(f"  어긋남 시각(최저가인데 on-peak 최고보다 더러움): {bad}")
    print(f"  최고 {w}시 {c[w]:.1f} g / 최저 {b}시 {c[b]:.1f} g / 비율 {c[w]/c[b]:.2f}배")
    print(f"  on-peak 최고 {onmax:.1f} g")
    print(f"  chart.svg 작성 ({len(open(FIG).read()):,} bytes)")
