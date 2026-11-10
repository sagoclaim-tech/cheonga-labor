#!/usr/bin/env python3
"""청아 노무수첩 새 소식 알림(웹 푸시) 발송.

무엇을 하나
- 저장소의 현재 내용과 tools/push_state.json(이미 알린 목록)을 비교해 새로 올라온 것을 찾는다.
  · 노동뉴스: news/YYYY-MM-DD.html (최근 3일 안의 날짜만 알림)
  · 행정해석·설명자료: interp.json, guides.json의 새 id
  · 기준 수치·제도 변경: data.json의 items 이력, scheduled, notices, grants
- 새 소식이 있으면 종류별로 알림 1건씩을 구독 기기 전체에 보낸다.
  안드로이드는 읽지 않은 알림이 있는 동안 앱 아이콘에 배지가 붙는다.
- 보낸 뒤 push_state.json을 갱신한다(워크플로가 커밋).

설정
- 환경변수 PUSH_CONFIG(JSON, GitHub Secret): {"key": 구독 저장소 관리 키, "vapid_private": VAPID 개인키(base64url)}
  구독 저장소(Apps Script 웹 앱) 주소는 index.html의 PUSH.url에서 읽는다. "url"을 넣으면 그 값을 쓴다.
- PUSH_CONFIG가 없으면 보내지 않고 상태만 갱신한다(나중에 설정해도 지난 소식이 한꺼번에 나가지 않게).
- push_state.json이 없으면 처음 실행으로 보고 현재 내용을 기록만 한다.

사용
  python3 tools/push_notify.py            새 소식 확인 후 발송
  python3 tools/push_notify.py --dry      보낼 내용만 출력(발송·기록 안 함)
  python3 tools/push_notify.py --test "문구"   시험 알림 1건 발송(기록 안 함)
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "tools", "push_state.json")
KST = timezone(timedelta(hours=9))
WD = "월화수목금토일"


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def cut(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def news_focus(t):
    m = re.search(r'class="summary-bar"[^>]*>([\s\S]*?)</div>', t or "")
    if not m:
        return []
    s = re.sub(r"<strong>[\s\S]*?</strong>", "", m.group(1), count=1)
    s = re.sub(r"<[^>]+>", "", s).replace("&amp;", "&").replace("&middot;", "·")
    s = re.sub(r"\s+", " ", s).strip()
    return [x for x in s.split(" · ") if x]


def current():
    """지금 저장소에 있는 소식의 키와 표시용 정보."""
    cur = {"news": {}, "interp": {}, "data": {}}
    for p in glob.glob(os.path.join(ROOT, "news", "*.html")):
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.html", os.path.basename(p))
        if m:
            cur["news"][m.group(1)] = p
    for name, kind in (("interp.json", "행정해석"), ("guides.json", "설명자료")):
        try:
            for it in load(name).get("items", []):
                if it.get("id"):
                    cur["interp"][it["id"]] = {"title": it.get("title", ""), "kind": kind}
        except FileNotFoundError:
            pass
    d = load("data.json")
    for iid, it in d.get("items", {}).items():
        for h in it.get("hist", []):
            cur["data"][f"item|{iid}|{h.get('from')}"] = it.get("name", iid)
    for c in d.get("scheduled", []):
        cur["data"][f"sched|{c.get('from')}|{c.get('title')}|{c.get('status')}"] = c.get("title", "")
    for n in d.get("notices", []):
        cur["data"][f"notice|{n.get('date')}|{cut(n.get('text'), 40)}"] = cut(n.get("text"), 60)
    for g in d.get("grants", []):
        if isinstance(g, dict) and g.get("id"):
            cur["data"][f"grant|{g['id']}"] = g.get("name", g["id"])
    return cur


def messages(cur, seen, today):
    """새 소식을 종류별 알림으로 묶는다."""
    out = []
    stamp = datetime.now(KST).strftime("%Y-%m-%d-%H%M")  # 같은 날 두 번 올라와도 앞 알림을 덮어쓰지 않게
    lo = (today - timedelta(days=3)).isoformat()
    for day in sorted(k for k in cur["news"] if k not in seen["news"] and k >= lo):
        dt = datetime.strptime(day, "%Y-%m-%d")
        foc = news_focus(open(cur["news"][day], encoding="utf-8").read())[:3]
        out.append({"title": f"노동뉴스 브리핑 {dt.month}.{dt.day}.({WD[dt.weekday()]})",
                    "body": cut(" · ".join(foc), 140) if foc else "오늘의 데일리 브리핑이 올라왔습니다.",
                    "url": "./#news", "tab": "news", "tag": "news-" + day})
    ni = [k for k in cur["interp"] if k not in seen["interp"]]
    if ni:
        kinds = sorted({cur["interp"][k]["kind"] for k in ni})
        first = cur["interp"][ni[0]]["title"]
        only_interp = len(ni) == 1 and cur["interp"][ni[0]]["kind"] == "행정해석" and re.fullmatch(r"[A-Za-z0-9_-]+", ni[0])
        out.append({"title": f"새 {'·'.join(kinds)} {len(ni)}건",
                    "body": cut(first, 110) + (f" 외 {len(ni) - 1}건" if len(ni) > 1 else ""),
                    "url": f"./?i={ni[0]}" if only_interp else "./#interp", "tab": "interp",
                    "tag": "interp-" + stamp})
    nd = [k for k in cur["data"] if k not in seen["data"]]
    if nd:
        names = []
        for k in nd:
            if cur["data"][k] not in names:
                names.append(cur["data"][k])
        out.append({"title": f"기준 수치·제도 변경 {len(names)}건",
                    "body": cut(names[0], 110) + (f" 외 {len(names) - 1}건" if len(names) > 1 else ""),
                    "url": "./#summary", "tab": "summary", "tag": "data-" + stamp})
    return out


def config():
    raw = os.environ.get("PUSH_CONFIG", "").strip()
    if not raw:
        return None
    try:
        c = json.loads(raw)
    except ValueError:
        print("PUSH_CONFIG가 올바른 JSON이 아닙니다.")
        return None
    if not c.get("url"):
        # 구독 저장소 주소는 공개 값이라 화면(index.html의 PUSH.url)에서 읽는다
        m = re.search(r'const PUSH=\{url:"([^"]*)"', open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
        c["url"] = m.group(1) if m else ""
    return c if all(c.get(k) for k in ("url", "key", "vapid_private")) else None


def api(cfg, body):
    import requests
    r = requests.post(cfg["url"], data=json.dumps(body).encode("utf-8"),
                      headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=60)
    r.raise_for_status()
    return r.json()


def vapid_auth(cfg, endpoint):
    """VAPID 인증 머리말(RFC 8292). 연락 주소(sub)는 앱 주소를 쓴다."""
    import base64
    import time
    from urllib.parse import urlsplit
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    b64 = lambda x: base64.urlsafe_b64encode(x).rstrip(b"=").decode()
    raw = base64.urlsafe_b64decode(cfg["vapid_private"] + "=" * (-len(cfg["vapid_private"]) % 4))
    key = ec.derive_private_key(int.from_bytes(raw, "big"), ec.SECP256R1())
    u = urlsplit(endpoint)
    claims = {"aud": f"{u.scheme}://{u.netloc}", "exp": int(time.time()) + 12 * 3600,
              "sub": cfg.get("subject") or "https://app.xn--o80bq8pj4a8ztxwcn2k.com/"}
    head = b64(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    body = b64(json.dumps(claims, separators=(",", ":")).encode())
    r, sg = decode_dss_signature(key.sign(f"{head}.{body}".encode(), ec.ECDSA(hashes.SHA256())))
    sig = b64(r.to_bytes(32, "big") + sg.to_bytes(32, "big"))
    pub = b64(key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
    return {"Authorization": f"vapid t={head}.{body}.{sig}, k={pub}"}


def send(cfg, msgs):
    """구독 기기 전체에 발송. (성공 수, 실패 수, 만료 수)를 돌려준다."""
    from pywebpush import webpush, WebPushException
    res = api(cfg, {"action": "list", "key": cfg["key"]})
    if not res.get("ok"):
        raise RuntimeError("구독 목록을 받지 못했습니다: " + str(res.get("error")))
    subs = res.get("subs", [])
    ok = bad = 0
    gone = []
    for s in subs:
        info = {"endpoint": s["endpoint"], "keys": {"p256dh": s["p256dh"], "auth": s["auth"]}}
        for m in msgs:
            try:
                webpush(info, data=json.dumps(m, ensure_ascii=False), headers=vapid_auth(cfg, s["endpoint"]),
                        ttl=86400, timeout=20)
                ok += 1
            except WebPushException as e:
                code = getattr(e.response, "status_code", None)
                if code in (404, 410):
                    gone.append(s["endpoint"])
                    break
                bad += 1
                print(f"발송 실패({code})")
            except Exception as e:  # 네트워크 오류 등: 다음 기기로 계속
                bad += 1
                print(f"발송 오류: {type(e).__name__}")
    if gone:
        try:
            api(cfg, {"action": "remove", "key": cfg["key"], "endpoints": gone})
        except Exception as e:
            print(f"만료 구독 정리 실패: {type(e).__name__}")
    return len(subs), ok, bad, len(gone)


def main():
    args = sys.argv[1:]
    cfg = config()
    today = datetime.now(KST).date()
    if args[:1] == ["--test"]:
        if not cfg:
            print("PUSH_CONFIG가 없어 시험 알림을 보낼 수 없습니다.")
            sys.exit(1)
        body = args[1] if len(args) > 1 else "알림과 배지가 정상으로 표시되는지 확인하는 시험 알림입니다."
        n, ok, bad, gone = send(cfg, [{"title": "청아 노무수첩 시험 알림", "body": body, "url": "./#summary",
                                       "tab": "", "tag": "test-" + datetime.now(KST).strftime("%H%M%S")}])
        print(f"시험 알림: 구독 {n}대, 성공 {ok}건, 실패 {bad}건, 만료 {gone}대")
        return
    dry = "--dry" in args
    cur = current()
    now = {k: sorted(v) for k, v in cur.items()}
    if not os.path.exists(STATE):
        print("처음 실행: 현재 내용을 기록만 하고 알림은 보내지 않습니다.")
        if not dry:
            json.dump(now, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return
    old = json.load(open(STATE, encoding="utf-8"))
    seen = {k: set(old.get(k, [])) for k in cur}
    msgs = messages(cur, seen, today)
    for m in msgs:
        print("알림:", m["title"], "|", m["body"])
    if dry:
        return
    if msgs and cfg:
        try:
            n, ok, bad, gone = send(cfg, msgs)
            print(f"발송: 구독 {n}대, 성공 {ok}건, 실패 {bad}건, 만료 {gone}대")
            if bad and not ok:
                print("한 건도 보내지 못해 기록하지 않습니다. 다음 실행에서 다시 시도합니다.")
                sys.exit(0)
        except Exception as e:
            # 목록을 못 받은 경우: 기록하지 않고 다음 실행에서 다시 시도
            print(f"발송하지 못했습니다({type(e).__name__}: {e}). 다음 실행에서 다시 시도합니다.")
            sys.exit(0)
    elif msgs:
        print("PUSH_CONFIG가 없어 발송하지 않고 기록만 합니다.")
    # 이미 알린 것은 지우지 않고 누적(파일이 잠시 빠졌다 돌아와도 다시 알리지 않게). 노동뉴스는 최근 120일만 보관
    keep = (today - timedelta(days=120)).isoformat()
    new = {k: sorted(seen[k] | set(now[k])) for k in cur}
    new["news"] = [d for d in new["news"] if d >= keep]
    if new != {k: sorted(seen[k]) for k in cur}:
        json.dump(new, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
