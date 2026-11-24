"""Build an offline street graph (routing.json) for the recommender's map mode.
Uses the same offline OSM extract as build_osm_bg.py (tlv_streets_osm.json, ODbL).
Nodes are street junctions and way ends; edges follow the street between them.
usage: python3 -I build_routing.py tlv_streets_osm.json routing.json"""
import json, sys, math, collections
BASE_X, BASE_Y = 3474000, 3202600            # lon/lat * 1e5 offsets, keeps numbers short
NOWALK = {'motorway', 'motorway_link', 'trunk', 'trunk_link'}
NOCAR = {'pedestrian'}
# class index -> typical urban car speed (km/h); used for the car time estimate
CLS = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'living_street', 'pedestrian', 'unclassified']
def cls_of(hw):
    base = hw.replace('_link', '')
    return CLS.index(base) if base in CLS else CLS.index('unclassified')
KX = 111320 * math.cos(math.radians(32.08)) / 1e5; KY = 110570 / 1e5   # metres per 1e-5 degree
def dist(a, b): return math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY)

st = json.load(open(sys.argv[1], encoding='utf-8'))
ways = [(hw, [tuple(p) for p in g]) for _, hw, he, en, g in st['w'] if len(g) >= 2]
use = collections.Counter()
for hw, g in ways:
    for p in set(g): use[p] += 1
isnode = lambda p: use[p] > 1
nid = {}; nodes = []
def node(p):
    if p not in nid: nid[p] = len(nodes); nodes.append(p)
    return nid[p]
edges = []   # (a, b, metres, cls, flags, mid points)
for hw, g in ways:
    c = cls_of(hw); fl = (0 if hw in NOWALK else 1) | (0 if hw in NOCAR else 2)
    start = 0
    for i in range(1, len(g)):
        if i == len(g) - 1 or isnode(g[i]):
            seg = g[start:i + 1]
            L = sum(dist(seg[k], seg[k + 1]) for k in range(len(seg) - 1))
            if L > 0.5: edges.append((node(seg[0]), node(seg[-1]), L, c, fl, seg[1:-1]))
            start = i
# keep the largest connected component (walk or car usable)
adj = collections.defaultdict(list)
for a, b, *_ in edges: adj[a].append(b); adj[b].append(a)
seen = {}; best = None
for s in range(len(nodes)):
    if s in seen: continue
    comp = [s]; seen[s] = s; q = [s]
    while q:
        u = q.pop()
        for v in adj[u]:
            if v not in seen: seen[v] = s; comp.append(v); q.append(v)
    if best is None or len(comp) > len(best): best = comp
keep = set(best); remap = {}
for o in sorted(keep): remap[o] = len(remap)
N = []
for o in sorted(keep): x, y = nodes[o]; N += [x - BASE_X, y - BASE_Y]
E = []; G = []
for a, b, L, c, fl, mid in edges:
    if a not in keep: continue
    E += [remap[a], remap[b], round(L), c * 4 + fl]
    # mid geometry, delta-encoded from the start node; thinned to ~8 m
    ax, ay = nodes[a]; out = []; px, py = ax, ay; last = (ax, ay)
    for p in mid:
        if dist(p, last) < 8: continue
        out += [p[0] - px, p[1] - py]; px, py = p; last = p
    G.append(out)
json.dump({'src': 'OpenStreetMap contributors (ODbL), extract ' + st['ts'][:10], 'bx': BASE_X, 'by': BASE_Y,
           'cls': CLS, 'n': N, 'e': E, 'g': G}, open(sys.argv[2], 'w'), separators=(',', ':'))
print('nodes', len(keep), 'of', len(nodes), 'edges', len(E) // 4)
