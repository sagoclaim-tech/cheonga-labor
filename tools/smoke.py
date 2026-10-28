#!/usr/bin/env python3
"""청아 노무수첩 화면·계산기 점검(Playwright).

로컬 서버로 앱을 띄워 계산기 전부를 오늘 기준과 다음 해 1월 기준으로 열어 보고,
스크립트 오류, 결과 영역의 NaN·undefined·Infinity 표시를 찾는다.
data.json 수치나 표를 고친 뒤 계산기가 깨지지 않았는지 확인하는 용도다.

사용: python3 tools/smoke.py   (문제가 있으면 종료코드 1)
"""
import http.server, os, re, socketserver, sys, threading
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD = re.compile(r"NaN|undefined|Infinity|\[object Object\]")


def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = lambda *a, **k: Q(*a, directory=ROOT, **k)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright 없음: pip install playwright && python3 -m playwright install chromium")
        sys.exit(1)
    httpd = serve()
    base = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"
    probs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.on("pageerror", lambda e: probs.append(f"스크립트 오류: {e}"))
        pg.on("console", lambda m: m.type == "error" and not re.search(r"favicon|google|gtag|ERR_|Failed to load resource", m.text) and probs.append(f"콘솔 오류: {m.text}"))
        pg.goto(base + "#calc-mw", wait_until="domcontentloaded")
        pg.wait_for_selector(".cgrid .chip[data-c]", timeout=20000)
        calcs = pg.eval_on_selector_all(".cgrid .chip[data-c]", "els=>els.map(e=>e.dataset.c)")
        months = pg.eval_on_selector_all("#month option", "els=>els.map(e=>e.value)")
        nxt = f"{date.today().year + 1}-01"
        for label, ym in (("오늘", None), (nxt, nxt)):
            if ym:
                if ym not in months:
                    probs.append(f"조회 월 목록에 {ym} 없음"); continue
                pg.select_option("#month", ym)
                pg.wait_for_timeout(300)
            for c in calcs:
                pg.click(f'nav.tabs button[data-tab="calc"]')
                pg.click(f'.cgrid .chip[data-c="{c}"]')
                pg.wait_for_timeout(200)
                txt = pg.inner_text("main") if pg.query_selector("main") else pg.inner_text("body")
                m = BAD.search(txt)
                if m:
                    i = m.start()
                    probs.append(f"[{label}] 계산기 {c}: '{m.group(0)}' 표시 ... {txt[max(0,i-60):i+20]!r}")
        for t in pg.eval_on_selector_all("nav.tabs button[data-tab]", "els=>els.map(e=>e.dataset.tab)"):
            pg.click(f'nav.tabs button[data-tab="{t}"]')
            pg.wait_for_timeout(200)
            m = BAD.search(pg.inner_text("body"))
            if m:
                probs.append(f"탭 {t}: '{m.group(0)}' 표시")
        b.close()
    httpd.shutdown()
    for x in dict.fromkeys(probs):
        print("문제", x)
    print(f"화면 점검 완료: 계산기 {len(calcs)}종 x 2개 기준일, 문제 {len(set(probs))}건")
    sys.exit(1 if probs else 0)


if __name__ == "__main__":
    main()
