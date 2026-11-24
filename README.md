# ReCircle ♻️

**פלטפורמה לגילוי צריכה מקיימת וכלכלה מעגלית בתל אביב-יפו**

פרויקט בקורס "הפיכת רעיון למוצר חי" · שימי פריש ואלון פרוינד

> **English summary:** ReCircle helps people in Tel Aviv-Yafo find second-hand shops, repair services, sharing points, food rescue, community gardens, eco-art and sustainable shopping near them. The repo holds a hand-labelled dataset of 303 real records (v0.2), a personal recommendation dashboard with offline map routing, and the spec for a 7-class text classifier (`Primary_Category`).

## 🔗 קישורים מהירים

| מה | קישור |
| --- | --- |
| **דשבורד ההמלצות (האתר)** | **https://alonfruend.github.io/Project-X/** |
| הדשבורד כ-Artifact ב-claude.ai | https://claude.ai/artifact/NLnKSnUFaCKoPxzC7LFcAr |
| מפת כל הרשומות (v0.1) | https://alonfruend.github.io/Project-X/maps/recircle_map.html |
| מפת שווקי וינטג׳ | https://alonfruend.github.io/Project-X/maps/vintage_map.html |
| גלריית כרטיסי מידע | https://alonfruend.github.io/Project-X/maps/cards/recircle_cards.html |

> קישורי `alonfruend.github.io` יעבדו אחרי ש-GitHub Pages יופעל בריפו (Settings ← Pages ← Deploy from a branch ← `main` ← `/ (root)`). עד אז אפשר להשתמש בקישור ה-Artifact, או להריץ מקומית (ראו למטה).

## מה זה ReCircle?

מידע על חנויות יד שנייה, בעלי מלאכה, מקררים קהילתיים, גינות קהילתיות ואירועי החלפות מפוזר בין אתרים, רשתות חברתיות ושכבות GIS של העירייה. ReCircle מרכזת אותו במקום אחד, מסווגת אותו ומציגה לכל משתמש את מה שמתאים לו ונמצא קרוב אליו.

קהלי היעד: צרכנים מודעי סביבה, משפחות, חובבי וינטג׳, סטודנטים וצעירים, וגם עסקים ויוזמות שרוצים להגיע לקהל הזה.

## מה יש כרגע

1. **מאגר נתונים v0.2:** 303 רשומות אמיתיות מתל אביב-יפו (147 עסקים, 103 יוזמות, 53 אירועים), 252 מהן עם מיקום. המקורות: שכבות ה-GIS של עיריית תל אביב, לוח האירועים העירוני ומקורות רשת נוספים. לכל רשומה יש קישור למקור וסטטוס אימות.
2. **דשבורד המלצות אישי:** שאלון קצר (שלב בחיים, גיל, תקציב, תחומי עניין, אזור), ציון התאמה 0 עד 100 עם הסבר, המלצות בקבוצות ומשוב "מתאים לי / פחות מתאים". במצב "חיפוש על המפה" נועצים סיכה ומקבלים זמני הגעה ומסלול ברחובות (הליכה, אופניים, תחבורה ציבורית, רכב), הכול בדפדפן בלי שירות חיצוני. הדירוג מבוסס כללים ואינו מודל ML.
3. **מפות וכרטיסי מידע (v0.1):** מפות עצמאיות עם רקע רחובות לא-מקוון מ-OpenStreetMap.
4. **אפיון משימת ML:** סיווג טקסט לקטגוריה ראשית אחת מתוך 7.

## משימת למידת המכונה

| | |
| --- | --- |
| סוג המשימה | סיווג טקסט רב-מחלקתי |
| עמודת היעד | `Primary_Category` (תיוג ידני של רשומות אמיתיות, לא סימולציה) |
| קלט | `Name`, `Description_ML`, `Services` ותוכן פרסומי |
| פלט | `Predicted_Category` (הצעה בלבד, נבדקת לפני פרסום) |
| הערכה | Accuracy, Macro-F1, מטריצת בלבול, ביצועים לכל קטגוריה. חלוקה לפי `Entity_Group` כדי שאותו גוף לא יופיע גם באימון וגם בבדיקה |

התפלגות הקטגוריות ב-v0.2:

| קטגוריה | משמעות | רשומות |
| --- | --- | --- |
| `REPAIR` | תיקון ובעלי מלאכה | 97 |
| `NATURE_COMMUNITY` | גינות קהילתיות ופעילות סביבתית | 80 |
| `SECOND_HAND` | יד שנייה ווינטג׳ | 52 |
| `SHARING` | החלפה, השאלה ושיתוף | 32 |
| `ECO_ART` | אמנות ותרבות סביבתית | 16 |
| `FOOD_RESCUE` | הצלת מזון | 15 |
| `SUSTAINABLE_SHOPPING` | קנייה מקיימת | 11 |

מצב: עדיין לא אומן מודל. רוב התוויות ממתינות לאימות של הצוות. הקטגוריות הקטנות (`FOOD_RESCUE`, `ECO_ART`, `SUSTAINABLE_SHOPPING`) צריכות עוד רשומות. פירוט מלא ב-[`data/v0.2/README_v0.2.md`](data/v0.2/README_v0.2.md).

## מבנה הריפו

```
├── index.html                  דף הכניסה של GitHub Pages (מפנה לדשבורד)
├── data/
│   ├── recircle_dataset_v0.1.csv / .xlsx   מאגר v0.1 (268 רשומות)
│   ├── README_sources_v0.1.md               המקורות של v0.1 ואיך נאספו
│   ├── v0.2/                    מאגר v0.2, סקריפט הבנייה ותיעוד הטקסונומיה
│   ├── vintage/                 שווקי וינטג׳ ויד שנייה בתל אביב
│   ├── osm_offline/             חילוץ OSM לא-מקוון (רחובות ומים) + embed_streets.py
│   └── recommender/             דשבורד ההמלצות, records.json, osm_bg.json, routing.json וסקריפטי הבנייה
├── maps/
│   ├── recircle_map.html        מפת כל הרשומות (v0.1)
│   ├── vintage_map.html         מפת שווקי וינטג׳
│   └── cards/                   גלריית כרטיסי מידע ולוגו
└── docs/
    ├── spec_v0.1.md             מסמך האפיון הראשוני (6 קטגוריות, לפני הטקסונומיה של v0.2)
    └── ReCircle_presentation.pptx
```

## הרצה מקומית

הדשבורד טוען קבצי JSON, ולכן צריך שרת סטטי:

```bash
python3 -m http.server 8000
# ואז לפתוח http://localhost:8000/
```

המפות והגלריה ב-`maps/` עצמאיות ונפתחות גם בלחיצה כפולה.

בנייה מחדש של הנתונים (Python 3, pandas, openpyxl):

```bash
python3 data/v0.2/build_v0.2.py                      # v0.1 + vintage + תוספות → v0.2
cd data/recommender
python3 -I build_osm_bg.py ../osm_offline/tlv_streets_osm.json ../osm_offline/tlv_water_osm.json osm_bg.json
python3 -I build_routing.py ../osm_offline/tlv_streets_osm.json routing.json
```

## רישוי ומקורות

נתוני המפה © OpenStreetMap contributors, ברישיון ODbL. נתוני העירייה מתוך שכבות ה-GIS הפתוחות של עיריית תל אביב-יפו. פרטים אישיים (שמות וטלפונים של אנשים פרטיים) הוסרו מהמאגר.
