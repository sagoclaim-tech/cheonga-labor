#!/usr/bin/env python3
"""청아 노무수첩 법령·고시 개정 감시.

1) 법령: 국가법령정보센터 법령 검색 결과에서 감시 대상 법령(법률·시행령·시행규칙)의
   연혁(시행일, 법률번호, 공포일, 개정구분)을 읽어, 지정한 날짜 이후 시행되는 버전을
   모두 나열한다. law_watch.json의 reviewed(키: lsiSeq)에 없는 버전은 NEW로 표시한다.
2) 행정규칙(고시·공고): 금액·요율을 정하는 고시(최저임금, 최고·최저 보상기준금액,
   대지급금 상한, 출산전후휴가 급여 상한, 산재보험료율, 두루누리, 국민연금 기준소득월액,
   장애인 고용부담금 등)를 국가법령정보센터 행정규칙 웹 검색(발령일자 내림차순, 안 되면
   오픈API target=admrul)으로 찾아, 지정한 날짜 이후 발령된 것 중
   reviewed_admrul(키: 행정규칙일련번호)에 없는 것을 NEW로 표시한다.
   고시 원문: https://www.law.go.kr/LSW/admRulInfoR.do?admRulSeq={행정규칙일련번호}

사용: python3 tools/law_watch.py [--since 2026-01-01] [--json] [--only law|admrul]
종료코드: 0 정상, 2 일부 조회 실패(실패 목록 출력)
"""
import argparse, html, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH = os.path.join(ROOT, "law_watch.json")
# 2026. 11. 국가법령정보센터 검색 화면 개편으로 lsScListR.do, admRulScListR.do가 오류페이지만 돌려준다.
# 새 검색 화면(lsSc.do, admRulSc.do)은 GET 요청에 결과 표를 HTML로 바로 담아 준다. 연혁 탭을 쓴다.
URL = "https://www.law.go.kr/LSW/lsSc.do?menuId=1&subMenuId=17&tabMenuId=93"
API = "https://www.law.go.kr/DRF/lawSearch.do"
ADM_URL = "https://www.law.go.kr/LSW/admRulSc.do?menuId=5&subMenuId=43&tabMenuId=193"
PAT = re.compile(r"lsViewWideAll\('(\d+)','(\d+)'.*?title=\"([^\"]+)\"", re.S)
TITLE = re.compile(r"^(.*?) \[시행 ([0-9. ]+)\] \[([^\]]+)\]$")
EMPTY = re.compile(r"총\s*<span>\s*0\s*</span>\s*건")
ROWPOP = re.compile(r"lawInfoPop\('(\d+)','(\d+)','(\d*)',\s*'(\d+)'")


def curl(args, tries=6):
    for i in range(tries):
        r = subprocess.run(["curl", "-sS", "-m", "40"] + args, capture_output=True)
        t = r.stdout.decode("utf-8", "ignore")
        if r.returncode == 0 and len(t) > 500:
            yield t
        time.sleep(3 + i * 2)


