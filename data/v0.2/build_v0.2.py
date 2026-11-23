"""Build ReCircle dataset v0.2 from v0.1 + vintage file.

- Does NOT modify v0.1 files. Writes recircle_dataset_v0.2.csv / .xlsx next to this script.
- `Category` (v0.1, 6 classes) is kept as-is. New ML target = `Primary_Category` (7 classes).
- New attributes are filled ONLY from text that already exists in the sources (rules below).
  Anything not stated stays UNKNOWN. Nothing is invented.
"""
import os
import re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = ROOT + 'v0.2/'
d = pd.read_csv(ROOT + 'recircle_dataset_v0.1.csv')
v = pd.read_csv(ROOT + 'vintage/recircle_vintage_markets_TLV.csv')

# ------------------------------------------------------------------ taxonomy
PRIMARY = {
    'SECOND_HAND': "יד שנייה ווינטג'",
    'SHARING': 'שיתוף, השאלה והחלפה',
    'REPAIR': 'תיקון ומחדוש',
    'FOOD_RESCUE': 'הצלת מזון',
    'NATURE_COMMUNITY': 'טבע, גינות וקהילה',
    'ECO_ART': 'אמנות, עיצוב ותרבות',
    'SUSTAINABLE_SHOPPING': 'קנייה מקיימת',
}
ACTIVITY = {
    'STORE': 'חנות / בית עסק', 'SERVICE': 'שירות (תיקון)', 'MARKET': 'שוק / יריד',
    'WORKSHOP': 'סדנה / קורס / הרצאה', 'EXHIBITION_SHOW': 'תערוכה / מופע', 'TOUR': 'סיור',
    'COMMUNITY_SPOT': 'נקודה קהילתית', 'APP_ONLINE': 'אפליקציה / אונליין',
}
SH_CLOTH, SH_HOME, SH_ANTIQ, SH_ART, SH_MIX = 'בגדים ואופנה', 'ריהוט ובית', 'עתיקות ואספנות', 'חומרי יצירה', 'כללי / מעורב'
# old subcategory -> (Primary_Category, new Subcategory, Activity_Type)
SUBMAP = {
    # ECO_ART
    'אירוע אופנה בת-קיימא': ('ECO_ART', 'אופנה בת-קיימא', 'EXHIBITION_SHOW'),
    'אמנות ותרבות סביבתית': ('ECO_ART', 'יצירה מחומרים ממוחזרים', 'EXHIBITION_SHOW'),
    'ביאנלה לאומנות ועיצוב': ('ECO_ART', 'תערוכה', 'EXHIBITION_SHOW'),
    'מוצרי עיצוב מחומרים ממוחזרים': ('ECO_ART', 'עיצוב ממוחזר', 'STORE'),
    'סטודיו לעיצוב מחומרים קיימים': ('ECO_ART', 'אופנה בת-קיימא', 'STORE'),
    'תערוכה בנושא סביבה': ('ECO_ART', 'תערוכה', 'EXHIBITION_SHOW'),
    'תערוכה בנושא סביבה וצומח': ('ECO_ART', 'תערוכה', 'EXHIBITION_SHOW'),
    'תערוכה מחומרים ממוחזרים': ('ECO_ART', 'תערוכה', 'EXHIBITION_SHOW'),
    'תערוכת אמנות מחומרים ממוחזרים': ('ECO_ART', 'תערוכה', 'EXHIBITION_SHOW'),
    # ENVIRONMENTAL_ACTIVITY
    'גידול ביתי': ('NATURE_COMMUNITY', 'חינוך והרצאות', 'WORKSHOP'),
    'גינון קהילתי': ('NATURE_COMMUNITY', 'גינה קהילתית', 'COMMUNITY_SPOT'),
    'גן ירק יצרני': ('NATURE_COMMUNITY', 'גינה קהילתית', 'COMMUNITY_SPOT'),
    'הרצאה/קורס סביבתי': ('NATURE_COMMUNITY', 'חינוך והרצאות', 'WORKSHOP'),
    'חינוך סביבתי לילדים': ('NATURE_COMMUNITY', 'חינוך והרצאות', 'WORKSHOP'),
    'יצירה לילדים מחומרים ממוחזרים': ('ECO_ART', 'יצירה מחומרים ממוחזרים', 'WORKSHOP'),
    'יצירה מחומרים ממוחזרים': ('ECO_ART', 'יצירה מחומרים ממוחזרים', 'WORKSHOP'),
    'סדנת שימוש חוזר': ('ECO_ART', 'יצירה מחומרים ממוחזרים', 'WORKSHOP'),
    'סיור טבע עירוני': ('NATURE_COMMUNITY', 'טבע עירוני', 'TOUR'),
    'פעילות ילדים בגינה קהילתית': ('NATURE_COMMUNITY', 'גינה קהילתית', 'WORKSHOP'),
    'פעילות/סדנה סביבתית': ('NATURE_COMMUNITY', 'חינוך והרצאות', 'WORKSHOP'),
    'קהילת פעילי קיימות': ('NATURE_COMMUNITY', 'קהילת פעילים', 'WORKSHOP'),
    # FOOD_RESCUE
    'אפליקציית הצלת מזון': ('FOOD_RESCUE', 'פלטפורמה להצלת מזון', 'APP_ONLINE'),
    'מבצעי סוף יום במאפייה': ('FOOD_RESCUE', 'עודפים מעסקים', 'STORE'),
    'מקרר/מזווה קהילתי': ('FOOD_RESCUE', 'מקרר / מזווה קהילתי', 'COMMUNITY_SPOT'),
    # MARKET_EVENT -> SECOND_HAND + MARKET
    "יריד בגדי וינטג' שבועי": ('SECOND_HAND', SH_CLOTH, 'MARKET'),
    "יריד וינטג', יד שנייה ועתיקות": ('SECOND_HAND', SH_MIX, 'MARKET'),
    'יריד יד שנייה': ('SECOND_HAND', SH_CLOTH, 'MARKET'),
    'יריד יד שנייה שכונתי': ('SECOND_HAND', SH_MIX, 'MARKET'),
    "יריד קהילתי עם מכירת וינטג'": ('SECOND_HAND', SH_CLOTH, 'MARKET'),
    'יריד/שוק החלפות ויד שנייה': ('SECOND_HAND', SH_MIX, 'MARKET'),
    'מכירת בגדי יד שנייה ניידת': ('SECOND_HAND', SH_CLOTH, 'MARKET'),
    'מכירת בגדי ילדים משומשים': ('SECOND_HAND', SH_CLOTH, 'MARKET'),
    'שוק יד שנייה לילדים': ('SECOND_HAND', SH_MIX, 'MARKET'),
    "שוק עתיקות ווינטג' חוזר": ('SECOND_HAND', SH_ANTIQ, 'MARKET'),
    'שוק עתיקות ופריטי אספנות': ('SECOND_HAND', SH_ANTIQ, 'MARKET'),
    # REPAIR_REUSE
    'אירוע תיקונים קהילתי': ('REPAIR', 'תיקון כללי (בר תיקון)', 'SERVICE'),
    'חידוש רהיטים': ('REPAIR', 'רהיטים וריפוד', 'SERVICE'),
    'ריפוד וחידוש רהיטים': ('REPAIR', 'רהיטים וריפוד', 'SERVICE'),
    'מחסן השאלת ציוד': ('SHARING', 'מחסן השאלה', 'COMMUNITY_SPOT'),
    'מסגרות ותיקוני מתכת': ('REPAIR', 'מתכת וכלי בית', 'SERVICE'),
    'תיקון כלי בישול': ('REPAIR', 'מתכת וכלי בית', 'SERVICE'),
    'מרכז תיקון ומיחדוש אופניים': ('REPAIR', 'אופניים', 'SERVICE'),
    'תיקון אופניים': ('REPAIR', 'אופניים', 'SERVICE'),
    'סדנה/אירוע תיקון ומיחדוש': ('REPAIR', 'ביגוד וטקסטיל', 'WORKSHOP'),
    'סדנת מחדוש טקסטיל': ('REPAIR', 'ביגוד וטקסטיל', 'WORKSHOP'),
    'תיקון ותפירת בגדים': ('REPAIR', 'ביגוד וטקסטיל', 'SERVICE'),
    'תיקון מוצרי חשמל ואלקטרוניקה': ('REPAIR', 'חשמל ואלקטרוניקה', 'SERVICE'),
    'תיקון מכשירים סלולריים ואלקטרוניקה': ('REPAIR', 'חשמל ואלקטרוניקה', 'SERVICE'),
    'תיקון מצלמות': ('REPAIR', 'חשמל ואלקטרוניקה', 'SERVICE'),
    'תיקון ציוד סטריאו': ('REPAIR', 'חשמל ואלקטרוניקה', 'SERVICE'),
    'תיקון נעליים': ('REPAIR', 'נעליים ותיקים', 'SERVICE'),
    'תיקון שעונים': ('REPAIR', 'שעונים ותכשיטים', 'SERVICE'),
    'תיקון תכשיטים': ('REPAIR', 'שעונים ותכשיטים', 'SERVICE'),
    # SECOND_HAND
    'ארון/ביתן החלפה ונתינה': ('SHARING', 'ארון החלפה ונתינה', 'COMMUNITY_SPOT'),
    'חומרי גלם יד שנייה לאמנות': ('SECOND_HAND', SH_ART, 'STORE'),
    'חנות יד שנייה': ('SECOND_HAND', SH_MIX, 'STORE'),
    # vintage-file subcategories
    "וינטג' בית": ('SECOND_HAND', SH_HOME, 'STORE'),
    "וינטג' בית ועתיקות": ('SECOND_HAND', SH_HOME, 'STORE'),
    "וינטג' ריהוט": ('SECOND_HAND', SH_HOME, 'STORE'),
    'שוק קבוע': ('SECOND_HAND', SH_ANTIQ, 'MARKET'),
    'יריד חוזר': ('SECOND_HAND', SH_CLOTH, 'MARKET'),
}
CLOTH_STORE_SUBS = {"בגדי וינטג'", "בגדי וינטג' ויוקרה", 'בגדים יד שנייה', 'בגדים יד שנייה - מיזם חברתי',
                    'בגדים יד שנייה - עמותה', 'בגדים יד שנייה לפי משקל', 'בגדים יד שנייה משודרגים',
                    "וינטג' ויוקרה יד שנייה", 'חנות בגדי יד שנייה ניידת',
                    "וינטג' בגדים", 'יד שנייה בגדים', 'יד שנייה גברים', 'יד שנייה יוקרה', "וינטג' יוקרה",
                    "וינטג' מעצבים", "וינטג' ספורט", "וינטג' תיקים", 'יד שנייה לפי משקל', 'חנות חברתית', 'חנות צדקה'}
