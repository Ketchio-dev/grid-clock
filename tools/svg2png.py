#!/usr/bin/env python3
"""SVG -> PNG. **제출 준비용이지 분석 경로가 아니다.**

Devpost 이미지 갤러리는 JPG·PNG·GIF 만 받는다 (SVG 불가, 최대 5 MB, 3:2 권장).
우리 그림은 전부 손으로 쓴 SVG 라 업로드하려면 변환이 필요하다.

**README 의 실행 목록에 넣지 않는다.** 분석은 표준 라이브러리만 쓰고 의존성이 0이며,
이건 사람이 제출 직전에 한 번 돌리는 도구다. macOS(QuickLook) + Pillow 필요.

왜 이렇게 복잡한가: qlmanage 는 SVG 를 **정사각 뷰포트에 맞추면서 가로로 긴 그림의
오른쪽을 잘라낸다.** 차트(980x420)를 그냥 넘기면 19~21시 노란 띠 — 이 그림의 요점 — 가
통째로 사라진다. 실제로 그렇게 잘린 PNG 를 만들 뻔했다.
그래서 **먼저 정사각 캔버스에 얹어** 자를 것이 없게 만든 뒤, 흰 여백만 도로 잘라낸다.

사용:  python3 tools/svg2png.py figures/*.svg
"""
import glob, hashlib, io, json, os, re, subprocess, sys, tempfile

def convert(svg_path, out_dir, render=1800):
    svg = io.open(svg_path, encoding="utf-8").read()
    m = re.search(r'width="(\d+)"\s+height="(\d+)"', svg)
    if not m:
        return None, "SVG 에서 width/height 를 못 읽었다"
    w, h = int(m.group(1)), int(m.group(2))
    side = max(w, h)
    inner = svg.replace(f'width="{w}" height="{h}"',
                        f'width="{w}" height="{h}" x="0" y="{(side - h) // 2}"', 1)
    wrapped = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{side}" height="{side}">'
               f'<rect width="{side}" height="{side}" fill="#ffffff"/>{inner}</svg>')

    with tempfile.TemporaryDirectory() as td:
        sq = os.path.join(td, "sq.svg")
        io.open(sq, "w", encoding="utf-8").write(wrapped)
        subprocess.run(["qlmanage", "-t", "-s", str(render), "-o", td, sq],
                       capture_output=True, check=False)
        pngs = glob.glob(os.path.join(td, "*.png"))
        if not pngs:
            return None, "qlmanage 가 PNG 를 만들지 못했다"
        from PIL import Image
        im = Image.open(pngs[0]).convert("RGB")
        W, H = im.size
        px = im.load()
        # 전수 검사. 샘플링하면 가장자리의 얇은 내용을 놓친다.
        col_white = lambda x: all(px[x, y] == (255, 255, 255) for y in range(H))
        row_white = lambda y: all(px[x, y] == (255, 255, 255) for x in range(W))
        lo = next((x for x in range(W) if not col_white(x)), 0)
        hi = next((x for x in range(W - 1, -1, -1) if not col_white(x)), W - 1)
        tp = next((y for y in range(H) if not row_white(y)), 0)
        bt = next((y for y in range(H - 1, -1, -1) if not row_white(y)), H - 1)
        im = im.crop((lo, tp, hi + 1, bt + 1))

        got, want = im.size[0] / im.size[1], w / h
        warn = "" if abs(got - want) / want < 0.10 else \
               f"  [경고] 비율 {got:.2f} 가 원본 {want:.2f} 와 10% 넘게 다르다 — 잘렸을 수 있다"
        dst = os.path.join(out_dir, os.path.splitext(os.path.basename(svg_path))[0] + ".png")
        im.save(dst, optimize=True)
        return dst, f"{im.size[0]}x{im.size[1]} 비율 {got:.2f} (원본 {want:.2f}){warn}"

def make_thumb(png_path, out_path, ratio=3/2):
    """Devpost 썸네일은 3:2 를 권장한다. 자르지 않고 **여백을 덧대** 맞춘다 —
    자르면 카드의 각주(주장하지 않는 것)가 날아간다."""
    from PIL import Image
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    if w / h > ratio:          # 너무 넓다 → 위아래 덧댐
        nh, nw = int(round(w / ratio)), w
    else:                       # 너무 좁다 → 좌우 덧댐
        nw, nh = int(round(h * ratio)), h
    # 모서리 픽셀을 쓰면 안 된다 — 카드는 모서리가 둥글어 바깥이 흰색이라
    # 검은 카드에 흰 띠가 붙었다. 가장 많이 쓰인 색을 쓴다.
    bg = max(im.getcolors(maxcolors=1 << 24), key=lambda kv: kv[0])[1]
    canvas = Image.new("RGB", (nw, nh), bg)
    canvas.paste(im, ((nw - w) // 2, (nh - h) // 2))
    canvas.save(out_path, optimize=True)
    return canvas.size


# PNG 가 어느 SVG 에서 나왔는지 **내용으로** 남긴다.
# 시각(mtime)으로 묶으면 SVG 를 다시 그리는 것만으로 PNG 가 '낡은 것'이 된다 —
# 실제로 그렇게 만들었다가 검사가 영원히 빨개졌다. 해시는 그런 일이 없다.
STAMP = "figures/.png-from.json"


def _sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()[:16]


def stamp(root, pairs):
    """pairs: [(png 이름, 출처 파일 경로)]"""
    f = os.path.join(root, STAMP)
    cur = {}
    if os.path.exists(f):
        try:
            cur = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            cur = {}
    for png, src in pairs:
        cur[os.path.basename(png)] = {"from": os.path.basename(src), "sha": _sha(src)}
    io.open(f, "w", encoding="utf-8").write(json.dumps(cur, ensure_ascii=False, indent=1,
                                                      sort_keys=True) + "\n")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--thumb"]:
        src, dst = sys.argv[2], sys.argv[3]
        sz = make_thumb(src, dst)
        stamp(os.path.dirname(os.path.dirname(os.path.abspath(dst))), [(dst, src)])
        print(f"  썸네일 {os.path.basename(dst)} {sz[0]}x{sz[1]} 비율 {sz[0]/sz[1]:.2f} "
              f"{os.path.getsize(dst)/1024:.0f} KB")
        raise SystemExit(0)
    args = sys.argv[1:]
    if not args:
        raise SystemExit("사용: python3 tools/svg2png.py <svg...>")
    done = []
    for svg in args:
        dst, info = convert(svg, os.path.dirname(os.path.abspath(svg)))
        kb = f"{os.path.getsize(dst)/1024:.0f} KB" if dst else ""
        print(f"  {os.path.basename(svg):<12} -> {os.path.basename(dst) if dst else '실패':<12} {info} {kb}")
        if dst:
            done.append((dst, svg))
    if done:
        stamp(os.path.dirname(os.path.dirname(os.path.abspath(args[0]))), done)
        print(f"  출처 해시를 {STAMP} 에 적었다")
