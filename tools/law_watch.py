#!/usr/bin/env python3
"""청아 노무수첩 법령·고시 개정 감시.

1) 법령: 국가법령정보센터 법령 검색 결과에서 감시 대상 법령(법률·시행령·시행규칙)의
   연혁(시행일, 법률번호, 공포일, 개정구분)을 읽어, 지정한 날짜 이후 시행되는 버전을
   모두 나열한다. law_watch.json의 reviewed(키: lsiSeq)에 없는 버전은 NEW로 표시한다.
2) 행정규칙(고시·공고): 금액·요율을 정하는 고시(최저임금, 최고·최저 보상기준금액,
   대지급금 상한, 출산전후휴가 급여 상한, 산재보험료율, 두루누리, 국민연금 기준소득월액,
   장애인 고용부담금 등)를 국가법령정보센터 오픈API(target=admrul)로 찾아, 지정한 날짜
   이후 발령된 것 중 reviewed_admrul(키: 행정규칙일련번호)에 없는 것을 NEW로 표시한다.

사용: python3 tools/law_watch.py [--since 2026-01-01] [--json] [--only law|admrul]
종료코드: 0 정상, 2 일부 조회 실패(실패 목록 출력)
"""
import argparse, html, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH = os.path.join(ROOT, "law_watch.json")
URL = "https://www.law.go.kr/LSW/lsScListR.do?menuId=1&subMenuId=15&tabMenuId=81"
API = "https://www.law.go.kr/DRF/lawSearch.do"
PAT = re.compile(r"lsViewWideAll\('(\d+)','(\d+)'.*?title=\"([^\"]+)\"", re.S)
TITLE = re.compile(r"^(.*?) \[시행 ([0-9. ]+)\] \[([^\]]+)\]$")
EMPTY = re.compile(r"총\s*(<[^>]*>\s*)*0\s*(<[^>]*>\s*)*건")


def curl(args, tries=6):
    for i in range(tries):
        r = subprocess.run(["curl", "-sS", "-m", "40"] + args, capture_output=True)
        t = r.stdout.decode("utf-8", "ignore")
        if r.returncode == 0 and len(t) > 500:
            yield t
        time.sleep(3 + i * 2)


def fetch_law(q):
    """검색 결과 HTML. 결과 0건이면 빈 문자열, 접속 실패면 None."""
    for t in curl(["-X", "POST", URL, "--data-urlencode", f"q={q}",
                   "--data", "outmax=50&pg=1&section=lawNm&fsort=10,41,21,31"]):
        if "lsViewWideAll" in t:
            return t
        if EMPTY.search(t) or "검색결과 가 없습니다" in t or "검색결과가 없습니다" in t:
            return ""
    return None


def fetch_admrul(q):
    """행정규칙 검색(오픈API JSON). 접속 실패면 None."""
    for t in curl(["-G", API, "--data-urlencode", "OC=test", "--data-urlencode", "target=admrul",
                   "--data-urlencode", "type=JSON", "--data-urlencode", f"query={q}",
                   "--data-urlencode", "display=100", "--data-urlencode", "sort=ddes"]):
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
            for seq, ef, title in PAT.findall(t):
                title = re.sub(r"\s+", " ", html.unescape(title)).strip()
                m = TITLE.match(title)
                if not m or m.group(1).replace(" ", "") != name.replace(" ", ""):
                    continue
                eff = ymd(m.group(2))
                if eff < since:
                    continue
                out.append({"kind": "law", "law": m.group(1), "eff": eff, "meta": m.group(3),
                            "lsiSeq": seq, "new": seq not in seen})
            time.sleep(1)


def watch_admrul(w, since, out, fail):
    cfg = w.get("admrul", {})
    orgs = set(cfg.get("orgs", []))
    kinds = set(cfg.get("kinds", []))
    seen = set(w.get("reviewed_admrul", {}).keys())
    got = {}
    for q in cfg.get("queries", []):
        rows = fetch_admrul(q)
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
        print(f'NEW 법령 {sum(1 for x in out if x["new"] and x["kind"]=="law")}건, NEW 고시 {sum(1 for x in out if x["new"] and x["kind"]=="admrul")}건')
        if fail:
            print("조회 실패:", ", ".join(fail))
    sys.exit(2 if fail else 0)


if __name__ == "__main__":
    main()