for s in CLOTH_STORE_SUBS:
    SUBMAP[s] = ('SECOND_HAND', SH_CLOTH, 'STORE')
for s in ['בית קפה המוכר עודפים דרך אפליקציה', 'מאפייה המוכרת עודפים דרך אפליקציה',
          'מסעדה המוכרת עודפים דרך אפליקציה', 'מעדנייה המוכרת עודפים דרך אפליקציה',
          'מעדניית גבינות המוכרת עודפים דרך אפליקציה', 'פטיסרי המוכר עודפים דרך אפליקציה']:
    SUBMAP[s] = ('FOOD_RESCUE', 'עודפים מעסקים', 'STORE')

# per-record overrides: (Primary, Subcategory, Activity, note)
OVERRIDE = {
    'RC-0191': ('SUSTAINABLE_SHOPPING', 'עודפי מלאי חדשים', 'MARKET', 'v0.2: עודפי בגדים חדשים -> SUSTAINABLE_SHOPPING (קטגוריה חדשה)'),
    'RC-0206': ('SHARING', 'השאלת ביגוד', 'MARKET', 'v0.2: השקת מיזם השאלת שמלות + קח/תן -> SHARING'),
    'RC-0204': ('REPAIR', 'תיקון כללי (בר תיקון)', 'SERVICE', 'v0.2: בר תיקון כללי'),
    'RC-0208': ('NATURE_COMMUNITY', 'טבע עירוני', 'WORKSHOP', 'v0.2: הקמת בוסתן -> טבע עירוני'),
}

