"""ReCircle - screening log (sustainable / not sustainable) - build script.

Builds recircle_screening_v0.1.csv/.xlsx from two real sources:
  Stage A: the 303 records of recircle_dataset_v0.2.csv (collected from thematic sources)
  Stage B: every shop=* / craft=* object in OpenStreetMap inside a Tel Aviv bounding box
           (osm_shops_craft_raw_2026-11-24.json, Overpass, 1,825 objects),
           clipped to the Tel Aviv-Yafo municipal boundary (tlv_boundary_nominatim_r1382494.json).
Every row gets Decision + Criterion_Code + Decision_Reason + Evidence. Criteria: METHODOLOGY_screening.md.
No row is invented; rules only read the OSM tags and name that are in the raw file.
usage: python3 -I build_screening.py   (run from this folder)
"""
import json, re, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(HERE, *a)

RAW = json.load(open(P('osm_shops_craft_raw_2026-11-24.json'), encoding='utf-8'))
POLY = json.load(open(P('tlv_boundary_nominatim_r1382494.json'), encoding='utf-8'))['coords']
V2 = pd.read_csv(P('..', 'v0.2', 'recircle_dataset_v0.2.csv'))
OSM_TS = RAW['osm3s']['timestamp_osm_base']


def inside(lon, lat, poly=POLY):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


# ---------------------------------------------------------------- criteria
CRIT = {
    'I1': 'שימוש חוזר / יד שנייה',
    'I2': 'תיקון והארכת חיי מוצר',
    'I3': 'צמצום אריזות / מילוי חוזר',
    'I4': 'שיתוף, השאלה והחלפה',
    'I5': 'הצלת מזון ועודפים',
    'I6': 'אמנות ועיצוב מחומרים ממוחזרים',
    'I7': 'צרכנות מקיימת (מקומי, אתי, חקלאי)',
    'I8': 'קהילה, טבע וחינוך סביבתי',
    'X1': 'מכירת מוצרים חדשים בלבד',
    'X2': 'קמעונאות מזון רגילה',
    'X3': 'שירות אישי שאינו מאריך חיי מוצר',
    'X4': 'רכב ותחבורה ממונעת',
    'X5': 'לא עסק בודד / לא פעיל',
    'X6': 'אין מספיק מידע להערכה',
    'G1': 'מחוץ לגבולות תל אביב-יפו',
    'R1': 'גבולי, דורש החלטת צוות',
}

KW = [  # (criterion, regex on name, evidence label)
    ('I1', r'יד ?שני|וינטג|ווינטג|vintage|second ?hand|thrift|antique|עתיקות|אנטיק|פשפש|רה-?סייקל|recycl', 'שם העסק'),
    ('I2', r'תיקון|תיקונים|repair|\bfix\b|סנדלר|חייט|תופר|מתפרה|שען|ריפוד|upholster', 'שם העסק'),
    ('I3', r'refill|zero ?waste|ללא אריזה|עירום|בתפזורת|bulk', 'שם העסק'),
    ('I4', r'השאלה|library of things|ספריית חפצים|swap', 'שם העסק'),
]

REPAIR_CRAFT = {'shoemaker', 'tailor', 'watchmaker', 'clockmaker', 'electronics_repair', 'upholsterer',
                'dressmaker', 'jeweller_repair', 'computer_repair'}
FOOD = {'supermarket', 'convenience', 'bakery', 'greengrocer', 'kiosk', 'butcher', 'confectionery', 'pastry',
        'alcohol', 'wine', 'seafood', 'spices', 'coffee', 'cheese', 'deli', 'nuts', 'tea', 'beverages', 'food',
        'chocolate', 'grocery', 'take-away_food', 'water', 'health_food', 'nutrition_supplements', 'dairy'}
SERVICE = {'hairdresser', 'beauty', 'laundry', 'dry_cleaning', 'tattoo', 'massage', 'estate_agent',
           'travel_agency', 'psychic', 'copyshop', 'photo', 'ticket', 'lottery', 'pet_grooming', 'optician',
           'hearing_aids', 'chemist', 'outpost', 'money_lender', 'pawnbroker', 'funeral_directors', 'betting'}
