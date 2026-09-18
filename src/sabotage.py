"""검사가 살아 있는지 측정한다. 통과 개수는 품질 지표가 아니다.

각 사보타주는 코드나 문서에 **진짜 고장**을 하나 심고, `check_demo.py` 를 돌린 뒤,
**지정된 검사가 BAD 로 바뀌었는가**를 본다. 원본은 항상 복원된다.

두 가지를 같이 본다:
  1. 검출률 — 심은 고장을 검사가 잡는가
  2. **분모 불변** — 어떤 고장에도 검사 개수가 줄지 않는가.
     앞 판본은 검사가 조건문 안에 있어 실패 시 통째로 사라졌고,
     10/10 -> 6/9 -> 3/9 가 "9/9 통과"로 읽혔다.

**놓침(미검출)은 두 가지 뜻이다. 어느 쪽인지 반드시 가려야 한다:**
  (a) 검사가 죽었다, 또는
  (b) **심은 것이 애초에 고장이 아니었다.**
실제로 겪었다. `better = [h for h in ahead if c[h] < c[now_h]]` 를 `better = list(ahead)`
로 바꿔도 검사가 통과했는데, 검사가 죽어서가 아니라 `min` 이 전체 최소를 그대로 돌려주어
"지금보다 더러운 시각을 권고하지 않는다"가 여전히 참이었기 때문이다. 동작을 바꾸지 않는
변이는 사보타주가 아니다. 그래서 지금은 비교 방향을 뒤집는다.
기본 가정을 "검사가 죽었다"로 두면 멀쩡한 검사를 고치게 된다.

사용:  python3 src/sabotage.py
"""
import atexit, hashlib, io, os, re, shutil, signal, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["README.md", "src/baseline.py", "src/chart.py", "src/card.py",
         "src/align8.py", "src/scale.py", "src/parse_ieso.py",
         "src/sabotage.py", "submission/video-script.md",
         "VERIFICATION.md", "src/determinism.py"]

# 파일을 통째로 치우는 사보타주. 문자열 치환으로는 "파일이 없다"를 만들 수 없다.
DATA_REL = os.path.join("data", "fuel2026.xml")

