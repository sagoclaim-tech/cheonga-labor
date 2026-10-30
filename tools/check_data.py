#!/usr/bin/env python3
"""청아 노무수첩 데이터 무결성 점검.

data.json, interp.json, law_watch.json을 읽어 구조, 출처 도메인, 수치 정합성,
표기 원칙을 기계적으로 검사한다. 평일 자동 점검과 수동 수정 모두 커밋 전에 실행한다.

사용: python3 tools/check_data.py   (오류가 있으면 종료코드 1, 경고만 있으면 0)
"""
import json, os, re, sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERR, WARN = [], []
ALLOWED = ("law.go.kr", "opinion.lawmaking.go.kr", "easylaw.go.kr", "korea.kr", "moel.go.kr",
           "work24.go.kr", "comwel.or.kr", "nhis.or.kr", "nps.or.kr", "kead.or.kr", "bokjiro.go.kr",
           "mohw.go.kr", "minimumwage.go.kr", "likms.assembly.go.kr")
BAD_CHARS = re.compile(r"[—→←▶◀]")
BAD_TERMS = {"체당금": "대지급금", "장의비": "장례비", "출산휴가급여": "출산전후휴가 급여"}
STATUS = {"확정", "입법예고", "국회 계류", "정부안", "예산안"}
CATS = {"일·가정 양립", "임금·퇴직금", "근로시간·휴가", "고용보험", "사회보험", "산재보상", "지원금", "기타"}
TOPICS = {"최저임금", "임금", "퇴직금", "연차휴가", "근로시간", "실업급여", "모성보호", "지원금", "대지급금", "산재보상", "사회보험", "기타"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# 수치 기준의 상식 범위(단위 오류·자릿수 오류 차단용). 범위를 벗어나면 오류로 본다.
RANGE = {
    "min_wage_hourly": (9000, 20000), "min_wage_monthly": (1800000, 4200000),
    "ui_daily_max": (60000, 120000), "ui_daily_min": (55000, 120000),
    "np_rate": (8, 14), "hi_rate": (6, 9), "ltc_rate": (0.5, 1.5), "ei_ui_rate": (1.5, 2.5),
    "ei_ui_worker": (0.75, 1.25), "ia_avg_rate": (1, 2.5), "disabled_quota": (2.5, 4.5),
    "np_upper": (5000000, 9000000), "np_lower": (300000, 600000),
    "it_meal_free": (100000, 400000),
}

# 해마다 새 값이 정해지는 기준: (다음 해 시행 월-일, 올해 경고 시작 월-일)
RENEW = {
    "min_wage_hourly": ("01-01", "08-10"), "min_wage_monthly": ("01-01", "08-10"), "ui_daily_min": ("01-01", "08-10"),
    "ia_max": ("01-01", "12-15"), "ia_min": ("01-01", "12-15"), "funeral_max": ("01-01", "12-15"), "funeral_min": ("01-01", "12-15"),
    "hi_rate": ("01-01", "11-15"), "ltc_rate": ("01-01", "11-15"), "hi_cap_upper": ("01-01", "12-15"), "hi_cap_lower": ("01-01", "12-15"),
    "mat_cap": ("01-01", "12-20"), "spouse_leave_cap": ("01-01", "12-20"), "grant_min_pay": ("01-01", "12-20"),
    "np_upper": ("07-01", "06-20"), "np_lower": ("07-01", "06-20"), "ia_avg_rate": ("01-01", "12-20"),
}


def src_ok(u):
    if not u:
        return True
    m = re.match(r"^https?://([^/]+)", u)
    if not m:
        return False
    h = m.group(1).lower()
    return any(h == a or h.endswith("." + a) for a in ALLOWED)


def text_check(where, s, ctx=""):
    """ctx: 같은 항목의 다른 문장. 옛 명칭을 쓰면서 새 명칭을 함께 설명한 경우(명칭 변경 안내)는 허용한다."""
    if not isinstance(s, str):
        return
    if BAD_CHARS.search(s):
        WARN.append(f"{where}: em dash 또는 화살표 기호 사용")
    for b, g in BAD_TERMS.items():
        if b in s and g.replace(" ", "") not in (s + ctx).replace(" ", ""):
            WARN.append(f"{where}: '{b}' 대신 '{g}'")


def load(name):
    p = os.path.join(ROOT, name)
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception as e:
        ERR.append(f"{name}: JSON 오류 {e}")
        return None


def check_data(d):
    today = date.today().isoformat()
    items = d.get("items", {})
    for k, it in items.items():
        h = it.get("hist") or []
        if not h:
            ERR.append(f"items.{k}: hist 없음"); continue
        froms = [e.get("from") for e in h]
        if len(set(froms)) != len(froms):
            ERR.append(f"items.{k}: 같은 시행일(from) 중복 {froms}")
        for e in h:
            w = f"items.{k}[{e.get('from')}]"
            if not DATE.match(str(e.get("from", ""))):
                ERR.append(f"{w}: from 형식 오류")
            if not isinstance(e.get("value"), (int, float)) or isinstance(e.get("value"), bool):
                ERR.append(f"{w}: value가 숫자가 아님")
            elif k in RANGE and not (RANGE[k][0] <= e["value"] <= RANGE[k][1]):
                ERR.append(f"{w}: value {e['value']} 범위 밖 {RANGE[k]}")
            if not e.get("basis"):
                WARN.append(f"{w}: basis 없음")
            if not src_ok(e.get("src")):
                ERR.append(f"{w}: 허용되지 않은 출처 {e.get('src')}")
            if e.get("checked") and e["checked"] > today:
                ERR.append(f"{w}: checked가 미래 날짜")
            text_check(w + ".note", e.get("note"))
        # 직전 값 대비 급변(±40%) 경고
        hs = sorted(h, key=lambda e: e["from"])
        recent = (date.today() - timedelta(days=365)).isoformat()
        for a, b in zip(hs, hs[1:]):
            if b["from"] < recent:
                continue
            if isinstance(a.get("value"), (int, float)) and a["value"] and isinstance(b.get("value"), (int, float)):
                r = b["value"] / a["value"]
                if r > 1.4 or r < 0.6:
                    WARN.append(f"items.{k}: {a['from']} {a['value']} 에서 {b['from']} {b['value']}로 급변, 단위 확인")

    def at(k, f):
        cur = None
        for e in sorted(items.get(k, {}).get("hist", []), key=lambda e: e["from"]):
            if e["from"] <= f:
                cur = e
        return cur and cur.get("value")

    # 최저임금 연동 수치 정합성
    for e in items.get("min_wage_hourly", {}).get("hist", []):
        f, hw = e["from"], e["value"]
        mm = at("min_wage_monthly", f)
        if mm is not None and mm != hw * 209:
            ERR.append(f"min_wage_monthly[{f}]: {mm} 이 시간급 {hw} x 209 = {hw*209} 과 다름")
        if f >= "2019-01-01":
            lo = at("ui_daily_min", f)
            if lo is not None and round(lo) != round(hw * 8 * 0.8):
                WARN.append(f"ui_daily_min[{f}]: {lo} 이 최저임금 x 8 x 80% = {round(hw*8*0.8)} 과 다름(구직급여 하한 확인)")
            hi = at("ui_daily_max", f)
            if lo and hi and lo > hi:
                WARN.append(f"구직급여 {f}: 하한액 {lo} 이 상한액 {hi} 보다 큼(상한액 개정 여부 확인, 계산기는 하한액 지급으로 처리)")

    # 매년 바뀌는 기준: 다음 해 값이 들어갈 시기가 됐는데 비어 있으면 경고(고시 발령 여부 확인용)
    for k, (mmdd, when) in RENEW.items():
        if k not in items:
            continue
        y = date.today().year
        target = f"{y}-{mmdd}" if f"{y}-{mmdd}" > today else f"{y+1}-{mmdd}"
        ty = int(target[:4])
        start = f"{ty if when <= mmdd else ty-1}-{when}"
        if today >= start and not any(e["from"] >= target for e in items[k]["hist"]):
            WARN.append(f"items.{k}: {target} 시행 값 미반영(매년 고시·결정 사항, 발령 여부 확인)")

    # 표 자료
    for k, t in d.get("tables", {}).items():
        vs = t.get("versions") or []
        fr = [v.get("from") for v in vs]
        if len(set(fr)) != len(fr):
            ERR.append(f"tables.{k}: from 중복")
        for v in vs:
            if not src_ok(v.get("src")):
                ERR.append(f"tables.{k}[{v.get('from')}]: 허용되지 않은 출처")
        if k == "it_simple":
            for v in vs:
                rows = [list(map(lambda x: 0 if x == "-" else float(x), r.split(","))) for r in v["rows"]]
                for i, r in enumerate(rows):
                    if len(r) != 13:
                        ERR.append(f"it_simple[{v['from']}] {i}행: 칸 수 {len(r)}"); break
                    if i and r[0] != rows[i - 1][1]:
                        ERR.append(f"it_simple[{v['from']}] {i}행: 구간이 이어지지 않음 {rows[i-1][1]} {r[0]}")
                    if any(r[2 + j] < r[3 + j] for j in range(10)):
                        ERR.append(f"it_simple[{v['from']}] {i}행: 가족 수가 늘수록 세액이 커짐")
                for j in range(2, 13):
                    col = [r[j] for r in rows]
                    if any(b < a for a, b in zip(col, col[1:])):
                        ERR.append(f"it_simple[{v['from']}]: {j-1}인 열이 급여 증가에 따라 줄어듦"); break

    # 제도 변경
    seen = set()
    for i, s in enumerate(d.get("scheduled", [])):
        w = f"scheduled[{i}] {s.get('title','')}"
        for f in ("from", "cat", "title", "status", "basis"):
            if not s.get(f):
                ERR.append(f"{w}: {f} 없음")
        if s.get("status") not in STATUS:
            ERR.append(f"{w}: status '{s.get('status')}' 허용값 아님")
        if s.get("cat") not in CATS:
            ERR.append(f"{w}: cat '{s.get('cat')}' 허용값 아님")
        if not src_ok(s.get("src")):
            ERR.append(f"{w}: 허용되지 않은 출처 {s.get('src')}")
        key = (s.get("from"), s.get("title"))
        if key in seen:
            ERR.append(f"{w}: 같은 시행일·제목 중복")
        seen.add(key)
        for f in ("title", "before", "after", "note"):
            text_check(f"{w}.{f}", s.get(f))
    for i, n in enumerate(d.get("notices", [])):
        if not src_ok(n.get("src")):
            ERR.append(f"notices[{i}]: 허용되지 않은 출처 {n.get('src')}")
        text_check(f"notices[{i}]", n.get("text"))
    for g in d.get("grants", []):
        for k2, v in g.items():
            if isinstance(v, str) and k2 in ("src",) and not src_ok(v):
                ERR.append(f"grants.{g.get('id')}: 허용되지 않은 출처 {v}")


def check_interp(j):
    its = j.get("items", [])
    ids = [x.get("id") for x in its]
    if len(set(ids)) != len(ids):
        ERR.append("interp: id 중복")
    nos = [x.get("no") for x in its if x.get("no")]
    if len(set(nos)) != len(nos):
        dup = sorted({n for n in nos if nos.count(n) > 1})
        WARN.append(f"interp: 문서번호 중복 {dup[:5]}")
    if j.get("meta", {}).get("count") != len(its):
        ERR.append(f"interp: meta.count {j.get('meta',{}).get('count')} 와 실제 {len(its)} 불일치")
    for x in its:
        w = f"interp {x.get('id')}"
        if x.get("topic") not in TOPICS:
            ERR.append(f"{w}: topic '{x.get('topic')}' 허용값 아님")
        if not DATE.match(str(x.get("date", ""))):
            ERR.append(f"{w}: date 형식 오류")
        if not src_ok(x.get("src")):
            ERR.append(f"{w}: 허용되지 않은 출처 {x.get('src')}")
        if not x.get("orig"):
            WARN.append(f"{w}: orig 비어 있음")
        ctx = " ".join(str(x.get(f) or "") for f in ("q", "a", "note"))
        for f in ("q", "a", "note"):
            text_check(f"{w}.{f}", x.get(f), ctx)


def check_guides(g):
    its = g.get("items", [])
    if g.get("meta", {}).get("count") != len(its):
        ERR.append("guides: meta.count 불일치")
    for x in its:
        w = f"guides {x.get('id')}"
        if x.get("topic") not in TOPICS:
            ERR.append(f"{w}: topic 허용값 아님")
        if not re.match(r"^\d{4}-\d{2}(-\d{2})?$", str(x.get("date", ""))):
            ERR.append(f"{w}: date 형식 오류")
        f = x.get("file")
        if f and not os.path.exists(os.path.join(ROOT, f)):
            ERR.append(f"{w}: 파일 없음 {f}")
        if not src_ok(x.get("src")):
            ERR.append(f"{w}: 허용되지 않은 출처")
        for i, t in enumerate(x.get("points") or []):
            text_check(f"{w}.points[{i}]", t)
        text_check(f"{w}.note", x.get("note"))


def check_watch(w):
    for k, v in w.get("reviewed", {}).items():
        if not v.get("decision"):
            ERR.append(f"law_watch.reviewed {k}: decision 없음")
    for k, v in w.get("reviewed_admrul", {}).items():
        if not v.get("decision"):
            ERR.append(f"law_watch.reviewed_admrul {k}: decision 없음")


def main():
    d, j, w = load("data.json"), load("interp.json"), load("law_watch.json")
    if d: check_data(d)
    if j: check_interp(j)
    if w: check_watch(w)
    if os.path.exists(os.path.join(ROOT, "guides.json")):
        g = load("guides.json")
        if g: check_guides(g)
    for e in ERR: print("오류", e)
    for e in WARN: print("경고", e)
    print(f"점검 완료: 오류 {len(ERR)}건, 경고 {len(WARN)}건")
    sys.exit(1 if ERR else 0)


if __name__ == "__main__":
    main()