VEHICLE = {'car', 'car_repair', 'tyres', 'car_parts', 'motorcycle', 'motorcycle_parts', 'motorcycle_repair',
           'fuel', 'car_wash'}
NOTBIZ = {'mall', 'vacant', 'disused'}
SERVICE_CRAFT = {'key_cutter', 'photographer', 'caterer', 'winery', 'confectionery', 'grinding_mill'}
HEB = {'supermarket': 'סופרמרקט', 'convenience': 'מכולת', 'bakery': 'מאפייה', 'greengrocer': 'ירקן',
       'clothes': 'חנות בגדים', 'hairdresser': 'מספרה', 'bicycle': 'חנות אופניים', 'kiosk': 'קיוסק',
       'books': 'חנות ספרים', 'shoes': 'חנות נעליים', 'mobile_phone': 'חנות סלולר', 'electronics': 'אלקטרוניקה',
       'furniture': 'רהיטים', 'jewelry': 'תכשיטים', 'cosmetics': 'קוסמטיקה', 'mall': 'קניון',
       'car_repair': 'מוסך', 'laundry': 'מכבסה', 'dry_cleaning': 'ניקוי יבש'}


def decide(t):
    """Return (decision, code, reason_he, evidence, method). decision in INCLUDE/EXCLUDE/REVIEW."""
    shop, craft = t.get('shop'), t.get('craft')
    name = t.get('name') or t.get('name:he') or t.get('name:en') or ''
    kind = f'shop={shop}' if shop else f'craft={craft}'
    kh = HEB.get(shop, kind)
    # ---- explicit tags first
    if shop in ('second_hand', 'charity', 'antiques') or t.get('second_hand') == 'only':
        ev = kind if shop in ('second_hand', 'charity', 'antiques') else 'second_hand=only'
        return 'INCLUDE', 'I1', f'אושר: העסק מוכר פריטים משומשים (תגית OSM {ev}), כלומר שימוש חוזר במוצרים קיימים.', ev, 'rule_tag'
    if shop in ('shoe_repair', 'repair') or craft in REPAIR_CRAFT:
        return 'INCLUDE', 'I2', f'אושר: עסק תיקון ({kind}). תיקון מאריך את חיי המוצר ומונע קנייה חדשה.', kind, 'rule_tag'
    if shop == 'bicycle' and t.get('service:bicycle:repair') == 'yes':
        return 'INCLUDE', 'I2', 'אושר: חנות אופניים עם שירות תיקון (service:bicycle:repair=yes).', 'service:bicycle:repair=yes', 'rule_tag'
    if t.get('bulk_purchase') in ('only', 'yes') or t.get('zero_waste') in ('only', 'yes'):
        k = 'bulk_purchase' if t.get('bulk_purchase') else 'zero_waste'
        return 'INCLUDE', 'I3', f'אושר: מכירה בתפזורת / ללא אריזה ({k}={t[k]}).', f'{k}={t[k]}', 'rule_tag'
    if t.get('second_hand') == 'yes':
        return 'REVIEW', 'R1', 'גבולי: העסק מוכר גם פריטים משומשים (second_hand=yes) לצד חדשים. צריך לבדוק איזה חלק מהפעילות.', 'second_hand=yes', 'rule_tag'
    if shop in VEHICLE:
        return 'EXCLUDE', 'X4', f'נפסל: {kh}, עיסוק ברכב ממונע. מחוץ לתחום הצריכה המעגלית של ReCircle (מוצרי צריכה, מזון, קהילה).', kind, 'rule_tag'
    # ---- name keywords (weaker evidence -> flagged)
    for code, rx, lab in KW:
        m = re.search(rx, name, re.I)
        if m:
            return 'INCLUDE', code, f'אושר (לפי השם): השם "{name}" מעיד על {CRIT[code]}. התיוג נשען על השם בלבד ודורש אימות.', f'name~"{m.group(0)}"', 'rule_name'
    # ---- borderline
    if t.get('organic') in ('only', 'yes'):
        return 'REVIEW', 'R1', f'גבולי: {kh}, עם תגית organic={t["organic"]}. אורגני לבדו אינו קריטריון לכלכלה מעגלית, וצריך החלטת צוות (I7?).', f'organic={t["organic"]}', 'rule_tag'
    if shop == 'farm':
        return 'REVIEW', 'R1', 'גבולי: חנות חקלאית (shop=farm). ייתכן שמתאים ל-I7 (תוצרת מקומית), אבל צריך לבדוק מקור הסחורה.', kind, 'rule_tag'
    if shop in ('laundry', 'dry_cleaning'):
        return 'EXCLUDE', 'X3', f'נפסל: {kh}, שירות תחזוקה שגרתי, לא תיקון או שימוש חוזר. (גבולי: מאריך במעט את חיי הבגד.)', kind, 'rule_tag'
    if shop == 'rental':
        return 'REVIEW', 'R1', 'גבולי: עסק השכרה (shop=rental). השכרה יכולה להיות שיתוף (I4), אבל לא ידוע מה מושכר.', kind, 'rule_tag'
    # ---- exclusions
    if not shop and not craft:
        return 'EXCLUDE', 'X6', 'נפסל: אין סוג עסק.', '', 'rule_tag'
    if shop in NOTBIZ:
        why = 'קניון הוא מתחם ולא עסק בודד. החנויות שבתוכו נבחנות כל אחת בנפרד.' if shop == 'mall' else 'העסק לא פעיל.'
        return 'EXCLUDE', 'X5', f'נפסל: {why}', kind, 'rule_tag'
    if shop in VEHICLE:
        return 'EXCLUDE', 'X4', f'נפסל: {kh}, עיסוק ברכב ממונע. מחוץ לתחום הצריכה המעגלית של ReCircle (מוצרי צריכה, מזון, קהילה).', kind, 'rule_tag'
    if shop in FOOD:
        return 'EXCLUDE', 'X2', f'נפסל: {kh}, קמעונאות מזון רגילה. אין עדות להצלת עודפים או למכירה ללא אריזה.', kind, 'rule_tag'
    if shop in SERVICE or craft in SERVICE_CRAFT:
        return 'EXCLUDE', 'X3', f'נפסל: {kind} הוא שירות או ייצור שאינו כולל תיקון, שימוש חוזר או שיתוף.', kind, 'rule_tag'
    if shop == 'yes' and not name:
        return 'EXCLUDE', 'X6', 'נפסל: אין שם ואין סוג עסק מוגדר (shop=yes), אי אפשר להעריך.', kind, 'rule_tag'
    if shop == 'yes':
        return 'REVIEW', 'R1', f'לא ידוע: סוג העסק לא מוגדר ב-OSM (shop=yes). צריך לבדוק מה "{name}" מוכר.', kind, 'rule_tag'
    return 'EXCLUDE', 'X1', f'נפסל: {kh}, מכירת מוצרים חדשים בלבד. אין עדות ליד שנייה, תיקון, מילוי חוזר או שיתוף.', kind, 'rule_tag'


