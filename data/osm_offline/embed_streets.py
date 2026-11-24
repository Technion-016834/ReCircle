"""Embed OSM streets + names as vector data into the ReCircle SVG maps, replace online tiles.
usage: python3 -I embed_streets.py streets.json in.html out.html
"""
import json, math, re, sys

AL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
CLS = {'motorway': 'm', 'trunk': 'm', 'primary': 'm', 'motorway_link': 'm', 'trunk_link': 'm', 'primary_link': 'm',
       'secondary': 's', 'tertiary': 's', 'secondary_link': 's', 'tertiary_link': 's',
       'residential': 'r', 'unclassified': 'r', 'living_street': 'r', 'pedestrian': 'f'}
COS = math.cos(math.radians(32.08))
TOL = 2.0  # metres, Douglas-Peucker tolerance


def enc_num(n):
    v = (-n - 1) << 1 | 1 if n < 0 else n << 1
    s = ''
    while v >= 32:
        s += AL[32 | (v & 31)]
        v >>= 5
    return s + AL[v]


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    m = [(p[0] * 1.11 * COS, p[1] * 1.11) for p in pts]  # 1e-5 deg -> metres
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop()
        ax, ay = m[a]; bx, by = m[b]; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy)
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, py = m[i]
            d = abs(dx * (ay - py) - dy * (ax - px)) / L if L else math.hypot(px - ax, py - ay)
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True; st += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def build(d):
    names = ['']; nidx = {'': 0}
    out = {}
    for c in 'msrf':
        ways = [w for w in d['w'] if CLS.get(w[1]) == c]
        ways.sort(key=lambda w: (w[4][0][1], w[4][0][0]))  # spatial-ish order -> smaller deltas
        x = y = 0; strs = []; ni = []
        for _, hw, he, en, g in ways:
            g = dp(g, TOL)
            s = ''
            for px, py in g:
                s += enc_num(px - x) + enc_num(py - y); x, y = px, py
            strs.append(s)
            nm = he or en
            if nm not in nidx:
                nidx[nm] = len(names); names.append(nm)
            ni.append(nidx[nm])
        out[c] = [' '.join(strs), ni]
    return out, names


def enc_ways(ways, tol=TOL):
    x = y = 0; strs = []
    for g in ways:
        s = ''
        for px, py in dp(g, tol):
            s += enc_num(px - x) + enc_num(py - y); x, y = px, py
        strs.append(s)
    return ' '.join(strs)


def chain(segs):
    """join open polylines that share endpoints into longer lines / rings"""
    segs = [list(s) for s in segs]; out = []
    while segs:
        cur = segs.pop(0); grown = True
        while grown and cur[0] != cur[-1]:
            grown = False
            for i, s in enumerate(segs):
                if s[0] == cur[-1]: cur += s[1:]
                elif s[-1] == cur[-1]: cur += s[::-1][1:]
                elif s[-1] == cur[0]: cur = s + cur[1:]
                elif s[0] == cur[0]: cur = s[::-1] + cur[1:]
                else: continue
                segs.pop(i); grown = True; break
        out.append(cur)
    return out


def build_water(wd):
    G = lambda g: [(round(p['lon'] * 1e5), round(p['lat'] * 1e5)) for p in g]
    els = wd['elements']
    coast = chain([G(e['geometry']) for e in els if e['tags'].get('natural') == 'coastline' and e['geometry'][0] != e['geometry'][-1]])
    coast.sort(key=len, reverse=True)
    line = coast[0]  # north -> south, land on the left
    W = 3440000  # far west (34.40E)
    sea = [(W, line[0][1] + 20000)] + [(line[0][0], line[0][1] + 20000)] + line + [(line[-1][0], line[-1][1] - 20000), (W, line[-1][1] - 20000)]
    polys = []
    for e in els:
        t = e['tags']
        if e['type'] == 'way' and t.get('natural') == 'water' and e['geometry'][0] == e['geometry'][-1]:
            polys.append(G(e['geometry']))
        elif e['type'] == 'relation':
            polys += chain([G(m['geometry']) for m in e.get('members', []) if m.get('geometry')])
    lines = [G(e['geometry']) for e in els if e['type'] == 'way' and t_get(e, 'waterway') in ('river', 'canal')]
    streams = [G(e['geometry']) for e in els if e['type'] == 'way' and t_get(e, 'waterway') == 'stream']
    return {'sea': enc_ways([sea], 3), 'w': enc_ways(polys, 1.5), 'wl': enc_ways(lines), 'ws': enc_ways(streams, 3)}


def t_get(e, k):
    return e['tags'].get(k)


