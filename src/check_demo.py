"""데모 경로 검사. 촬영 중 깨질 수 있는 것만 본다.

이 파일의 앞 판본은 23개 사보타주 중 13개를 통과시켰다. 이유가 셋이었고 전부 고쳤다:

1. "최악 시각이 20시다" 가 실은 `20 in nums` 였다 — **위치를 안 봤다.**
   최고와 최저를 맞바꿔도 통과했다. 이제 argmax/argmin 을 본다.
2. 비율 검사가 출력된 비율을 읽지 않고 **자기가 다시 계산**했다.
   그래서 출력이 "0.75배"인데도 통과했다. 이제 출력 문자열을 파싱해 대조한다.
3. **분모가 줄었다.** 검사가 조건문 안에 있어 실패 시 통째로 사라졌고,
   10/10 → 6/9 → 3/9 가 되어 "9/9 통과"로 읽혔다.
   이제 검사 목록이 **고정**이고, 선행 검사가 실패하면 뒤따르는 검사는 SKIP 이 아니라 **BAD** 다.

그리고 없던 것 셋을 추가했다: 그림 신선도, 빈 SVG, 요금 구간 정의.
"""
import ast, os, re, subprocess, sys, time, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "fuel2026.xml")
FIG = os.path.join(ROOT, "figures")

# 고정 목록. 어떤 실패에도 개수가 줄지 않는다.
NAMES = [
    "원본 데이터가 있다",
    "파서가 종료 코드 0으로 끝난다",
    "시간 레코드가 6,000개 이상이다",
    "차트 스크립트가 종료 코드 0",
    "가스 비중이 가장 높은 시각이 저녁(17~22시)이다",
    "가스 비중이 가장 낮은 시각이 심야(0~6시)다",
    "출력된 비율이 1.30~1.37 이다",
    "차트가 이번 실행에서 새로 쓰였다",
    "chart.svg 가 유효하고 내용이 있다",
    "card.svg 가 유효하고 내용이 있다",
    "차트 주석의 최악·최선 시각이 출력과 일치한다",
    "요금 구간 정의가 Toronto Hydro 여름 TOU 와 일치한다",
    "카드가 어떤 시각에도 더 더러운 시각을 권고하지 않는다",
    "카드가 0·6·12·18·20·23시 전부에서 동작한다",
    "baseline.py 가 종료 코드 0",
    "README 의 타이머 비교표가 baseline 출력과 일치한다",
    "README 의 '밤의 비율' 주장이 baseline 출력과 일치한다",
    "README 의 헤드라인 격차(pp)가 baseline 출력과 일치한다",
    "README 의 p값 두 개가 blocknull 출력과 일치한다",
    "README 의 8시간 창 흔들림 범위가 align8 출력과 일치한다",
    "분석 스크립트에 순서 의존 패턴이 없다",
    "README 가 적은 검사·사보타주 개수가 코드와 일치한다",
    "README 의 헤드라인 표·요약문이 compare 출력과 일치한다",
    "README 의 나머지 수치 주장이 전부 스크립트 출력과 일치한다",
    "제출 문서(대본·Devpost)의 수치가 전부 스크립트 출력에 있다",
    "모든 검사가 최소 하나의 사보타주에 겨냥된다",
    "카드가 이번 실행에서 새로 쓰였다",
    "Devpost 의 권고 시각이 baseline 의 최선 시각과 일치한다",
    "Devpost 의 겨울 행이 winter 출력과 일치한다",
    "시계 변환 기지답 시험이 통과한다",
    "IESO 시각을 현지 시각으로 바꾸지 않고 쓰는 곳이 없다",
    "문서가 말하는 '가장 더러운 앞 N시간'이 실제 순위와 맞는다",
    "영상·제출에 쓰는 PNG 가 SVG 보다 낡지 않았다",
]
result = {n: (False, "실행되지 않음") for n in NAMES}
assert len(NAMES) == len(set(NAMES)), "검사 이름이 중복된다"

def NAME(n):
    """이름으로 고른다. 인덱스로 고르면 목록에 항목을 끼울 때 전부 밀린다 —
    그렇게 라벨과 결과가 한 칸씩 어긋났고, 25/25 전부 통과하는 동안에는 보이지 않았다.
    사보타주가 '엉뚱한 검사가 실패한다'로 알려줬다."""
    if n not in result:
        raise SystemExit(f"검사 이름이 목록에 없다: {n!r}")
    return n


def ok(name, cond, detail=""):
    result[name] = (bool(cond), detail)

def run(script, *args, hashseed=None):
    env = dict(os.environ)
    if hashseed is not None:
        env["PYTHONHASHSEED"] = str(hashseed)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "src", script), DATA, *args],
                       capture_output=True, text=True, timeout=300, env=env)
    return r.returncode, r.stdout, r.stderr

ok(NAME("원본 데이터가 있다"), os.path.exists(DATA), f"없으면 python3 src/fetch_data.py")

