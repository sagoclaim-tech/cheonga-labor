#!/usr/bin/env python3
"""포털 검색용 정적 페이지와 sitemap.xml을 만든다.

앱(index.html)은 자바스크립트로 화면을 그리고 주소가 하나뿐이라 네이버·구글·다음이 내용을 읽지 못한다.
이 도구는 data.json, interp.json을 읽어 항목마다 글이 미리 들어 있는 페이지를 만든다.

  interp/<id>.html     행정해석·법제처 해석·판례·민원 답변 한 건씩
  interp/index.html    분야별 목록
  figures/<id>.html    기준 수치(최저임금, 구직급여 상·하한, 4대보험 요율 등) 한 종류씩, 연도별 이력 포함
  figures/index.html   기준 수치 목록
  grants/<id>.html     고용지원금 한 건씩
  grants/index.html    지원금 목록
  changes.html         시행 예정·최근 시행 제도 변경과 입법 동향
  sitemap.xml          위 페이지 전체(내용이 바뀐 날을 lastmod로 기록)

- 페이지 내용이 이전과 같으면 파일을 다시 쓰지 않고 lastmod도 그대로 둔다(tools/pages_lastmod.json).
- 데이터에서 빠진 항목의 페이지는 지운다(위 세 폴더는 이 도구 전용).
- 출처 링크는 앱과 같은 허용 도메인만 넣는다.
- GitHub Actions(.github/workflows/pages.yml)가 data.json, interp.json이 바뀔 때마다 자동으로 실행한다.

사용: python3 tools/build_pages.py
"""
import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://app.xn--o80bq8pj4a8ztxwcn2k.com/"
APP_NAME = "청아 노무수첩"
FIRM = "청아노무법인"
STATE = os.path.join(ROOT, "tools", "pages_lastmod.json")
OWNED_DIRS = ["interp", "figures", "grants"]
OK_SRC = re.compile(r"^https?://([a-z0-9-]+\.)*(law\.go\.kr|lawmaking\.go\.kr|korea\.kr|moel\.go\.kr|work24\.go\.kr|ei\.go\.kr|comwel\.or\.kr|nhis\.or\.kr|nps\.or\.kr|kead\.or\.kr|bokjiro\.go\.kr|mohw\.go\.kr|minimumwage\.go\.kr|assembly\.go\.kr|4insure\.or\.kr|kosha\.or\.kr)([/?#]|$)", re.I)

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

KNAME = {"interp": "고용노동부 질의회시", "moleg": "법제처 법령해석", "prec": "법원 판결", "civil": "고용노동부 국민신문고 민원 답변"}
KSHORT = {"interp": "노동부 회시", "moleg": "법제처 해석", "prec": "판례", "civil": "민원 답변"}
TOPIC_ORDER = ["최저임금", "임금", "퇴직금", "연차휴가", "근로시간", "실업급여", "모성보호", "지원금", "대지급금", "산재보상", "사회보험", "기타"]
TOPIC_CALC = {"최저임금": "mw", "퇴직금": "sev", "연차휴가": "al", "실업급여": "ui", "모성보호": "pl", "산재보상": "sj", "대지급금": "dg", "사회보험": "ins", "임금": "net"}
CALC_NAME = {"mw": "최저임금", "ui": "실업급여", "pl": "육아휴직급여", "mat": "출산전후휴가 급여", "sp": "배우자 출산전후휴가 급여", "sj": "산재 보험급여", "ins": "4대보험료", "net": "급여 실수령액", "sev": "퇴직금", "al": "연차일수", "dg": "대지급금", "dis": "장애인 고용부담금"}
ITEM_CALC = {"mat_cap": "mat", "spouse_leave_cap": "sp", "pl_cap_1": "pl", "pl_cap_4": "pl", "pl_cap_7": "pl", "disabled_quota": "dis", "it_meal_free": "net"}
GROUP_CALC = {"최저임금": "mw", "실업급여": "ui", "산재보험": "sj", "4대보험 요율": "ins", "근로소득세": "net"}

E = lambda s: html.escape(str("" if s is None else s), quote=True)


def kind(x):
    return x.get("kind") if x.get("kind") in KNAME else "interp"


def ok(u):
    return bool(u) and bool(OK_SRC.match(str(u)))


