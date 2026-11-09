# FlipType

תוכנה קטנה ל-Windows שמתקנת טקסט שהוקלד בשפת מקלדת לא נכונה.

`akuo kfo` ← סימון + **Ctrl+Shift+Q** ← `שלום לכם`
`יקךךם` ← סימון + **Ctrl+Shift+Q** ← `hello`

אחרי ההמרה, שפת המקלדת של Windows מתחלפת אוטומטית לשפה הנכונה.

## הפעלה
- **הקובץ המוכן:** לחיצה כפולה על `dist\FlipType.exe`. מופיע אייקון ליד השעון (לפעמים מוסתר מתחת לחץ ^).
- **מהקוד:** `.venv\Scripts\pythonw.exe FlipType.pyw`

בתפריט של האייקון (קליק ימני):
- **הפעלה עם Windows** – התוכנה תעלה אוטומטית בכל הדלקה של המחשב.
- **יציאה**

## איך זה עובד
1. מעתיקה את הטקסט המסומן (Ctrl+C).
2. אם יש בו אותיות עבריות, ממירה לאנגלית. אחרת, ממירה לעברית (לפי פריסת המקלדת העברית הסטנדרטית).
3. מדביקה את התוצאה במקום הטקסט המסומן (Ctrl+V).
4. מחליפה את שפת המקלדת ומחזירה ללוח את מה שהיה בו קודם.

## פיתוח
```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest tests   # בדיקות
.\build.ps1                            # בניית dist\FlipType.exe
```

## מבנה
- `fliptype/converter.py` – טבלת המיפוי וההמרה
- `fliptype/winapi.py` – קיצור מקשים גלובלי, שליחת מקשים, החלפת שפה
- `fliptype/clipboard.py` – גישה ללוח, שמירה ושחזור
- `fliptype/app.py` – אייקון המגש והזרימה הראשית
