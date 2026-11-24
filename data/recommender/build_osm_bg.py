"""Build a small OSM background (sea, water, streets) for the recommender mini map.
Projects the offline OSM extracts in ../osm_offline onto the map's 300x330 viewBox.
usage: python3 -I build_osm_bg.py streets.json water.json out.json"""
import json, sys, importlib.util
spec = importlib.util.spec_from_file_location('emb', sys.argv[4] if len(sys.argv) > 4 else 'embed_streets.py')
B = dict(lat0=32.028, lat1=32.147, lon0=34.742, lon1=34.848); W, H = 300, 330
CLS = {'motorway': 'm', 'trunk': 'm', 'primary': 'm', 'motorway_link': 'm', 'trunk_link': 'm', 'primary_link': 'm',
       'secondary': 's', 'tertiary': 's', 'residential': 'r', 'unclassified': 'r', 'living_street': 'r'}
def P(lon, lat): return ((lon - B['lon0']) / (B['lon1'] - B['lon0']) * W, (B['lat1'] - lat) / (B['lat1'] - B['lat0']) * H)
def dp(pts, tol):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); ax, ay = pts[a]; bx, by = pts[b]; dx, dy = bx - ax, by - ay; L = (dx * dx + dy * dy) ** .5
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, py = pts[i]; d = abs(dx * (ay - py) - dy * (ax - px)) / L if L else ((px - ax) ** 2 + (py - ay) ** 2) ** .5
            if d > best: best, bi = d, i
        if best > tol: keep[bi] = True; st += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]
inside = lambda p: -20 < p[0] < W + 20 and -20 < p[1] < H + 20
def path(lines, tol, closed=False):
    out = []
    for g in lines:
        if not any(inside(p) for p in g): continue
        g = dp(g, tol)
        if len(g) < 2: continue
        out.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in g) + ('Z' if closed else ''))
    return ''.join(out)
st = json.load(open(sys.argv[1], encoding='utf-8'))
roads = {'m': [], 's': [], 'r': []}
for _, hw, he, en, g in st['w']:
    c = CLS.get(hw)
    if c: roads[c].append([P(x / 1e5, y / 1e5) for x, y in g])
wd = json.load(open(sys.argv[2], encoding='utf-8'))
els = wd['elements']
def chain(segs):
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
G = lambda g: [(p['lon'], p['lat']) for p in g]
coast = chain([G(e['geometry']) for e in els if e['tags'].get('natural') == 'coastline' and e['geometry'][0] != e['geometry'][-1]])
coast.sort(key=len, reverse=True); line = coast[0]
sea = [(34.40, line[0][1] + .2), (line[0][0], line[0][1] + .2)] + line + [(line[-1][0], line[-1][1] - .2), (34.40, line[-1][1] - .2)]
polys = []
for e in els:
    t = e['tags']
    if e['type'] == 'way' and t.get('natural') == 'water' and e['geometry'][0] == e['geometry'][-1]: polys.append(G(e['geometry']))
    elif e['type'] == 'relation': polys += chain([G(m['geometry']) for m in e.get('members', []) if m.get('geometry')])
rivers = [G(e['geometry']) for e in els if e['type'] == 'way' and e['tags'].get('waterway') in ('river', 'canal')]
pr = lambda ls: [[P(x, y) for x, y in g] for g in ls]
out = {'date': st['ts'][:10], 'sea': path(pr([sea]), .3, True), 'w': path(pr(polys), .3, True), 'wl': path(pr(rivers), .3),
       'm': path(roads['m'], .3), 's': path(roads['s'], .35), 'r': path(roads['r'], .45)}
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), separators=(',', ':'))
print({k: len(v) for k, v in out.items()})
