"""같은 입력에 같은 답이 나오는가. 해시 시드를 바꿔 가며 확인한다.

**검증 스크립트가 재현되지 않으면 검증이 아니다.**

실제로 겪은 일: `align8.py` 와 `scale.py` 가 창의 요금 계층을 다수결로 정하면서
동수를 `max(set(labs), key=labs.count)` 로 깼다. 집합은 순회 순서가 없고 파이썬은
문자열 해시를 프로세스마다 무작위화하므로, 8시간 창 하나가 실행마다 `+7.0 g` 였다가
`비교 불가` 였다가 했다. README·Devpost·영상 대본이 인용한 범위가 실행마다 달랐다.

`check_demo.py` 는 소스에서 그 **꼴**을 막는다(정적, 빠름).
이 파일은 **실제로 돌려서** 확인한다(느림, 그래서 따로 둔다).
정적 검사가 모르는 것까지 잡는다 — 시간 의존, 씨 없는 난수, 딕셔너리 순서, 파일 순서.

사용:  python3 src/determinism.py data/fuel2026.xml
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "fuel2026.xml")
SEEDS = (0, 1, 2, 3, 12345)
SCRIPTS = ["parse_ieso.py", "profile.py", "compare.py", "chart.py", "nulls.py",
           "blocknull.py", "scale.py", "align8.py", "winter.py", "baseline.py",
           "replay.py", "export_web.py", "check_time.py"]

def run(script, seed):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "src", script), DATA],
                       capture_output=True, text=True, timeout=600, env=env)
    return r.returncode, r.stdout

print(f"\n  각 스크립트를 PYTHONHASHSEED {', '.join(map(str, SEEDS))} 로 돌려 출력을 비교한다.\n")
unstable, failed = [], []
for sc in SCRIPTS:
    outs, rcs = set(), set()
    for s in SEEDS:
        rc, out = run(sc, s)
        rcs.add(rc); outs.add(out)
    if rcs != {0}:
        failed.append(sc); print(f"  [오류]  {sc:<16} 종료코드 {sorted(rcs)}")
    elif len(outs) > 1:
        unstable.append(sc); print(f"  [불안정] {sc:<16} 서로 다른 출력 {len(outs)}가지")
    else:
        print(f"  [안정]  {sc}")

print()
if unstable or failed:
    if unstable:
        print(f"  {len(unstable)}개 스크립트가 같은 입력에 다른 답을 낸다: {unstable}")
        print(f"  집합 순회, 씨 없는 난수, 딕셔너리 순서, 시각 의존을 의심하라.")
    if failed:
        print(f"  {len(failed)}개 스크립트가 실패했다: {failed}")
    sys.exit(1)
print(f"  {len(SCRIPTS)}개 스크립트 전부 시드에 무관하게 같은 답을 낸다.")
