"""시계 변환만 따로 검정한다. **기대값은 손으로 정했다 — 변환으로 만들지 않았다.**

이게 이 파일의 요점이다. 시험 대상이 만든 값을 기대값으로 쓰면 시험이 아니라 복사다.
아래 표의 오른쪽은 전부 두 공개 규칙에서 사람이 계산한 것이다:
  · IESO 는 연중 EST(UTC-05:00) 고정, hour H = H-1:00~H:00
  · 토론토 서머타임은 3월 둘째 일요일 02:00 현지 ~ 11월 첫 일요일 02:00 현지
"""
import sys, os, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_ieso import to_local, toronto_offset_hours

# (보고일, hour-ending) -> (현지 날짜, 현지 0~23시), 그리고 왜 그런지
KNOWN = [
    # 겨울: IESO 시계 = 현지 시계. hour 19 = 18:00~19:00.
    ("2026-01-15", 19, "2026-01-15", 18, "겨울엔 EST=현지. hour-ending 19 는 18시 시작"),
    ("2026-01-15", 24, "2026-01-15", 23, "겨울 마지막 시간은 같은 날 23시"),
    ("2026-01-15",  1, "2026-01-15",  0, "겨울 첫 시간은 같은 날 0시"),
    # 여름: 현지는 EDT. 한 시간 뒤가 된다.
    ("2026-07-15", 19, "2026-07-15", 19, "여름 hour 19 = 18~19 EST = 19~20 EDT → 19시"),
    ("2026-07-15", 18, "2026-07-15", 18, "여름 hour 18 = 17~18 EST = 18~19 EDT → 18시"),
    ("2026-07-15", 24, "2026-07-16",  0, "여름 마지막 시간은 **다음 날** 0시로 넘어간다"),
    ("2026-07-15",  1, "2026-07-15",  1, "여름 첫 시간은 같은 날 1시"),
    # 봄 전환일(2026-03-08). 02:00 현지에 서머타임이 시작한다.
    ("2026-03-08",  1, "2026-03-08",  0, "00~01 EST 는 아직 EST"),
    ("2026-03-08",  2, "2026-03-08",  1, "01~02 EST 도 아직 EST"),
    ("2026-03-08",  3, "2026-03-08",  3, "02:00 EST = 07:00 UTC 에 EDT 시작 → 03시로 건너뛴다"),
    # 가을 전환일(2026-11-01). 02:00 현지에 끝난다. 현지 01시가 두 번 나온다.
    ("2026-11-01",  1, "2026-11-01",  1, "00~01 EST = 05:00 UTC, 아직 EDT → 01시"),
    ("2026-11-01",  2, "2026-11-01",  1, "01~02 EST = 06:00 UTC, EST 로 복귀 → **다시** 01시"),
]

def main():
    bad = []
    for day, he, want_d, want_h, why in KNOWN:
        got_d, got_h = to_local(day, he)
        if (got_d, got_h) != (want_d, want_h):
            bad.append(f"{day} hour {he}: 기대 {want_d} {want_h}시, 실제 {got_d} {got_h}시 ({why})")

    # 규칙을 직접 적은 것과 **표준 라이브러리의 tz 데이터**가 같은 말을 하는지 따로 본다.
    # 둘이 갈리면 어느 쪽이 틀렸는지는 몰라도 **믿을 수 없다는 것은 안다.**
    tz_bad = []
    try:
        from zoneinfo import ZoneInfo
        TOR = ZoneInfo("America/Toronto")
        EST = dt.timezone(dt.timedelta(hours=-5))
        d = dt.date(2026, 1, 1)
        while d < dt.date(2027, 1, 1):
            for he in (1, 3, 12, 19, 24):
                start = dt.datetime.combine(d, dt.time(0), EST) + dt.timedelta(hours=he - 1)
                ref = start.astimezone(TOR)
                got_d, got_h = to_local(d, he)
                if (got_d, got_h) != (ref.date().isoformat(), ref.hour):
                    tz_bad.append(f"{d} hour {he}: 규칙 {got_d} {got_h} vs tzdata "
                                  f"{ref.date()} {ref.hour}")
            d += dt.timedelta(days=1)
        tz_note = f"tzdata 와 {'일치' if not tz_bad else '불일치'} (1년치 5시각 = 1,825자리)"
    except Exception as e:
        tz_bad.append(f"zoneinfo 를 못 썼다: {e}")
        tz_note = "tzdata 대조 실패"

    print(f"  기지답 {len(KNOWN)}자리 — {'전부 맞음' if not bad else f'{len(bad)}자리 틀림'}")
    for b in bad:
        print("    BAD ", b)
    print(f"  {tz_note}")
    for b in tz_bad[:5]:
        print("    BAD ", b)
    fail = len(bad) + len(tz_bad)
    print(f"\n{len(KNOWN) - len(bad)}/{len(KNOWN)} 기지답 통과" + ("" if not tz_bad else " · tzdata 대조 실패"))
    return 1 if fail else 0

if __name__ == "__main__":
    sys.exit(main())
