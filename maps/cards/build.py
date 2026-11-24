"""Build ReCircle info cards (per Shimi's template) into a gallery + inject into both maps.

One-time build step (2026-11-15). The maps in ../ already contain the cards.
Re-running needs the pre-cards originals (*_backup_before_cards.html) next to the maps;
they are not kept in the repo."""
import base64, json, os, re, shutil, io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
ROOT = os.path.dirname(HERE.rstrip('/')) + '/'  # maps/
OUT = HERE

buf = io.BytesIO(); Image.open(HERE + 'logo.png').resize((76, 102), Image.LANCZOS).save(buf, 'PNG', optimize=True)
LOGO = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

CARD_CSS = r"""
/* ---- ReCircle info card (template by Shimi) ---- */
.rc-card{--rc-head:#0f5c63;--rc-head-ink:#fff;--rc-orange:#f29c1f;--rc-orange-ink:#1f1a10;--rc-val:#0f5c63;--rc-lab:#3c4542;--rc-bg:#fff;--rc-ink:#1c2420;--rc-line:#dde3e0;--rc-ph:#8a9590;
  direction:rtl;background:var(--rc-bg);color:var(--rc-ink);border-radius:18px;overflow:hidden;border:1px solid var(--rc-line);box-shadow:0 2px 10px rgba(0,0,0,.08);font-family:"Assistant",system-ui,-apple-system,"Segoe UI",Arial,sans-serif;text-align:right;break-inside:avoid}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .rc-card{--rc-bg:#19201d;--rc-ink:#e4ebe6;--rc-val:#7fd0c4;--rc-lab:#a8b5ae;--rc-line:#2b3530;--rc-ph:#7d8a84;--rc-head:#0d4a50}}
:root[data-theme="dark"] .rc-card{--rc-bg:#19201d;--rc-ink:#e4ebe6;--rc-val:#7fd0c4;--rc-lab:#a8b5ae;--rc-line:#2b3530;--rc-ph:#7d8a84;--rc-head:#0d4a50}
.rc-head{background:var(--rc-head);color:var(--rc-head-ink);display:flex;align-items:center;gap:16px;padding:20px 22px}
.rc-head-txt{flex:1;min-width:0;display:flex;flex-direction:column;gap:12px}
.rc-name{margin:0;font-weight:700;font-size:clamp(20px,2.6vw,26px);line-height:1.2;overflow-wrap:anywhere;color:var(--rc-head-ink)}
.rc-pills{display:flex;flex-wrap:wrap;gap:10px}
.rc-pill{display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;border-radius:999px;padding:5px 18px;min-width:76px}
.rc-pill.t{background:#fff;color:var(--rc-head)}
.rc-pill.c{background:var(--rc-orange);color:var(--rc-orange-ink)}
.rc-logo{flex:none;width:84px;height:84px;border-radius:50%;background:#fff;display:grid;place-items:center}
.rc-logo img{width:44px;height:auto;display:block}
.rc-body{padding:20px 22px 22px}
.rc-desc{margin:0 0 18px;font-style:italic;font-size:16px;line-height:1.55;color:var(--rc-ink);overflow-wrap:anywhere}
.rc-desc.ph{color:var(--rc-ph)}
.rc-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px 28px;margin:0}
.rc-grid>div{min-width:0}
.rc-grid dt{font-size:14px;color:var(--rc-lab);margin-bottom:4px}
.rc-grid dd{margin:0;font-weight:700;font-size:16.5px;line-height:1.35;color:var(--rc-val);overflow-wrap:anywhere}
.rc-grid dd a{color:var(--rc-val);text-decoration:underline;text-underline-offset:3px}
.rc-grid dd.ph{color:var(--rc-ph);font-weight:600}
@media (max-width:480px){.rc-grid{grid-template-columns:1fr}.rc-logo{width:64px;height:64px}.rc-logo img{width:34px}.rc-head{padding:16px}.rc-body{padding:16px}}
"""