def norm(s):
    return re.sub(r'[^0-9a-zא-ת]', '', str(s).lower())


v2_names = {}
for r in V2.itertuples():
    for n in (r.Name, getattr(r, 'Name_EN', None)):
        if isinstance(n, str) and len(norm(n)) >= 4:
            v2_names.setdefault(norm(n), r.Record_ID)

PC2CRIT = {'SECOND_HAND': 'I1', 'REPAIR': 'I2', 'SUSTAINABLE_SHOPPING': 'I7', 'SHARING': 'I4',
           'FOOD_RESCUE': 'I5', 'ECO_ART': 'I6', 'NATURE_COMMUNITY': 'I8'}
rows = []
# ---------------------------------------------------------------- Stage B: OSM general pool
for e in RAW['elements']:
    t = e.get('tags', {})
    lat = e.get('lat', e.get('center', {}).get('lat')); lon = e.get('lon', e.get('center', {}).get('lon'))
    name = t.get('name') or t.get('name:he') or t.get('name:en') or ''
    addr = ' '.join(x for x in (t.get('addr:street', ''), t.get('addr:housenumber', '')) if x)
    city = t.get('addr:city', '')
    kind = f"shop={t['shop']}" if 'shop' in t else f"craft={t.get('craft', '')}"
    if not inside(lon, lat):
        d = ('OUT_OF_SCOPE', 'G1', f'לא נבחן: המיקום מחוץ לגבול המוניציפלי של תל אביב-יפו{" (" + city + ")" if city else ""}. הפיילוט מוגבל לעיר.', f'lat={lat:.5f}, lon={lon:.5f}', 'rule_geo')
    else:
        d = decide(t)
    match = v2_names.get(norm(name)) if name else None
    rule_dec = d[0]
    if match and d[0] == 'EXCLUDE':
        # the OSM tag alone excluded it, but a richer real source (Stage A record) shows a sustainable activity
        rr = V2[V2.Record_ID == match].iloc[0]
        code = PC2CRIT[rr.Primary_Category]
        d = ('INCLUDE', code, f'אושר לפי מקור נוסף: לפי תגית OSM ({kind}) העסק היה נפסל, אבל רשומה {match} '
             f'({rr.Source_Name}) מתעדת פעילות של {CRIT[code]} ({rr.Subcategory}). מקרה שמראה שתגית סוג עסק לבדה מפספסת.',
             f'{kind}; {match}', 'cross_source')
    elif match and d[0] == 'OUT_OF_SCOPE':
        d = (d[0], d[1], d[2] + f' שים לב: העסק קיים במאגר v0.2 כ-{match} עם כתובת בתל אביב, צריך לתקן שם.', d[3], d[4])
    rows.append(dict(
        Screen_ID=f"OSM-{e['type'][0]}{e['id']}", Stage='B_osm_general_pool', Name=name,
        Business_Type=kind, Address=addr, City_Tag=city, Latitude=round(lat, 6), Longitude=round(lon, 6),
        Source_Name=f'OpenStreetMap (Overpass, data as of {OSM_TS})',
        Source_URL=f"https://www.openstreetmap.org/{e['type']}/{e['id']}", Website=t.get('website', t.get('contact:website', '')),
        Decision=d[0], Is_Sustainable={'INCLUDE': 1, 'EXCLUDE': 0}.get(d[0], ''), Criterion_Code=d[1],
        Criterion=CRIT[d[1]], Decision_Reason=d[2], Evidence=d[3], Label_Method=d[4], Rule_Only_Decision=rule_dec,
        Needs_Human_Check='yes' if d[4] in ('rule_name', 'cross_source') or d[0] == 'REVIEW' else 'no',
        In_ReCircle_v0_2=match or '', Primary_Category='', Has_Name='yes' if name else 'no'))