JS = r'''
/* ---- embedded OSM street layer (works offline, no tile server) ----
   STREETS[cls] = [ways, nameIdx]: ways separated by spaces, each a run of polyline-encoded (dx,dy) deltas on a
   1e-5 degree grid (base64url alphabet), deltas continue from the previous way's last point. */
const STREETS=__STREETS__;
const STREET_NAMES=__NAMES__;
const STREET_DATE='__DATE__';
function decStreets(s){let x=0,y=0;const ways=[];for(const w of s.split(' ')){let v=0,sh=0,isX=true,px=0;const pts=[];
  for(let i=0;i<w.length;i++){const d=OSMAL.indexOf(w[i]);v|=(d&31)<<sh;if(d<32){const n=v&1?~(v>>1):v>>1;v=0;sh=0;
    if(isX){px=n}else{x+=px;y+=n;pts.push(proj(x/1e5,y/1e5))}isX=!isX}else sh+=5}
  ways.push(pts)}return ways}
const WATER=__WATER__;
const wPath=(s,closed)=>decStreets(s).map(p=>'M'+p.map(q=>q[0].toFixed(2)+','+q[1].toFixed(2)).join('L')+(closed?'Z':'')).join('');
const SEA_D=wPath(WATER.sea,true);
const waterSvg=`<path class="wt-a" fill-rule="evenodd" d="${wPath(WATER.w,true)}"/><path class="wt-s" d="${wPath(WATER.ws)}"/><path class="wt-l" d="${wPath(WATER.wl)}"/>`;
const STREET_LABELS=[];
const streetSvg=['f','r','s','m'].map(c=>{const [s,ni]=STREETS[c];const ways=decStreets(s);let d='';
  ways.forEach((pts,i)=>{d+='M'+pts.map(p=>p[0].toFixed(2)+','+p[1].toFixed(2)).join('L');
    const nm=STREET_NAMES[ni[i]];if(!nm||pts.length<2)return;
    // label anchor: middle of the way, direction from 25% to 75% of its length
    const cum=[0];for(let k=1;k<pts.length;k++)cum.push(cum[k-1]+Math.hypot(pts[k][0]-pts[k-1][0],pts[k][1]-pts[k-1][1]));
    const L=cum[cum.length-1];if(L<3)return;
    const at=t=>{const s=t*L;let k=1;while(k<cum.length-1&&cum[k]<s)k++;const f=(s-cum[k-1])/((cum[k]-cum[k-1])||1);
      return [pts[k-1][0]+(pts[k][0]-pts[k-1][0])*f,pts[k-1][1]+(pts[k][1]-pts[k-1][1])*f]};
    const a=at(.2),b=at(.8),m=at(.5);let ang=Math.atan2(b[1]-a[1],b[0]-a[0])*180/Math.PI;if(ang>90)ang-=180;if(ang<-90)ang+=180;
    STREET_LABELS.push({n:nm,c,x:m[0],y:m[1],ang,fit:Math.hypot(b[0]-a[0],b[1]-a[1])/0.6*0.85,pr:{m:0,s:1,r:2,f:3}[c],L})});
  return `<path class="st st-${c}" d="${d}"/>`}).join('');
STREET_LABELS.sort((p,q)=>p.pr-q.pr||q.L-p.L);
const LBL_MINPPU={m:0.6,s:1.1,r:2.3,f:3};
let lq=0;function queueLabels(){if(!lq)lq=requestAnimationFrame(()=>{lq=0;drawStreetLabels()})}
function drawStreetLabels(){const W=svg.clientWidth;if(!W)return;const ppu=W/vb.w,s=1/ppu;
  svg.style.setProperty('--zk',Math.max(1,Math.min(5,Math.sqrt(ppu/1.2))).toFixed(2));
  const placed=[],byName={},out=[];const x0=vb.x,x1=vb.x+vb.w,y0=vb.y,y1=vb.y+vb.h;
  for(const l of STREET_LABELS){if(ppu<LBL_MINPPU[l.c])continue;if(l.x<x0||l.x>x1||l.y<y0||l.y>y1)continue;
    const fs=l.c==='m'?12.5:l.c==='s'?12:11;const tw=l.n.length*fs*0.56+8;if(l.fit*ppu<tw)continue;
    const r=l.ang*Math.PI/180,c=Math.abs(Math.cos(r)),si=Math.abs(Math.sin(r));
    const sx=(l.x-x0)*ppu,sy=(l.y-y0)*ppu,hw=(tw*c+fs*si)/2,hh=(tw*si+fs*c)/2;
    if(placed.some(b=>sx-hw<b[2]&&sx+hw>b[0]&&sy-hh<b[3]&&sy+hh>b[1]))continue;
    const same=byName[l.n]||(byName[l.n]=[]);if(same.some(p=>Math.hypot(p[0]-sx,p[1]-sy)<260))continue;
    placed.push([sx-hw,sy-hh,sx+hw,sy+hh]);same.push([sx,sy]);
    out.push(`<text class="stl stl-${l.c}" font-size="${(fs*s).toFixed(3)}" stroke-width="${(3*s).toFixed(3)}" transform="translate(${l.x.toFixed(2)} ${l.y.toFixed(2)}) rotate(${l.ang.toFixed(1)})" dy="${(fs*0.35*s).toFixed(3)}">${esc(l.n)}</text>`);
    if(out.length>=450)break}
  gsl.innerHTML=out.join('')}
'''