# style / model tags extracted out of old subcategory strings
STYLE_RULES = [("וינטג'", "וינטג'"), ('יוקרה', 'יוקרה'), ('מעצבים', 'מעצבים'), ('ספורט', 'ספורט וסטריט'),
               ('לפי משקל', 'לפי משקל'), ('עמותה', 'עמותה'), ('צדקה', 'עמותה'), ('מיזם חברתי', 'מיזם חברתי'),
               ('חנות חברתית', 'מיזם חברתי'), ('משודרגים', 'שדרוג בגדים'), ('תיקים', 'תיקים'),
               ('דרך אפליקציה', 'דרך אפליקציה'), ('עתיקות', 'עתיקות'), ('ניידת', 'נייד')]
AREA_TAGS = {'דרום', 'צפון מזרח', 'צפון מערב', 'מזרח', 'דרום מזרח', 'דרום מערב', 'מרכז', 'יפו', 'פלורנטין'}
DROP_TAGS = {'OSM', 'עירייה'}

# ------------------------------------------------------------------ merge vintage file
MATCH = {'VS-01': 'RC-0233', 'VS-02': 'RC-0228', 'VS-03': 'RC-0229', 'VS-04': 'RC-0227', 'VS-05': 'RC-0236',
         'VS-07': 'RC-0234', 'VS-14': 'RC-0235', 'VS-21': 'RC-0237', 'VS-23': 'RC-0230', 'VS-24': 'RC-0268',
         'VS-25': 'RC-0190', 'VS-26': 'RC-0185', 'VS-30': 'RC-0210', 'VS-31': 'RC-0251'}