# (설명, 파일, 찾을 문자열, 바꿀 문자열, BAD 가 되어야 할 검사 이름의 일부)
#
# 주의: 원본 파일에 실제로 있는 문자열이어야 한다. 없으면 "무효"로 보고하고 종료코드 1 이다 —
# 조용히 건너뛰면 검출률이 부풀려진다.
SABS = [
    ("차트가 최고/최저 시각을 뒤바꿔 보고", "src/chart.py",
     "bad, w, b, onmax = svg(c, FIG)", "bad, b, w, onmax = svg(c, FIG)",
     "가장 높은 시각"),
    ("차트가 비율을 절반으로 보고", "src/chart.py",
     "비율 {c[w]/c[b]:.2f}배", "비율 {c[w]/c[b]*0.5:.2f}배",
     "출력된 비율"),
    ("차트가 파일을 쓰지 않음(옛 그림이 남는다)", "src/chart.py",
     'open(out,"w",encoding="utf-8").write("\\n".join(s))', 'pass',
     "새로 쓰였다"),
    ("차트가 껍데기만 남은 SVG 를 씀", "src/chart.py",
     '"\\n".join(s))', '"\\n".join(s[:1] + s[-1:]))',
     "chart.svg 가 유효하고"),
    ("요금 구간을 틀리게 정의(19시를 mid-peak 로)", "src/chart.py",
     "for h in list(range(19,24))+list(range(0,7))",
     "for h in list(range(20,24))+list(range(0,7))",
     "요금 구간 정의"),
    ("카드의 비교 방향이 뒤집힘 (< 가 > 로)", "src/card.py",
     "better = [h for h in ahead if c[h] < c[now_h]]",
     "better = [h for h in ahead if c[h] > c[now_h]]",
     "더 더러운 시각을 권고하지"),
    ("README 타이머 행의 수치를 조작", "README.md",
     r"re:(timer set to 2 a\.m\.\*{0,2} \| [^|]*\| \*{0,2})\d+\.\d+ %",
     r"\g<1>**18.50 %", "타이머 비교표"),
    ("README 헤드라인 표의 최악 시각 수치를 조작", "README.md",
     r"re:(\| \d+ p\.m\. \| )\*\*\d+\.\d+ %\*\*( \| 9\.8)", r"\g<1>**18.50 %**\g<2>",
     "헤드라인 표"),
    ("README 사이클 손해 수치를 조작", "README.md",
     r"re:costs \*\*\d+\.\d+ pp\*\* — under a third of", "costs **9.999 pp** — under a third of",
     "타이머 비교표"),
    # 그림은 check_demo 가 다시 그리므로 SVG 를 직접 고쳐도 덮어써진다. **생성기**를 겨냥한다.
    # 대본은 사람이 카메라 앞에서 읽는다. 낡은 수가 남으면 못 되돌린다.
    ("영상 대본의 수치를 낡게 만듦", "submission/video-script.md",
     r"re:p equals \d+\.\d+", "p equals 0.9999", "제출 문서"),
    # 밤별 승률을 100% 로 부풀리는 것 — 가장 유혹적인 거짓말이다.
    ("README 의 밤별 승률을 부풀림", "README.md",
     r"re:\*\*\d+ / \d+ \(\d+\.\d+ %\)\*\*", "**92 / 92 (100.0 %)**",
     "나머지 수치 주장"),
    ("카드가 표본 일수를 거짓으로 그림", "src/card.py",
     "Mean of {N_DAYS} summer weeknights", "Mean of 999 summer weeknights",
     "나머지 수치 주장"),
    ("차트가 비율을 거짓으로 그림", "src/chart.py",
     "varies {c[worst]/c[best]:.3f}x", "varies 9.999x",
     "나머지 수치 주장"),
    # 감사 이력을 부록으로 옮겼으니 부록도 결속 대상이다 — 옮긴 수치가 거기서 썩으면 안 된다.
    ("부록의 척도 스윕 수치를 조작", "VERIFICATION.md",
     r"re:monotonically\s*\n?\s*\(\d+\.\d+ → \d+\.\d+\)", "monotonically\n  (9.999 → 0.001)",
     "나머지 수치 주장"),
    ("부록의 p값을 조작", "VERIFICATION.md",
     r"re:permutation test gave p = \d+\.\d+", "permutation test gave p = 0.9999",
     "p값 두 개가"),
    ("README 겨울 표의 비율을 조작(이전엔 어떤 검사도 안 읽던 줄)", "README.md",
     r"re:(\| Winter \(Nov[^|]*\|[^|]*\|[^|]*\| )\d+\.\d+×", r"\g<1>9.999×",
     "나머지 수치 주장"),
    ("README 교차 여유(가장 약한 문장)를 조작", "README.md",
     r"re:= \d+\.\d+ pp\*\*\. The perturbation", "= 5.00 pp**. The perturbation", "헤드라인 표"),
    ("README 머리 요약문의 범위를 조작", "README.md",
     r"re:\*\*\d+\.\d+ % to \d+\.\d+ %\*\*", "**10.00 % to 99.00 %**",
     "헤드라인 표"),
    ("README 의 우리 수치를 조작", "README.md",
     r"re:(Grid Clock's recommendation \| [^|]+\| \*{0,2})\d+\.\d+ %",
     r"\g<1>17.00 %", "타이머 비교표"),
    ("README 제목의 타이머 비율을 조작", "README.md",
     r"re:## A \$12 timer captures \d+\.\d+ % of this",
     "## A $12 timer captures 50.0 % of this", "타이머 비교표"),
    ("README 의 '밤의 비율' 을 조작", "README.md",
     r"re:\*\*\d+\.\d+ % of nights\*\*", "**40.0 % of nights**", "밤의 비율"),
    ("baseline 이 타이머를 2시가 아닌 4시로 평가", "src/baseline.py",
     '("timer set to 2 a.m.",        2, g[2],', '("timer set to 2 a.m.",        4, g[4],',
     "타이머 비교표"),
    ("baseline 에서 권고 표식을 제거", "src/baseline.py",
     'mark = "  <- what we recommend" if h == g_best else ""', 'mark = ""',
     "밤의 비율"),
    ("README 헤드라인 격차를 조작", "README.md",
     r"re:The \d+\.\d+ pp is an \*\*opportunity", "The 9.00 pp is an **opportunity",
     "헤드라인 격차"),
    ("부록의 8시간 흔들림 상한을 조작", "VERIFICATION.md",
     r"re:swings it from \u2212\d+\.\d+ to \+\d+\.\d+",
     "swings it from \u22128.6 to +9.9", "8시간 창 흔들림"),
    ("align8 의 동수 처리를 옛 버그로 되돌림(해시 순서 의존)", "src/align8.py",
     'best = max(sorted(set(labs)), key=labs.count)',
     'best = max(set(labs), key=labs.count)',
     "순서 의존 패턴이 없다"),
    # 새 스크립트를 재현성 목록에 안 넣는 실수 — 실제로 replay.py 가 그랬다.
    # **리터럴로 쓰면 목록이 자랄 때마다 조용히 무효가 된다** — export_web.py 를 더한 날
    # 이 사보타주가 "무효"로 찍혔다. 마지막 항목을 정규식으로 겨냥해 목록에 따라간다.
    ("determinism 목록에서 마지막 스크립트를 뺌", "src/determinism.py",
     r're:,\s*"[a-z_]+\.py"\]', ']',
     "순서 의존 패턴이 없다"),
    ("scale 의 동수 처리를 옛 버그로 되돌림", "src/scale.py",
     'top = max(sorted(set(labs)), key=labs.count)',
     'top = max(set(labs), key=labs.count)',
     "순서 의존 패턴이 없다"),
    # --- 여태 한 번도 겨냥되지 않던 검사 8개. 사보타주가 없는 검사는 죽어 있어도 모른다. ---
    ("파서를 실패시킴", "src/parse_ieso.py",
     'print(f"  시간 레코드: {n:,}  (현지 시각으로 변환됨)")', 'raise SystemExit(2)',
     "파서가 종료 코드 0"),
    ("파서가 레코드 수를 10분의 1로 보고", "src/parse_ieso.py",
     'print(f"  시간 레코드: {n:,}  (현지 시각으로 변환됨)")', 'print(f"  시간 레코드: {n//10:,}  (현지 시각으로 변환됨)")',
     "시간 레코드가 6,000개 이상"),
    ("차트 스크립트를 실패시킴", "src/chart.py",
     "    c = carbon(sys.argv[1])", "    raise SystemExit(4)\n    c = carbon(sys.argv[1])",
     "차트 스크립트가 종료 코드 0"),
    ("차트가 최저 시각을 엉뚱하게 보고", "src/chart.py",
     "최저 {b}시 {c[b]:.1f} g", "최저 {(b+5)%24}시 {c[b]:.1f} g",
     "가장 낮은 시각이 심야"),
    ("차트 주석의 최선 시각 표기를 어긋나게", "src/chart.py",
     'f"{best}:00 · {c[best]:.1f}% gas · 9.8c, same price"',
     'f"{(best+2)%24}:00 · {c[best]:.1f}% gas · 9.8c, same price"',
     "차트 주석의 최악"),
    ("카드가 껍데기 SVG 를 씀", "src/card.py",
     's.append(\'</svg>\')', 's = [s[0], \'</svg>\']',
     "card.svg 가 유효하고"),
    ("카드가 6시에 죽음", "src/card.py",
     "def card(c, now_h, appliance, out):",
     "def card(c, now_h, appliance, out):\n    assert now_h != 6, 'sabotage'",
     "카드가 0·6·12·18·20·23시"),
    ("사보타주 하나의 겨냥 대상을 존재하지 않는 검사로 바꿈", "src/sabotage.py",
     '"파서가 종료 코드 0"),', '"존재하지 않는 검사 이름"),',
     "모든 검사가 최소 하나의"),
    # --- Devpost 결속. 문서 검사가 소수만 훑어서 "3 a.m." 같은 정수는 안 보였다. ---
    ("Devpost 가 다른 시각을 권고하게", "submission/devpost.md",
     r"re:run it at \d+ a\.m\. tonight", "run it at 5 a.m. tonight",
     "Devpost 의 권고 시각이"),
    ("Devpost 의 겨울 비율을 옛 값으로 되돌림", "submission/devpost.md",
     r"re:2 a\.m\., 20\.04 % \| 1\.178×", "2 a.m., 19.98 % | 1.180×",
     "Devpost 의 겨울 행이"),
    ("README 의 검사 개수를 부풀림", "README.md",
     r"re:\d+ checks run on the path", "99 checks run on the path",
     "검사·사보타주 개수가"),
    ("카드가 파일을 쓰지 않음(옛 카드가 남는다)", "src/card.py",
     'open(out,"w",encoding="utf-8").write("\\n".join(s))', 'pass',
     "카드가 이번 실행에서 새로 쓰였다"),
    ("baseline 을 즉시 실패시킴", "src/baseline.py",
     "import sys, datetime, statistics", "import sys, datetime, statistics\nraise SystemExit(3)",
     "baseline.py 가 종료 코드 0"),
    ("시계 변환을 꺼서 IESO 시각을 그대로 현지 시각으로 쓴다", "src/parse_ieso.py",
     "    off = toronto_offset_hours(start_est.astimezone(dt.timezone.utc))",
     "    off = -5",
     "시계 변환 기지답 시험"),
    ("분석 스크립트가 원시 시각을 다시 쓴다", "src/compare.py",
     "    acc[hour] += mix.get(\"GAS\", 0.0) * 100.0 / tot",
     "    acc[hour - 1] += mix.get(\"GAS\", 0.0) * 100.0 / tot",
     "바꾸지 않고 쓰는 곳이 없다"),
    ("README 가 '앞 몇 시간'을 **거짓이 되는 수**로 적는다", "README.md",
     "The four dirtiest hours of those twelve are the first four",
     "The eight dirtiest hours of those twelve are the first eight",
     "가장 더러운 앞 N시간"),
    ("PNG 출처 해시를 옛 것으로 되돌린다", "figures/.png-from.json",
     r"re:\"sha\": \"[0-9a-f]{16}\"", '"sha": "deadbeefdeadbeef"',
     "PNG 가 SVG 보다 낡지 않았다"),
    ("VERIFICATION.md 의 검사 개수를 옛 값으로 되돌린다", "VERIFICATION.md",
     r"re:#\s*\d+ checks on the path", "# 27 checks on the path",
     "어느 문서도 검사·사보타주 개수를"),
    ("Devpost 산문의 겨울 어긋남을 0으로 되돌린다", "submission/devpost.md",
     "**Two misaligned hours.**", "**Zero misaligned hours.**",
     "겨울 **산문**이 winter 출력과"),
    ("Devpost 제목의 승률을 부풀린다", "submission/devpost.md",
     r"re:## Does it work on a given night\? \d+ % of them\.",
     "## Does it work on a given night? 86 % of them.",
     "'밤마다 되는가' 제목이 replay 출력과"),
]

