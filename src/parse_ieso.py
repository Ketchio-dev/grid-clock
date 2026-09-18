"""IESO Generator Output by Fuel Type Hourly -> 시간별 배출집약도.

표준 라이브러리만 사용. Canopy 의 스트리밍 파싱 습관을 그대로 가져온다.

**시계가 둘이다. 이 파일이 그 둘을 잇는 유일한 자리다.**

IESO 시장은 연중 **EST 고정**으로 돈다 — 서머타임을 따르지 않는다. 반면 OEB 의
시간대별 요금 구간(off-peak 19:00-07:00 등)은 **고객의 현지 시계**, 즉 여름에는 EDT 다.
그래서 IESO 의 hour 를 그대로 현지 시각으로 쓰면 **여름 내내 한 시간씩 밀린다.**

이 자료 안에서 직접 확인된다: 2026-03-08 은 서머타임 전환일인데 이 파일에 **24시간**이
들어 있다. 현지 시계였다면 23시간이어야 한다. 256일 전부 정확히 24시간이다 → 고정 시계다.

고치기 전 실측: 6,144 관측 중 **4,558 건이 어긋나 있었고**(3/8~9/13 전부),
그중 190 건은 현지 **날짜까지** 넘어간다. 여름 분석은 100 % 밀려 있었다.

`rows()` 는 일부러 없앴다. 이름을 그대로 두면 `hour - 1` 을 하던 열두 곳이
**조용히** 한 시간 틀린 채로 계속 돌았을 것이다. 안 옮긴 곳은 ImportError 로 죽는다.
"""
import sys, datetime as dt, xml.etree.ElementTree as ET
from collections import defaultdict

NS = "{http://www.ieso.ca/schema}"
EST = dt.timezone(dt.timedelta(hours=-5))          # IESO 시장 시계. 연중 고정.


def _nth_weekday(year, month, weekday, n):
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(days=7 * (n - 1))


def toronto_offset_hours(utc_moment):
    """그 순간 토론토의 UTC 오프셋(시간). **규칙을 직접 적는다 — tzdata 에 기대지 않는다.**

    미국·캐나다 규칙(2007~): 3월 둘째 일요일 02:00 현지에 시작, 11월 첫 일요일 02:00 현지에 끝.
    경계는 UTC 로 비교한다: 시작은 07:00 UTC, 끝은 06:00 UTC.
    """
    y = utc_moment.year
    start = dt.datetime.combine(_nth_weekday(y, 3, 6, 2), dt.time(7), dt.timezone.utc)
    end = dt.datetime.combine(_nth_weekday(y, 11, 6, 1), dt.time(6), dt.timezone.utc)
    return -4 if start <= utc_moment < end else -5


def to_local(report_date, hour_ending):
    """(보고일, hour-ending 1~24) -> (현지 날짜, 현지 0~23시). 구간 **시작** 기준이다.

    IESO 의 hour H 는 H-1:00~H:00 EST 다. 그 시작 순간을 토론토 현지로 옮긴다.
    여름에는 한 시간 뒤가 되고, hour 24 는 **다음 날**로 넘어간다.
    """
    d = report_date if isinstance(report_date, dt.date) else dt.date.fromisoformat(report_date)
    start_est = dt.datetime.combine(d, dt.time(0), EST) + dt.timedelta(hours=hour_ending - 1)
    off = toronto_offset_hours(start_est.astimezone(dt.timezone.utc))
    loc = start_est.astimezone(dt.timezone(dt.timedelta(hours=off)))
    return loc.date().isoformat(), loc.hour


def raw_rows(path):
    """(보고일, hour-ending 1~24, {fuel: MW}) — **IESO 시계 그대로.** 변환하지 않는다."""
    day = None
    for event, el in ET.iterparse(path, events=("end",)):
        if el.tag == NS + "Day":
            day = el.text
        elif el.tag == NS + "HourlyData":
            hour = int(el.findtext(NS + "Hour"))
            mix = {}
            for ft in el.findall(NS + "FuelTotal"):
                fuel = ft.findtext(NS + "Fuel")
                ev = ft.find(NS + "EnergyValue")
                out = ev.findtext(NS + "Output") if ev is not None else None
                if out is not None:
                    mix[fuel] = float(out)
            yield day, hour, mix
            el.clear()


def expected_hours(local_date):
    """그 **현지** 날짜에 있어야 할 시간 수. 서머타임 전환일은 24가 아니다.

    봄 전환일은 02시가 없어 23시간, 가을 전환일은 01시가 두 번이라 25시간이다.
    이걸 24로 놓고 "불완전한 날"이라 부르면 **정상인 날을 버린다.**
    """
    d = local_date if isinstance(local_date, dt.date) else dt.date.fromisoformat(local_date)
    if d == _nth_weekday(d.year, 3, 6, 2):
        return 23
    if d == _nth_weekday(d.year, 11, 6, 1):
        return 25
    return 24


def local_rows(path, whole_days=True):
    """(현지 날짜, **현지 0~23시**, {fuel: MW}). 요금 구간·휴일·요일은 전부 이걸로 따진다.

    쓰는 쪽에서 `hour - 1` 을 하면 안 된다. 이미 0~23 이다.

    `whole_days=True` 면 **시간이 덜 찬 현지 날짜를 통째로 버린다.** 시계를 옮기면
    자료 끝에서 조각 날이 생긴다 — 이 자료에서는 2026-09-14 에 한 시간만 남았고,
    그 한 시간이 하루 평균으로 들어가 표본 일수를 93 으로 부풀리고 있었다.
    버릴 때 **서머타임 전환일은 버리지 않는다**(23·25시간이 그 날의 정상이다).
    """
    buf = {}
    for day, hour, mix in raw_rows(path):
        ld, lh = to_local(day, hour)
        buf.setdefault(ld, []).append((lh, mix))
    for ld in sorted(buf):
        rows_ = buf[ld]
        if whole_days and len(rows_) != expected_hours(ld):
            continue
        for lh, mix in sorted(rows_):
            yield ld, lh, mix


if __name__ == "__main__":
    n = 0
    fuels = defaultdict(float)
    first = last = None
    for day, hour, mix in local_rows(sys.argv[1]):
        n += 1
        first = first or (day, hour)
        last = (day, hour)
        for f, v in mix.items():
            fuels[f] += v
    print(f"  시간 레코드: {n:,}  (현지 시각으로 변환됨)")
    print(f"  범위: {first} ~ {last}")
    tot = sum(fuels.values())
    print("  연간 발전량 비중:")
    for f, v in sorted(fuels.items(), key=lambda x: -x[1]):
        print(f"    {f:<10} {v/tot*100:6.2f} %")