d['Merged_From'] = ''
d['Name_EN'] = ''
d['Geocode_Source'] = ''
d['Subcategory_v01'] = d['Subcategory']
d['_extra_text'] = ''
src_geo = {'GIS עירוני': 'GIS עירוני (מקור)', 'לוח אירועים עירוני': 'לוח אירועים (המרה מ-ITM)', 'OSM (ODbL)': 'OpenStreetMap'}
d.loc[d.Latitude.notna(), 'Geocode_Source'] = d.loc[d.Latitude.notna(), 'Source_Type'].map(src_geo).fillna('לא תועד')

vi = v.set_index('Record_ID')
for vs, rc in MATCH.items():
    r = vi.loc[vs]; i = d.index[d.Record_ID == rc][0]
    d.at[i, 'Merged_From'] = vs
    d.at[i, 'Name_EN'] = r.Name_EN
    d.at[i, '_extra_text'] = f"{r.Description} {r.What_They_Sell}"
    filled = []
    if pd.isna(d.at[i, 'Latitude']):
        d.at[i, 'Latitude'], d.at[i, 'Longitude'] = r.Latitude, r.Longitude
        d.at[i, 'Geocode_Source'] = r.Geocode_Source; filled.append('קואורדינטות')
    if pd.isna(d.at[i, 'Opening_Hours']) and 'לא נמצא' not in str(r.Opening_Hours):
        d.at[i, 'Opening_Hours'] = r.Opening_Hours; filled.append('שעות')
    if pd.isna(d.at[i, 'Services']):
        d.at[i, 'Services'] = r.What_They_Sell; filled.append('Services')
    addr = str(d.at[i, 'Address'])
    if pd.isna(d.at[i, 'Address']) or re.fullmatch(r'\s*(מרכז )?תל אביב.*', addr):
        d.at[i, 'Address'] = r.Address; filled.append('כתובת')
    if filled:
        note = f"v0.2: הושלם מ-{vs} (קובץ הווינטג'): " + ', '.join(filled)
        d.at[i, 'Data_Note'] = note if pd.isna(d.at[i, 'Data_Note']) else f"{d.at[i, 'Data_Note']}; {note}"