def src_label(u):
    u = str(u)
    if "lawmaking.go.kr" in u:
        return "입법예고 원문"
    if re.search(r"law\.go\.kr/(행정규칙|%ED%96%89%EC%A0%95%EA%B7%9C%EC%B9%99)", u, re.I):
        return "고시 원문(국가법령정보센터)"
    if "law.go.kr" in u:
        return "국가법령정보센터 원문"
    if "assembly.go.kr" in u:
        return "국회 의안정보"
    if "moel.go.kr" in u:
        return "고용노동부 원문"
    if "korea.kr" in u:
        return "정책브리핑 원문"
    return "기관 원문"


def ymd_dot(s):
    s = str(s or "")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    return f"{int(m.group(1))}. {int(m.group(2))}. {int(m.group(3))}." if m else s


def clip(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def fmt_val(v, unit):
    if isinstance(v, (int, float)):
        if unit == "원":
            return f"{round(v):,}원"
        num = f"{v:,.4f}".rstrip("0").rstrip(".")
        return num + ("%" if unit == "%" else (" " + unit if unit else ""))
    return str(v)


CSS = """*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:#eaf1f9;color:#13233a;font-family:"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;font-size:16px;line-height:1.7;word-break:keep-all;overflow-wrap:break-word}
a{color:#12396e}
header.top{background:#1a4c8c;color:#fff}
header.top .in,main,footer .in{max-width:760px;margin:0 auto;padding:0 16px}
header.top .in{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-top:14px;padding-bottom:14px}
header.top a.brand{color:#fff;text-decoration:none;font-weight:700;font-size:18px}
header.top a.brand small{display:block;font-weight:400;font-size:12px;opacity:.85}
header.top a.open{color:#1a4c8c;background:#fff;border-radius:999px;padding:7px 14px;font-size:13px;font-weight:700;text-decoration:none;white-space:nowrap}
nav.crumb{font-size:13px;color:#56687f;margin:18px 0 6px}nav.crumb a{color:#56687f}
h1{font-size:23px;line-height:1.4;margin:4px 0 10px;letter-spacing:-.4px}
h2{font-size:17px;margin:0 0 10px;color:#12396e}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px;padding:0;list-style:none;font-size:13px}
.meta li{background:#fff;border:1px solid #ccd9e8;border-radius:999px;padding:3px 10px;color:#56687f}
.meta li.k{background:#12396e;border-color:#12396e;color:#fff;font-weight:700}
.box{background:#fff;border:1px solid #ccd9e8;border-radius:12px;padding:18px;margin:0 0 14px}
.box p{margin:0 0 8px}.box p:last-child{margin:0}
.qa dt{font-weight:700;color:#12396e;margin:0 0 4px}.qa dd{margin:0 0 12px}.qa dd:last-child{margin:0}
.orig h3{font-size:15px;margin:14px 0 6px;color:#12396e}.orig h3:first-child{margin-top:0}
.orig .t{white-space:pre-wrap;font-size:15px}
.big{font-size:30px;font-weight:700;color:#12396e;letter-spacing:-.5px;margin:0}
.next{margin:6px 0 0;font-size:15px}.next b{color:#c0392b}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border-bottom:1px solid #e1eaf5;padding:9px 6px;text-align:left;vertical-align:top}
th{color:#56687f;font-weight:600;white-space:nowrap}
td.v{font-weight:700;white-space:nowrap}
.src{font-size:14px;color:#56687f}
.note{font-size:13.5px;color:#56687f}
ul.list{list-style:none;margin:0;padding:0}ul.list li{border-bottom:1px solid #e1eaf5;padding:10px 0}ul.list li:last-child{border:0}
ul.list a{text-decoration:none;font-weight:600}ul.list small{display:block;color:#56687f;font-size:13px;font-weight:400}
.cta{background:#12396e;color:#fff;border-radius:12px;padding:18px;margin:18px 0}
.cta p{margin:0 0 10px}.cta .btns{display:flex;flex-wrap:wrap;gap:8px}
.cta a{display:inline-block;background:#fff;color:#12396e;border-radius:999px;padding:8px 14px;font-size:14px;font-weight:700;text-decoration:none}
.cta a.tel{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.6)}
.toc{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px}.toc a{background:#fff;border:1px solid #ccd9e8;border-radius:999px;padding:4px 11px;font-size:13px;text-decoration:none}
footer{background:#13233a;color:#c9d6e6;font-size:12.5px;margin-top:28px;padding:20px 0 28px}footer a{color:#fff}
footer p{margin:0 0 6px}
@media (max-width:480px){h1{font-size:20px}.big{font-size:26px}}"""


def page(path, title, desc, body, crumbs, ld=None):
    """path: 저장소 기준 경로(예: interp/law-1.html). 반환: html 문자열."""
    url = BASE + path.replace("index.html", "")
    depth = path.count("/")
    up = "../" * depth if depth else "./"
    crumb_html = " &gt; ".join(f'<a href="{up}{E(h)}">{E(t)}</a>' if h is not None else E(t) for t, h in crumbs)
    lds = []
    bl = [{"@type": "ListItem", "position": i + 1, "name": t, **({"item": BASE + h.replace("index.html", "")} if h is not None else {})} for i, (t, h) in enumerate(crumbs)]
    lds.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": bl})
    if ld:
        lds.append(ld)
    ld_html = "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>" for x in lds)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(url)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{APP_NAME} | {FIRM}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:image" content="{BASE}icons/icon-512.png?v=3">