CARD_JS = r"""
const RC_LOGO='__LOGO__';
const RC_CAT={SECOND_HAND:'יד שנייה ווינטג׳',FOOD_RESCUE:'הצלת מזון',MARKET_EVENT:'שווקים ואירועי יד שנייה',ENVIRONMENTAL_ACTIVITY:'פעילויות סביבתיות',ECO_ART:'אמנות ותרבות סביבתית',REPAIR_REUSE:'תיקון ושימוש חוזר',NONE:'ללא קטגוריה'};
const RC_TYPE={BUSINESS:'עסק',EVENT:'אירוע',INITIATIVE:'יוזמה'};
const rcEsc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const rcFmtDate=s=>{const m=String(s||'').match(/^(\d{4})-(\d{2})-(\d{2})/);return m?`${+m[3]}.${+m[2]}.${m[1]}`:String(s||'')};
function rcCard(r){
  const v=(x,ph='לא צוין')=>x&&String(x).trim()?`<dd>${rcEsc(x)}</dd>`:`<dd class="ph">${ph}</dd>`;
  const isEv=r.type==='EVENT';
  const when=isEv?[rcFmtDate(r.date),r.hours].filter(Boolean).join(' · '):r.hours;
  const src=r.url?`<dd><a href="${rcEsc(r.url)}" target="_blank" rel="noopener">${rcEsc(r.sname||'קישור')} ↗</a></dd>`:'<dd class="ph">לא צוין</dd>';
  return `<article class="rc-card" data-id="${rcEsc(r.id)}">
  <header class="rc-head"><div class="rc-head-txt"><h3 class="rc-name">${rcEsc(r.name)}</h3>
    <div class="rc-pills"><span class="rc-pill t">${rcEsc(RC_TYPE[r.type]||r.type||'')}</span><span class="rc-pill c">${rcEsc(RC_CAT[r.cat||'NONE'])}</span></div></div>
    <div class="rc-logo"><img src="${RC_LOGO}" alt="ReCircle"></div></header>
  <div class="rc-body">${r.desc?`<p class="rc-desc">${rcEsc(r.desc)}</p>`:'<p class="rc-desc ph">אין תיאור במקור המידע</p>'}
  <dl class="rc-grid">
    <div><dt>כתובת</dt>${v(r.addr)}</div>
    <div><dt>${isEv?'מועד ושעות':'שעות פעילות'}</dt>${v(when)}</div>
    <div><dt>${r.servLabel||'שירותים'}</dt>${v(r.serv)}</div>
    <div><dt>מחיר</dt>${v(r.price)}</div>
    <div><dt>מקור</dt>${src}</div>
    <div><dt>אומת לאחרונה</dt>${v(r.verified&&rcFmtDate(r.verified),'טרם אומת')}</div>
  </dl></div></article>`;}
""".replace('__LOGO__', LOGO)


def load(path):
    s = open(path, encoding='utf-8').read()
    return s, json.loads(re.search(r'const DATA=(\[.*?\]);\n', s).group(1))


# ---------- brand theme (applies the card's look to the whole UI) ----------
HDR_LOGO = '<div class="rc-logo hdr-logo"><img src="' + LOGO + '" alt="ReCircle"></div>'
THEME_CSS = r"""
/* ---- ReCircle brand theme: same palette, logo and type as the info card ---- */
:root{--brand:#0f5c63;--brand-ink:#fff;--orange:#f29c1f;--orange-ink:#1f1a10;--bg:#eef2f0;--accent:#0f5c63;--accent-ink:#fff;--line:#dde3e0;--r:18px;
  --f-display:"Assistant",system-ui,-apple-system,"Segoe UI",Arial,sans-serif;--f-body:"Assistant",system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--brand:#0d4a50;--bg:#111614;--accent:#7fd0c4;--accent-ink:#0d1512;--line:#2b3530}}
:root[data-theme="dark"]{--brand:#0d4a50;--bg:#111614;--accent:#7fd0c4;--accent-ink:#0d1512;--line:#2b3530}
body{font-family:var(--f-body)}
.wrap>header{display:flex;flex-wrap:wrap;background:var(--brand);color:var(--brand-ink);border-radius:var(--r);padding:18px 22px;align-items:center!important;justify-content:flex-start!important;gap:16px 18px;box-shadow:0 2px 10px rgba(0,0,0,.08)}
.wrap>header .hdr-title{flex:1 1 260px;min-width:0}
.wrap>header h1{font-family:var(--f-display);font-weight:700;color:var(--brand-ink)}
.wrap>header h1 span{color:var(--orange)!important}
.wrap>header .sub{color:rgba(255,255,255,.82)!important}
.wrap>header .notice{background:var(--orange);color:var(--orange-ink);border-radius:999px;padding:6px 16px;font-weight:700}
.hdr-logo{width:72px;height:72px;flex:none}.hdr-logo img{width:38px}
@media (max-width:480px){.hdr-logo{width:56px;height:56px}.hdr-logo img{width:30px}.wrap>header{padding:14px 16px}}
h1,h2,h3,.detail h2,.month h3,.ev .date b,.kpi b{font-family:var(--f-display);font-weight:700}
nav.tabs button[aria-selected="true"]{color:var(--accent);border-bottom-color:var(--orange)}
.panel,.kpi,.ev,.mapbox{border-radius:var(--r);box-shadow:0 2px 10px rgba(0,0,0,.05)}
.ev:hover{border-color:var(--orange)}
.chip[aria-pressed="true"]{border-color:var(--accent)}
.seg button[aria-pressed="true"],.mapctl button:hover{background:var(--accent);color:var(--accent-ink)}
.item.sel{box-shadow:inset -4px 0 0 var(--orange)}
.pt.sel{stroke:var(--orange);stroke-width:3}
.linkbtn,a{color:var(--accent)}
.kpi b{color:var(--accent)}
"""