def fetch_law(q):
    """법령 연혁 검색 결과 행 목록. 결과 0건이면 [], 접속 실패면 None.
    각 행: {"seq", "name", "anc"(공포일 YYYY. M. D.), "kind", "no", "eff"(YYYY-MM-DD), "rv"}"""
    for t in curl(["-G", URL, "--data-urlencode", f"query={q}", "--data", "outmax=300"]):
        if "오류페이지" in t[:3000]:
            continue
        rows = []
        for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S):
            m = ROWPOP.search(tr)
            if not m:
                continue
            tds = [_cell(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(tds) < 7:
                continue
            rows.append({"seq": m.group(1), "name": tds[1], "anc": tds[2], "kind": tds[3], "no": tds[4],
                         "eff": d8(m.group(4)), "rv": tds[6]})
        if rows:
            return rows
        if EMPTY.search(t):
            return []
    return None


def _cell(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()


def _d8(s):
    p = [x for x in re.split(r"[. ]+", re.sub(r"[^0-9. ]", "", s or "")) if x]
    return f"{int(p[0]):04d}{int(p[1]):02d}{int(p[2]):02d}" if len(p) >= 3 else ""


def fetch_admrul_html(q, since="2026-01-01", pages=3):
    """행정규칙 검색(국가법령정보센터 웹 검색 화면, 발령일자 내림차순).
    오픈API와 같은 키(소관부처명, 행정규칙종류, 발령일자 등)의 dict 목록을 돌려준다.
    결과 0건이면 [], 접속 실패면 None."""
    lim = since.replace("-", "")
    rows = []
    for pg in range(1, pages + 1):
        got = None
        for t in curl(["-G", ADM_URL, "--data-urlencode", f"query={q}",
                       "--data", f"outmax=100&pg={pg}"]):
            if "오류페이지" in t[:3000]:
                continue
            if "lawInfPop(" in t or "showDefAdmRul" in t or "showAdmRulCts" in t:
                got = t; break
            if EMPTY.search(t) or "검색결과가 없습니다" in t or "검색결과 가 없습니다" in t:
                got = ""; break
        if got is None:
            return None if pg == 1 else rows
        older = False
        for tr in re.findall(r"<tr>(.*?)</tr>", got, re.S):
            sn = re.search(r"(?:lawInfPop|showDefAdmRul|showAdmRulCts)\('(\d+)'", tr)
            tds = [_cell(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if not sn or len(tds) < 8:
                continue
            org, kindfull = tds[7], tds[2]
            kind = next((k for k in ("고시", "공고", "훈령", "예규", "지침") if kindfull.endswith(k)), kindfull)
            issued = _d8(tds[4])
            if issued and issued < lim:
                older = True
            rows.append({"행정규칙일련번호": sn.group(1), "행정규칙명": tds[1], "행정규칙종류": kind,
                         "발령번호": re.sub(r"^제|호$", "", tds[3]), "발령일자": issued,
                         "시행일자": _d8(tds[5]), "제개정구분명": tds[6], "소관부처명": org})
        if older or got.count("lawInfPop(") < 100:
            break
        time.sleep(1)
    return rows


def fetch_admrul(q, since="2026-01-01"):
    """행정규칙 검색. 웹 검색 화면을 먼저 쓰고, 안 되면 오픈API(JSON)를 쓴다.
    ※ 오픈API는 OC=test 계정이 2026.11.2.부터 '사용자 정보 검증 실패'로 거절되어 보조 경로로만 둔다.
    접속 실패면 None."""
    r = fetch_admrul_html(q, since)
    if r is not None:
        return r
    for t in curl(["-G", API, "--data-urlencode", "OC=test", "--data-urlencode", "target=admrul",
                   "--data-urlencode", "type=JSON", "--data-urlencode", f"query={q}",
                   "--data-urlencode", "display=100", "--data-urlencode", "sort=ddes"], tries=2):
        try:
            d = json.loads(t)["AdmRulSearch"]
        except Exception:
            continue
        r = d.get("admrul") or []
        return [r] if isinstance(r, dict) else r
    return None


def ymd(s):
    p = [x for x in re.split(r"[. ]+", s) if x]
    return f"{int(p[0]):04d}-{int(p[1]):02d}-{int(p[2]):02d}"


def d8(s):
    s = str(s or "")
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else s


def watch_laws(w, since, out, fail):
    seen = set(w.get("reviewed", {}).keys())
    for law in w["laws"]:
        for suf in ("", " 시행령", " 시행규칙"):
            name = law + suf
            t = fetch_law(name)
            if t is None:
                fail.append(name); continue
            for r in t:
                if r["name"].replace(" ", "") != name.replace(" ", ""):
                    continue
                if r["eff"] < since:
                    continue
                out.append({"kind": "law", "law": r["name"], "eff": r["eff"],
                            "meta": f'{r["kind"]} {r["no"]}, {r["anc"]}, {r["rv"]}',
                            "lsiSeq": r["seq"], "new": r["seq"] not in seen})
            time.sleep(1)


def watch_admrul(w, since, out, fail):
    cfg = w.get("admrul", {})
    orgs = set(cfg.get("orgs", []))
    kinds = set(cfg.get("kinds", []))
    seen = set(w.get("reviewed_admrul", {}).keys())
    got = {}
    for q in cfg.get("queries", []):
        rows = fetch_admrul(q, since)
        if rows is None:
            fail.append(f"고시:{q}"); continue
        for x in rows:
            if orgs and x.get("소관부처명") not in orgs:
                continue
            if kinds and x.get("행정규칙종류") not in kinds:
                continue
            issued = d8(x.get("발령일자"))
            if issued < since:
                continue
            sn = str(x.get("행정규칙일련번호"))
            got[sn] = {"kind": "admrul", "law": x.get("행정규칙명"), "eff": d8(x.get("시행일자")),
                       "issued": issued, "no": str(x.get("발령번호") or ""),
                       "meta": f'{x.get("소관부처명")} {x.get("행정규칙종류")} 제{x.get("발령번호")}호, {x.get("제개정구분명")}',
                       "serial": sn, "query": q, "new": sn not in seen}
        time.sleep(1)
    out.extend(got.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", choices=["law", "admrul"], default=None)
    a = ap.parse_args()
    w = json.load(open(WATCH, encoding="utf-8"))
    since = a.since or w.get("since", "2026-01-01")
    out, fail = [], []
    if a.only in (None, "law"):
        watch_laws(w, since, out, fail)
    if a.only in (None, "admrul"):
        watch_admrul(w, since, out, fail)
    out.sort(key=lambda x: (x["kind"], x["eff"], x["law"]))
    if a.json:
        print(json.dumps({"items": out, "fail": fail}, ensure_ascii=False, indent=1))
    else:
        for x in out:
            flag = "NEW " if x["new"] else "    "
            if x["kind"] == "law":
                print(f'{flag}{x["eff"]} {x["law"]} [{x["meta"]}] lsiSeq={x["lsiSeq"]}')
            else:
                print(f'{flag}[고시] 시행 {x["eff"]} {x["law"]} [{x["meta"]}, 발령 {x["issued"]}] serial={x["serial"]}')
                if x["new"]:
                    print(f'      원문: https://www.law.go.kr/LSW/admRulInfoR.do?admRulSeq={x["serial"]}')
        print(f'NEW 법령 {sum(1 for x in out if x["new"] and x["kind"]=="law")}건, NEW 고시 {sum(1 for x in out if x["new"] and x["kind"]=="admrul")}건')
        if fail:
            print("조회 실패:", ", ".join(fail))
    sys.exit(2 if fail else 0)


if __name__ == "__main__":
    main()