new_rows = []
n = int(d.Record_ID.str[3:].astype(int).max())
for vs, r in vi.iterrows():
    if vs in MATCH:
        continue
    n += 1
    thin = 'במקור יש רק' in str(r.Description)
    notes = [x for x in [r.Note if pd.notna(r.Note) else None,
                         f"שעות לפי {r.Hours_Source}" if pd.notna(r.Hours_Source) else None,
                         f"מקורות נוספים: {r.Additional_Sources}" if pd.notna(r.Additional_Sources) else None] if x]
    new_rows.append({
        'Record_ID': f'RC-{n:04d}', 'Name': r.Name, 'Name_EN': r.Name_EN,
        'Record_Type': 'BUSINESS' if vs == 'VS-29' else r.Record_Type,
        'Description': r.Description, 'Services': r.What_They_Sell, 'Category': r.Category,
        'Subcategory': r.Subcategory, 'Subcategory_v01': r.Subcategory, 'Tags': '', 'Address': r.Address,
        'Latitude': r.Latitude, 'Longitude': r.Longitude, 'Geocode_Source': r.Geocode_Source,
        'Opening_Hours': None if 'לא נמצא' in str(r.Opening_Hours) else r.Opening_Hours,
        'Source_URL': r.Source_URL, 'Verification_Status': r.Verification_Status, 'Source_Name': r.Source_Name,
        'Source_Type': 'OSM (ODbL)' if r.Source_Name == 'OpenStreetMap' else ('לוח אירועים עירוני' if 'לוח אירועים' in r.Source_Name else 'כתבה / אתר תוכן'),
        'Source_Published': r.Source_Published, 'Entity_Group': f'vintage-{vs}',
        'Text_Quality': 'thin' if thin else 'rich_paraphrased', 'Merged_From': vs,
        'Labeling_Note': 'v0.2: שוק קבוע עם שעות פתיחה -> BUSINESS' if vs == 'VS-29' else None,
        'Data_Note': '; '.join(notes) if notes else None, '_extra_text': '',
    })
d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)

# ------------------------------------------------------------------ v0.2 additions (real sources, 2026-11-23)
import sys; sys.path.insert(0, OUT)
from additions_v0_2 import ADDITIONS, ENRICH
DEPT_EXTRA, PRICE_EXTRA, LM_EXTRA = {}, {}, {}
add_rows = []
for a in ADDITIONS:
    n += 1; rid = f'RC-{n:04d}'
    row = {k: v for k, v in a.items() if k not in ('key', 'P', 'S', 'A', 'T', 'LM', 'dept', 'price')}
    row.update(Record_ID=rid, Record_Type=a['T'], Primary_Category=a['P'], Subcategory=a['S'], Activity_Type=a['A'],
               Subcategory_v01='', Category='', Retrieved='2026-11-23', Source_Type='כתבה / אתר תוכן',
               Text_Quality='rich_paraphrased', Merged_From='', Name_EN=a.get('Name_EN', ''), _extra_text='',
               Geocode_Source='', Tags='')
    row.setdefault('Verification_Status', 'pending'); row.setdefault('Entity_Group', f"v02-{a['key']}")
    lab = 'v0.2: רשומה חדשה שנאספה לחיזוק מחלקה חלשה'
    row['Labeling_Note'] = f"{lab}; {a['Labeling_Note']}" if a.get('Labeling_Note') else lab
    if 'dept' in a: DEPT_EXTRA[rid] = a['dept']
    if 'price' in a: PRICE_EXTRA[rid] = a['price']
    if 'LM' in a: LM_EXTRA[rid] = a['LM']
    add_rows.append(row)
d = pd.concat([d, pd.DataFrame(add_rows)], ignore_index=True)
for rid, e in ENRICH.items():
    if rid == 'LIMONADA':
        rid = d.loc[d.Merged_From == 'VS-06', 'Record_ID'].iloc[0]
    i = d.index[d.Record_ID == rid][0]
    if 'Price' in e and pd.isna(d.at[i, 'Price']): d.at[i, 'Price'] = e['Price']
    if 'dept' in e: DEPT_EXTRA[rid] = e['dept']
    if 'LM' in e: LM_EXTRA[rid] = e['LM']
    d.at[i, 'Data_Note'] = e['note'] if pd.isna(d.at[i, 'Data_Note']) else f"{d.at[i, 'Data_Note']}; {e['note']}"