# ---------- 1. inject into maps ----------
NEW_SELECT_BODY = r"""  $('detail').innerHTML=rcCard(r)+`${r.lnote?`<div class="note"><b>הערת תיוג:</b> ${esc(r.lnote)}</div>`:''}${r.dnote?`<div class="note"><b>הערת נתונים:</b> ${esc(r.dnote)}</div>`:''}<p class="rc-meta">מזהה ${esc(r.id)} · ${esc(STATUSNAME[r.status]||r.status)} · ${esc(r.sub||'')}</p>`;"""

def inject(path, serv_label):
    import os
    bak = path.replace('.html', '_backup_before_cards.html')
    if not os.path.exists(bak):
        shutil.copy(path, bak)
    s, data = load(bak)  # always rebuild from the pre-cards original
    s = s.replace('</style>', THEME_CSS + '</style>', 1)
    # sandboxed previews (about:srcdoc) forbid history.replaceState -> guard it
    s = s.replace("if(location.hash.slice(1)!==v)history.replaceState(null,'','#'+v);", "try{if(location.hash.slice(1)!==v)history.replaceState(null,'','#'+v)}catch(e){}")
    assert 'history.replaceState' not in s.replace("try{if(location.hash.slice(1)!==v)history.replaceState", ''), path
    s = re.sub(r'(<header>\s*)<div>', lambda m: m.group(1) + HDR_LOGO + '<div class="hdr-title">', s, count=1)
    s = s.replace('</style>', CARD_CSS + '#detail{padding:0;border:0;background:none;gap:10px}#detail .empty{padding:18px 20px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r);margin:0}.rc-meta{font-size:12.5px;color:var(--muted);margin:0}\n</style>', 1)
    s = s.replace('<script>\nconst DATA=', '<script>\n' + CARD_JS + '\nconst DATA=', 1)
    pat = re.compile(r"  const kv=\[\['סוג רשומה'.*?\n  \$\('detail'\)\.innerHTML=.*?\$\{r\.dnote\?`<div class=\"note\"><b>הערת נתונים:</b> \$\{esc\(r\.dnote\)\}</div>`:''\}`;", re.S)
    assert len(pat.findall(s)) == 1, path
    body = NEW_SELECT_BODY
    if serv_label:
        body = "  r.servLabel='" + serv_label + "';\n" + body
    s = pat.sub(lambda m: body, s)
    open(path, 'w', encoding='utf-8').write(s)
    return data

d_main = inject(ROOT + 'recircle_map.html', None)
d_vin = inject(ROOT + 'vintage_map.html', 'מה מוכרים')

# ---------- 2. gallery ----------
for r in d_main: r['ds'] = 'main'
for r in d_vin: r['ds'] = 'vintage'; r['servLabel'] = 'מה מוכרים'
allrows = d_main + d_vin
keep = ['id','name','type','desc','serv','cat','addr','hours','date','price','url','sname','ds','servLabel','sub','tags']
rows = [{k: r.get(k, '') for k in keep if r.get(k)} for r in allrows]
for r in rows:
    r['cat'] = r.get('cat') or 'NONE'

