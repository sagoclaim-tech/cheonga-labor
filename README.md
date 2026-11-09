# 청아노무법인 기준 앱

청아노무법인 사내용 웹앱입니다. 노동 기준금액·요율 조회, 계산기, 고용지원금 적용 검토, 통합 검색을 제공합니다.

- 화면: `index.html`
- 기준 데이터: `data.json` (수치·근거·출처·이력, 매일 아침 자동 점검으로 갱신)
- 설치·오프라인: `manifest.webmanifest`, `sw.js`, `icons/`

※ 본 앱은 1차 검토용이며, 최종 판단은 원문 법령·고시·지침으로 확인합니다.
- 법령·고시 개정 감시: `tools/law_watch.py`가 `law_watch.json`의 감시 법령(법률·시행령·시행규칙, laws)과 금액·요율 고시 검색어(admrul)로 국가법령정보센터를 조회해, 아직 검토하지 않은 개정(시행 또는 발령 2026.1.1. 이후)을 NEW로 보여 줍니다. 평일 자동 점검이 NEW 항목을 검토해 `data.json`에 반영하고, 결과를 `law_watch.json`의 reviewed(법령), reviewed_admrul(고시)에 기록합니다.
- 계산기 산식 감시: 산식·기간·비율이 화면 코드에 들어 있는 조문은 `law_watch.json`의 calc_deps에 있습니다. 해당 조문이 바뀌면 자동 점검은 화면을 고치지 않고 calc_pending에 기록해 보고하며, 화면 수정은 별도로 합니다.
- 데이터 점검: `python3 tools/check_data.py` (구조, 출처 도메인, 최저임금 연동 수치, 간이세액표 구간, 매년 갱신 기준 누락, 표기 원칙). 오류가 있으면 커밋하지 않습니다.
- 노동뉴스 탭: `sagoclaim-tech/labor-briefing` 저장소의 `daily/YYYY-MM-DD.html`을 화면에서 직접 읽어 이번 주와 지난 4주를 주 단위로 보여 줍니다(홈페이지 노동뉴스와 같은 방식). 브리핑을 올리면 별도 작업 없이 반영되며, 목록의 요약은 브리핑의 `summary-bar`(Today's Focus)에서 가져옵니다. 카카오 채널 구독 안내, 사무소 연락처, 간단 소식(부산·울산·경남 지역 소식)을 모두 그대로 표시하고, 노무수첩 배너만 뺍니다. ※ 홈페이지 게시본은 구독 안내, 연락처, 간단 소식을 빼는 기준이라 서로 다릅니다.
- 화면 점검: `python3 tools/smoke.py` (계산기 전부를 오늘과 다음 해 1월 기준으로 열어 오류·NaN 표시 확인, Playwright 필요).

## 포털 검색용 페이지
- 앱은 자바스크립트로 그리는 한 페이지라 포털이 내용을 읽지 못합니다. 그래서 `tools/build_pages.py`가 같은 데이터로 글이 들어 있는 페이지를 만듭니다: `interp/`(행정해석 한 건씩과 분야별 목록), `figures/`(기준 수치와 연도별 이력), `grants/`(고용지원금), `changes.html`(제도 변경·입법 동향), `sitemap.xml`.
- 자동 갱신: `.github/workflows/pages.yml`이 data.json, interp.json이 main에 올라올 때와 매일 0시 10분(한국시간)에 도구를 돌려 바뀐 페이지와 사이트맵만 커밋합니다. 손으로 고칠 필요가 없습니다. ※ 이 세 폴더와 changes.html, sitemap.xml은 도구 전용이니 직접 고치지 않습니다.
- lastmod: 페이지 내용이 바뀐 날만 `tools/pages_lastmod.json`에 기록해 사이트맵에 씁니다.
- 앱 연결: 페이지의 "앱에서 보기"는 `?i=<행정해석 id>`, `?g=<지원금 id>`, `#calc-<계산기>`로 앱의 해당 항목을 엽니다.

## 홈페이지 연동(embed)
- embed/nm.js: 청아노무법인 홈페이지(그누보드) 「노무수첩」 메뉴가 앱의 data.json, interp.json을 실시간으로 읽어 표시합니다. 앱 데이터가 갱신되면 홈페이지도 함께 바뀝니다.
- 홈페이지 내용관리 페이지: nm_figures(자주 찾는 숫자), nm_changes(개정·시행 예정), nm_grants(지원금 안내), nm_calc(노동 계산기). 본문에 `<div class="nm-embed nm-figures">` 형식으로 지정합니다. ※ 그누보드가 data- 속성을 지우므로 class로 지정합니다.
- 홈페이지 환경설정 추가 메타태그의 `ca-nm-css`, `ca-nm-js` 블록이 상단 배너(embed/sub06_bg.jpg, mo_sub06_bg.jpg)와 스크립트 로더입니다.
- 화면 계산 로직(요약 탭 GROUPS, changeList)을 바꾸면 embed/nm.js도 함께 맞춥니다.