# ------------------------------------------------------------------ taxonomy fields
d['Text_Quality'] = d['Text_Quality'].replace({'rich (תיאור מנוסח מחדש מהמקור)': 'rich_paraphrased'})
prim, sub, act = [], [], []
for _, r in d.iterrows():
    if pd.notna(r.get('Primary_Category')) and r.Primary_Category:
        p, s, a = r.Primary_Category, r.Subcategory, r.Activity_Type
    elif r.Record_ID in OVERRIDE:
        p, s, a, note = OVERRIDE[r.Record_ID]
        d.loc[d.Record_ID == r.Record_ID, 'Labeling_Note'] = (note if pd.isna(r.Labeling_Note) else f"{r.Labeling_Note}; {note}")
    else:
        p, s, a = SUBMAP[r.Subcategory_v01]
    prim.append(p); sub.append(s); act.append(a)
d['Primary_Category'], d['Subcategory'], d['Activity_Type'] = prim, sub, act

# notes on records whose borderline issue the new taxonomy resolves
res = d.Subcategory_v01.isin(['ארון/ביתן החלפה ונתינה', 'מחסן השאלת ציוד'])
d.loc[res, 'Labeling_Note'] = d.loc[res, 'Labeling_Note'].fillna('') + '; v0.2: נפתר -> SHARING'
d['Labeling_Note'] = d['Labeling_Note'].str.lstrip('; ')

# tags
def tags_for(r):
    t = [x.strip() for x in str(r.Tags).split(';') if x.strip() and str(r.Tags) != 'nan']
    area = [x for x in t if x in AREA_TAGS]
    t = [x for x in t if x not in AREA_TAGS and x not in DROP_TAGS]
    for k, tag in STYLE_RULES:
        if k in str(r.Subcategory_v01) and tag not in t:
            t.append(tag)
    return ';'.join(t), ';'.join(area)
tg = d.apply(tags_for, axis=1)
d['Tags'] = [a for a, _ in tg]
d['Area'] = [b for _, b in tg]

# ------------------------------------------------------------------ attributes (text-evidence only)
def txt(r):
    return ' '.join(str(x) for x in [r.Name, r.Description, r.Services, r._extra_text, r.Price] if pd.notna(x))

# Department: only for clothing listings
is_cloth = ((d.Primary_Category.isin(['SECOND_HAND', 'SUSTAINABLE_SHOPPING']) & (d.Subcategory == SH_CLOTH))
            | (d.Subcategory.isin(['ארון החלפה ונתינה', 'השאלת ביגוד']) & d.Description.str.contains('בגד', na=False))
            | d.Record_ID.isin(['RC-0191']) | d.Name.isin(['Petitzen', 'קום איל פו - בית בנמל', 'אתא - "מאחד יוצא אחד"']))
DEPT_MANUAL = {  # record -> (value, status, evidence) ; each checked by hand against the text
    **DEPT_EXTRA,
    'RC-0228': ('ALL', 'SOURCE', 'VS-02: "לנשים, לגברים וקצת לילדים"'),
    'RC-0227': ('ALL', 'SOURCE', 'VS-04: "בגדי נשים וגברים"'),
    'RC-0176': ('ALL', 'SOURCE', '"בגדים לכל הגילאים והמגדרים"'),
    'RC-0177': ('ALL', 'SOURCE', '"בגדים לכל הגילאים והמגדרים"'),
    'RC-0178': ('ALL', 'SOURCE', '"בגדים לכל הגילאים והמגדרים"'),
    'RC-0255': ('ALL', 'SOURCE', '"דוכני וינטג\' ויד שנייה לנשים וגברים"'),
    'RC-0164': ('KIDS', 'SOURCE', '"מיועד רק עבור פריטים לילדים, גילאי 0-12"'),
    'RC-0254': ('KIDS', 'SOURCE', '"בגדי מעצבים יד שנייה לילדים מגיל לידה עד 14"'),
    'VS-11': ('UNISEX', 'SOURCE', '"חנות יוניסקס"'),
    'VS-12': ('MEN', 'SOURCE', '"מתמקדת ביד שנייה לגברים"'),
    'VS-19': ('WOMEN', 'SOURCE', '"בגדי מעצבים יד שנייה לנשים", "בעיקר לנשים"'),
    'VS-08': ('WOMEN', 'INFERRED', '"בסגנון נשי"; שמלות וחולצות (לא נאמר במפורש שאין לגברים)'),
}
dept, dst, dev = [], [], []
for _, r in d.iterrows():
    m = DEPT_MANUAL.get(r.Record_ID) or DEPT_MANUAL.get(r.Merged_From)
    if not is_cloth[_]:
        dept.append(''); dst.append(''); dev.append('')
    elif m:
        dept.append(m[0]); dst.append(m[1]); dev.append(m[2])
    else:
        dept.append('UNKNOWN'); dst.append('UNKNOWN'); dev.append('')
