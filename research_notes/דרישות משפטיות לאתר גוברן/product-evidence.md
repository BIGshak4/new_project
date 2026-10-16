# JobRun — עובדות מוצר וקוד לצורך בדיקה משפטית

> מסמך רקע מחקרי. לתכנון העבודה ראו את [תוכנית הביצוע המעודכנת](https://github.com/BIGshak4/new_project/blob/master/docs/legal-protection-execution-plan-2026-10-16.md); ממצאים, פרשנויות ופערי אימות כאן אינם אישור ציות או הכרעה משפטית.

תאריך: 2026-10-16. מקור: סקירה לקריאה בלבד של `C:/Projects/Job_Run/new_project` בגרסה `e0e460c`. אין במסמך בדיקת חדירה, בדיקה משפטית או אישור תאימות. לא נקראו מפתחות או קובצי סודות, לא נבדקו המסד החי/הגדרות הספקים ולא הורצו פעולות באתר. עובדה שנמצאה בקוד אינה הוכחה שהמסלול מופעל בפריסה החיה.

מידע עסקי שנמסר ישירות בידי הראל למחבר הדוח: **השקה בתשלום, ישראל בלבד בשלב הראשון, הישות המשפטית וסוג העסק עדיין לא הוחלטו ולא נפתח עסק.** זהו מידע אנושי עדכני; אין להסיק ממנגנון הפיילוט החינמי בקוד שההשקה תהיה בחינם.

## 1. איזה שירות ונתונים קיימים בפועל בקוד?

### Takeaway

זהו אתר לימוד ותרגול אישי לראיונות, עם חשבון, יעדי קריירה, תשובות טכניות, תמונות, ציוני AI והיסטוריית התקדמות. קיימים נתונים אישיים גם מעבר לדוא״ל וסיסמה; אין להסיק שמדובר באתר תדמית שאינו אוסף מידע.

### Cited Findings

- **נמצא בקוד:** קהל היעד המוצהר הוא סטודנטים להנדסת חשמל/אלקטרוניקה ומועמדים בתחילת הדרך בישראל; קיים אתר משימות פרטי נפרד למייסדים. המקור מזהיר שחלק ממלאי התוכן המתואר בו הוא היסטורי. [מקור: PRODUCT.md](https://github.com/BIGshak4/new_project/blob/e0e460c/PRODUCT.md#L7).
- **נמצא בקוד:** הרשמה והתחברות בדוא״ל וסיסמה ישירות ל־Supabase Auth; דוא״ל לא מאומת מקבל מסר אישור; אין להסיק מכך שאימות מופעל תמיד בפריסה החיה. [מקור: auth.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/auth.tsx#L92).
- **נמצא בקוד:** גישה לפיילוט נבדקת מול `jr_members`; הרשאת ניהול משימות היא `can_manage_tasks`. [מקור: users.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/repo/users.py#L34), [מקור: auth.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/auth.tsx#L61).
- **נמצא בקוד ובטופס:** סוג התפקיד, תאריך ראיון אופציונלי, דקות לימוד ליום ורמת ניסיון שמוערכת עצמית. הטופס מסביר שישמשו לתוכנית, סדר השאלות והראיון המדומה. [מקור: goal-setup.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/goal-setup.tsx#L81), [מקור: me.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/api/v1/me.py#L38).
- **נמצא בקוד:** שמירת תשובות חופשיות וקוד, גרסאות הגשה, רמזים שנצפו, חשיפה לפתרון, תוצאות בדיקה, הערכה, רמת תשובה ודגלי משוב. [מקור: attempts.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/repo/attempts.py#L23), [מקור: api.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/schemas/api.py#L47).
- **נמצא בקוד:** פרופיל מיומנויות מתמשך, היסטוריית תשובות, ציונים/XP ומועדי הערכה; היסטוריה עשויה להקיף את כל התשובות ולא רק סשן נוכחי. [מקור: profiles.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/repo/profiles.py#L35), [מקור: attempts.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/repo/attempts.py#L200), [מקור: attempts.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/repo/attempts.py#L272).
- **נמצא בקוד:** מדדי הערכה ושימוש נכתבים עם מזהה משתמש ומזהה ניסיון. מקור ההגעה/מסך והתקן ברמה גסה נגזרים גם מ־User-Agent במסלול פתיחת ניסיון. אלה נתוני שימוש אישיים, גם ללא Google Analytics. [מקור: events.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/repo/events.py#L37), [מקור: practice.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/api/v1/practice.py#L58), [מקור: practice.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/api/v1/practice.py#L139).
- **נמצא בקוד:** משתמש יכול לצרף עד ארבע תמונות לתשובה, בתבניות PNG/JPEG/WebP, עד 10MB לכל קובץ לפני שינוי גודל. התמונות מפוענחות ומקודדות מחדש בדפדפן להסרת מטא־נתוני מצלמה, ומועלות ל־Supabase Storage. [מקור: visual-answer.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/visual-answer.tsx#L17), [מקור: visual-answer.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/visual-answer.tsx#L157).
- **נמצא בקוד:** תמונות תשובה נגישות באמצעות קישורים חתומים ל־900 שניות; השרת מביא תמונות לאימות ולהערכה. אין בכך הוכחה שאין אפשרות שמקבל קישור יעתיק/יוריד תמונה. [מקור: visual-answer.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/visual-answer.tsx#L71), [מקור: storage_images.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/services/storage_images.py#L35).
- **נמצא בקוד:** מודל פרופיל כולל גם `display_name`, שדות רקע, יעדי חברות ותפקידים, העדפות התראה, `plan_tier` ו־`b2b_data_consent` עם ברירת מחדל false. עצם קיום עמודות אינו הוכחה שהן נאספות/מופעלות בממשק. [מקור: users.sql](https://github.com/BIGshak4/new_project/blob/e0e460c/supabase/migrations/20260917130154_users.sql#L11).

### Inferences

- מפת המידע המשפטית צריכה לכסות חשבון, פרופיל/תוכנית, תשובות/קוד/שרטוטים/תמונות, תמלול שהופך לטקסט, ציונים והיסטוריה, מדדי שימוש ולוגים. יש לאפיין שימושים בנפרד, למשל שירות הליבה, תמיכה, אבטחה ושיפור המודל.
- תוכן חופשי ותמונות מאפשרים למשתמש למסור בטעות פרטי צד שלישי, חומר של מעסיק, מידע סודי או מידע רגיש. רצויה הנחיה לא להעלות כאלה, לצד כללי טיפול ותמיכה.
- יש לבדוק משפטית את סיווג ציוני הכשירות והערכת המיומנויות; אין לקבוע שאין מידע בעל רגישות מיוחדת רק מפני שאין שדות רפואיים.

### Gaps

- לא נבדקו היקף משתמשים, כמויות רשומות, פרטי מייסדים, ספק תמיכה/דיוור, תנאי סליקה עתידיים, נתונים שנאספים מחוץ לאפליקציה או הרשאות תפעוליות בדשבורדים.
- לא נמצאה במסלול הציבורי שנבדק בחירת גיל או הצהרת 18+. קהל סטודנטים אינו מבטיח שכל המשתמשים בגירים. אין לבחור מדיניות קטינים בלי החלטת מפעילים ובדיקה משפטית.
- לא הוכח שהאתר משמש מעסיקים לקבלת החלטות גיוס. קוד הליבה שנבדק מתאר אימון למועמד; עמודות B2B עתידיות אינן הוכחה לשיתוף עם מעסיקים. שינוי למיון/דירוג מועמדים מחייב בחינה נפרדת.

## 2. ספקים, AI, הכתבה, אחסון ולוגים

### Takeaway

נמצאו חיבורים ל־Supabase, Netlify, Render ולספק המודל Anthropic, ובנפרד לשירות ההכתבה שהדפדפן בוחר. מיקום אחסון אמיתי, ספקי משנה, שימוש לאימון ומשך שמירה אינם ניתנים לקביעה מהקוד; יש להשלים אותם מחוזים והגדרות החשבונות.

### Cited Findings

- **נמצא בקוד:** Next/Supabase JS בצד לקוח, Supabase Auth/Database/Storage, התאמת Netlify ליישום ו־Render ל־API. [מקור: supabase.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/supabase.ts#L1), [מקור: netlify.toml](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/netlify.toml#L1), [מקור: render.yaml](https://github.com/BIGshak4/new_project/blob/e0e460c/render.yaml#L5).
- **נמצא בקובץ פריסה:** `region: frankfurt` ב־Render blueprint. זו כוונת תצורה בלבד, לא אימות המיקום בפריסה החיה ולא קביעה שכל המידע נשאר בגרמניה. [מקור: render.yaml](https://github.com/BIGshak4/new_project/blob/e0e460c/render.yaml#L12).
- **נמצא בקוד:** Anthropic SDK שולח הודעות למודל. במסלול evaluator מועברים תשובת המשתמש, הקשר השאלה, מחוון, תוצאות בדיקה וראיות חזותיות; תמונות נשלחות כ־base64. אין להבטיח שהמודל מקבל רק מזהה אנונימי או שאלה ציבורית. [מקור: evaluator.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/evaluator.py#L92), [מקור: evaluator.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/evaluator.py#L142), [מקור: providers.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/providers.py#L302).
- **נמצא בקוד:** קריאות נפרדות ליצירת משוב, שאלות המשך ודוח מסכם; נתוני התשובה/סיכומה ומצב הלמידה משתתפים בבניית בקשות. [מקור: feedback.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/feedback.py#L90), [מקור: generator.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/generator.py#L88), [מקור: reporter.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/reporter.py#L192).
- **נמצא בקוד:** ספק המודל נבחר מתצורה; יש גם ספק scripted/פיתוח, ולכן קיום קוד Anthropic אינו אישור שכל בקשה בפריסה החיה נשלחת אליו. המודלים המדויקים מוגדרים בתצורה ולא אומתו בזמן הסקירה. [מקור: config.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/config.py#L51), [מקור: runtime.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/runtime.py#L44).
- **נמצא בקוד:** מסלול Anthropic מפעיל prompt caching של בלוקי מערכת ו־server-side fallback כשמאופשר. אין להסיק מהשם fallback שהוא יישאר באותה מדינה או אפילו שמספר ספקי המשנה ידוע. [מקור: providers.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/providers.py#L257), [מקור: providers.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/engine/providers.py#L264).
- **נמצא בקוד:** הכתבה משתמשת ב־Web Speech `SpeechRecognition`/`webkitSpeechRecognition`, מופעלת בלחיצה, ומוסיפה טקסט להסבר; הטקסט אינו נשלח אוטומטית. לפני הפעלה יש גילוי שהדפדפן עשוי לשלוח אודיו לספק ההכתבה שלו. [מקור: dictation-controls.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/dictation-controls.tsx#L8), [מקור: speech-dictation.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/speech-dictation.ts#L127).
- **נמצא בקוד:** הפסקה/ביטול במעבר לרקע או יציאה מהעמוד. לא נמצא מסלול הקלטת אודיו או העלאת קובץ אודיו ב־`apps/web/src` וב־`backend/app` שנבדקו. אין להסיק שאין עיבוד אודיו אצל ספק הדפדפן. [מקור: dictation-controls.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/dictation-controls.tsx#L57).
- **נמצא בקוד:** ראיון מדומה הוא כתוב, עם אפשרות קוד/תמונות; במסך הכניסה כתוב שאין שיחה קולית ואין צורך במיקרופון. הכתבה היא כלי קלט נוסף, לא הקלטת ראיון בידי JobRun. [מקור: interview-session.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/interview-session.tsx#L111).
- **נמצא בקוד:** לוגי API כוללים request ID, שיטה, נתיב, מזהה משתמש, סטטוס ומשך. קיים מאמץ מפורש לא לרשום גוף בקשה או token בלוג הרגיל; מסלול חריגה עשוי לרשום exception, וחלק מלוגי תמונות כוללים נתיב. אין בכך בדיקה של לוגי תשתית או דליפת מידע בשגיאות צד שלישי. [מקור: main.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/main.py#L184), [מקור: storage_images.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/services/storage_images.py#L46).
- **נמצא בקוד:** בחירת שפה/ערכת נושא ודילוג על הגדרת יעד ב־localStorage; טיוטות תשובה וקוד ומטמון שאלות ב־sessionStorage, מופרדים במפתחות משתמש/ניסיון. [מקור: page.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/app/page.tsx#L81), [מקור: theme.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/theme.ts#L8), [מקור: practice-ui.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/practice-ui.ts#L154), [מקור: practice-session.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/practice-session.tsx#L109), [מקור: question-cache.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/question-cache.ts#L40).
- **נמצא בקוד:** Supabase client נוצר ללא override של הגדרות auth. בגרסת הספרייה המותקנת ברירת המחדל היא `persistSession: true`, ובדפדפן נבחר localStorage כשזמין. [מקור: supabase.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/supabase.ts#L2), [מקור ספרייה מותקנת: constants.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/node_modules/%40supabase/supabase-js/src/lib/constants.ts#L42), [מקור: GoTrueClient.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/node_modules/%40supabase/auth-js/src/GoTrueClient.ts#L520).
- **לא נמצא בחיפוש במקור היישום וחבילתו:** שילוב מפורש של Google Analytics/gtag, Sentry, PostHog, Mixpanel, Hotjar, Meta pixel או כתיבת cookie מותאמת. זה אינו אישור שאין Cookies, analytics או IP logs מצד Netlify/Supabase/Render, הזרקת סקריפטים בדשבורד, ספק עתידי או תוסף דפדפן. היקף החיפוש: `apps/web/src` ו־`apps/web/package.json`; חיפושים במילים `cookie`, `document.cookie`, `gtag`, `sentry`, `posthog`, `mixpanel`, `hotjar`, `next/script`. [מקור היקף: package.json](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/package.json#L1).

### Inferences

- נדרשת רשימת ספקים אמיתית ותפקידי עיבוד, כולל מדינות אחסון/גישה, ספקי משנה, גיבויים, שמירה, מחיקה, אבטחה, אימון מודלים והסכמי עיבוד; גם אם המכירה בישראל בלבד, ספק חוץ עשוי לעבד מידע מחוץ לישראל.
- אין בסיס להוסיף אוטומטית פופ־אפ Cookie גרפי רק משום שזה אתר. קודם למפות storage וטרקרים בפועל ולבדוק איזה דין חל. גם אין בסיס להצהיר ״אין cookies״ או ״כל האודיו נשאר אצלנו במכשיר״.
- אין לתאר שמירת מזהה משתמש שהוחלף בהאש כהבטחת אנונימיות מלאה ללא בדיקה של יכולת זיהוי מחדש, קישוריות וטקסט שנשאר.

### Gaps

- לא אומתו מיקום Supabase, אזורי CDN/Functions/לוגים/גיבויים, הסכמי DPA, מגבלות אימון/שמירה של AI, SMTP, ספקי fallback או תצורת החשבון בפועל. אין לקבוע אותם על סמך default בקוד או השם Frankfurt.
- לא נבדק האם auth session נמחק כנדרש בכל תרחיש, או האם כל הטיוטות מתנקות בעת יציאה; יש לבחון זאת כחלק ממדיניות מכשיר משותף/שמירה.
- המונח `retention` בקוד תוכנית הלמידה מציין חזרה ושימור ידע, **לא** מדיניות שמירת מידע אישי. לא נמצאה עבודת מחיקה תקופתית כללית של מידע אישי בסקירה של services/repos.

## 3. ממשקי זכויות, צרכנות, תוכן, נגישות ואבטחה — מה קיים ומה חסר?

### Takeaway

יש כמה אמצעי הגנה ותכונות נגישות מועילות, אך חסרה שכבת התפעול המשפטית הציבורית; אין בסיס להגיד שהאתר ״עומד בכל הדרישות״. לקראת השקה בתשלום הפערים הבולטים הם זהות/קשר של העסק, תנאים/פרטיות והליך בקשות מידע, תהליך רכישה וביטול, בדיקת נגישות ותיעוד זכויות התוכן.

### Cited Findings

- **לא נמצא בחיפוש בממשק וב־API:** דפי/קישורי מדיניות פרטיות, תנאי שימוש, הצהרת נגישות, כתובת קשר ציבורית משפטית, מחיקת חשבון או ייצוא מידע. יש footer שמזהה את הראל ושקד כסטודנטים וכותב שזה פיילוט וששאלות/משוב בבדיקה; הוא אינו מציג שם ישות, כתובת, מספר עסק, טלפון או דוא״ל לפניות. היקף חיפוש: `apps/web/src`, `backend/app/api`, במונחים עבריים ואנגליים `privacy`, `terms`, `accessibility`, `mailto:`, `מחיקת חשבון`, `תנאי שימוש`, `הצהרת נגישות`, `מדיניות פרטיות`. [מקור footer: sign-off.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/sign-off.tsx#L6), [מקור מסלולי משתמש: me.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/api/v1/me.py#L25).
- **לא נמצא בקוד טופס ההרשמה שנבדק:** checkbox/תיעוד הסכמה לתנאי שימוש, הודעת פרטיות בנקודת האיסוף, הפרדת הסכמה לדיוור או שער גיל. [מקור: auth.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/auth.tsx#L174).
- **נמצא בסכמה בלבד:** `deleted_at` וטריגר שמחליף את מזהה המשתמש ב־evaluation_metrics בהאש בעת מחיקה רכה/קשיחה; יש FKs מסוימים ב־cascade. זה אינו הליך מחיקת חשבון שלם, אינו מכסה אוטומטית תמונות ב־Storage, גיבויים, לוגים וספק AI, ואין להבטיח אנונימיות רק משם הפונקציה. [מקור: users.sql](https://github.com/BIGshak4/new_project/blob/e0e460c/supabase/migrations/20260917130154_users.sql#L33), [מקור: evaluation.sql](https://github.com/BIGshak4/new_project/blob/e0e460c/supabase/migrations/20260917130659_evaluation.sql#L275).
- **נמצא בסכמה בלבד:** הרשאות קריאה/מחיקה על `user_document`. אלה אינן הוכחה לממשק משתמש או תהליך למחיקת כל המידע. [מקור: rls.sql](https://github.com/BIGshak4/new_project/blob/e0e460c/supabase/migrations/20260917130820_rls.sql#L177).
- **לא נמצא בחיפוש האפליקציה/מסלולי API/תלויות:** Stripe/PayPal/Paddle/checkout/billing ותהליך רכישה, ביטול מנוי, החזרים או קבלות. `plan_tier=free` בסכמה הוא נתון פיילוט/תכנון, לא ראיה שאין צורך לבנות את חובות המכירה העתידית בתשלום. [מקור: users.sql](https://github.com/BIGshak4/new_project/blob/e0e460c/supabase/migrations/20260917130154_users.sql#L26), [מקור: package.json](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/package.json#L1), [מקור: requirements.txt](https://github.com/BIGshak4/new_project/blob/e0e460c/requirements.txt#L1).
- **נמצא בתיעוד הקטלוג:** 67 רשומות מקור בסקירה האחרונה: 30 ראשונות ו־37 שנאספו ידנית; סקירת ניסוחים אינה אישור הנדסי/כיול/אימות דיווחי חברות. ארכיון המקור כולל צילומים וקובצי קוד. [מקור: content-wording-review.md](https://github.com/BIGshak4/new_project/blob/e0e460c/docs/content-wording-review-2026-10-15.md#L7), [מקור: preparation-bank-integration.md](https://github.com/BIGshak4/new_project/blob/e0e460c/docs/preparation-bank-integration-2026-09-30.md#L9).
- **נמצא בקוד:** מקור `sources/`/צילומי מקור מסוימים מסוננים מחשיפה באתר; זה מפחית חשיפה אך אינו מוכיח הרשאה לפרסם טקסט, איורים משוחזרים או קוד שמבוססים עליהם. [מקור: question_resources.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/services/question_resources.py#L43), [מקור: question-media.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/question-media.ts#L4).
- **נמצא בקוד:** שיוך שאלה לחברות מוצג כדיווח מועמדים/מקורות, לא פרסום רשמי מטעמן; בדף שער יש הבהרה שהדיווחים אינם מעידים על שיתוף פעולה רשמי. החברות מוצגות בשמות טקסטואליים במסלולים אלה. [מקור: question-discovery.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/question-discovery.ts#L86), [מקור: landing-company-reports.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/landing-company-reports.tsx#L7).
- **נמצא בקוד:** בשאלה המסומנת לבדיקה מקצועית מוצגת אזהרה שהמשוב ראשוני, שהתרגול נשמר ושהוא אינו משנה רמת שליטה או מעניק נקודות עד לאישור תוכן וקושי. בפתרון מוצע כזה מופיע תיוג ביקורת מקצועית. זו הבחנה קיימת שכדאי לשמר; היא אינה אישור שכל תוצאה אחרת מדויקת. [מקור: practice-session.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/practice-session.tsx#L540), [מקור: practice-session.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/practice-session.tsx#L950).
- **נמצא בקוד:** ביקורות ציבוריות מופרדות מטיוטות/ראיות הסכמה פרטיות; נדרשים `approved`, אישור פרסום, גרסה תואמת ותאריך תקין; רשימת הביקורות הציבורית ריקה כרגע. לא אומתו מסמכי הסכמה בפועל, מפני שאין רשומה לפרסום. [מקור: public-testimonials.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/lib/public-testimonials.ts#L35), [מקור: landing-testimonials.ts](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/content/landing-testimonials.ts#L4).
- **נמצא בקוד:** כפתורים מקוריים, תוויות/aria, מוקד נראה, הודעות status, עזרה ליציאה מעורך הקוד (`Esc` ואז `Tab`), חלופת חיבור ברשימה במקום גרירה במעגל, וטבלת אמת סמנטית; העיצוב כולל reduced motion. אלה אינן בדיקת WCAG/ת״י 5568. [מקור: answer-editor.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/answer-editor.tsx#L134), [מקור: circuit-editor.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/circuit-editor.tsx#L740), [מקור: circuit-truth-table.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/circuit-truth-table.tsx#L119), [מקור: ion.css](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/app/ion.css#L164), [מקור: ion.css](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/app/ion.css#L875).
- **נמצא בקוד:** תמונת תשובה משתמשת בשם הקובץ כ־alt; זה אינו בהכרח תיאור משמעותי של המעגל/תוכן בתמונה. חלק מהשרטוטים הדקורטיביים מסומנים `aria-hidden`; צריך להבחין בין דקורציה לבין מידע טכני שחייב חלופה. [מקור: visual-answer.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/visual-answer.tsx#L90), [מקור: sketches.tsx](https://github.com/BIGshak4/new_project/blob/e0e460c/apps/web/src/components/sketches.tsx#L5).
- **נמצא בקוד:** אימות JWT כולל חתימה, issuer, audience ותפוגה; השרת מייחס בקשה למשתמש מאומת; migrations כוללות RLS ומדיניות בעלות. אין בכך הוכחה שהמסד החי מוגדר כך או שבוצעה בדיקת הרשאות מלאה לכל ישות. [מקור: auth.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/auth.py#L66), [מקור: deps.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/api/deps.py#L38), [מקור: rls.sql](https://github.com/BIGshak4/new_project/blob/e0e460c/supabase/migrations/20260917130820_rls.sql#L34), [מקור: practice_submissions.sql](https://github.com/BIGshak4/new_project/blob/e0e460c/supabase/migrations/20260918170000_practice_submissions.sql#L91).
- **נמצא בקוד:** הגבלת גוף בקשה, rate limit לכל caller (600 לדקה בקבוע הנוכחי), מגבלת ניסיונות יומית מתצורה, והפרדת service-role key לצד שרת. קיום אלה אינו אישור עמידה בתקנות אבטחת מידע או SOC/ISO. [מקור: main.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/main.py#L94), [מקור: config.py](https://github.com/BIGshak4/new_project/blob/e0e460c/backend/app/config.py#L38).

### Inferences

פערים שכדאי להכניס לדוח המשפטי הראשי, לפי קדימות מוצרית, בלי לקבוע לבדם מהי חובה בדין:

1. **לפני מכירה:** לקבוע מפעיל/ישות, מידע עסקי וערוצי קשר; לתכנן מחיר, משך/חידוש, ביטול, החזר, קבלה ותמיכה. הקוד הנוכחי אינו תהליך מסחרי מוכן.
2. **כעת, גם בפיילוט:** מפת מידע, הודעת פרטיות בשעת האיסוף, מסמך פרטיות, מטרות/חוקיות, הגבלת שימוש, מדיניות שמירה והליך מאומת לפניות עיון/תיקון/מחיקה לפי הדין החל. אין להציג כפתור מחיקה לפני שברור מה הוא מוחק ומה חייבים לשמור.
3. **לפני השקה רחבה:** הסכמי עיבוד ומפת העברות חוץ, כללי גישה למייסדים/עובדים, תיעוד אבטחה, גיבוי/התאוששות/אירועים ובדיקות הרשאות חוצות משתמשים. אי אפשר לאשר תאימות מאוסף קבצי migrations.
4. **תוכן:** מרשם זכויות לכל שאלה/תמונה/איור/קוד/גופן/נכס, רישיון או יצירה מקורית מתועדת ובדיקת סודיות/תנאי מקורות. ניסוח מחדש או מחיקת screenshot אינם היתר שימוש אוטומטי; ייחוס לחברה אינו הרשאת פרסום ממנה.
5. **נגישות:** בדיקת תחולה/פטור על בסיס הישות/מחזור ותנאי השירות, ובכל מקרה בדיקה אמיתית של מסלולי הרשמה, תרגול, קוד, מעגל/טבלה, משוב ומובייל, עברית ואנגלית. אין להסיק ש־ARIA או תוסף נגישות מספיקים. להוסיף הצהרה וערוץ פנייה לפי הממצאים והדין החל, בלי הצהרה כוזבת על תאימות מלאה.
6. **AI/הבטחות מוצר:** לשקף שזה כלי למידה עם הערכה אוטומטית שעלולה לטעות; לא להבטיח מעבר ראיון/קבלה לעבודה, שותפות חברות, בדיקה מקצועית או דיוק שלא הוכחו. לציין מה נשלח לספק ולא לטעון שכל התוכן נשאר בישראל.
7. **שינויים עתידיים:** שיתוף ציונים עם מעסיקים/מכירת נתונים, שיווק בדוא״ל/מסרונים, פרסום/טרקרים, ילדים, מכירה בחו״ל או נתונים ביומטריים דורשים בדיקת תחולה ומנגנונים נפרדת; אין להציגם כפיצ׳רים שכבר פועלים רק כי יש עמודות סכמה.

### Gaps

- אין בסקירה מספרי מחזור, סטטוס עוסק/חברה, פטור נגישות, בעל שליטה מוגדר, רישום/הודעת מאגר או צורך ב־DPO; אלה שאלות משפטיות תלויות עובדות ולא משהו שניתן להכריע מהקוד.
- לא נבדקו אסמכתאות זכויות/רישיונות לכל מקור, בעלות על תכנים שיצר AI, רישיונות dependency assets, אישורי אנשים לביקורות, או תנאי אתר שממנו נלקחו שאלות.
- לא נבדקו עמידה בקורא מסך, ניגודיות בכל מצבים, zoom/reflow, RTL, פקדי מובייל, מוקד/מלכודות מקלדת בפועל, תשלום עתידי, או PDF/קבצים להורדה. אין הצהרת נגישות מלאה בסקירה זו.
- ה־API הנוכחי מאפשר צפייה בהיסטוריה אך אין מכאן זכות ייצוא במתכונת מסוימת: מה שחובה לספק ומה שמומלץ כמוצר חייבים להיקבע בדוח הדין. באופן דומה, לא כל נתון חייב להימחק מיד בכל בקשה.
