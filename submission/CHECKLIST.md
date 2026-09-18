# 제출 체크리스트 — NextStep Hacks 2026

**마감 2026-09-20 17:00 EDT.** 미리 제출해 두는 게 엄격하게 유리하다 —
Devpost 공식 문서: *"You can access and make changes to your submission until the submission
deadline."* **마감 후에는 손대지 마라** (제출물에 반영되지 않고 자격 위험).

---

## 1. 제출 전 저장소 확인

```bash
python3 src/check_demo.py                       # 27/27, 분모 고정
python3 src/sabotage.py                         # 전부 검출 · 걸린 시간은 스크립트가 찍는다
python3 src/determinism.py data/fuel2026.xml    # 시드 5종에서 동일
```

- [ ] 위 셋 전부 통과 (사보타주는 수 분 걸린다. **도는 동안 저장소를 건드리지 마라** —
      복원이 네 편집을 되돌린다. 도구가 그런 일이 있었으면 경고를 찍는다)
- [ ] `python3 src/card.py data/fuel2026.xml 20` — **제출용 카드는 20시(차이 89 g)** 여야 한다
- [ ] `python3 tools/svg2png.py figures/card.svg figures/chart.svg` — PNG 재생성
      (**빼먹으면 검사가 잡는다** — PNG 는 출처 SVG 의 해시로 묶여 있다. 한 번 빼먹어서
      사흘 묵은 차트가 영상에 실린 적이 있다)
- [ ] `python3 tools/svg2png.py --thumb figures/card.png figures/thumbnail.png` — 3:2 썸네일
- [ ] **그림 넷을 눈으로 열어 본다.** 변환기가 한 번 차트 오른쪽을 잘라먹은 적 있다(49절)

## 2. git

- [ ] `git add -A && git commit` — 저장소는 `grid-clock/` 이고 `git init` 은 되어 있다
- [ ] `data/fuel2026.xml`(5.5 MB)이 **커밋에 들어갔는지 확인.** 빠지면 클론이 안 돈다
- [ ] GitHub 에 push, 공개 저장소

## 3. 영상

**영상은 코드로 만든다. 촬영하지 않는다.** 파이프라인은
`_workflow/video/hackathon-video/` (덱: `tools/decks/grid-clock.mjs`).

```bash
cd ~/Desktop/Hackerthon/_workflow/video/hackathon-video
./make.sh grid-clock          # 수치 읽기 → 음성 → 실측 길이 → 타입검사
npx remotion render GridClock out/grid-clock.mp4
```

- [x] 수치가 **스크립트 출력에 묶여 있다** — 분석이 바뀌면 빌드가 죽는다
- [x] 길이 **4:36** (규정 3~5분). 상·하한을 `limits: [180, 300]` 로 덱에 박아 뒀다
- [x] 낭독 15장면 전부 **본인 목소리 복제**(로컬, 업로드 없음), 라우드니스 -16 LUFS 통일
- [ ] **사람이 한 번 끝까지 본다** — 자동 검사는 잘림·속도까지만 잡는다. 말투는 못 잡는다
- [ ] **YouTube 나 Vimeo 에 업로드** — Devpost 는 파일 업로드가 아니라 **링크**를 받는다
- [ ] 공개 또는 링크 공개(비공개면 심사위원이 못 본다)

타이머 장면(6번, "A timer already captures 100.0 % of what we offer")이 이 영상의 핵심이다.
`submission/video-script.md` 는 **촬영용 옛 대본**이다 — 실제 대본은 덱의 `narration` 이다.

## 3-2. 라이브 앱 (새로 생김 — "(if applicable)" 이지만 Completion 에 쓰인다)

```bash
python3 src/export_web.py data/fuel2026.xml   # web/data.json + web/index.html 생성
open web/index.html                            # 서버 없이 그냥 열린다
```

- [x] 의존성 0 · 백엔드 0 · **파일로 열림**(클론 → 더블클릭)
- [x] 템플릿 `web/page.html` 에 **분석 수치 0개** — `export_web.py` 가 주입한다
- [ ] 어디에 올릴지 (GitHub Pages 가 가장 싸다. `web/` 를 그대로 게시)
- [ ] Devpost "Try it out links" 에 저장소 URL + 페이지 URL 둘 다

## 4. Devpost 폼 (칸 순서대로)

| # | 칸 | 우리 것 |
|---|---|---|
| 1 | Project name | **Grid Clock** |
| 2 | Project tagline (필수) | `submission/devpost.md` 맨 위 후보 A/B/C 중 **택1** |
| 3 | Thumbnail image | `figures/thumbnail.png` (3:2, 152 KB) |
| 4 | Project story | `submission/devpost.md` 본문 — **Inspiration 을 먼저 채워라** |
| 5 | Built with tags | `python` `xml` `svg` `ieso-open-data` `no-dependencies` |
| 6 | Try it out links | GitHub 저장소 URL **+ `web/index.html` 게시 주소** |
| 7 | Image gallery | `figures/chart.png`, `figures/card.png` |
| 8 | Video demo link | YouTube/Vimeo URL |

**형식 제한**: 이미지는 JPG·PNG·GIF 만, 최대 5 MB. **SVG 안 받는다.**

## 5. 사람만 할 수 있는 것

- [ ] **Inspiration 문단** — `devpost.md` 에 뼈대만 있다. 본인 경험으로 채워라. 대신 쓰지 않았다
- [ ] **tagline 택1** — A 를 추천하지만 정하는 건 사람이다
- [ ] **영상 전체 시청** 후 업로드 (게시는 사람이 한다)
- [ ] 저장소 커밋·푸시
- [ ] 제출 버튼

## 6. 제출 후

- [ ] 제출 완료 화면과 시각을 기록
- [ ] **마감 전까지는 수정 가능.** 마감 후에는 건드리지 마라