# ---------------------------------------------------------------- Stage A: thematic sources (v0.2)
for r in V2.itertuples():
    code = PC2CRIT[r.Primary_Category]
    if r.Subcategory in ('ללא אריזה ומילוי חוזר',):
        code = 'I3'
    src = r.Source_Name if isinstance(r.Source_Name, str) else r.Source_Type
    reason = (f'אושר: {CRIT[code]} ({r.Subcategory}). הרשומה נאספה ממקור שנבחר מראש כמקור בנושא קיימות ({src}), '
              f'וסווגה ידנית ל-{r.Primary_Category}.')
    if r.Record_ID == 'RC-0191':
        reason = ('אושר בתנאי: מכירת עודפי מלאי של בגדים חדשים. ב-v0.1 סומנה "לא מתאים לאף קטגוריה"; ב-v0.2 שויכה ל-SUSTAINABLE_SHOPPING '
                  '(עודפי מלאי חדשים). גבולי, דורש החלטת צוות.')
    rows.append(dict(
        Screen_ID=r.Record_ID, Stage='A_thematic_sources', Name=r.Name, Business_Type=f'{r.Record_Type} / {r.Subcategory}',
        Address=r.Address if isinstance(r.Address, str) else '', City_Tag='', Latitude=r.Latitude, Longitude=r.Longitude,
        Source_Name=src, Source_URL=r.Source_URL, Website='',
        Decision='REVIEW' if r.Record_ID == 'RC-0191' else 'INCLUDE', Is_Sustainable='' if r.Record_ID == 'RC-0191' else 1,
        Criterion_Code='R1' if r.Record_ID == 'RC-0191' else code,
        Criterion=CRIT['R1' if r.Record_ID == 'RC-0191' else code], Decision_Reason=reason,
        Evidence=f'Source_Type={r.Source_Type}; Subcategory={r.Subcategory}', Label_Method='source_selection+manual_category', Rule_Only_Decision='',
        Needs_Human_Check='yes' if r.Verification_Status != 'verified' else 'no', In_ReCircle_v0_2=r.Record_ID,
        Primary_Category=r.Primary_Category, Has_Name='yes'))