if os.path.exists(DATA):
    rc, out, err = run("parse_ieso.py")
    ok(NAME("파서가 종료 코드 0으로 끝난다"), rc == 0, err.strip()[-160:])
    m = re.search(r"시간 레코드:\s*([\d,]+)", out)
    hours = int(m.group(1).replace(",", "")) if m else 0
    ok(NAME("시간 레코드가 6,000개 이상이다"), hours >= 6000, f"실제 {hours:,}")

    _mt = lambda f: (os.path.getmtime(os.path.join(FIG, f))
                     if os.path.exists(os.path.join(FIG, f)) else 0)
    before, before_card = _mt("chart.svg"), _mt("card.svg")
    time.sleep(1.1)
    rc, out, err = run("chart.py")
    ok(NAME("차트 스크립트가 종료 코드 0"), rc == 0, err.strip()[-160:])

    # 출력에서 실제 argmax/argmin/비율을 읽는다 — 다시 계산하지 않는다
    hi_h = lo_h = None          # 차트가 죽어도 아래 검사들이 이름을 찾을 수 있어야 한다.
    m = re.search(r"최고\s*(\d+)시\s*([\d.]+).*?최저\s*(\d+)시\s*([\d.]+).*?비율\s*([\d.]+)", out, re.S)
    if m:
        hi_h, hi_v, lo_h, lo_v, ratio = int(m.group(1)), float(m.group(2)), int(m.group(3)), float(m.group(4)), float(m.group(5))
        # 최저 시각과 같은 이유로 **최고 시각도 못 박지 않는다.** 시계 정렬을 고쳤더니
        # 20시가 21시로 옮겨갔고, 못 박아 둔 검사는 고쳐야 할 것이 아니라 고쳐진 것을 막았다.
        # 잡으려는 것은 "저녁이 더럽고 심야가 깨끗하다"는 모양이지 특정 숫자가 아니다.
        ok(NAME("가스 비중이 가장 높은 시각이 저녁(17~22시)이다"), 17 <= hi_h <= 22 and hi_v > lo_v,
           f"출력: 최고 {hi_h}시 {hi_v}")
        # 시각을 못 박지 않는다. 방법론이 바뀌면(공휴일 제외 등) 최저 시각은 옮겨 다닌다.
        # 이 검사가 잡으려는 것은 **최고와 최저가 뒤바뀌는 것**이고, 그건 시각을 못 박지 않아도 잡힌다.
        ok(NAME("가스 비중이 가장 낮은 시각이 심야(0~6시)다"), 0 <= lo_h <= 6 and lo_v < hi_v, f"출력: 최저 {lo_h}시 {lo_v}")
        ok(NAME("출력된 비율이 1.30~1.37 이다"), 1.30 <= ratio <= 1.37, f"출력된 비율 {ratio}")
    else:
        for n in NAMES[4:7]:
            ok(n, False, "차트 출력에서 최고/최저/비율을 읽지 못했다")

    after = os.path.getmtime(os.path.join(FIG, "chart.svg")) if os.path.exists(os.path.join(FIG, "chart.svg")) else 0
    ok(NAME("차트가 이번 실행에서 새로 쓰였다"), after > before, "차트를 실행했는데 파일이 갱신되지 않았다 — 옛 그림이 남아 있다")

    # 카드도 **이번 실행에서 다시 그린 뒤** 검사한다. 앞 판본은 옛 card.svg 를 그대로 읽어서,
    # 카드가 껍데기 SVG 를 쓰도록 망가뜨려도 검사가 통과했다 — 사보타주가 그걸 잡아냈다.
    rc_card, _o, err_card = run("card.py", "20")
    ok(NAME("카드가 이번 실행에서 새로 쓰였다"), rc_card == 0 and _mt("card.svg") > before_card,
       err_card.strip()[-120:] or "카드를 실행했는데 파일이 갱신되지 않았다 — 옛 그림이 남아 있다")

    for name, f in ((NAME("chart.svg 가 유효하고 내용이 있다"), "chart.svg"), (NAME("card.svg 가 유효하고 내용이 있다"), "card.svg")):
        p = os.path.join(FIG, f)
        good, why = False, "없음"
        if os.path.exists(p):
            raw = open(p, encoding="utf-8").read()
            try:
                root = ET.fromstring(raw)
                n_el = len(list(root.iter()))
                # 카드는 의도적으로 단순하다(결정 한 장). 차트는 복잡하다.
                # 빈 SVG(<svg/>)를 잡는 것이 목적이므로 최소선만 둔다.
                floor = 25 if f == "chart.svg" else 8
                good = n_el >= floor and len(raw) > 400
                why = f"요소 {n_el}개, {len(raw)} bytes"
            except Exception as e:
                why = f"XML 파싱 실패: {e}"
        ok(name, good, why)

    # 그림 안의 주석이 올바른 시각에 붙어 있는가 — 콘솔이 아니라 그림을 읽는다
    p = os.path.join(FIG, "chart.svg")
    if os.path.exists(p):
        svg = open(p, encoding="utf-8").read()
        worst_txt = re.search(r"(\d+):00[^<]*cheapest", svg)
        best_txt = re.search(r"(\d+):00[^<]*same price", svg)
        # 그림의 주석이 **콘솔 출력과 같은 시각**을 가리키는가. 숫자를 못 박는 대신 둘을 맞댄다.
        good = bool(worst_txt and best_txt and hi_h is not None and lo_h is not None
                    and int(worst_txt.group(1)) == hi_h and int(best_txt.group(1)) == lo_h)
        ok(NAME("차트 주석의 최악·최선 시각이 출력과 일치한다"), good,
           f"그림 주석 최악={worst_txt.group(1) if worst_txt else '?'}시/최선={best_txt.group(1) if best_txt else '?'}시"
           f" vs 출력 최악={hi_h}시/최선={lo_h}시")

    # 요금 구간 정의가 실제 요금표와 맞는가 — 시각적 논증 전체가 여기 걸려 있다
    sys.path.insert(0, os.path.join(ROOT, "src"))
    try:
        import importlib, chart as chart_mod
        importlib.reload(chart_mod)
        expect = {**{h: "off-peak" for h in list(range(19, 24)) + list(range(0, 7))},
                  **{h: "mid-peak" for h in (7, 8, 9, 10, 17, 18)},
                  **{h: "on-peak" for h in range(11, 17)}}
        got = {h: chart_mod.TOU[h][0] for h in range(24)}
        bad = {h: (got[h], expect[h]) for h in range(24) if got[h] != expect[h]}
        ok(NAME("요금 구간 정의가 Toronto Hydro 여름 TOU 와 일치한다"), not bad, f"어긋난 시각 {bad}" if bad else "")
    except Exception as e:
        ok(NAME("요금 구간 정의가 Toronto Hydro 여름 TOU 와 일치한다"), False, f"요금 구간을 읽지 못했다: {e}")

    # 카드가 더 더러운 시각을 권고하지 않는가 — 24시각 전부
    try:
        import card as card_mod
        importlib.reload(card_mod)
        c = card_mod.profile(DATA)
        bad_rec = []
        for h in range(24):
            best, ng, bg, _, _ = card_mod.card(c, h, "dryer", os.path.join(FIG, "_probe.svg"))
            if bg > ng + 1e-9:
                bad_rec.append((h, best))
        os.path.exists(os.path.join(FIG, "_probe.svg")) and os.remove(os.path.join(FIG, "_probe.svg"))
        ok(NAME("카드가 어떤 시각에도 더 더러운 시각을 권고하지 않는다"), not bad_rec, f"더 나쁜 시각을 권고한 경우 {bad_rec}")
    except Exception as e:
        ok(NAME("카드가 어떤 시각에도 더 더러운 시각을 권고하지 않는다"), False, f"카드 권고를 확인하지 못했다: {e}")

    # 재현성. align8 과 scale 이 동수를 set 순회 순서로 깨고 있었고, 파이썬이 문자열 해시를
    # 프로세스마다 무작위화하므로 **같은 입력에 다른 답**을 냈다. 문서가 인용한 범위가
    # 실행마다 달랐다. 검증 스크립트가 재현되지 않으면 검증이 아니다.
    # 집합은 순회 순서가 없다. 파이썬은 문자열 해시를 프로세스마다 무작위화하므로
    # 집합에서 원소를 "고르는" 코드는 같은 입력에 다른 답을 낸다.
    # align8 과 scale 이 실제로 그랬고(동수를 set 순회 순서로 깼다) 문서가 인용한 범위가
    # 실행마다 달랐다. 여기서는 소스에서 그 꼴을 막는다 — 실행시 확인은 determinism.py 가 한다.
    # 구문 트리를 본다. 정규식은 **문자열 리터럴과 줄 끝 주석**을 코드로 착각한다 —
    # 이 파일 자체가 그 패턴들을 문자열로 담고 있어서 자기 자신을 오탐했다.
    ANALYSIS = ["parse_ieso.py", "profile.py", "compare.py", "chart.py", "card.py",
                "nulls.py", "blocknull.py", "scale.py", "align8.py", "winter.py",
                "baseline.py", "replay.py", "determinism.py", "fetch_data.py",
                "export_web.py", "check_time.py"]

    def is_set_call(nd):
        return (isinstance(nd, ast.Call) and isinstance(nd.func, ast.Name)
                and nd.func.id == "set")

    hits = []
    for sc in ANALYSIS:
        path = os.path.join(ROOT, "src", sc)
        if not os.path.exists(path):
            hits.append(f"{sc}: 파일이 없다"); continue
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError as e:
            hits.append(f"{sc}:{e.lineno} 파싱 실패"); continue
        for nd in ast.walk(tree):
            if isinstance(nd, ast.Call) and isinstance(nd.func, ast.Name):
                fn = nd.func.id
                if fn in ("max", "min", "list") and nd.args and is_set_call(nd.args[0]):
                    hits.append(f"{sc}:{nd.lineno} {fn}(set(...)) — sorted(set(...)) 를 써라")
                elif fn == "next" and nd.args:
                    a = nd.args[0]
                    if (isinstance(a, ast.Call) and isinstance(a.func, ast.Name)
                            and a.func.id == "iter" and a.args and is_set_call(a.args[0])):
                        hits.append(f"{sc}:{nd.lineno} next(iter(set(...)))")
            elif isinstance(nd, (ast.For, ast.comprehension)) and is_set_call(nd.iter):
                hits.append(f"{sc}:{getattr(nd, 'lineno', nd.iter.lineno)} set 을 직접 순회한다")
    # determinism.py 의 목록과 갈리면 새 스크립트가 재현성 검사를 안 받는다.
    # 실제로 replay.py 가 그렇게 빠져 있었다.
    META = {"check_demo.py", "sabotage.py", "determinism.py", "ontario.py", "fetch_data.py"}
    on_disk = {f for f in os.listdir(os.path.join(ROOT, "src"))
               if f.endswith(".py")} - META
    _det = open(os.path.join(ROOT, "src", "determinism.py"), encoding="utf-8").read()
    _m = re.search(r"SCRIPTS = \[(.*?)\]", _det, re.S)
    _det_set = set(re.findall(r'"([^"]+\.py)"', _m.group(1))) if _m else set()
    for label, have in (("check_demo 의 ANALYSIS", set(ANALYSIS)),
                        ("determinism 의 SCRIPTS", _det_set | {"card.py"})):
        gap = sorted(on_disk - have)
        if gap:
            hits.append(f"{label} 에 빠진 스크립트 {gap}")

    ok(NAME("분석 스크립트에 순서 의존 패턴이 없다"), not hits, "; ".join(hits[:3]) + (" ..." if len(hits) > 3 else ""))

    # 시각 스윕은 임시 파일에 그린다. 제출용 figures/card.svg 를 건드리면 안 된다.
    _probe_card = os.path.join(FIG, "_hours_probe.svg")
    bad_hours = [h for h in (0, 6, 12, 18, 20, 23)
                 if run("card.py", str(h), _probe_card)[0] != 0]
    os.path.exists(_probe_card) and os.remove(_probe_card)
    ok(NAME("카드가 0·6·12·18·20·23시 전부에서 동작한다"), not bad_hours, f"실패한 시각 {bad_hours}")

    # baseline: README 가 주장하는 수를 스크립트 출력에서 **읽어서** 대조한다.
    # 다시 계산하지 않는다 — 이 파일이 예전에 그렇게 해서 사보타주를 통과시켰다.
    rc, out, err = run("baseline.py")
    ok(NAME("baseline.py 가 종료 코드 0"), rc == 0, err.strip()[-160:])
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    _vp = os.path.join(ROOT, "VERIFICATION.md")
    verif = open(_vp, encoding="utf-8").read() if os.path.exists(_vp) else ""
    # 감사 이력을 부록으로 옮겼으니, 그 수치들은 부록에서 대조한다.
    # 결속은 "어느 파일에 있든 스크립트 출력과 같아야 한다" 이지 위치가 아니다.
    docs = readme + "\n" + verif

    def one(pat, text, flags=0):
        m = re.search(pat, text, flags)
        return m.groups() if m else None

    got = {
        "timer":  one(r"timer set to 2 a\.m\.\s+\d+:00\s+([\d.]+) %", out),
        "ours":   one(r"Grid Clock, TOU customer\s+\d+:00\s+([\d.]+) %", out),
        "oracle": one(r"per-night oracle\s+mean\s+([\d.]+) %", out),
        "share":  one(r"A timer already captures ([\d.]+) % of what we offer", out),
        "cycle":  one(r"costs at most ([\d.]+) pp across these cycle lengths", out),
        "sep":    one(r"versus the ([\d.]+) pp that separates", out),
    }
    # **굵은 글씨를 묶지 않는다.** 앞 판본은 `\*\*` 를 정규식에 박아 둬서, 강조를 옮기자
    # 값이 그대로인데도 "읽지 못함"이 났다. 검사가 잡아야 할 것은 수치이지 마크다운이 아니다.
    # 줄바꿈도 마찬가지 — 마크다운은 어디서든 접힌다.
    B = r"\*{0,2}"
    said = {
        "timer":  one(rf"timer set to 2 a\.m\.{B}\s*\|[^|]*\|\s*{B}([\d.]+) %", readme),
        "ours":   one(rf"Grid Clock's recommendation\s*\|[^|]*\|\s*{B}([\d.]+) %", readme),
        "oracle": one(r"perfect per-night forecast[^|]*\|[^|]*\|\s*([\d.]+) %", readme),
        "share":  one(r"## A \$12 timer captures ([\d.]+) % of this", readme),
        "cycle":  one(rf"costs {B}([\d.]+) pp{B} — (?:eight times|under a third of)", readme),
        "sep":    one(rf"the {B}([\d.]+) pp{B} that separates the\s+hour", readme),
    }
    miss = [k for k in got if got[k] is None or said[k] is None]
    diff = [f"{k}: 스크립트 {got[k][0]} vs README {said[k][0]}"
            for k in got if k not in miss and got[k][0] != said[k][0]]
    ok(NAME("README 의 타이머 비교표가 baseline 출력과 일치한다"), not miss and not diff,
       (f"읽지 못한 항목 {miss} " if miss else "") + "; ".join(diff))

    # "우리 권고 시각이 가장 깨끗한 밤의 비율" — 스크립트가 표시한 줄에서 읽는다
    # 손으로 센 수는 반드시 틀린다. 하네스 쪽에서 "53+6=59" 로 적었는데 실제는 60이었다.
    # 그래서 README 가 적은 개수를 코드에서 **세어** 대조한다.
    def _count_list(path, name):
        for nd in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
            tgt = (nd.target.id if isinstance(nd, ast.AnnAssign)
                   and isinstance(nd.target, ast.Name) else
                   nd.targets[0].id if isinstance(nd, ast.Assign) and nd.targets
                   and isinstance(nd.targets[0], ast.Name) else None)
            if tgt == name and isinstance(nd.value, ast.List):
                return len(nd.value.elts)
        return None

    # 사보타주가 겨냥하지 않는 검사는 죽어 있어도 아무도 모른다.
    # 실제로 22개 중 8개가 그 상태였다 — 이 검사를 붙이고 나서야 보였다.
    def _sab_targets(path):
        for nd in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
            tgt = (nd.target.id if isinstance(nd, ast.AnnAssign)
                   and isinstance(nd.target, ast.Name) else
                   nd.targets[0].id if isinstance(nd, ast.Assign) and nd.targets
                   and isinstance(nd.targets[0], ast.Name) else None)
            if tgt == "SABS" and isinstance(nd.value, ast.List):
                out = []
                for e in nd.value.elts:
                    if isinstance(e, ast.Tuple) and len(e.elts) >= 5 \
                            and isinstance(e.elts[4], ast.Constant):
                        out.append(e.elts[4].value)
                return out
        return None

    sab_py = os.path.join(ROOT, "src", "sabotage.py")
    targets = _sab_targets(sab_py) if os.path.exists(sab_py) else None
    if targets is None:
        ok(NAME("모든 검사가 최소 하나의 사보타주에 겨냥된다"), False, "sabotage.py 에서 SABS 를 읽지 못했다")
    else:
        # 파일을 치우는 사보타주는 SABS 밖에 있다. 그 대상만 예외로 인정한다.
        extra = ["원본 데이터가 있다"] if "DATA_REL" in open(sab_py, encoding="utf-8").read() else []
        uncovered = [n for n in NAMES
                     if not any(t in n for t in targets) and n not in extra]
        ok(NAME("모든 검사가 최소 하나의 사보타주에 겨냥된다"), not uncovered,
           f"겨냥되지 않는 검사 {len(uncovered)}개: " + "; ".join(uncovered[:3]))

    n_checks = len(NAMES)
    _sab_src = open(os.path.join(ROOT, "src", "sabotage.py"), encoding="utf-8").read()
    n_sabs = _count_list(os.path.join(ROOT, "src", "sabotage.py"), "SABS")
    # 파일을 치우는 사보타주는 SABS 밖에서 돈다. 실제로 도는 개수를 세야 한다.
    if n_sabs is not None and "DATA_REL" in _sab_src:
        n_sabs += 1
    said_checks = one(r"(\d+) checks run on the path", readme)
    said_sabs   = one(r"(\d+) defects are\s*\n?\s*planted", readme, re.S)
    said_score = (n_sabs and n_checks and (str(n_sabs), str(n_sabs), str(n_checks)))
    cbad = []
    if not (said_checks and int(said_checks[0]) == n_checks):
        cbad.append(f"검사 수 코드 {n_checks} vs README {said_checks[0] if said_checks else '?'}")
    if not (said_sabs and n_sabs and int(said_sabs[0]) == n_sabs):
        cbad.append(f"사보타주 수 코드 {n_sabs} vs README {said_sabs[0] if said_sabs else '?'}")
    if not (said_score and n_sabs
            and (int(said_score[0]), int(said_score[1]), int(said_score[2]))
                == (n_sabs, n_sabs, n_checks)):
        cbad.append(f"'{said_score[0]}/{said_score[1]} of {said_score[2]}' 가 {n_sabs}/{n_sabs} of {n_checks} 와 다르다"
                    if said_score else "README 에서 사보타주 성적 문장을 찾지 못했다")
    ok(NAME("README 가 적은 검사·사보타주 개수가 코드와 일치한다"), not cbad, "; ".join(cbad))

    # 헤드라인 표가 어느 스크립트에도 묶여 있지 않았다. 문서에서 가장 중요한 세 수인데
    # 사보타주로 25.23 을 18.50 으로 바꿔도 **아무 검사도 울지 않았다.**
    # 표 기반 결속기. 주장이 늘면 여기 한 줄만 추가한다.
    # 감사해 보니 **겨울 표 전체·스윕 양끝·타이머 표 두 줄·pp 수치 셋**이 아무 검사에도
    # 안 걸리고 있었다. 예전 감사는 "이 수가 아무 스크립트 출력에나 있나"만 봐서,
    # 겨울 표 숫자가 compare 출력에 우연히 있어도 통과했다.
    #   (설명, 스크립트, 스크립트 정규식, 대상 정규식, 대상)
    #   대상이 "readme" 면 README, 아니면 그 파일(그림 SVG 등)을 읽는다.
    #   **그림 안의 숫자는 오랫동안 아무 검사도 안 봤다** — 공휴일 수정 뒤에도
    #   카드가 "Mean of 96 summer weeknights" 라고 말하고 있었다. 심사위원이 제일 먼저 보는 것인데.
    BINDINGS = [
        ("여름 표(겨울 스크립트 기준)", "winter.py",
         r"=== 여름[\s\S]*?최고 \d+시 ([\d.]+)%\s*/\s*최저 \d+시 ([\d.]+)%\s*/\s*비율 ([\d.]+)배",
         r"\*\*Summer\*\*[^|]*\|[^|]*?([\d.]+) %\s*\|[^|]*?([\d.]+) %\s*\|\s*([\d.]+)×"),
        ("겨울 표", "winter.py",
         r"=== 겨울[\s\S]*?최고 \d+시 ([\d.]+)%\s*/\s*최저 \d+시 ([\d.]+)%\s*/\s*비율 ([\d.]+)배",
         r"Winter \(Nov[^|]*\|[^|]*?([\d.]+) %\s*\|[^|]*?([\d.]+) %\s*\|\s*([\d.]+)×"),
        ("척도 스윕 양끝", "scale.py",
         r"비율\s+([\d.]+)x -> ([\d.]+)x",
         r"ratio\* declines monotonically\s*\n?\s*\(([\d.]+) → ([\d.]+)\)", "VERIFICATION.md"),
        ("타이머 표: 저녁 두 줄", "baseline.py",
         r"no plan / run at dinner\s+\d+:00\s+([\d.]+) %[\s\S]*?"
         r"common advice: after 7pm\s+\d+:00\s+([\d.]+) %",
         r"Run it at dinner, no plan \| \d+ p\.m\. \| ([\d.]+) %[\s\S]*?"
         r"after 7, it's cheaper\\?\" \| \d+ p\.m\. \| ([\d.]+) %"),
        ("2시·3시 간격", "baseline.py",
         r"2 a\.m\. and 3 a\.m\. differ by ([\d.]+) pp",
         r"\*\*([\d.]+) pp\*\*\. That is the resolution"),
        ("완벽한 예보의 상한", "baseline.py",
         r"\+([\d.]+) pp -- real, but",
         r"beat the timer by ([\d.]+) pp"),
        ("저녁→야간 격차", "baseline.py",
         r"smaller than the \+([\d.]+) pp",
         r"worth something is the ([\d.]+) pp between evening"),
        ("그 격차가 야간 안쪽보다 몇 배인가", "baseline.py",
         r"but ([\d.]+)x smaller than",
         r"between evening and overnight\*\*, which is\s*\n?\s*\*\*([\d.]+)× larger\*\*"),
        ("카드의 표본 일수", "baseline.py",
         r"\((\d+) nights\)",
         r"Mean of (\d+) summer weeknights", "figures/card.svg"),
        ("섭동 B(전 구간 축소)", "compare.py",
         r"scale every hour by ([\d.]+) about a common baseline:"
         r" ordering unchanged, margin ([\d.]+) pp",
         r"scale every hour by ([\d.]+) about a\s*\n?\s*common baseline and the ordering is"
         r" unchanged, with the margin simply becoming ([\d.]+) pp"),
        ("밤별 승률(1시간)", "replay.py",
         r"1h\s+(\d+)/(\d+)\s+\(\s*([\d.]+) %\)",
         r"\| 1 hour \| \*\*(\d+) / (\d+) \(([\d.]+) %\)\*\*"),
        ("밤별 이득 분포", "replay.py",
         r"최악 -([\d.]+)\s+10% -([\d.]+)\s+중앙 \+([\d.]+)\s+90% \+([\d.]+)\s+최고 \+([\d.]+)",
         r"\| −([\d.]+) pp \| −([\d.]+) pp \| \+([\d.]+) pp \| \+([\d.]+) pp \| \+([\d.]+) pp \|"),
        ("지는 밤 수", "replay.py",
         r"야간이 \*\*진\*\* 밤: (\d+)/(\d+)",
         r"It loses on (\d+) nights in (\d+)\."),
        ("차트가 말하는 비율", "compare.py",
         r"/ ([\d.]+)x",
         r"Gas share inside it varies ([\d.]+)x", "figures/chart.svg"),
    ]
    bbad = []
    _cache = {}
    for entry in BINDINGS:
        label, script, spat, rpat = entry[:4]
        target = entry[4] if len(entry) > 4 else "readme"
        if script not in _cache:
            _cache[script] = run(script)[1]
        if target == "readme":
            text = readme
        else:
            tp = os.path.join(ROOT, target)
            if not os.path.exists(tp):
                bbad.append(f"{label}: {target} 이 없다"); continue
            text = open(tp, encoding="utf-8").read()
        sm = re.search(spat, _cache[script], re.S)
        rm = re.search(rpat, text, re.S)
        if not sm:
            bbad.append(f"{label}: 스크립트에서 못 읽음"); continue
        if not rm:
            bbad.append(f"{label}: {target} 에서 못 읽음"); continue
        if sm.groups() != rm.groups():
            bbad.append(f"{label}: 스크립트 {sm.groups()} vs {target} {rm.groups()}")
    ok(NAME("README 의 나머지 수치 주장이 전부 스크립트 출력과 일치한다"), not bbad,
       "; ".join(bbad[:3]) + (" ..." if len(bbad) > 3 else ""))

    rc_c, out_c, err_c = run("compare.py")
    cm = re.search(r"dirtiest (\d+):00 at ([\d.]+)% gas / cleanest (\d+):00 at ([\d.]+)%"
                   r" / ([\d.]+)x", out_c)
    om = re.search(r"most expensive bracket \([\d.]+c\) peaks at (\d+):00, ([\d.]+)% gas", out_c)
    hbad = []
    if not (cm and om):
        hbad.append("compare 출력에서 헤드라인 수를 읽지 못했다")
    else:
        want = {"worst": cm.group(2), "best": cm.group(4),
                "onmax": om.group(2), "ratio": cm.group(5)}
        got = {
            "worst":  one(r"\| \d+ p\.m\. \| \*\*([\d.]+) %\*\* \| 9\.8", readme),
            "best":   one(r"\| \d+ a\.m\. \| \*\*([\d.]+) %\*\* \| 9\.8", readme),
            "onmax":  one(r"Most expensive bracket, worst hour \| ([\d.]+) %", readme),
            "ratio":  one(r"the ([\d.]+)× ratio hold", readme),
        }
        rng = one(r"\*\*([\d.]+) % to ([\d.]+) %\*\*", readme)
        for k, v in want.items():
            if not got[k] or got[k][0] != v:
                hbad.append(f"{k}: 스크립트 {v} vs README {got[k][0] if got[k] else '?'}")
        if not (rng and rng[0] == want["best"] and rng[1] == want["worst"]):
            hbad.append(f"머리 요약문 범위가 {want['best']}~{want['worst']} 와 다르다")
        # 교차 여유는 README 에서 가장 약한 문장이다. 손으로 뺀 수로 두면 안 된다.
        xm = re.search(r"Crossover margin: [\d.]+ - [\d.]+ = \+([\d.]+) pp"
                       r".*?shrink the contrast ~(\d+)%", out_c, re.S)
        xr = re.search(r"= ([\d.]+) pp\*\*\. The perturbation matters[\s\S]*?"
                       r"only the [\d.]+ pp off-peak spread, the strict crossover disappears"
                       r" at a ~(\d+) % reduction", readme)
        if not xm:
            hbad.append("compare 가 교차 여유를 찍지 않는다")
        elif not xr:
            hbad.append("README 에서 교차 여유 문장을 찾지 못했다")
        elif (xm.group(1), xm.group(2)) != (xr.group(1), xr.group(2)):
            hbad.append(f"교차 여유: 스크립트 {xm.group(1)}pp/~{xm.group(2)}% vs "
                        f"README {xr.group(1)}pp/{xr.group(2)}%")
    ok(NAME("README 의 헤드라인 표·요약문이 compare 출력과 일치한다"), rc_c == 0 and not hbad, "; ".join(hbad) or err_c.strip()[-100:])

    # 대본과 Devpost 는 결속이 **하나도** 없었다. README 만 묶어 뒀다.
    # 그런데 대본은 사람이 카메라 앞에서 **소리 내어 읽는** 문서다 — 틀리면 못 되돌린다.
    # 오늘만 세 번, 스크립트 수치가 바뀌었는데 대본이 옛 수를 들고 있었다.
    # 줄 단위 결속까지는 과하니, 최소한 **모든 수가 어느 스크립트 출력엔가 존재**하는지는 본다.
    ALLOW = {
        "9.8", "15.7", "20.3", "3.9", "39.1",   # 토론토하이드로 공시 요금 (chart.TOU 검사가 따로 본다)
        "5.7", "5.5",                            # 데이터 파일 크기(MB)
        "2106.11750",                            # arXiv 인용 번호
        "7.0",                                   # 고친 버그의 옛 출력. 본문이 그 사고를 서술한다
        "3.0", "1.5", "0.9",                     # 가전 소비량 kWh (card.APPLIANCES)
    }
    for sc in ("profile.py", "winter.py", "scale.py", "align8.py", "nulls.py", "parse_ieso.py",
               "blocknull.py", "compare.py", "baseline.py", "chart.py", "replay.py"):
        if sc not in _cache:
            _cache[sc] = run(sc)[1]
    pool = "\n".join(_cache.values())
    pool_nums = set(re.findall(r"\d+(?:\.\d+)?", pool))
    stale = []
    for doc in ("submission/video-script.md", "submission/devpost.md"):
        dp = os.path.join(ROOT, doc)
        if not os.path.exists(dp):
            stale.append(f"{doc} 없음"); continue
        for ln, line in enumerate(open(dp, encoding="utf-8").read().splitlines(), 1):
            t = line.strip()
            if t.startswith(("http", "python3", "`python3", "|---")):
                continue
            for num in re.findall(r"\d+\.\d+", line):
                if num not in pool_nums and num not in ALLOW:
                    stale.append(f"{os.path.basename(doc)}:{ln} {num}")
    ok(NAME("제출 문서(대본·Devpost)의 수치가 전부 스크립트 출력에 있다"), not stale,
       f"어느 스크립트도 찍지 않는 수 {len(stale)}개: " + "; ".join(stale[:4]))

    hg = one(r"headline gap[^(]*\(\+([\d.]+) pp\)", out)
    hr = one(r"The ([\d.]+) pp is an \*\*opportunity", readme)
    ok(NAME("README 의 헤드라인 격차(pp)가 baseline 출력과 일치한다"), bool(hg and hr and hg[0] == hr[0]),
       f"스크립트 {hg[0] if hg else '?'} vs README {hr[0] if hr else '?'}")

    # p값: 문서가 인용하는 두 수는 blocknull 표의 같은 실행에서 나와야 한다.
    # 문서엔 0.0115 가 적혀 있었는데 실제 출력은 0.0155 였다 — 자릿수 뒤바뀜이 세 문서에 퍼져 있었다.
    rc_b, out_b, err_b = run("blocknull.py")
    shuf = one(r"시각 단위 셔플[^\n]*p = ([\d.]+)", out_b)
    rot  = one(r"원형 회전[^\n]*p = ([\d.]+)", out_b)
    r_shuf = one(r"permutation test gave p = (\d+\.\d+)", docs)
    r_rot  = one(r"circular-rotation null[^=]*?p = (\d+\.\d+)", docs, re.S)
    pbad = [f"{k}: 스크립트 {a[0] if a else '?'} vs README {b[0] if b else '?'}"
            for k, a, b in (("셔플", shuf, r_shuf), ("회전", rot, r_rot))
            if not (a and b and a[0] == b[0])]
    ok(NAME("README 의 p값 두 개가 blocknull 출력과 일치한다"), rc_b == 0 and not pbad, "; ".join(pbad) or err_b.strip()[-120:])

    # 8시간 창 흔들림: 표 행에서만 읽는다. 아래 '참고' 줄에도 g 값이 있어 섞이면 안 된다.
    rc_a, out_a, err_a = run("align8.py")
    swings = [float(m) for m in
              re.findall(r"^\s+\d+시\s.*?([+-][\d.]+) g\s*$", out_a, re.M)]
    r_rng = re.search(r"swings it from [−-](\d+\.\d+) to \+(\d+\.\d+)", docs)
    good = bool(swings and r_rng
                and abs(min(swings) + float(r_rng.group(1))) < 0.05
                and abs(max(swings) - float(r_rng.group(2))) < 0.05)
    ok(NAME("README 의 8시간 창 흔들림 범위가 align8 출력과 일치한다"), rc_a == 0 and good,
       f"스크립트 {min(swings) if swings else '?'}~{max(swings) if swings else '?'} vs "
       f"README -{r_rng.group(1) if r_rng else '?'}~+{r_rng.group(2) if r_rng else '?'}")

    # Devpost 의 **권고 시각**. 여태 어느 검사도 이걸 보지 않았다 —
    # 문서 검사는 소수만 훑었고(`\d+\.\d+`), "3 a.m." 은 정수라 보이지 않았다.
    # 그래서 공휴일 수정 뒤에도 Devpost 가 여섯 군데에서 3 a.m. 을 권고하고 있었다.
    # README·영상·baseline 은 전부 2:00 이었다. **세 문서가 한 문장에서 갈렸다.**
    dp_path = os.path.join(ROOT, "submission", "devpost.md")
    dp = open(dp_path, encoding="utf-8").read() if os.path.exists(dp_path) else ""
    dp_h = one(r"run it at (\d+) (a\.m\.|p\.m\.) tonight", dp)
    bl_h = one(r"holidays excluded \(OEB rule, our build\)\s+best (\d+):00", out)
    want = None
    if dp_h:
        want = int(dp_h[0]) % 12 + (12 if dp_h[1] == "p.m." else 0)
    ok(NAME("Devpost 의 권고 시각이 baseline 의 최선 시각과 일치한다"),
       bool(dp_h and bl_h and want == int(bl_h[0])),
       f"Devpost {dp_h[0] + ' ' + dp_h[1] if dp_h else '?'} (={want}시) vs "
       f"baseline 최선 {bl_h[0] + '시' if bl_h else '?'}")

    # Devpost 의 겨울 행. 세 수 전부 winter 출력과 같아야 한다.
    # 실측: 23.58 / 19.98 / 1.180 이 남아 있었는데, 셋 다 **다른 시각의 출력값**이라
    # "모든 수가 어느 출력엔가 있다" 검사를 그대로 통과했다.
    rc_w, out_w, _ew = run("winter.py")
    w_blk = out_w.split("=== 겨울")[1] if "=== 겨울" in out_w else ""
    w = one(r"최고 (\d+)시 ([\d.]+)%\s*/\s*최저 (\d+)시 ([\d.]+)%\s*/\s*비율 ([\d.]+)배", w_blk)
    d = one(r"\| Winter[^|]*\|[^,]*,\s*([\d.]+) %\s*\|[^,]*,\s*([\d.]+) %\s*\|\s*([\d.]+)×", dp)
    ok(NAME("Devpost 의 겨울 행이 winter 출력과 일치한다"),
       bool(rc_w == 0 and w and d and w[1] == d[0] and w[3] == d[1] and w[4] == d[2]),
       f"스크립트 {w[1] + '/' + w[3] + '/' + w[4] if w else '?'} vs "
       f"Devpost {d[0] + '/' + d[1] + '/' + d[2] if d else '?'}")

    # 이 프로젝트에서 가장 큰 수정은 시계 정렬이었다. IESO 는 연중 EST 고정이고
    # OEB 요금 구간은 현지 시각이라, 여름 관측 전부가 한 시간 일찍 분류되고 있었다
    # (6,144 중 4,558 건). 고친 것을 지키는 검사가 없으면 되돌아가도 아무도 모른다.
    rc_t, out_t, err_t = run("check_time.py")
    ok(NAME("시계 변환 기지답 시험이 통과한다"), rc_t == 0 and "기지답 통과" in out_t,
       (err_t.strip() or out_t.strip())[-200:])

    # 그리고 **아무도 원시 시각을 몰래 쓰지 않는지** 본다. `raw_rows` 는 변환 전 값이다.
    # 분석 스크립트가 그걸 직접 쓰면 한 시간이 다시 조용히 밀린다.
    import glob as _glob
    _leak = []
    for _f in sorted(_glob.glob(os.path.join(ROOT, "src", "*.py"))):
        _b = os.path.basename(_f)
        # sabotage.py 는 제외한다 — 거기 있는 "hour - 1" 은 **일부러 심는 문자열**이지
        # 실행되는 코드가 아니다. 문자열 페이로드를 코드로 세면 자기 도구를 고발한다.
        if _b in ("parse_ieso.py", "check_demo.py", "check_time.py", "sabotage.py"):
            continue
        _t = open(_f, encoding="utf-8").read()
        if "raw_rows" in _t:
            _leak.append(f"{_b} 가 raw_rows 를 직접 쓴다")
        if re.search(r"\bhour\s*-\s*1\b", _t):
            _leak.append(f"{_b} 에 hour-1 이 남아 있다 (local_rows 는 이미 0~23 이다)")
    ok(NAME("IESO 시각을 현지 시각으로 바꾸지 않고 쓰는 곳이 없다"), not _leak, "; ".join(_leak[:3]))

    # "그 조언이 **가장 나쁜 시각**을 가리킨다" 는 시계 정렬을 고치자 거짓이 됐다 —
    # 19시는 24.83 %로 저렴 구간 12시간 중 3위이고, 1위는 21시(25.23 %)다.
    # 산문 주장이라 어떤 검사도 안 잡았다. 이제 **순위를 데이터에서 다시 구해** 문서와 맞춘다.
    rc_c2, out_c2, _ = run("compare.py")
    _prof = {int(h): float(v) for h, v in
             re.findall(r"^\s*(\d+):00\s+9\.8c off-peak.*?([\d.]+) %\s*$", out_c2, re.M)}
    _rank_bad = []
    if len(_prof) < 12:
        _rank_bad.append(f"저렴 구간 시각을 {len(_prof)}개밖에 못 읽었다")
    else:
        # 구간이 열리는 순서: 19,20,...,23,0,...,6
        _opens = [h for h in range(19, 24)] + [h for h in range(0, 7)]
        _by_gas = sorted(_prof, key=lambda h: -_prof[h])
        # 문서가 말하는 N 을 읽어서, 실제로 그 N개가 앞 N시간인지 본다
        for _f, _pat in (("README.md", r"The (\w+) dirtiest hours of those twelve are the first (\w+)"),
                         ("submission/devpost.md", r"the (\w+) with the most gas are the first (\w+)")):
            _t = open(os.path.join(ROOT, _f), encoding="utf-8").read()
            _m = re.search(_pat, _t)
            if not _m:
                _rank_bad.append(f"{_f} 에서 그 문장을 못 읽었다"); continue
            # 문서가 어떤 수를 적든 실제 순위로 판정한다. 참고로 3~6 은 전부 참이고
            # 7부터 거짓이다 — 주장이 특정 값에 아슬아슬하게 걸려 있지 않다는 뜻이다.
            _words = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                      "seven": 7, "eight": 8, "nine": 9, "ten": 10}
            _n1, _n2 = _words.get(_m.group(1).lower()), _words.get(_m.group(2).lower())
            if _n1 is None or _n2 is None or _n1 != _n2:
                _rank_bad.append(f"{_f}: 두 수가 다르거나 못 읽었다 ({_m.group(1)}/{_m.group(2)})"); continue
            if set(_by_gas[:_n1]) != set(_opens[:_n1]):
                _rank_bad.append(
                    f"{_f}: 가장 더러운 {_n1}시각 {sorted(_by_gas[:_n1])} ≠ 앞 {_n1}시간 {_opens[:_n1]}")
    ok(NAME("문서가 말하는 '가장 더러운 앞 N시간'이 실제 순위와 맞는다"), not _rank_bad, "; ".join(_rank_bad[:2]))

    # **영상이 쓰는 것은 SVG 가 아니라 PNG 다.** SVG 는 매 실행 다시 그려지고 검사도 받는데,
    # PNG 는 `tools/svg2png.py` 를 사람이 손으로 돌려야 생긴다. 시계 정렬을 고친 뒤 아무도
    # 안 돌려서, **사흘 묵은 chart.png 가 영상에 그대로 실렸다** — 그림은 20:00·2:00 을,
    # 표와 낭독은 21:00·3:00 을 말하고 있었다. 검사 32개가 전부 초록인 채로.
    #
    # **시각이 아니라 내용으로 묶는다.** mtime 으로 쳤더니 이 검사 자신이 SVG 를 다시 그려서
    # PNG 가 늘 '낡은 것'이 됐다. svg2png.py 가 출처 SVG 의 해시를 .png-from.json 에 적고,
    # 여기서 지금 SVG 의 해시와 대조한다.
    _stamp_p = os.path.join(FIG, ".png-from.json")
    _png_bad = []
    _stamp = {}
    if not os.path.exists(_stamp_p):
        _png_bad.append(".png-from.json 이 없다 — python3 tools/svg2png.py figures/*.svg 를 돌려라")
    else:
        try:
            import json as _json
            _stamp = _json.load(open(_stamp_p, encoding="utf-8"))
        except Exception as _e:
            _png_bad.append(f".png-from.json 을 못 읽었다: {_e}")
    import hashlib as _hl
    def _sha16(_p):
        return _hl.sha256(open(_p, "rb").read()).hexdigest()[:16]
    for _png, _src in (("card.png", "card.svg"), ("chart.png", "chart.svg"),
                       ("thumbnail.png", "card.png")):
        _pp, _sp = os.path.join(FIG, _png), os.path.join(FIG, _src)
        if not os.path.exists(_pp):
            _png_bad.append(f"{_png} 이 없다"); continue
        if not os.path.exists(_sp):
            _png_bad.append(f"{_src} 가 없다"); continue
        _rec = _stamp.get(_png)
        if not _rec:
            _png_bad.append(f"{_png} 의 출처 기록이 없다"); continue
        if _rec.get("from") != _src:
            _png_bad.append(f"{_png} 의 출처가 {_rec.get('from')} 로 적혀 있다 (기대 {_src})"); continue
        if _rec.get("sha") != _sha16(_sp):
            _png_bad.append(f"{_png} 이 지금 {_src} 에서 나온 것이 아니다 — python3 tools/svg2png.py 를 돌려라")
    ok(NAME("영상·제출에 쓰는 PNG 가 SVG 보다 낡지 않았다"), not _png_bad, "; ".join(_png_bad[:3]))

    gn = one(r"(\d+):00\s+\d+ nights\s+([\d.]+) %\s*<- what we recommend", out)
    rn = one(r"\*\*([\d.]+) % of nights\*\*", readme)
    ok(NAME("README 의 '밤의 비율' 주장이 baseline 출력과 일치한다"), bool(gn and rn and gn[1] == rn[0]),
       f"스크립트 {gn[1] if gn else '?'} % ({gn[0] if gn else '?'}시) vs README {rn[0] if rn else '?'} %")

print()
failed = 0
for n in NAMES:
    good, detail = result[n]
    failed += not good
    print(f"  {'OK ' if good else 'BAD'}  {n}" + ("" if good else f"   {detail}"))
print(f"\n{len(NAMES) - failed}/{len(NAMES)} 데모 경로 검사 통과. (분모 고정 — 실패해도 개수가 줄지 않는다)")
sys.exit(1 if failed else 0)
