# 영상 대본 — Grid Clock

**목표 4:10~5:00.** 규정 페이지가 "3-5 minutes" 이고 이게 최신이다 — 메인의 "5분 이하"는
2021년부터 복붙된 문구다(`hackathon research` 가 이 어긋남을 잡아냈다). **상한 5분을 넘기지 마라.**
비동기 심사이므로 **말로 보충할 기회가 없다.** 화면에 보이는 것이 전부다.

---

## 0:00–0:20 — 문제와 해결을 트랙 단어로 먼저 말한다

**화면**: 카드 한 장 (`figures/card.svg`). 다른 것 없음.

> "The **environmental problem** is this: Ontario's electricity price tells you *when it's
> cheap*, and people read that as *when it's clean*. It isn't.
> My **solution** is a clock that tells you the difference."

**자막으로 동시에**: `problem: price ≠ carbon` / `solution: a clock that says which hour`

> "This card says: run the dryer at 3 a.m., not 9 p.m. Same price. Less gas."

*(심사위원이 추론하게 두지 않는다. 트랙 원문의 두 단어를 20초 안에 말로 박는다.)*

---

## 0:20–1:10 — 반직관적 사실 하나

**화면**: 차트 (`figures/chart.svg`)가 왼쪽에서 그려진다. 회색 띠 먼저, 빨간 선 나중.

> "Ontario's off-peak rate is one price — 9.8 cents — for twelve hours, 7 p.m. to 7 a.m.
> Inside that single price, this is how much of the province's electricity comes from
> natural gas."

**노란 칠이 나타나는 순간 멈춘다.**

> "Nine p.m. is 25.23 percent gas. Three a.m. is 19.06 percent. Same price.
> And here's the part I didn't expect —"

**on-peak 최고 지점에 선을 긋는다.**

> "— the worst hour inside the *cheapest* bracket burns more gas than **any** hour inside
> the most expensive one. The cheap window hides its own peak."

*(여기가 심사위원이 기억할 한 문장이다. 100편 중 기억되는 건 반직관적 사실 하나다.)*

---

## 1:10–1:40 — 왜 이런 일이 생기는가 (기전, 통계 아님)

**화면**: 수요 곡선과 배출 곡선을 겹쳐 놓은 간단한 도해 (또는 차트 위 주석)

> "This isn't a coincidence, and it isn't a statistical fluke. Tariff brackets were drawn to
> follow **demand**. Off-peak starts at 7 p.m. because demand falls there.
> But gas plants are still ramping down until nine. Demand is not carbon."

*(p값으로 우기지 않는다. 기전이 더 강하고 반박하기 어렵다.)*

---

## 1:40–2:40 — 어떻게 만들었나

**화면**: 터미널. 실제로 실행한다.

```
python3 src/parse_ieso.py data/fuel2026.xml
python3 src/chart.py data/fuel2026.xml
```

> "IESO publishes an hourly fuel-mix report. No key, no signup, 5.7 megabytes of XML.
> I stream it with Python's standard library — 6,144 hours, January first to September
> thirteenth."

> "Every figure you've seen is drawn by the standard library too. No matplotlib, no
> dependencies. The SVG is written by hand."

**한 줄 강조 자막**: `zero dependencies — including the chart`

> "And the headline needs **no emission factor at all.** Gas share is measured.
> Whatever number you assign to a gas plant, the ordering and the 1.324× ratio don't move."

*(심사위원이 빅테크 현업이다. "가정을 하나 제거했다"가 먹히는 종류의 청중이다.)*

---

## 2:40–3:30 — 내가 틀린 것들

**화면**: 표 한 장. 일곱 줄 — 화면에 한 번에 다 띄우지 말고 한 줄씩 나타나게.

| 내가 예상한 것 | 측정 결과 |
|---|---|
| 창을 넓히면 어긋남이 사라진다 | 사라지지 않는다. 튄다. 단조인 건 비율뿐(1.324→1.224) |
| p = 0.0005, 유의하다 | 자기상관(0.933)이 부풀렸다. 보수적 귀무에서 0.0240 — 48배 |
| 8시간 창의 튐은 신호다 | 정렬 인공물이다. 창 시작점만 옮기면 −4.2~+6.4로 흔들린다 |
| 우리 도구가 대안보다 낫다 | **2시 타이머가 우리 것의 96.2 %를 이미 준다** |
| 검증 스크립트는 당연히 재현된다 | **둘이 실행마다 다른 답을 냈다.** 집합 순회 순서에 기대고 있었다 |
| 주말만 거르면 평일이 나온다 | **공휴일이 섞여 있었다.** 빼니 최선 시각이 4시→3시로 뒤집혔다 |
| 우리가 고르는 변수가 중요하다 | 사이클 길이 무시 비용 0.064 pp, 시각 해상도 0.217 pp — **둘 다 작다** |