df = pd.DataFrame(rows)


def training_use(r):
    if r.Decision not in ('INCLUDE', 'EXCLUDE'):
        return 'no: not labeled (out of scope / review)'
    if r.Stage == 'B_osm_general_pool' and r.In_ReCircle_v0_2:
        return f'no: same business as {r.In_ReCircle_v0_2} (Stage A row is used)'
    if r.Has_Name != 'yes':
        return 'no: no name, no text to learn from'
    return 'yes'


df['Training_Use'] = df.apply(training_use, axis=1)

# Cap on negative training examples (Shimi, 2026-11-24: "up to 1000"). If more qualify, keep a sample
# stratified by exclusion criterion (fixed seed); the rest stay in the log with Training_Use explaining why.
MAX_NEG = 1000
neg = df[(df.Training_Use == 'yes') & (df.Is_Sustainable == 0)]
if len(neg) > MAX_NEG:
    keep = neg.groupby('Criterion_Code', group_keys=False).apply(
        lambda g: g.sample(round(len(g) * MAX_NEG / len(neg)), random_state=42)).index
    df.loc[neg.index.difference(keep), 'Training_Use'] = f'no: over the cap of {MAX_NEG} negatives (stratified sample kept)'
df.to_csv(P('recircle_screening_v0.1.csv'), index=False, encoding='utf-8-sig')

# ---------------------------------------------------------------- summaries
summ_stage = df.pivot_table(index='Stage', columns='Decision', values='Screen_ID', aggfunc='count', fill_value=0)
summ_crit = df.groupby(['Stage', 'Decision', 'Criterion_Code', 'Criterion']).size().rename('Count').reset_index()
B = df[df.Stage == 'B_osm_general_pool']
top_types = B[B.Decision != 'OUT_OF_SCOPE'].groupby(['Business_Type', 'Decision']).size().unstack(fill_value=0)
top_types = top_types.assign(Total=top_types.sum(axis=1)).sort_values('Total', ascending=False)
crit_tbl = pd.DataFrame([dict(Code=k, Criterion=v, Type={'I': 'הכללה', 'X': 'פסילה', 'G': 'תחום', 'R': 'גבולי'}[k[0]]) for k, v in CRIT.items()])
with pd.ExcelWriter(P('recircle_screening_v0.1.xlsx')) as w:
    df.to_excel(w, sheet_name='screening', index=False)
    summ_stage.to_excel(w, sheet_name='summary_stage')
    summ_crit.to_excel(w, sheet_name='summary_criteria', index=False)
    top_types.to_excel(w, sheet_name='osm_by_business_type')
    crit_tbl.to_excel(w, sheet_name='criteria', index=False)

print(summ_stage)
print(summ_crit.to_string())
print(df.groupby(['Training_Use', 'Is_Sustainable'], dropna=False).size())
print('OSM matched to v0.2:', (B.In_ReCircle_v0_2 != '').sum())
