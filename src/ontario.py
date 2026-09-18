"""온타리오 요금제 달력. 어느 날이 "여름 평일"인가 — 한 군데서만 정한다.

**공휴일은 평일이 아니다.** 온타리오 TOU 는 공휴일에 하루 종일 off-peak 로 과금한다.
공휴일을 평일로 섞으면 11~17시에 "on-peak 20.3¢" 라는 **사실이 아닌 요금표**를 붙이게 된다.
첫 판본이 그랬다. 주말만 걸러내고 공휴일은 그대로 뒀다.

이게 결론을 바꿨다: 공휴일 4일을 빼면 **가장 깨끗한 시각이 3시에서 2시로 넘어간다.**
둘의 차이가 0.01 pp 안쪽이라 공휴일 처리 하나로 순위가 뒤집힌다 —
우리가 시각을 고르는 능력이 그 정도라는 뜻이고, 그건 README 에 적혀 있다.

출처: Ontario Energy Board, "Holiday schedule - Time-of-Use and Ultra-Low Overnight"
https://www.oeb.ca/consumer-information-and-protection/electricity-rates/holiday-schedule-time-use-and-ultra-low
2026-09-15 확인. 2026년 전체 목록을 그대로 옮긴다(데이터 범위 밖의 날도 함께 둔다 —
나중에 데이터가 늘어도 이 파일을 다시 고치지 않도록).
"""
import datetime

# OEB 2026 목록 전문. 이 날들은 하루 종일 최저 요금이다.
TOU_HOLIDAYS_2026 = {
    datetime.date(2026, 1, 1):   "New Year's Day",
    datetime.date(2026, 2, 16):  "Family Day",
    datetime.date(2026, 4, 3):   "Good Friday",
    datetime.date(2026, 5, 18):  "Victoria Day",
    datetime.date(2026, 7, 1):   "Canada Day",
    datetime.date(2026, 8, 3):   "Civic Holiday",
    datetime.date(2026, 9, 7):   "Labour Day",
    datetime.date(2026, 10, 12): "Thanksgiving Day",
    datetime.date(2026, 12, 25): "Christmas Day",
    datetime.date(2026, 12, 28): "Boxing Day",
}

SUMMER_MONTHS = (5, 6, 7, 8, 9, 10)     # TOU 여름 요금: 5/1 ~ 10/31
WINTER_MONTHS = (11, 12, 1, 2, 3, 4)


def to_date(day: str) -> datetime.date:
    """IESO 의 'YYYY-MM-DD' 를 date 로."""
    return datetime.date(int(day[:4]), int(day[5:7]), int(day[8:10]))


def is_holiday(d: datetime.date) -> bool:
    return d in TOU_HOLIDAYS_2026


def summer_weekday(day: str) -> bool:
    """여름 요금 기간의 평일인가. 주말과 공휴일은 제외한다.

    요금 구간 비교의 모집단이다 — on/mid/off 가 실제로 구분되는 날만 들어간다.
    """
    d = to_date(day)
    return (d.month in SUMMER_MONTHS and d.weekday() < 5 and not is_holiday(d))


def winter_weekday(day: str) -> bool:
    d = to_date(day)
    return (d.month in WINTER_MONTHS and d.weekday() < 5 and not is_holiday(d))