def check():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "src", "check_demo.py")],
                       capture_output=True, text=True, timeout=900)
    m = re.search(r"(\d+)/(\d+) 데모", r.stdout)
    return r.stdout, (int(m.group(1)), int(m.group(2))) if m else (None, None)

# **복원 목록은 손으로 관리하지 않는다.** SABS 가 건드리는 파일에서 유도한다.
# 실제로 이걸 어겼다: Devpost 를 겨냥하는 사보타주 둘을 더했는데 FILES 에 넣지 않아
# **저장소가 사보타주된 상태로 남았다.** 검사는 그 뒤로도 계속 BAD 를 찍었고,
# 나는 그게 사보타주의 잔해인 줄 모르고 "검사가 실패한다"고 읽을 뻔했다.
# 두 손 목록은 서로를 검증하지 못한다 — 한쪽은 다른 쪽에서 나와야 한다.
_targeted = {f for _d, f, _o, _n, _m in SABS}
_missing = sorted(_targeted - set(FILES))
if _missing:
    print(f"  복원 목록에 없던 사보타주 대상 {len(_missing)}개를 자동으로 넣는다: {_missing}")
FILES = sorted(set(FILES) | _targeted)

bak = tempfile.mkdtemp(prefix="gridclock-sab-")
for f in FILES:
    d = os.path.join(bak, os.path.dirname(f))
    os.makedirs(d, exist_ok=True)
    shutil.copy2(os.path.join(ROOT, f), os.path.join(bak, f))
