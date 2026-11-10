/* 청아 노무수첩 새 소식 알림: 구독 저장소 (Google Apps Script)

   구글 스프레드시트에 붙여 쓰는 스크립트입니다. 알림을 켠 기기의 구독 주소를 「구독」 시트에 저장하고,
   발송 도구(tools/push_notify.py)가 관리 키로 목록을 읽어 갑니다.

   설치
   1. 구글 스프레드시트를 새로 만든다(이름 예: 청아 노무수첩 알림 구독).
   2. 확장 프로그램 > Apps Script를 열고 이 파일 내용을 전부 붙여 넣는다.
   3. 아래 KEY를 관리 키로 바꾼다(저장소에는 올리지 않는다).
   4. 배포 > 새 배포 > 유형: 웹 앱, 실행 사용자: 나, 액세스 권한: 모든 사용자 로 배포한다.
   5. 나온 웹 앱 주소(…/exec)를 index.html의 PUSH.url과 GitHub Secret PUSH_CONFIG의 url에 넣는다.
   ※ 코드를 고친 뒤에는 배포 관리에서 "새 버전"으로 다시 배포해야 반영됩니다. */

const KEY = '여기에_관리_키';
const SHEET = '구독';
const MAX = 20000;
const HOSTS = /^https:\/\/([a-z0-9-]+\.)*(fcm\.googleapis\.com|push\.services\.mozilla\.com|notify\.windows\.com|push\.apple\.com)\//;
const B64 = /^[A-Za-z0-9_-]{16,200}$/;

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET);
  if (!sh) {
    sh = ss.insertSheet(SHEET);
    sh.getRange('A:E').setNumberFormat('@');
    sh.getRange(1, 1, 1, 5).setValues([['endpoint', 'p256dh', 'auth', '등록일시', '기기']]);
    sh.setFrozenRows(1);
  }
  return sh;
}

function rows_(sh) {
  const n = sh.getLastRow() - 1;
  return n > 0 ? sh.getRange(2, 1, n, 5).getValues() : [];
}

function write_(sh, rows) {
  const n = sh.getLastRow() - 1;
  if (n > 0) sh.getRange(2, 1, n, 5).clearContent();
  if (rows.length) sh.getRange(2, 1, rows.length, 5).setNumberFormat('@').setValues(rows);
}

function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  return out_({ ok: true, service: 'cheonga-push' });
}

function doPost(e) {
  let b;
  try { b = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad request' }); }
  const lock = LockService.getScriptLock();
  try { lock.waitLock(20000); } catch (err) { return out_({ ok: false, error: 'busy' }); }
  try {
    const sh = sheet_();
    const rows = rows_(sh);
    if (b.action === 'subscribe') {
      const s = b.sub || {}, k = s.keys || {};
      if (typeof s.endpoint !== 'string' || s.endpoint.length > 1000 || !HOSTS.test(s.endpoint) || !B64.test(k.p256dh || '') || !B64.test(k.auth || '')) return out_({ ok: false, error: 'invalid' });
      const row = [s.endpoint, k.p256dh, k.auth, Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm'), String(b.device || '').slice(0, 40)];
      const i = rows.findIndex(r => r[0] === s.endpoint);
      if (i >= 0) { sh.getRange(i + 2, 1, 1, 5).setNumberFormat('@').setValues([row]); return out_({ ok: true }); }
      if (rows.length >= MAX) return out_({ ok: false, error: 'full' });
      sh.getRange(rows.length + 2, 1, 1, 5).setNumberFormat('@').setValues([row]);
      return out_({ ok: true });
    }
    if (b.action === 'unsubscribe') {
      if (typeof b.endpoint !== 'string') return out_({ ok: false, error: 'invalid' });
      const keep = rows.filter(r => r[0] !== b.endpoint);
      if (keep.length !== rows.length) write_(sh, keep);
      return out_({ ok: true });
    }
    if (b.key !== KEY || KEY.indexOf('여기에') === 0) return out_({ ok: false, error: 'forbidden' });
    if (b.action === 'list') {
      return out_({ ok: true, subs: rows.filter(r => r[0]).map(r => ({ endpoint: r[0], p256dh: r[1], auth: r[2] })) });
    }
    if (b.action === 'remove') {
      const gone = {};
      (b.endpoints || []).forEach(x => { gone[x] = 1; });
      const keep = rows.filter(r => !gone[r[0]]);
      if (keep.length !== rows.length) write_(sh, keep);
      return out_({ ok: true, removed: rows.length - keep.length });
    }
    return out_({ ok: false, error: 'unknown action' });
  } finally {
    lock.releaseLock();
  }
}
