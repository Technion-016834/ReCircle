"""Build map label candidates (labels.json) for the recommender maps: neighbourhood names and street names.
Neighbourhoods: Tel Aviv-Yafo municipal GIS boundaries, as embedded in recircle_map.html (GEO.n).
Streets: the offline OpenStreetMap extract (tlv_streets_osm.json, ODbL).
Coordinates are pre-projected to the maps' 300x330 viewBox. The page decides at runtime which
candidates to show for the current zoom, skipping any that would overlap.
usage: python3 -I build_labels.py recircle_map.html tlv_streets_osm.json records.json labels.json"""
import json, sys, math, re, collections
B = dict(lat0=32.028, lat1=32.147, lon0=34.742, lon1=34.848); W, H = 300, 330
def P(lon, lat): return ((lon - B['lon0']) / (B['lon1'] - B['lon0']) * W, (B['lat1'] - lat) / (B['lat1'] - B['lat0']) * H)
M_PER_UNIT = (B['lon1'] - B['lon0']) / W * 111320 * math.cos(math.radians(32.08))   # ~31.4 m per viewBox unit
norm = lambda t: ' '.join((t or '').replace('׳', "'").replace('״', '"').split())

# ---- neighbourhoods
page = open(sys.argv[1], encoding='utf-8').read()
i = page.index('const GEO=') + 10; geo = json.loads(page[i:page.index(';\n', i)])
dec = lambda p: P((p[0] + 347000) / 1e4, (p[1] + 320000) / 1e4)
recs = [P(r['lon'], r['lat']) for r in json.load(open(sys.argv[3], encoding='utf-8')) if r.get('lat') is not None]
def inside(pt, ring):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: c = not c
    return c
def label_point(ring):
    # area centroid; if it falls outside (concave shapes) use the inside grid point farthest from the edge
    a = cx = cy = 0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        f = x1 * y2 - x2 * y1; a += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f
    if abs(a) < 1e-9: return ring[0], 0
    c = (cx / (3 * a), cy / (3 * a))
    if inside(c, ring): return c, abs(a) / 2
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]; best, bd = ring[0], -1
    for gx in range(21):
        for gy in range(21):
            q = (min(xs) + (max(xs) - min(xs)) * gx / 20, min(ys) + (max(ys) - min(ys)) * gy / 20)
            if not inside(q, ring): continue
            d = min(math.hypot(q[0] - p[0], q[1] - p[1]) for p in ring)
            if d > bd: best, bd = q, d
    return best, abs(a) / 2
hoods = []
for name, rings in geo['n']:
    ring = max(([dec(p) for p in r] for r in rings), key=lambda r: abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))))
    (x, y), area = label_point(ring)
    n_rec = sum(1 for q in recs if inside(q, ring))
    short = norm(name).split(' - ')[0].split(',')[0].replace('-', ' ')   # 'הצפון הישן - החלק הצפוני' -> 'הצפון הישן'
    hoods.append([short, round(x, 1), round(y, 1), round(area, 1), n_rec])
hoods.sort(key=lambda h: -(h[4] * 4 + math.sqrt(h[3])))
seen = set(); hoods = [h for h in hoods if not (h[0] in seen or seen.add(h[0]))]   # one label per name, at its best part

# ---- streets: one candidate per long, fairly straight stretch of a named way
CLS = {'motorway': 0, 'trunk': 0, 'primary': 0, 'secondary': 1, 'tertiary': 1, 'residential': 2, 'living_street': 2, 'unclassified': 2, 'pedestrian': 2}
st = json.load(open(sys.argv[2], encoding='utf-8'))
# Every named street gets candidates: OSM ways of the same name are chained end to end, simplified, and each
# straight run becomes one or more anchor points (every ~150 m on long runs) with its angle and usable length.
# Short streets keep at least their longest run, so they show up once the map is zoomed in far enough.
total = collections.Counter(); byname = collections.defaultdict(list)
for _, hw, he, en, g in st['w']:
    nm = norm(he) or norm(en); c = CLS.get(hw)
    if not nm or c is None or len(g) < 2: continue
    pts = [P(x / 1e5, y / 1e5) for x, y in g]
    total[nm] += sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    byname[nm].append((c, pts))
key = lambda p: (round(p[0], 2), round(p[1], 2))
def chains(parts):
    ends = collections.defaultdict(list)
    for i, (_, g) in enumerate(parts): ends[key(g[0])].append(i); ends[key(g[-1])].append(i)
    used = set(); out = []
    def take(p):
        for j in ends[key(p)]:
            if j not in used: used.add(j); return parts[j]
    for i, (c, g) in enumerate(parts):
        if i in used: continue
        used.add(i); cur = list(g); cls = c
        for _ in range(2):
            while (nx := take(cur[-1])):
                cls = min(cls, nx[0]); seg = nx[1] if key(nx[1][0]) == key(cur[-1]) else nx[1][::-1]; cur += seg[1:]
            cur.reverse()
        out.append((cls, cur))
    return out
def dp(pts, tol):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop(); (ax, ay), (bx, by) = pts[a], pts[b]; L = math.hypot(bx - ax, by - ay); best, bi = -1, -1
        for i in range(a + 1, b):
            px_, py_ = pts[i]; d = abs((bx - ax) * (ay - py_) - (by - ay) * (ax - px_)) / L if L else math.hypot(px_ - ax, py_ - ay)
            if d > best: best, bi = d, i
        if best > tol: keep[bi] = True; stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]
MIN_RUN = 25 / M_PER_UNIT; STEP = 150 / M_PER_UNIT
cand = []
for nm, parts in byname.items():
    runs = []
    for c, g in chains(parts):
        g = dp(g, 0.12)                                             # ~4 m: a street that bends less than that counts as straight
        for a, b in zip(g, g[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L > 0: runs.append((L, c, a, b))
    if not runs: continue
    runs.sort(key=lambda r: -r[0])
    for k, (L, c, a, b) in enumerate(runs):
        if L < MIN_RUN and k: break
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        n = max(1, int(L / STEP))
        for i in range(n):
            t = (i + .5) / n; x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if not (0 <= x <= W and 0 <= y <= H): continue
            fit = 2 * min(t, 1 - t) * L if n > 1 else L          # room for the text along the run, centred on the anchor
            cand.append([nm, c, round(x, 1), round(y, 1), round(ang), round(fit, 1)])
# order: class, then how long the street is overall (famous long streets first), then this stretch's straight run
cand.sort(key=lambda r: (r[1], -total[r[0]], -r[5]))
names = []; nix = {}
out = []
for nm, c, x, y, ang, fit in cand:
    if nm not in nix: nix[nm] = len(names); names.append(nm)
    out += [nix[nm], c, x, y, ang, fit]
json.dump({'src': 'Neighbourhoods: Tel Aviv-Yafo municipality GIS. Streets: OpenStreetMap contributors (ODbL), extract ' + st['ts'][:10],
           'hoods': hoods, 'names': names, 'streets': out}, open(sys.argv[4], 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('hoods', len(hoods), 'street candidates', len(cand), 'names', len(names))