def restore():
    for f in FILES:
        shutil.copy2(os.path.join(bak, f), os.path.join(ROOT, f))


def _digests():
    d = {}
    for f in FILES:
        p_ = os.path.join(ROOT, f)
        if os.path.exists(p_):
            d[f] = hashlib.sha1(open(p_, "rb").read()).hexdigest()
    return d


# 중간에 죽으면 저장소가 **망가진 채로 남는다.** 실제로 그렇게 됐다 —
# 이 스크립트를 kill 했더니 README 에 조작된 +9.9 가 그대로 남아 있었고,
# 다음 check_demo 가 그걸 잡아냈다(잡지 못했다면 그대로 촬영했을 것이다).
atexit.register(restore)
for _sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(_sig, lambda *_: sys.exit(130))

# 실행 중 저장소를 건드리면 복원이 그 편집을 **조용히 되돌린다.**
# 실제로 겪었다 — 돌고 있는 줄 모르고 README 에 한 절을 추가했다가 통째로 날아갔고,
# 그 사이에 돌린 check_demo 는 사보타주된 중간 상태를 보고 있었다.
_START_DIGESTS = _digests()

_T0 = time.time()

print("\n  대조군 — 아무것도 망가뜨리지 않았을 때")
print(f"  (도는 동안 {', '.join(FILES)} 를 편집하지 마라 — 복원이 되돌린다)")
out, (passed, denom) = check()
if passed is None or passed != denom:
    print(f"    대조군이 통과하지 않는다 ({passed}/{denom}). 사보타주 결과는 의미가 없다.")
    sys.exit(2)
print(f"    {passed}/{denom} 통과. 기준 분모 = {denom}\n")

