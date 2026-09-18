"""IESO 시간별 연료믹스를 받아온다. 클론한 사람이 가장 먼저 실행하는 것.

원본은 5.7 MB 라 저장소에 넣지 않는다(.gitignore). 대신 이 스크립트가 받는다.
인증 없음, 무료, 공개.
"""
import os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = ("https://reports-public.ieso.ca/public/GenOutputbyFuelHourly/"
       "PUB_GenOutputbyFuelHourly_2026.xml")
DEST = os.path.join(ROOT, "data", "fuel2026.xml")

def main():
    if os.path.exists(DEST) and os.path.getsize(DEST) > 1_000_000:
        print(f"  already here: {DEST} ({os.path.getsize(DEST):,} bytes)")
        return 0
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    print(f"  fetching {URL}")
    tmp = DEST + ".part"
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "grid-clock/1.0"})
        with urllib.request.urlopen(req, timeout=180) as r, open(tmp, "wb") as f:
            f.write(r.read())
    except Exception as e:
        print(f"  download failed: {e}")
        print(f"  Fetch it by hand and save to: {DEST}")
        return 1
    # 부분 파일을 영구화하지 않는다
    if os.path.getsize(tmp) < 1_000_000:
        os.remove(tmp)
        print("  got a suspiciously small file; refusing to keep it")
        return 1
    os.replace(tmp, DEST)
    print(f"  saved {DEST} ({os.path.getsize(DEST):,} bytes)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
