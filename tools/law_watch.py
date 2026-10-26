#!/usr/bin/env python3
"""청아 노무수첩 법령 개정 감시.

국가법령정보센터 법령 검색 결과에서 감시 대상 법령(법률·시행령·시행규칙)의
연혁(시행일, 법률번호, 공포일, 개정구분)을 읽어, 지정한 날짜 이후 시행되는
버전을 모두 나열한다. law_watch.json의 reviewed 목록에 없는 버전은 NEW로 표시한다.

사용: python3 tools/law_watch.py [--since 2026-01-01] [--json]
"""
import argparse, html, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH = os.path.join(ROOT, "law_watch.json")
URL = "https://www.law.go.kr/LSW/lsScListR.do?menuId=1&subMenuId=15&tabMenuId=81"
PAT = re.compile(r"lsViewWideAll\('(\d+)','(\d+)'.*?title=\"([^\"]+)\"", re.S)
TITLE = re.compile(r"^(.*?) \[시행 ([0-9. ]+)\] \[([^\]]+)\]$")


def fetch(q):
    for _ in range(4):
        r = subprocess.run(["curl", "-sS", "-m", "40", "-X", "POST", URL,
                            "--data-urlencode", f"q={q}",
                            "--data", "outmax=50&pg=1&section=lawNm&fsort=10,41,21,31"],
                           capture_output=True)
        t = r.stdout.decode("utf-8", "ignore")
        if "lsViewWideAll" in t:
            return t
        time.sleep(4)
    return None


def ymd(s):
    p = [x for x in re.split(r"[. ]+", s) if x]
    return f"{int(p[0]):04d}-{int(p[1]):02d}-{int(p[2]):02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    w = json.load(open(WATCH, encoding="utf-8"))
    since = a.since or w.get("since", "2026-01-01")
    seen = set(w.get("reviewed", {}).keys())
    out, fail = [], []
    for law in w["laws"]:
        for suf in ("", " 시행령", " 시행규칙"):
            name = law + suf
            t = fetch(name)
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
                meta = m.group(3)
                key = f"{seq}"
                out.append({"law": m.group(1), "eff": eff, "meta": meta, "lsiSeq": seq,
                            "new": key not in seen})
            time.sleep(1)
    out.sort(key=lambda x: (x["eff"], x["law"]))
    if a.json:
        print(json.dumps({"items": out, "fail": fail}, ensure_ascii=False, indent=1))
    else:
        for x in out:
            print(("NEW " if x["new"] else "    ") + f'{x["eff"]} {x["law"]} [{x["meta"]}] lsiSeq={x["lsiSeq"]}')
        if fail:
            print("조회 실패:", ", ".join(fail))
    sys.exit(2 if fail else 0)


if __name__ == "__main__":
    main()