<meta name="naver-site-verification" content="32184885c8b561ba6dcf743867eb9a5fd3523963">
<link rel="icon" href="{up}icons/favicon-32.png">
<style>{CSS}</style>
{ld_html}
</head>
<body>
<header class="top"><div class="in"><a class="brand" href="{up}">{APP_NAME}<small>{FIRM} 무료 노무 실무 앱</small></a><a class="open" href="{up}">앱 열기</a></div></header>
<main>
<nav class="crumb" aria-label="위치">{crumb_html}</nav>
{body}
</main>
<footer><div class="in">
<p>이 페이지는 {FIRM}이 노동·사회보험 기준과 행정해석을 업무 참고용으로 정리한 일반 정보입니다. 개별 사안에 대한 법률 자문을 대신하지 않으며, 최종 판단은 원문 법령·고시·지침과 최신 판례로 확인해 주세요.</p>
<p>{FIRM} | 부산 <a href="tel:0518534421">051-853-4421</a> | 거제 <a href="tel:0556374421">055-637-4421</a> | <a href="https://www.xn--o80bq8pj4a8ztxwcn2k.com/">홈페이지</a> | <a href="{up}privacy.html">개인정보 처리방침</a></p>
</div></footer>
</body>
</html>
"""


def cta(up, app_link, app_text, calc=None):
    btns = [f'<a href="{up}{E(app_link)}">{E(app_text)}</a>']
    if calc:
        btns.append(f'<a href="{up}#calc-{calc}">{E(CALC_NAME[calc])} 계산기</a>')
    btns.append('<a class="tel" href="tel:0518534421">상담 051-853-4421</a>')
    return f'<div class="cta"><p>{APP_NAME}에서 기준 수치, 계산기, 지원금, 행정해석을 한곳에서 확인할 수 있습니다. 구체적 사안은 {FIRM}에 문의해 주세요.</p><div class="btns">{"".join(btns)}</div></div>'


def src_html(u, extra=""):
    if ok(u):
        return f'<p class="src">출처: <a href="{E(u)}" target="_blank" rel="noopener">{E(src_label(u))}</a>{extra}</p>'
    return f'<p class="src">출처: {FIRM} 보관 원문{extra}</p>' if extra == "" else f'<p class="src">{extra.lstrip(", ")}</p>'


# ---------------- 행정해석 ----------------
def interp_title(x):
    return f"{x['title']} | {KNAME[kind(x)]} {x.get('no','')}".strip()


def build_interp(items, out):
    by_topic = {}
    for x in items:
        by_topic.setdefault(x.get("topic") or "기타", []).append(x)
    for t in by_topic:
        by_topic[t].sort(key=lambda x: x.get("date") or "", reverse=True)
    for x in items:
        k = kind(x)
        path = f"interp/{x['id']}.html"
        up = "../"
        no = x.get("no") or ""
        meta = [f'<li class="k">{E(KSHORT[k])}</li>']
        if no:
            meta.append(f"<li>{E(no)}</li>")
        if x.get("date"):
            meta.append(f'<li><time datetime="{E(x["date"])}">{E(ymd_dot(x["date"]))}</time></li>')
        meta.append(f"<li>{E(x.get('topic') or '기타')}</li>")
        qa = ""
        if x.get("q") or x.get("a"):
            ql = "쟁점" if k == "prec" else ("민원 요지" if k == "civil" else "질의 요지")
            al = "판단" if k == "prec" else ("답변 요지" if k == "civil" else "회신 요지")
            qa = f'<div class="box"><h2>요약</h2><dl class="qa">' + (f"<dt>{ql}</dt><dd>{E(x['q'])}</dd>" if x.get("q") else "") + (f"<dt>{al}</dt><dd>{E(x['a'])}</dd>" if x.get("a") else "") + "</dl></div>"
        orig = ""
        if x.get("orig"):
            parts = []
            for o in x["orig"]:
                h = str(o.get("h") or "").strip()
                if h in ("질의요지", "질의"):
                    h = "민원 내용" if k == "civil" else "질의"
                elif h in ("회답", "회시"):
                    h = "답변" if k == "civil" else "회시"
                parts.append((f"<h3>{E(h)}</h3>" if h else "") + f'<div class="t">{E(o.get("t"))}</div>')
            orig = f'<div class="box orig"><h2>원문</h2>{"".join(parts)}</div>'
        notes = ""
        if x.get("note"):
            notes = f'<div class="box"><p class="note">※ {E(x["note"])}</p></div>'
        cav = {"moleg": "※ 법제처 법령해석은 행정부 내부의 법령해석으로 법원의 확정판결과 같은 기속력은 없으며, 해석 당시 법령을 대상으로 합니다.",
               "prec": "※ 판례는 해당 사건의 사실관계를 전제로 한 판단입니다.",
               "civil": "※ 국민신문고 민원 답변은 담당 부서의 의견으로, 개별 사실관계에 따라 달라질 수 있습니다.",
               "interp": "※ 행정해석은 행정기관의 법령 해석으로 법원을 기속하지 않으며, 이후 법령 개정이나 판례 변경으로 달라질 수 있습니다."}[k]
        basis = f"<p>관련 법령: {E(x['basis'])}</p>" if x.get("basis") else ""
        srcp = src_html(x.get("src")) if ok(x.get("src")) else f'<p class="src">출처: {E(KNAME[k])}{(" " + E(no)) if no else ""} ({E(ymd_dot(x.get("date")))}). ※ 국가법령정보센터 미수록 자료로 {FIRM} 보관 원문을 옮겼습니다.</p>'
        rel = [y for y in by_topic.get(x.get("topic") or "기타", []) if y["id"] != x["id"]][:6]
        rel_html = ""
        if rel:
            rel_html = '<div class="box"><h2>같은 분야 다른 해석</h2><ul class="list">' + "".join(f'<li><a href="{E(y["id"])}.html">{E(y["title"])}</a><small>{E(KSHORT[kind(y)])} {E(y.get("no") or "")} | {E(ymd_dot(y.get("date")))}</small></li>' for y in rel) + f'</ul><p class="note" style="margin-top:8px"><a href="index.html#t-{E(x.get("topic") or "기타")}">{E(x.get("topic") or "기타")} 분야 전체 보기</a></p></div>'
        body = (f'<article><h1>{E(x["title"])}</h1><ul class="meta">{"".join(meta)}</ul>{qa}{orig}{notes}'
                f'<div class="box">{basis}{srcp}<p class="note">{cav}</p></div></article>'
                + cta(up, f"?i={x['id']}", "앱에서 이 해석 보기", TOPIC_CALC.get(x.get("topic"))) + rel_html)
        desc = clip(f"{KNAME[k]} {no} ({ymd_dot(x.get('date'))}). " + (x.get("q") or "") + " " + (x.get("a") or ""), 160)
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": clip(x["title"], 110), "description": desc, "inLanguage": "ko",
              "about": KNAME[k], "author": {"@type": "Organization", "name": FIRM}, "publisher": {"@type": "Organization", "name": FIRM},
              "mainEntityOfPage": BASE + path}
        if x.get("added"):
            ld["datePublished"] = x["added"]
        out[path] = page(path, f"{interp_title(x)} | {APP_NAME}", desc, body, [(APP_NAME, ""), ("행정해석", "interp/index.html"), (clip(x["title"], 40), None)], ld)
    # 목록
    topics = [t for t in TOPIC_ORDER if t in by_topic] + [t for t in by_topic if t not in TOPIC_ORDER]
    toc = '<div class="toc">' + "".join(f'<a href="#t-{E(t)}">{E(t)} {len(by_topic[t])}</a>' for t in topics) + "</div>"
    secs = "".join(f'<div class="box" id="t-{E(t)}"><h2>{E(t)}</h2><ul class="list">' + "".join(f'<li><a href="{E(y["id"])}.html">{E(y["title"])}</a><small>{E(KSHORT[kind(y)])} {E(y.get("no") or "")} | {E(ymd_dot(y.get("date")))}</small></li>' for y in by_topic[t]) + "</ul></div>" for t in topics)
    body = (f'<h1>노동 행정해석 모음</h1><p>임금, 퇴직금, 연차휴가, 근로시간, 최저임금, 실업급여, 모성보호, 산재보상, 사회보험, 대지급금, 고용지원금에 관한 고용노동부 질의회시, 법제처 법령해석, 판례, 국민신문고 민원 답변 {len(items)}건을 분야별로 정리했습니다. 각 항목은 질의와 회시 원문을 담고 있습니다.</p>'
            + toc + secs + cta("../", "#interp", "앱에서 행정해석 검색하기"))
    out["interp/index.html"] = page("interp/index.html", f"노동 행정해석 모음 {len(items)}건 (임금·퇴직금·연차·최저임금·실업급여) | {APP_NAME}",
                                    f"고용노동부 질의회시, 법제처 법령해석, 판례, 국민신문고 민원 답변 {len(items)}건을 임금·퇴직금·연차휴가·근로시간·모성보호·실업급여 등 분야별로 정리했습니다.",
                                    body, [(APP_NAME, ""), ("행정해석", None)])


# ---------------- 기준 수치 ----------------
def cur_next(it):
    h = sorted(it["hist"], key=lambda e: e["from"])
    cur = None
    nxt = None
    for e in h:
        if e["from"] <= TODAY:
            cur = e
        elif nxt is None:
            nxt = e
    return cur, nxt, h


def fig_title(it):
    cur, nxt, _ = cur_next(it)
    base = cur or nxt
    if not base:
        return it["name"]
    t = f"{base['from'][:4]}년 {it['name']} {fmt_val(base['value'], it['unit'])}"
    if cur and nxt:
        t += f" ({nxt['from'][:4]}년 {fmt_val(nxt['value'], it['unit'])})"
    return t


def build_figures(items, out):
    groups = {}
    for k, it in items.items():
        groups.setdefault(it["group"], []).append(k)
    for k, it in items.items():
        path = f"figures/{k}.html"
        cur, nxt, h = cur_next(it)
        u = it["unit"]
        top = ""
        if cur:
            top = f'<div class="box"><p class="note">{E(ymd_dot(cur["from"]))}부터 적용</p><p class="big">{E(fmt_val(cur["value"], u))}</p>'
            if nxt:
                top += f'<p class="next"><b>{E(ymd_dot(nxt["from"]))}부터 {E(fmt_val(nxt["value"], u))}</b> 적용 예정</p>'
            top += (f'<p class="note">근거: {E(cur.get("basis"))}</p>' if cur.get("basis") else "") + (f'<p class="note">※ {E(cur["note"])}</p>' if cur.get("note") else "") + "</div>"
        elif nxt:
            top = f'<div class="box"><p class="note">{E(ymd_dot(nxt["from"]))}부터 적용 예정</p><p class="big">{E(fmt_val(nxt["value"], u))}</p>' + (f'<p class="note">근거: {E(nxt.get("basis"))}</p>' if nxt.get("basis") else "") + "</div>"
        rows = "".join(
            f'<tr><td>{E(ymd_dot(e["from"]))}</td><td class="v">{E(fmt_val(e["value"], u))}</td><td>{E(e.get("basis") or "")}'
            + (f'<br><span class="note">※ {E(e["note"])}</span>' if e.get("note") else "")
            + (f' <a href="{E(e["src"])}" target="_blank" rel="noopener">원문</a>' if ok(e.get("src")) else "")
            + "</td></tr>" for e in reversed(h))
        hist = f'<div class="box"><h2>연도별 변경 이력</h2><table><thead><tr><th>적용일</th><th>금액·요율</th><th>근거</th></tr></thead><tbody>{rows}</tbody></table></div>'
        last = cur or nxt or {}
        srcp = src_html(last.get("src"), f' (확인 {E(ymd_dot(last.get("checked")))})' if last.get("checked") else "") if ok(last.get("src")) else ""
        rel = [j for j in groups[it["group"]] if j != k]
        rel_html = ('<div class="box"><h2>' + E(it["group"]) + ' 관련 기준</h2><ul class="list">' + "".join(f'<li><a href="{E(j)}.html">{E(fig_title(items[j]))}</a></li>' for j in rel) + "</ul></div>") if rel else ""
        calc = ITEM_CALC.get(k) or GROUP_CALC.get(it["group"])
        title = fig_title(it)
        body = (f'<article><h1>{E(title)}</h1><ul class="meta"><li class="k">{E(it["group"])}</li><li>{E(it["name"])}</li></ul>{top}{hist}'
                + (f'<div class="box">{srcp}</div>' if srcp else "") + "</article>"
                + cta("../", "#summary", "앱에서 전체 기준 보기", calc) + rel_html)
        desc = clip(f"{title}. " + (f"근거: {last.get('basis')}. " if last.get("basis") else "") + "연도별 변경 이력과 근거 법령·고시를 함께 정리했습니다.", 160)
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": clip(title, 110), "description": desc, "inLanguage": "ko",
              "author": {"@type": "Organization", "name": FIRM}, "publisher": {"@type": "Organization", "name": FIRM}, "mainEntityOfPage": BASE + path}
        out[path] = page(path, f"{title} | {APP_NAME}", desc, body, [(APP_NAME, ""), ("기준 수치", "figures/index.html"), (it["name"], None)], ld)
    secs = "".join(f'<div class="box"><h2>{E(g)}</h2><ul class="list">' + "".join(f'<li><a href="{E(j)}.html">{E(fig_title(items[j]))}</a></li>' for j in ks) + "</ul></div>" for g, ks in groups.items())
    body = (f'<h1>노동·사회보험 기준 수치 {TODAY[:4]}</h1><p>최저임금, 구직급여 상·하한액, 출산전후휴가·육아휴직 급여 상한, 산재보험 보상기준, 4대보험 요율과 상·하한 등 자주 찾는 기준 수치를 근거 법령·고시와 함께 정리했습니다. 확정된 다음 연도 수치도 함께 표시합니다.</p>'
            + secs + cta("../", "#summary", "앱에서 전체 기준 보기"))
    out["figures/index.html"] = page("figures/index.html", f"{TODAY[:4]}년 노동·사회보험 기준 수치 (최저임금·실업급여·육아휴직·4대보험 요율) | {APP_NAME}",
                                     "최저임금, 구직급여 상·하한액, 출산전후휴가·육아휴직 급여 상한, 산재보험 보상기준, 4대보험 요율 등 기준 수치를 근거 법령·고시와 연도별 이력으로 정리했습니다.",
                                     body, [(APP_NAME, ""), ("기준 수치", None)])


# ---------------- 지원금 ----------------
GFIELDS = [("target", "지원 대상"), ("worker", "대상 근로자·요건"), ("amount", "지원 금액"), ("period", "지원 기간"), ("limit", "한도"),
           ("exclude", "지원 제외"), ("apply", "신청 방법·기한"), ("changes", "올해 달라진 점"), ("next", "향후 동향"), ("basis", "근거")]


def build_grants(grants, year_note, out):
    for g in grants:
        path = f"grants/{g['id']}.html"
        rows = "".join(f'<tr><th>{E(lab)}</th><td>{E(g[f])}</td></tr>' for f, lab in GFIELDS if g.get(f))
        srcp = src_html(g.get("src"), f' (확인 {E(ymd_dot(g.get("checked")))})' if g.get("checked") else "") if ok(g.get("src")) else ""
        body = (f'<article><h1>{E(g["name"])}</h1><ul class="meta"><li class="k">고용지원금</li><li>{E(g.get("family") or "")}</li><li>{E(year_note)}</li></ul>'
                + (f'<div class="box"><p class="big" style="font-size:21px">{E(g["headline"])}</p></div>' if g.get("headline") else "")
                + f'<div class="box"><table><tbody>{rows}</tbody></table></div>' + (f'<div class="box">{srcp}</div>' if srcp else "")
                + '<div class="box"><p class="note">※ 지원 요건과 금액은 연도별 공고와 예산에 따라 달라집니다. 신청 전 고용24 또는 관할 고용센터에서 최신 공고를 확인해 주세요.</p></div></article>'
                + cta("../", f"?g={g['id']}", "앱에서 우리 회사 해당 여부 확인"))
        desc = clip(f"{g['name']}: {g.get('headline') or ''}. 대상 {g.get('target') or ''}. {g.get('amount') or ''}", 160)
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": clip(g["name"], 110), "description": desc, "inLanguage": "ko",
              "author": {"@type": "Organization", "name": FIRM}, "publisher": {"@type": "Organization", "name": FIRM}, "mainEntityOfPage": BASE + path}
        out[path] = page(path, f"{g['name']} 지원 요건과 금액 | {APP_NAME}", desc, body, [(APP_NAME, ""), ("고용지원금", "grants/index.html"), (clip(g["name"], 40), None)], ld)
    fams = {}
    for g in grants:
        fams.setdefault(g.get("family") or "기타", []).append(g)
    secs = "".join(f'<div class="box"><h2>{E(f)}</h2><ul class="list">' + "".join(f'<li><a href="{E(g["id"])}.html">{E(g["name"])}</a><small>{E(g.get("headline") or "")}</small></li>' for g in gs) + "</ul></div>" for f, gs in fams.items())
    body = (f'<h1>고용지원금 안내</h1><p>{E(year_note)}으로 사업주가 받을 수 있는 고용지원금 {len(grants)}종의 지원 대상, 금액, 기간, 신청 방법을 정리했습니다.</p>'
            + secs + cta("../", "#grants", "앱에서 지원금 해당 여부 확인"))
    out["grants/index.html"] = page("grants/index.html", f"{TODAY[:4]}년 고용지원금 {len(grants)}종 지원 요건과 금액 | {APP_NAME}",
                                    f"{year_note}으로 고용유지지원금, 출산육아기 고용안정장려금 등 사업주 고용지원금 {len(grants)}종의 지원 대상, 금액, 신청 방법을 정리했습니다.",
                                    body, [(APP_NAME, ""), ("고용지원금", None)])


# ---------------- 제도 변경 ----------------
def build_changes(sched, notices, out):
    lim = (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    up = sorted([s for s in sched if s["from"] > TODAY], key=lambda s: s["from"])
    done = sorted([s for s in sched if lim <= s["from"] <= TODAY], key=lambda s: s["from"], reverse=True)

    def row(s):
        return (f'<li><b>{E(s["title"])}</b><small>{E(ymd_dot(s["from"]))} 시행 | {E(s.get("cat") or "")} | {E(s.get("status") or "")}</small>'
                + (f'<p class="note" style="margin:6px 0 0">개정 전: {E(s["before"])}</p>' if s.get("before") else "")
                + (f'<p style="margin:2px 0 0">개정 후: {E(s["after"])}</p>' if s.get("after") else "")
                + (f'<p class="note" style="margin:2px 0 0">※ {E(s["note"])}</p>' if s.get("note") else "")
                + (f'<p class="note" style="margin:2px 0 0">근거: {E(s.get("basis") or "")}' + (f' <a href="{E(s["src"])}" target="_blank" rel="noopener">{E(src_label(s["src"]))}</a>' if ok(s.get("src")) else "") + "</p>")
                + "</li>")
    body = '<h1>노동법·사회보험 제도 변경</h1><p>근로시간·휴가, 임금·퇴직금, 일·가정 양립, 고용보험, 산재보상, 사회보험, 지원금 분야에서 시행을 앞둔 변경과 최근 1년 안에 시행된 변경을 시행일 순으로 정리했습니다.</p>'
    if up:
        body += '<div class="box"><h2>시행 예정</h2><ul class="list">' + "".join(row(s) for s in up) + "</ul></div>"
    if notices:
        body += '<div class="box"><h2>입법 동향(확정 전)</h2><ul class="list">' + "".join(f'<li><small>{E(ymd_dot(n.get("date")))}</small>{E(n.get("text"))}' + (f' <a href="{E(n["src"])}" target="_blank" rel="noopener">{E(src_label(n["src"]))}</a>' if ok(n.get("src")) else "") + "</li>" for n in sorted(notices, key=lambda n: n.get("date") or "", reverse=True)) + "</ul></div>"
    if done:
        body += '<div class="box"><h2>최근 시행</h2><ul class="list">' + "".join(row(s) for s in done) + "</ul></div>"
    body += cta("./", "#summary", "앱에서 바뀌는 제도 보기")
    titles = ", ".join(clip(s["title"], 24) for s in (up[:3] or done[:3]))
    out["changes.html"] = page("changes.html", f"{TODAY[:4]}년 달라지는 노동법·사회보험 제도 | {APP_NAME}",
                               clip(f"시행 예정 {len(up)}건, 최근 1년 시행 {len(done)}건. {titles} 등 노동법·사회보험 제도 변경을 시행일 순으로 정리했습니다.", 160),
                               body, [(APP_NAME, ""), ("제도 변경", None)])


def main():
    d = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
    iv = json.load(open(os.path.join(ROOT, "interp.json"), encoding="utf-8"))
    out = {}
    build_interp(iv["items"], out)
    build_figures(d["items"], out)
    build_grants(d.get("grants", []), d.get("meta", {}).get("grantsYear", ""), out)
    build_changes(d.get("scheduled", []), d.get("notices", []), out)

    state = {}
    if os.path.exists(STATE):
        state = json.load(open(STATE, encoding="utf-8"))
    new_state, written = {}, 0
    for path, content in sorted(out.items()):
        hsh = hashlib.sha1(content.encode("utf-8")).hexdigest()[:16]
        prev = state.get(path)
        fp = os.path.join(ROOT, path)
        if prev and prev[0] == hsh and os.path.exists(fp):
            new_state[path] = prev
            continue
        os.makedirs(os.path.dirname(fp) or ROOT, exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        new_state[path] = [hsh, TODAY]
        written += 1
    removed = 0
    for dname in OWNED_DIRS:
        dp = os.path.join(ROOT, dname)
        if not os.path.isdir(dp):
            continue
        for fn in os.listdir(dp):
            rel = f"{dname}/{fn}"
            if fn.endswith(".html") and rel not in out:
                os.remove(os.path.join(dp, fn))
                removed += 1

    # sitemap: 앱 첫 화면과 개인정보 처리방침 + 생성 페이지
    app_mod = max([v[1] for v in new_state.values()] + [d.get("meta", {}).get("checked", TODAY)])
    urls = [(BASE, app_mod, "daily", "1.0")]
    pri = {"interp/index.html": "0.9", "figures/index.html": "0.9", "grants/index.html": "0.8", "changes.html": "0.8"}
    for path in sorted(new_state):
        loc = BASE + path.replace("index.html", "")
        p = pri.get(path, "0.7" if path.startswith("figures/") else "0.6")
        urls.append((loc, new_state[path][1], "weekly", p))
    urls.append((BASE + "privacy.html", None, "yearly", "0.2"))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, cf, p in urls:
        sm.append(f" <url><loc>{html.escape(loc)}</loc>" + (f"<lastmod>{mod}</lastmod>" if mod else "") + f"<changefreq>{cf}</changefreq><priority>{p}</priority></url>")
    sm.append("</urlset>\n")
    sm_txt = "\n".join(sm)
    sp = os.path.join(ROOT, "sitemap.xml")
    old = open(sp, encoding="utf-8").read() if os.path.exists(sp) else ""
    if old != sm_txt:
        open(sp, "w", encoding="utf-8").write(sm_txt)
    if new_state != state:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(new_state, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
    print(f"페이지 {len(out)}개(새로 씀 {written}, 삭제 {removed}), sitemap URL {len(urls)}개")


if __name__ == "__main__":
    sys.exit(main())