d['Department'], d['Department_Status'] = dept, dst

# Audience
KIDS_RX = re.compile(r'לילדים|ילדים וילדות|לילדות|לכל המשפחה|משפחות|מגיל \d|לגיל \d|בגילאי|כתות|ילדי השכונה|פריטים לילדים|גילאי \d')
# hits checked by hand: these mention children only as a clothing section, not as the audience
AUD_EXCLUDE = {'RC-0228', 'RC-0253'}
aud, ast, aev = [], [], []
for _, r in d.iterrows():
    t = txt(r)
    if 'ויצו' in t and 'לנשים ולילדים בסיכון' in t:
        t = t.replace('לנשים ולילדים בסיכון', '')
    mm = None if r.Record_ID in AUD_EXCLUDE else KIDS_RX.search(t)
    if mm:
        aud.append('FAMILIES_KIDS'); ast.append('SOURCE'); aev.append(mm.group(0))
    else:
        aud.append('UNKNOWN'); ast.append('UNKNOWN'); aev.append('')
d['Audience'], d['Audience_Status'] = aud, ast

# Price level
PRICE_RULES = [  # (regex, level, status)
    (r'כניסה חופשית|ללא עלות|ללא תשלום|בחינם', 'FREE', 'SOURCE'),
    (r'מחיר סמלי|במחירים סמליים|בתשלום סמלי|בזיל הזול|ארגז מציאות|במחירים נמוכים(?! יחסית)', 'BUDGET', 'SOURCE'),
    (r'יקרה יחסית', 'EXPENSIVE', 'SOURCE'),
    (r'המחירים נחשבים נגישים|המחירים נחשבים נוחים', 'AFFORDABLE', 'SOURCE'),
    (r'שליש מהמחיר המקורי', 'AFFORDABLE', 'INFERRED'),
]
PREMIUM_INFERRED = {'VS-10', 'VS-16', 'VS-20'}  # luxury/designer focus, no counter-evidence in text (VS-07 mixes cheaper items)
PRICE_EXCLUDE = {'RC-0230'}  # "בחינם" there refers to free alterations, not to item prices
pl, pst, pev = [], [], []
for _, r in d.iterrows():
    t = '' if r.Record_ID in PRICE_EXCLUDE else txt(r); hit = None
    for rx, lvl, stt in PRICE_RULES:
        mm = re.search(rx, t)
        if mm:
            hit = (lvl, stt, mm.group(0)); break
    if not hit and r.Record_ID in PRICE_EXTRA:
        hit = PRICE_EXTRA[r.Record_ID]
    if not hit and (r.Merged_From in PREMIUM_INFERRED or r.Record_ID in PREMIUM_INFERRED):
        hit = ('PREMIUM', 'INFERRED', 'מותגי יוקרה / מעצבים')
    if hit:
        pl.append(hit[0]); pst.append(hit[1]); pev.append(hit[2])
    else:
        pl.append('UNKNOWN'); pst.append('UNKNOWN'); pev.append('')
d['Price_Level'], d['Price_Level_Status'] = pl, pst
d['Attribute_Evidence'] = [
    '; '.join(x for x in [f'Department: {a}' if a else '', f'Audience: "{b}"' if b else '', f'Price: "{c}"' if c else ''] if x)
    for a, b, c in zip(dev, aev, pev)]

# Location
ONLINE = {'RC-0224', 'RC-0244'}
MOBILE = {'RC-0265'}
MULTI = {'RC-0233'}  # VS-01 note: "יש סניף נוסף בשינקין 33"
def loc_mode(r):
    t = txt(r) + ' ' + str(r.Data_Note)
    if r.Record_ID in LM_EXTRA: return LM_EXTRA[r.Record_ID]
    if r.Record_ID in ONLINE: return 'ONLINE'
    if r.Record_ID in MOBILE: return 'MOBILE'
    if 'רשת' in str(r.Tags).split(';') or r.Record_ID in MULTI or re.search(r'סניפים|סניף נוסף|חנויות בגדים של', t):
        return 'MULTI_BRANCH'
    return 'FIXED'