caught, shrunk, invalid = 0, [], []
for desc, f, old, new, must_fail in SABS:
    p = os.path.join(ROOT, f)
    s = io.open(p, encoding="utf-8").read()
    # `re:` 로 시작하면 정규식이다. 코드에서 세는 수를 겨냥하는 사보타주는 리터럴로 쓰면
    # 그 수가 바뀔 때마다 조용히 무효가 된다 — 실제로 "# 22 checks" 가 그렇게 낡았다.
    if old.startswith("re:"):
        pat = old[3:]
        if not re.search(pat, s):
            invalid.append(desc)
            print(f"  무효  {desc}\n        정규식이 맞는 곳이 없다: {pat}")
            continue
        io.open(p, "w", encoding="utf-8").write(re.sub(pat, new, s, count=1))
        out, (p_, d_) = check()
        restore()
        line = next((l for l in out.splitlines() if must_fail in l), None)
        hit = bool(line) and line.strip().startswith("BAD")
        caught += hit
        if d_ != denom:
            shrunk.append((desc, d_))
        print(f"  {'검출' if hit else '놓침'}  {desc}")
        print(f"        {p_}/{d_}" + (f"  <- 분모가 {denom} 에서 변했다!" if d_ != denom else "")
              + f"   {line.strip()[:96] if line else '해당 검사 줄을 찾지 못함'}")
        continue
    if old not in s:
        invalid.append(desc)
        print(f"  무효  {desc}\n        심을 자리를 못 찾았다 — 이 사보타주는 코드와 어긋났다")
        continue
    io.open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
    out, (p_, d_) = check()
    restore()
    line = next((l for l in out.splitlines() if must_fail in l), None)
    hit = bool(line) and line.strip().startswith("BAD")
    caught += hit
    if d_ != denom:
        shrunk.append((desc, d_))
    print(f"  {'검출' if hit else '놓침'}  {desc}")
    print(f"        {p_}/{d_}" + (f"  <- 분모가 {denom} 에서 변했다!" if d_ != denom else "")
          + f"   {line.strip()[:96] if line else '해당 검사 줄을 찾지 못함'}")

# 파일 자체를 치우는 사보타주 하나. "원본 데이터가 있다" 는 치환으로 못 만든다.
_data = os.path.join(ROOT, DATA_REL)
_moved = _data + ".sabotaged"
extra_total = 0
if os.path.exists(_data):
    extra_total = 1
    os.rename(_data, _moved)
    try:
        out, (p_, d_) = check()
    finally:
        os.rename(_moved, _data)
    line = next((l for l in out.splitlines() if "원본 데이터가 있다" in l), None)
    hit = bool(line) and line.strip().startswith("BAD")
    caught += hit
    if d_ != denom:
        shrunk.append(("원본 데이터를 치움", d_))
    print(f"  {'검출' if hit else '놓침'}  원본 데이터 파일을 치움")
    print(f"        {p_}/{d_}" + (f"  <- 분모가 {denom} 에서 변했다!" if d_ != denom else "")
          + f"   {line.strip()[:96] if line else '해당 검사 줄을 찾지 못함'}")
else:
    print("  무효  원본 데이터 파일이 애초에 없다")
    invalid.append("원본 데이터를 치움")

# 끝나고 나서, 시작 시점과 달라진 관리 파일이 있으면 그건 **내가 덮어쓴 남의 편집**이다.
_end = _digests()
_clobbered = [f for f in FILES if _START_DIGESTS.get(f) != _end.get(f)]
if _clobbered:
    print(f"\n  [경고] 실행 중에 바뀐 관리 파일이 있고, 복원이 그것을 되돌렸다: {_clobbered}")
    print(f"         도는 동안 편집한 내용이 있다면 다시 적용해야 한다.")

n = len(SABS) + extra_total
# 걸린 시간을 **도구가 찍는다.** 문서에 "약 6분"이라 적어 뒀는데 검사가 무거워지면서
# 거짓이 됐다. 셀 수 없으면 적지 않고, 셀 수 있으면 도구가 찍는다.
print(f"\n  {n}건 · {time.time() - _T0:.0f}초 걸림 ({(time.time() - _T0)/60:.1f}분)")
print(f"  {caught}/{n} 검출", end="")
print(f" · 분모 {denom} 고정" if not shrunk else f" · 분모가 변한 사보타주 {len(shrunk)}건: {shrunk}")
if invalid:
    print(f"  무효 사보타주 {len(invalid)}건 — 코드가 바뀌었는데 이 파일이 따라가지 않았다: {invalid}")
sys.exit(0 if caught == n and not shrunk and not invalid else 1)