> [!warning] 5분을 넘기면 **위 세 줄부터 잘라라.**
> 아래 네 줄(타이머·재현성·공휴일·사이클)이 강하다 — 전부 *우리에게 불리한* 발견이고,
> 심사위원이 기억하는 건 그쪽이다. 위 세 줄은 없어도 논지가 선다.
> 표를 읽지 말고 **화면에 띄운 채 말로는 한 줄만** 집어라.

> "I ran a permutation test and got p equals 0.0005. Then I checked whether hour-to-hour
> autocorrelation was inflating it. It was — lag-one is 0.933. Under a null that preserves the
> shape of the daily curve, p is 0.0240. Forty-eight times weaker."

> "So I stopped claiming statistical surprise. The measurement stands on its own."

**8초 척도스윕 문장**:
> "Widening the window from one hour to eight shrinks what you can act on — 1.324× down to
> 1.224×. That's why this says an hour, not an evening."

---

## 3:30–4:30 — 주장하지 않는 것 (타이머 문단이 이 영상의 핵심이다)

**화면**: 검은 화면에 흰 글씨. 숫자 두 개만 크게, 같은 크기로: `19.27 %` / `19.06 %`

> "Here's the objection I'd make if I were watching this. A twelve-dollar plug-in timer set to
> two a.m. lands on 19.27 percent gas. My recommendation is three a.m., at 19.06. I beat the
> timer by **two tenths of a percentage point.** A twelve-dollar timer already gets you
> ninety-six percent of this."

**멈춤.**

> "And I can show you exactly how little precision I have. I had been treating statutory holidays
> as ordinary weekdays. Ontario bills them off-peak all day, so that was wrong. Excluding four of
> them moved my answer from four a.m. to three a.m. Two a.m. and three a.m. differ by
> **two tenths of a percentage point.** That is the resolution of my hour-picking."

**자막**: `two a.m. vs three a.m. = 0.217 pp — a methodology choice decides it`

> "And it gets worse for me. I name a start hour and ignore how long your dryer actually runs.
> A three-hour cycle moves the best start to two a.m. Ignoring that costs 0.064 points, against
> the 0.217 that separates the hour I print from the next one. **Neither margin is large.**"

**다음 문장이 답이다. 여기서 톤이 바뀐다.**

> "So I stopped selling the hour. What the timer can't do is give you a *reason* to set it. The
> six-point-oh-six percentage points that matter are between *evening* and *overnight* — four
> times larger than anything available inside the night. And at seven p.m. your default tariff
> quotes you its cheapest price, at the hour with the highest gas share it sells. This isn't a scheduler.
> It's the measurement that argues with your electricity bill."

> "I'm not claiming carbon saved. A lower gas share at two a.m. doesn't prove a shifted
> kilowatt-hour burns less gas — gas may be marginal at both hours. That needs marginal intensity
> and measured load, and I have neither. This is an opportunity signal, not a saving."

> "Ontario's Ultra-Low Overnight plan already prices the evening at 39.1 cents. It's a baseline
> to beat, not proof that the tariffs contradict each other — they're separate products and
> nobody's on both. The point is which one you get **without asking.**"

*(불리한 사실을 심사위원보다 먼저 말한다. 비대칭 심사에서는 이것이 가장 값싼 신뢰다.
공휴일 실수를 직접 말하는 것이 특히 그렇다 — 심사위원이 찾아낼 수 있는 종류의 실수이고,
먼저 말하면 "이 사람은 자기 데이터를 안다"가 된다.)*

---

## 촬영 전 확인

- [ ] `python3 src/check_demo.py` 통과 (**25/25**, 분모 고정)
- [ ] `python3 src/sabotage.py` 통과 (**33/33 검출**) — 검사가 살아 있다는 증거
- [ ] `python3 src/determinism.py data/fuel2026.xml` 통과 — 같은 입력에 같은 답
- [ ] `python3 src/baseline.py data/fuel2026.xml` — 타이머 수치를 말하기 전에 눈으로 확인
- [ ] `python3 src/card.py data/fuel2026.xml 20` — **제출용 카드는 20시(차이 91 g)** 여야 한다.
      검사가 시각 스윕을 돌아도 이제 이 파일을 안 덮어쓴다(48절).
- [ ] `python3 tools/svg2png.py figures/card.svg figures/chart.svg` — **Devpost 는 SVG 를 안 받는다.**
      JPG·PNG·GIF 만, 최대 5 MB. 업로드용 PNG 를 다시 만들어라.
- [ ] 차트·카드 SVG를 화면에서 실제로 열어 확인
- [ ] 카드 시각을 바꿔 보이는 장면이 있다면 그 시각도 미리 실행
- [ ] 3:30 이상 4:30 이하
- [ ] 첫 20초에 problem / solution 두 단어가 **말로** 나왔는가