d['Location_Mode'] = d.apply(loc_mode, axis=1)
d['City'] = ['' if m == 'ONLINE' else 'תל אביב-יפו' for m in d.Location_Mode]
d['Short_Description'] = ''   # to be written in Priority 4 (kept separate from Description = ML input)

# ------------------------------------------------------------------ output
# ML input without the GIS layer label that opens templated descriptions (it names the class -> leakage)
GIS_PREFIX = re.compile(r'^\s*(ארון החלפות קהילתי|ארון החלפה קהילתי|מחסן השאלות קהילתי|מרכז תיקונים ומיחדוש|מקרר/מזווה קהילתי|מחסן מיחזור חומרים)\s*:\s*')
d['Description_ML'] = d.Description.astype(str).str.replace(GIS_PREFIX, '', regex=True)

COLS = ['Record_ID', 'Name', 'Name_EN', 'Record_Type', 'Description', 'Description_ML', 'Short_Description', 'Services',
        'Primary_Category', 'Subcategory', 'Activity_Type', 'Tags',
        'Audience', 'Audience_Status', 'Department', 'Department_Status', 'Price_Level', 'Price_Level_Status', 'Price',
        'Address', 'City', 'Area', 'Location_Mode', 'Latitude', 'Longitude', 'Geocode_Source',
        'Opening_Hours', 'Event_Date', 'Source_URL', 'Source_Name', 'Source_Type', 'Source_Published', 'Retrieved',
        'Verification_Status', 'Last_Verified', 'Predicted_Category',
        'Entity_Group', 'Text_Quality', 'Labeling_Note', 'Data_Note', 'Attribute_Evidence',
        'Category', 'Subcategory_v01', 'Merged_From']
out = d[COLS].copy()
assert out.Record_ID.is_unique
assert set(out.Primary_Category) <= set(PRIMARY)
assert set(out.Activity_Type) <= set(ACTIVITY)
out.to_csv(OUT + 'recircle_dataset_v0.2.csv', index=False, encoding='utf-8-sig')

# summaries
summ = (out.assign(rich=out.Text_Quality.str.startswith('rich'))
        .groupby('Primary_Category').agg(records=('Record_ID', 'size'), rich_text=('rich', 'sum'),
                                         entity_groups=('Entity_Group', 'nunique'),
                                         needs_review=('Verification_Status', lambda s: (s == 'needs_review').sum()))
        .reindex(list(PRIMARY)).reset_index())
summ.insert(1, 'label_he', summ.Primary_Category.map(PRIMARY))
mapping = (out.groupby(['Category', 'Subcategory_v01', 'Primary_Category', 'Subcategory', 'Activity_Type'], dropna=False)
           .size().reset_index(name='records'))
tax = pd.DataFrame([(k, PRIMARY[k], ' · '.join(sorted(out[out.Primary_Category == k].Subcategory.unique()))) for k in PRIMARY],
                   columns=['Primary_Category', 'label_he', 'subcategories'])
acts = pd.DataFrame(list(ACTIVITY.items()), columns=['Activity_Type', 'label_he'])
attrs = pd.DataFrame([(c, ' / '.join(f"{k}={v}" for k, v in out[c].replace('', '(לא רלוונטי)').value_counts().items()))
                      for c in ['Audience', 'Department', 'Price_Level', 'Location_Mode', 'Department_Status',
                                'Audience_Status', 'Price_Level_Status']], columns=['field', 'counts'])
with pd.ExcelWriter(OUT + 'recircle_dataset_v0.2.xlsx') as w:
    out.to_excel(w, sheet_name='records', index=False)
    summ.to_excel(w, sheet_name='summary_ml', index=False)
    tax.to_excel(w, sheet_name='taxonomy', index=False)
    acts.to_excel(w, sheet_name='activity_types', index=False)
    mapping.to_excel(w, sheet_name='mapping_v01_to_v02', index=False)
    attrs.to_excel(w, sheet_name='attribute_counts', index=False)
print(summ.to_string()); print(attrs.to_string())
print(len(out), 'records')