CSS = r'''
/* embedded OSM streets (offline vector basemap) */
.st{fill:none;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.st-f{stroke:var(--road);stroke-width:calc(var(--zk,1)*.9px);stroke-dasharray:4 3;opacity:.9}
.st-r{stroke:var(--road);stroke-width:calc(var(--zk,1)*1px)}
.st-s{stroke:var(--road);stroke-width:calc(var(--zk,1)*1.9px)}
.st-m{stroke:var(--road-m);stroke-width:calc(var(--zk,1)*2.6px)}
svg.far .st-r,svg.far .st-f{opacity:.55}
.wt-a{fill:var(--sea);stroke:none}
.wt-l{fill:none;stroke:var(--sea);stroke-width:calc(var(--zk,1)*3px);stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.wt-s{fill:none;stroke:var(--sea);stroke-width:calc(var(--zk,1)*1.4px);stroke-linecap:round;vector-effect:non-scaling-stroke}
.stl{fill:var(--ink);opacity:.78;stroke:var(--city);paint-order:stroke;stroke-linejoin:round;font-family:var(--f-body);text-anchor:middle;pointer-events:none}
.stl-m{font-weight:700;opacity:.85}.stl-r,.stl-f{fill:var(--muted);opacity:.95}
'''


def main(streets, water, src, dst):
    d = json.load(open(streets, encoding='utf-8'))
    data, names = build(d)
    wat = build_water(json.load(open(water, encoding='utf-8')))
    h = open(src, encoding='utf-8').read()
    date = d['ts'][:10]

    # drop the old coarse road classes, keep parks/water from the old OSM object
    m = re.search(r'const OSM=(\{.*?\});\n', h)
    osm = json.loads(m.group(1))
    for k in ('m', 's', 'r'):
        osm.pop(k, None)
    h = h[:m.start()] + 'const OSM=' + json.dumps(osm, ensure_ascii=False) + ';\n' + h[m.end():]

    js = (JS.replace('__STREETS__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
            .replace('__NAMES__', json.dumps(names, ensure_ascii=False, separators=(',', ':')))
            .replace('__DATE__', date)
            .replace('__WATER__', json.dumps(wat, separators=(',', ':'))))

    def rep(old, new, count=1):
        nonlocal h
        assert h.count(old) == count, (old[:60], h.count(old))
        h = h.replace(old, new)

    # streets go between parks and the neighbourhood outlines; labels above neighbourhood labels, under points
    rep("const osmSvg=", js + "const osmSvg=")
    rep('<g id="osmv">${osmSvg}</g>', '<g id="osmv">${osmSvg}${waterSvg}${streetSvg}</g>')
    # real OSM coastline instead of the approximate "west of the city boundary" sea
    rep('<path class="sea" d="${seaPath}"/>', '<path class="sea" d="${SEA_D}"/>')
    rep("const gp=document.createElementNS(NS,'g'); svg.appendChild(gp);",
        "const gsl=document.createElementNS(NS,'g'); svg.appendChild(gsl);\nconst gp=document.createElementNS(NS,'g'); svg.appendChild(gp);")
    rep("svg.classList.toggle('far',vb.w>HOME.w*0.6); queueTiles();",
        "svg.classList.toggle('far',vb.w>HOME.w*0.6); queueTiles(); queueLabels();")
    rep("gl.style.display=vb.w<HOME.w*0.55?'':'none'", "gl.style.display=vb.w<HOME.w*0.55&&vb.w>HOME.w*0.09?'':'none'")
    # allow zooming in to street level
    rep("Math.max(HOME.w/14,vb.w*f)", "Math.max(HOME.w/70,vb.w*f)")
    # no tile servers at all: the embedded vector map is the only background
    h = re.sub(r"const PROVIDERS=\[.*?\];", "const PROVIDERS=[];", h, count=1, flags=re.S)
    rep("autoTiles();\n", "useProvider(null);\n")
    h = re.sub(r'<div class="bgbox">.*?</div></div>', '', h, count=1, flags=re.S)
    rep("$('bgsel').value=p?p.id:'vector';", "")
    h = re.sub(r"\$\('bgsel'\)\.onchange=.*?\};\n", "", h, count=1, flags=re.S)
    attr_old = "'© <a href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\" rel=\"noopener\">OpenStreetMap contributors</a>'"
    attr_new = ("'© <a href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\" rel=\"noopener\">OpenStreetMap contributors</a>"
                " (ODbL), ' + STREET_DATE")
    rep(attr_old, attr_new)
    rep("$('attrtxt').innerHTML='רקע: ", "$('attrtxt').innerHTML='רחובות ושמות רחובות: ")
    rep('על רקע OpenStreetMap ושכונות', 'על רקע רחובות OpenStreetMap מוטמעים ושכונות')
    rep('svg.far .osm-r{display:none}', 'svg.far .osm-r{display:none}' + CSS)
    open(dst, 'w', encoding='utf-8').write(h)
    print(dst, len(h.encode('utf-8')), 'bytes;', 'streets', sum(len(v[0]) for v in data.values()), 'names', len(names))


if __name__ == '__main__':
    main(*sys.argv[1:])