GALLERY = r"""<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>כרטיסי ReCircle</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700&display=swap">
<style>
:root{--bg:#eef2f0;--surface:#fff;--ink:#1c2420;--muted:#5b6861;--line:#d7ded8;--accent:#0f5c63}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#111614;--surface:#19201d;--ink:#e4ebe6;--muted:#97a59d;--line:#2b3530;--accent:#7fd0c4;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111614;--surface:#19201d;--ink:#e4ebe6;--muted:#97a59d;--line:#2b3530;--accent:#7fd0c4;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Assistant",system-ui,sans-serif;padding:20px max(16px,env(safe-area-inset-right)) 40px max(16px,env(safe-area-inset-left))}
.wrap{max-width:1500px;margin:0 auto}
h1{margin:0;font-size:clamp(24px,3vw,32px)}h1 span{color:var(--accent)}
.sub{color:var(--muted);margin:4px 0 16px;font-size:14px}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:18px;z-index:2}@media (min-width:700px){.bar{position:sticky;top:8px}}
.bar input,.bar select{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);min-width:0}
.bar input{flex:1 1 220px}
.bar .n{color:var(--muted);font-size:14px;margin-inline-start:auto}
.bar button{font:inherit;font-weight:600;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:8px;padding:8px 12px;cursor:pointer}
.bar :focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,460px),1fr));gap:20px;align-items:start}
.empty{color:var(--muted)}
@media print{body{background:#fff;padding:0}.bar,.sub{display:none}.grid{display:block}.rc-card{margin:0 0 14px;box-shadow:none;page-break-inside:avoid}.rc-head,.rc-pill{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
__CARDCSS__
</style></head><body><div class="wrap">
<header>
<div><h1>כרטיסי <span>ReCircle</span></h1>
<p class="sub">כרטיס מידע לכל רשומה במאגר, לפי התבנית. הנתונים מהמקורות האמיתיים בלבד. שדה בלי מידע מסומן "לא צוין", וכל הרשומות עדיין ממתינות לאימות.</p></div>
</header>
<div class="bar">
 <input type="search" id="q" placeholder="חיפוש לפי שם, כתובת או תיאור" aria-label="חיפוש">
 <select id="ds" aria-label="מאגר"><option value="">כל המאגרים</option><option value="vintage">חנויות וינטג׳ ושווקים (31)</option><option value="main">המאגר הכללי (268)</option></select>
 <select id="type" aria-label="סוג"><option value="">כל הסוגים</option><option value="BUSINESS">עסק</option><option value="EVENT">אירוע</option><option value="INITIATIVE">יוזמה</option></select>
 <select id="cat" aria-label="קטגוריה"><option value="">כל הקטגוריות</option></select>
 <button id="print">הדפסה / PDF</button>
 <span class="n" id="n"></span>
</div>
<div class="grid" id="grid"></div>
</div>
<script>
__CARDJS__
const ROWS=__ROWS__;
const $=id=>document.getElementById(id);
$('cat').innerHTML+=Object.entries(RC_CAT).filter(([k])=>ROWS.some(r=>r.cat===k)).map(([k,v])=>`<option value="${k}">${v}</option>`).join('');
ROWS.forEach(r=>r.hay=[r.name,r.addr,r.desc,r.serv,r.tags,r.sub].join(' ').toLowerCase());
const st={q:'',ds:'vintage',type:'',cat:''};
try{const s=JSON.parse(localStorage.getItem('rc-cards')||'null');if(s)Object.assign(st,s,{q:''})}catch(e){}
['ds','type','cat'].forEach(k=>$(k).value=st[k]);
function draw(){const q=st.q.trim().toLowerCase();
  const rs=ROWS.filter(r=>(!st.ds||r.ds===st.ds)&&(!st.type||r.type===st.type)&&(!st.cat||r.cat===st.cat)&&(!q||r.hay.includes(q)));
  $('n').textContent=`${rs.length} כרטיסים`;
  $('grid').innerHTML=rs.map(rcCard).join('')||'<p class="empty">אין רשומות שמתאימות לסינון.</p>';}
$('q').oninput=e=>{st.q=e.target.value;draw()};
['ds','type','cat'].forEach(k=>$(k).onchange=e=>{st[k]=e.target.value;try{localStorage.setItem('rc-cards',JSON.stringify(st))}catch(_){}draw()});
$('print').onclick=()=>window.print();
draw();
</script></body></html>"""
html = (GALLERY.replace('__CARDCSS__', CARD_CSS + THEME_CSS + '.wrap>header{margin-bottom:16px}.wrap>header .sub{margin:4px 0 0}.bar{border-radius:var(--r)}.bar button{background:var(--orange);color:var(--orange-ink);border-color:transparent}').replace('<header>\n<div>', '<header>\n' + HDR_LOGO + '<div class="hdr-title">').replace('__CARDJS__', CARD_JS)
        .replace('__ROWS__', json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')))
import os; os.makedirs(OUT, exist_ok=True)
open(OUT + 'recircle_cards.html', 'w', encoding='utf-8').write(html)
print(len(rows), 'cards;', len(html)//1024, 'KB')
