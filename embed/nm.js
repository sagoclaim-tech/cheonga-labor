/* 청아 노무수첩 홈페이지 연동 스크립트
   사용법: <div class="nm-embed nm-figures"></div> (nm-figures, nm-changes, nm-grants, nm-calc, nm-interp, 행정해석 건수는 nm-limit-5)
           ※ 그누보드 내용관리는 data- 속성을 지우므로 class로 지정합니다.
           <script src="https://app.xn--o80bq8pj4a8ztxwcn2k.com/embed/nm.js" defer></script>
   ※ 앱의 data.json, interp.json을 실시간으로 읽으므로 앱이 갱신되면 홈페이지도 함께 갱신됩니다. */
(function(){
  if(window.__NM_EMBED__)return;window.__NM_EMBED__=1;
  var BASE="https://app.xn--o80bq8pj4a8ztxwcn2k.com/";
  var APP_LABEL="청아 노무수첩 앱으로 열기";
  var CSS=".nm-embed{--nm-c:#0b4f96;--nm-ink:#1d2b3d;--nm-mu:#5d6d80;--nm-ln:#dbe3ed;--nm-bg:#f4f7fb;color:var(--nm-ink);font-size:17px;line-height:1.7;word-break:keep-all;overflow-wrap:break-word;text-align:left}"+
  ".nm-embed *{box-sizing:border-box}.nm-embed a{color:var(--nm-c)}"+
  ".nm-top{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;justify-content:space-between;margin:0 0 18px}.nm-asof{color:var(--nm-mu);font-size:15px}"+
  ".nm-app{display:inline-flex;align-items:center;gap:6px;background:var(--nm-c);color:#fff!important;text-decoration:none;border-radius:999px;padding:11px 22px;font-size:16px;font-weight:600}.nm-app:hover{opacity:.9}"+
  ".nm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}"+
  ".nm-card{background:#fff;border:1px solid var(--nm-ln);border-radius:14px;padding:18px 20px}"+
  ".nm-card h3{margin:0 0 10px;font-size:20px;color:var(--nm-c);font-weight:700}.nm-card h3 small{font-size:14px;color:var(--nm-mu);font-weight:400;margin-left:6px}"+
  ".nm-row{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-top:1px solid var(--nm-ln)}.nm-row:first-of-type{border-top:0}"+
  ".nm-k{color:var(--nm-ink)}.nm-v{font-weight:700;white-space:nowrap;text-align:right}.nm-nx{display:block;font-weight:400;font-size:14px;color:#b5480c}"+
  ".nm-calc{display:inline-block;margin-top:10px;font-size:15px;text-decoration:none;border:1px solid var(--nm-c);border-radius:999px;padding:4px 12px}"+
  ".nm-sec{margin:0 0 28px}.nm-sec>h3{font-size:22px;margin:0 0 10px;color:var(--nm-ink)}.nm-sec>h3 .nm-cnt{color:var(--nm-c);margin-left:6px}"+
  ".nm-item{background:#fff;border:1px solid var(--nm-ln);border-radius:12px;padding:14px 18px;margin:0 0 10px}"+
  ".nm-ih{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center}.nm-date{font-weight:700;color:var(--nm-c);margin-right:4px}.nm-t{font-weight:700}"+
  ".nm-pill{display:inline-block;font-size:13.5px;border-radius:999px;padding:1px 9px;background:var(--nm-bg);color:var(--nm-mu);border:1px solid var(--nm-ln)}"+
  ".nm-ok{background:#e7f4ec;color:#1d6b3a;border-color:#bfe2cc}.nm-warn{background:#fdf1e3;color:#9a5300;border-color:#f3d4ad}.nm-no{background:#f1f2f5;color:#59606b}"+
  ".nm-ba{margin-top:6px}.nm-lab{color:var(--nm-mu);font-size:14.5px;margin-right:4px}.nm-note{color:var(--nm-mu);font-size:15px;margin-top:4px}"+
  ".nm-more{display:block;width:100%;margin:4px 0 0;padding:10px;border:1px dashed var(--nm-ln);background:var(--nm-bg);border-radius:10px;color:var(--nm-c);font-size:16px;cursor:pointer}"+
  ".nm-g{background:#fff;border:1px solid var(--nm-ln);border-radius:12px;margin:0 0 10px}.nm-g summary{list-style:none;cursor:pointer;padding:14px 18px}.nm-g summary::-webkit-details-marker{display:none}"+
  ".nm-g .nm-gn{display:block;font-weight:700;font-size:19px;margin-top:2px}.nm-g .nm-ga{display:block;color:var(--nm-c);font-weight:600}.nm-g[open] summary{border-bottom:1px solid var(--nm-ln)}"+
  ".nm-g dl{margin:0;padding:12px 18px 6px;display:grid;grid-template-columns:7.5em 1fr;gap:6px 12px}.nm-g dt{color:var(--nm-mu);font-size:15px}.nm-g dd{margin:0}.nm-g .nm-gs{padding:0 18px 14px;font-size:14.5px;color:var(--nm-mu)}"+
  ".nm-cg{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}"+
  ".nm-cb{display:flex;flex-direction:column;gap:4px;background:#fff;border:1px solid var(--nm-ln);border-radius:14px;padding:16px 18px;text-decoration:none;color:var(--nm-ink)!important;transition:border-color .15s,box-shadow .15s}"+
  ".nm-cb:hover{border-color:var(--nm-c);box-shadow:0 4px 14px rgba(11,79,150,.12)}.nm-cb b{font-size:19px;color:var(--nm-c)}.nm-cb span{font-size:15px;color:var(--nm-mu)}"+
  ".nm-foot{margin-top:18px;color:var(--nm-mu);font-size:14.5px}.nm-msg{color:var(--nm-mu);padding:20px 0}"+
  "@media (max-width:640px){.nm-embed{font-size:15px}.nm-card h3{font-size:18px}.nm-sec>h3{font-size:19px}.nm-note{font-size:14px}.nm-g .nm-gn,.nm-cb b{font-size:17px}.nm-card,.nm-item{padding:14px 15px}.nm-grid{grid-template-columns:1fr}.nm-g dl{grid-template-columns:1fr;gap:0 0}.nm-g dd{margin-bottom:8px}.nm-app{width:100%;justify-content:center}}";
  function addCss(){if(document.getElementById("nm-embed-css"))return;var s=document.createElement("style");s.id="nm-embed-css";s.textContent=CSS;document.head.appendChild(s);}
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
  function pad(n){return (n<10?"0":"")+n;}
  function today(){var d=new Date(Date.now()+9*3600e3);return d.getUTCFullYear()+"-"+pad(d.getUTCMonth()+1)+"-"+pad(d.getUTCDate());}
  var TODAY=today();
  function dayBefore(s){var x=new Date(s+"T00:00:00Z");x.setUTCDate(x.getUTCDate()-1);return x.toISOString().slice(0,10);}
  function won(n){return Number(n).toLocaleString("ko-KR")+"원";}
  function fmt(n){return Number(n).toLocaleString("ko-KR",{maximumFractionDigits:4});}
  var OK_SRC=/^https?:\/\/([a-z0-9-]+\.)*(law\.go\.kr|lawmaking\.go\.kr|korea\.kr|moel\.go\.kr|work24\.go\.kr|ei\.go\.kr|comwel\.or\.kr|nhis\.or\.kr|nps\.or\.kr|kead\.or\.kr|bokjiro\.go\.kr|mohw\.go\.kr|minimumwage\.go\.kr|assembly\.go\.kr|4insure\.or\.kr|kosha\.or\.kr)([\/?#]|$)/i;
  function okSrc(u){return OK_SRC.test(String(u||""));}
  function srcLabel(u){u=String(u||"");return /lawmaking\.go\.kr/.test(u)?"입법예고":/law\.go\.kr\/(행정규칙|%ED%96%89%EC%A0%95%EA%B7%9C%EC%B9%99)/i.test(u)?"고시 원문":/law\.go\.kr/.test(u)?"법령 원문":/assembly\.go\.kr/.test(u)?"국회 의안":/moel\.go\.kr/.test(u)?"고용노동부":/korea\.kr/.test(u)?"정책브리핑":"출처";}
  function srcA(u){return okSrc(u)?' <a href="'+esc(u)+'" target="_blank" rel="noopener">'+srcLabel(u)+'</a>':"";}
  function sorted(h){return h.slice().sort(function(a,b){return a.from<b.from?-1:1;});}
  function entry(D,id,date){var it=D.items[id];if(!it)return null;var cur=null;sorted(it.hist).forEach(function(e){if(e.from<=(date||TODAY))cur=e;});return cur;}
  function nextEntry(D,id){var it=D.items[id];if(!it)return null;var h=sorted(it.hist);for(var i=0;i<h.length;i++)if(h[i].from>TODAY)return h[i];return null;}
  function showVal(it,e){if(!e)return"-";if(typeof e.value==="number")return it.unit==="원"?won(e.value):fmt(e.value)+(it.unit?(it.unit==="%"?"%":" "+it.unit):"");return esc(e.value);}
  function appBtn(hash,label){return '<a class="nm-app" href="'+BASE+(hash?"#"+hash:"")+'" target="_blank" rel="noopener">'+esc(label||APP_LABEL)+'</a>';}
  function top(D,hash,label){return '<div class="nm-top"><span class="nm-asof">'+esc(TODAY)+' 기준 · 평일 자동 갱신</span>'+appBtn(hash,label)+'</div>';}
  var FOOT='<p class="nm-foot">※ 법제처, 정책브리핑, 고용노동부 등 공식 자료를 바탕으로 정리한 일반 정보이며 개별 사안의 자문을 대신하지 않습니다. 중요한 결정 전에는 원문을 확인하거나 상담해 주시기 바랍니다.</p>';
  function load(name){return fetch(BASE+name+"?t="+Math.floor(Date.now()/6e5),{cache:"no-store"}).then(function(r){if(!r.ok)throw new Error(r.status);return r.json();});}

  var GROUPS=[{t:"최저임금",calc:["mw","최저임금 계산"],rows:[["min_wage_hourly","시간급"],["min_wage_monthly","월 환산(209시간)"]]},
    {t:"4대보험 요율",calc:["ins","4대보험료 계산"],rows:[["np_rate","국민연금(노사 합계)"],["hi_rate","건강보험(노사 합계)"],["ltc_rate","장기요양(소득 대비)"],["ei_ui_worker","고용보험 실업급여(근로자)"],["ei_sp_1","고용안정·직능(사업주, 150인 미만)"]]},
    {t:"국민연금 기준소득월액",sub:"매년 7월 조정",calc:["ins","국민연금 보험료 계산"],rows:[["np_lower","하한"],["np_upper","상한"]]},
    {t:"건강보험료 월 상·하한",sub:"노사 합계",calc:["ins","4대보험료 계산"],rows:[["hi_cap_upper","상한"],["hi_cap_lower","하한"]]},
    {t:"출산·육아 급여 상한",calc:["pl","육아휴직급여 계산"],rows:[["mat_cap","출산전후휴가(월)"],["pl_cap_1","육아휴직 1~3개월(월)"],["pl_cap_4","육아휴직 4~6개월(월)"],["pl_cap_7","육아휴직 7개월 이후(월)"],["spouse_leave_cap","배우자 출산전후휴가"]]},
    {t:"구직급여 1일",calc:["ui","실업급여 계산"],rows:[["ui_daily_max","상한액"],["ui_daily_min","하한액(8시간)"]]},
    {t:"산재 보상기준",calc:["sj","보험급여 계산"],rows:[["ia_min","최저보상기준(1일)"],["ia_max","최고보상기준(1일)"],["funeral_min","장례비 최저"],["funeral_max","장례비 최고"]]},
    {t:"장애인 의무고용률",calc:["dis","의무고용·부담금 계산"],rows:[["disabled_quota","민간 사업주"]]}];

  function rFigures(D){
    var h=GROUPS.map(function(g){var rows=g.rows.map(function(r){var it=D.items[r[0]];if(!it)return"";var e=entry(D,r[0]),n=nextEntry(D,r[0]);
        return '<div class="nm-row"><span class="nm-k">'+esc(r[1])+'</span><span class="nm-v">'+showVal(it,e)+(n?'<span class="nm-nx">'+esc(n.from)+'부터 '+(e&&n.value===e.value?"변동 없음":showVal(it,n))+'</span>':"")+'</span></div>';}).join("");
      return '<div class="nm-card"><h3>'+esc(g.t)+(g.sub?'<small>'+esc(g.sub)+'</small>':"")+'</h3>'+rows+(g.calc?'<a class="nm-calc" href="'+BASE+'#calc-'+g.calc[0]+'" target="_blank" rel="noopener">'+esc(g.calc[1])+'</a>':"")+'</div>';}).join("");
    return top(D,"summary")+'<div class="nm-grid">'+h+'</div>'+FOOT;}

  var ST={"확정":"nm-ok","입법예고":"nm-warn"};
  function changeList(D,from,to){var out=[];
    Object.keys(D.items).forEach(function(id){var it=D.items[id];it.hist.forEach(function(e){if(e.from>from&&e.from<=to){var pv=entry(D,id,dayBefore(e.from));
      out.push({date:e.from,title:it.name,before:pv?showVal(it,pv):"",after:showVal(it,e),status:"확정",note:e.note||"",basis:e.basis||"",src:e.src||""});}});});
    (D.scheduled||[]).forEach(function(c){if(c.from>from&&c.from<=to)out.push({date:c.from,cat:c.cat||"",title:c.title,before:esc(c.before||""),after:esc(c.after||""),status:c.status||"",note:c.note||"",basis:c.basis||"",src:c.src||""});});
    return out.sort(function(a,b){return a.date<b.date?-1:a.date>b.date?1:(a.status==="확정"?-1:1);});}
  function changeItem(x){var ba="";if(x.before||x.after){ba=(x.before&&x.before===x.after)?'<div class="nm-ba">변동 없음(<b>'+x.after+'</b> 유지)</div>':'<div class="nm-ba">'+(x.before?'<span class="nm-lab">이전</span>'+x.before+'<br>':"")+'<span class="nm-lab">변경</span><b>'+x.after+'</b></div>';}
    return '<div class="nm-item"><div class="nm-ih"><span class="nm-date">'+esc(x.date)+'</span><span class="nm-t">'+esc(x.title)+'</span>'+(x.cat?'<span class="nm-pill">'+esc(x.cat)+'</span>':"")+'<span class="nm-pill '+(ST[x.status]||"nm-no")+'">'+esc(x.status)+'</span></div>'+ba+
      (x.note?'<div class="nm-note">※ '+esc(x.note)+'</div>':"")+(x.basis||x.src?'<div class="nm-note">'+esc(x.basis)+srcA(x.src)+'</div>':"")+'</div>';}
  function listWithMore(items,lim,id){if(items.length<=lim)return items.join("");
    return items.slice(0,lim).join("")+'<div class="nm-rest" id="'+id+'" hidden>'+items.slice(lim).join("")+'</div><button type="button" class="nm-more" data-nm-more="'+id+'">나머지 '+(items.length-lim)+'건 더 보기</button>';}
  function rChanges(D){
    var up=changeList(D,TODAY,"9999-12-31");
    var d120=new Date(new Date(TODAY+"T00:00:00Z").getTime()-120*864e5).toISOString().slice(0,10);
    var rec=changeList(D,dayBefore(d120),TODAY).filter(function(x){return x.status==="확정";}).reverse();
    var nt=(D.notices||[]).slice().sort(function(a,b){return a.date<b.date?1:-1;});
    return top(D,"summary")+
      '<div class="nm-sec"><h3>시행 예정 사항<span class="nm-cnt">'+up.length+'건</span></h3><p class="nm-note" style="margin:-4px 0 12px">확정은 공포·고시된 사항이고, 입법예고·국회 계류·정부안·예산안은 아직 바뀔 수 있는 사항입니다.</p>'+(up.length?listWithMore(up.map(changeItem),6,"nm-up"):'<p class="nm-msg">예정된 변경이 없습니다.</p>')+'</div>'+
      (rec.length?'<div class="nm-sec"><h3>최근 시행된 개정 사항<span class="nm-cnt">'+rec.length+'건</span></h3><p class="nm-note" style="margin:-4px 0 12px">최근 120일 동안 시행된 확정 사항입니다.</p>'+listWithMore(rec.map(changeItem),4,"nm-rec")+'</div>':"")+
      (nt.length?'<div class="nm-sec"><h3>입법 동향</h3>'+listWithMore(nt.map(function(n){return '<div class="nm-item"><span class="nm-date">'+esc(n.date)+'</span> '+esc(n.text)+srcA(n.src)+'</div>';}),5,"nm-nt")+'</div>':"")+FOOT;}

  function rGrants(D){var list=D.grants||[];
    var h=list.map(function(g){var dl=[["지원대상",g.target],["근로자 요건",g.worker],["지원금액",g.amount],["지원기간",g.period],["한도",g.limit],["제외·유의",g.exclude],["신청",g.apply],["올해 변경",g.changes],["내년 예정",g.next],["근거",g.basis]].filter(function(x){return x[1];}).map(function(x){return '<dt>'+x[0]+'</dt><dd>'+esc(x[1])+'</dd>';}).join("");
      return '<details class="nm-g"><summary><span class="nm-pill">'+esc(g.family||"")+'</span><span class="nm-gn">'+esc(g.name)+'</span><span class="nm-ga">'+esc(g.headline||"")+'</span></summary><dl>'+dl+'</dl><div class="nm-gs">'+(okSrc(g.src)?'<a href="'+esc(g.src)+'" target="_blank" rel="noopener">출처 원문</a> · ':"")+'확인 '+esc(g.checked||"")+'</div></details>';}).join("");
    return '<div class="nm-top"><span class="nm-asof">'+esc((D.meta&&D.meta.grantsYear)||"")+' · '+list.length+'개 지원금</span>'+appBtn("grants","우리 회사 해당 여부 앱에서 확인")+'</div>'+h+
      '<p class="nm-foot">※ 지원금은 연도별 사업운영지침과 예산 소진 여부에 따라 달라집니다. 신청 전 고용24 공고로 최종 확인하시기 바랍니다.</p>';}

  var CALC_INFO=[["mw","최저임금","시간급·월급·주급 등 5가지 방식 위반 여부"],["ui","실업급여","구직급여 일액과 총액"],["pl","육아휴직급여","기간별 상한을 반영한 월 급여"],["mat","출산전후휴가급여","우선지원대상기업 여부별 지급액"],["sp","배우자 출산전후휴가급여","단시간근로자 포함 지급액"],["sj","산재보상","휴업·장해·유족급여와 장례비"],["ins","4대보험료","근로자·사업주 부담분"],["net","급여 실수령액","4대보험과 소득세 공제 후 금액"],["sev","퇴직금","평균임금과 통상임금 비교"],["al","연차일수","입사일·회계연도 기준 발생일수"],["dg","대지급금 상한액","간이·도산 대지급금 항목별 상한 조회"],["dis","장애인 고용","의무고용 인원과 고용부담금"]];
  function rCalc(D){return top(D,"calc","전체 계산기 앱에서 열기")+'<div class="nm-cg">'+CALC_INFO.map(function(c){return '<a class="nm-cb" href="'+BASE+'#calc-'+c[0]+'" target="_blank" rel="noopener"><b>'+esc(c[1])+(c[0]==="dg"?"":" 계산기")+'</b><span>'+esc(c[2])+'</span></a>';}).join("")+'</div>'+
    '<p class="nm-foot">※ 계산기를 누르면 청아 노무수첩 앱이 새 창으로 열립니다. 입력값은 이용자의 기기에만 저장되며 결과는 일반 요건에 따른 추정치입니다.</p>';}

  function rInterp(I,lim){var it=(I.items||[]).slice().sort(function(a,b){return (a.date||"")<(b.date||"")?1:-1;}).slice(0,lim||5);
    return '<div class="nm-top"><span class="nm-asof">금전 관련 행정해석 최신순</span>'+appBtn("interp","행정해석 전체 앱에서 보기")+'</div>'+it.map(function(x){
      var k=x.kind==="civil"?"민원 답변":x.kind==="moleg"?"법제처 해석":"노동부 회시";
      return '<div class="nm-item"><div class="nm-ih"><span class="nm-date">'+esc(x.date)+'</span><span class="nm-pill">'+k+'</span>'+(x.topic?'<span class="nm-pill">'+esc(x.topic)+'</span>':"")+'</div><div class="nm-t" style="margin-top:4px">'+esc(x.title)+'</div><div class="nm-note">'+esc(x.a||"")+'</div><div class="nm-note">'+esc(x.no||"")+srcA(x.src)+'</div></div>';}).join("");}

  function run(){var els=Array.prototype.filter.call(document.querySelectorAll(".nm-embed"),function(el){el.__nm=el.getAttribute("data-nm")||((el.className.match(/\bnm-(figures|changes|grants|calc|interp)\b/)||[])[1]);var l=(el.className.match(/\bnm-limit-(\d+)\b/)||[])[1];if(l)el.__lim=+l;return !!el.__nm;});if(!els.length)return;addCss();
    var needD=false,needI=false;Array.prototype.forEach.call(els,function(el){if(el.__nm==="interp")needI=true;else needD=true;el.innerHTML='<p class="nm-msg">청아 노무수첩 자료를 불러오는 중입니다.</p>';});
    Promise.all([needD?load("data.json"):null,needI?load("interp.json"):null]).then(function(r){var D=r[0],I=r[1];
      Array.prototype.forEach.call(els,function(el){var m=el.__nm;try{
        el.innerHTML=m==="figures"?rFigures(D):m==="changes"?rChanges(D):m==="grants"?rGrants(D):m==="calc"?rCalc(D):m==="interp"?rInterp(I,el.__lim||+el.getAttribute("data-limit")||5):"";}catch(e){el.innerHTML='<p class="nm-msg">자료를 표시하지 못했습니다. '+appBtn("")+'</p>';}});
    }).catch(function(){Array.prototype.forEach.call(els,function(el){el.innerHTML='<p class="nm-msg">자료를 불러오지 못했습니다. 잠시 후 다시 시도하시거나 앱에서 확인해 주세요.</p>'+appBtn("");});});}
  document.addEventListener("click",function(e){var b=e.target.closest&&e.target.closest("[data-nm-more]");if(!b)return;var r=document.getElementById(b.getAttribute("data-nm-more"));if(r){r.hidden=false;b.remove();}});
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",run);else run();
})();
