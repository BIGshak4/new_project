# Circuit workspace handoff — 2026-10-17

The circuit editor now offers a roomier expanded window and a viewport-filling mode, with the current question available while drawing. This is an ordinary extension of the existing Adaptive Ion interface. It introduces no new visual world or raster assets.

## Implemented behavior

- `apps/web/src/components/circuit-editor.tsx` keeps one native `<dialog>` and one ReactFlow tree mounted. Inline mode exposes a nonmodal region; expanded and full-screen modes promote that same element with `showModal()`. Changing modes preserves the drawing, selection, viewport, simulation state and undo/redo history.
- **הרחבת הלוח / Expand drawing** opens the expanded workspace. **מסך מלא / Full screen** fills the browser viewport; **חלון מוגדל / Expanded window** returns to the expanded layout. This is a CSS viewport layout, not an operating-system or browser Fullscreen API request.
- **חזרה לתשובה / Back to answer** and Escape return to the inline editor. Modal mode locks background body scrolling, then restores the previous overflow value and returns focus to the expand control. Native dialog modality provides keyboard containment.
- An optional `CircuitQuestionReference` supplies a title and read-only reference content. **הסתרת השאלה / Hide question**, **הצגת השאלה / Show question**, and the reference close button control its visibility without resetting the circuit.
- `visual-answer.tsx` passes the reference through to the editor. `practice-session.tsx` provides the actual prompt, prompt figures or resource status, and choices. `interview-session.tsx` provides the interview question text. `site-preview/simulation.tsx` supplies equivalent sample context for preview verification. Reference content excludes solutions and evaluation feedback.
- `circuit-workspace.module.css` scopes the workspace layout. Desktop expanded mode has a 16px inset, a maximum width of 1560px and a question column from 320px to 380px. At widths of 800px and below, both expanded modes occupy the viewport and place the independently scrollable question above the editor, capped at 38dvh. The editor scrolls independently; controls wrap and account for safe areas.
- Expanded canvas height is at least 400px on desktop and 340px on narrow screens, with viewport-relative growth. These are local workspace measurements, not additions to the global spacing scale.

## Design-system comparison

Checked `PRODUCT.md`, `.impeccable/surfaces/apps-web-src-app-page-tsx.md`, `DESIGN.md`, `.impeccable/design.json`, `apps/web/src/app/ion.css`, the relevant circuit rules in `globals.css`, the workspace stylesheet, and the editor/question integration samples above. The completed finish review returned **SHIP**, with no material fixes; the supplied detector report at `backend/workdir/circuit-workspace-design-check.json` contains `[]`.

The palette remains semantic Ion: cream/deep purple in light mode and violet/lilac/amber in dark mode. Workspace surfaces, borders, reference paper and selected controls resolve `--surface`, `--surface-2`, `--paper`, `--ink`, `--line` and `--action`. Heebo remains the interface face; the workspace uses local 16px headings, 15px reference text with 1.85 line-height, and compact 12–13px toolbar text. The inherited global ramp remains unchanged. Controls retain at least 44px touch targets, the expanded panel uses the incumbent 12px radius, and palette controls use 7px corners.

The Theme Continuity, Labelled State, Direction-Aware Text and Quiet Depth rules remain applicable. Logical borders and independent text direction support Hebrew and English while the technical board remains LTR. Workspace geometry and its soft modal shadow/backdrop are component-specific implementation details, not new reusable system tokens or a new elevation rule. `DESIGN.md` and `.impeccable/design.json` remain unchanged.

Not canonized or repaired: the incumbent documentation's dormant Workbench selectors, incomplete task-sidecar snippets and unsampled drift remain outside this narrow extension; the review found no new material craft defect to adopt as a rule.

## Verification and evidence

The implementation pass reported 185 passing unit tests, a successful production build and successful TypeScript checks. The final isolated browser run passed **231/231 checks**, with ten captures and no browser console errors; console errors cause the runner to fail. The finish review's **SHIP** disposition covered the original eight captures, with no UI source changes afterward. Two additional phone captures and targeted assertions extend that evidence.

The browser scenarios cover Hebrew/light and English/dark at desktop 1440×1000 and emulated mobile 390×844. Assertions cover native modality, full viewport bounds, question hide/show, accessible close targets, page/dialog horizontal overflow, preserved gate/selection/simulation/DOM, Escape and Back restoration, and undo/redo after mode changes. Targeted viewport assertions also verify retention through all modes and Escape; the simultaneous phone question/canvas state leaves at least 275.92px of canvas visible, with 91px of Hebrew prompt prose or 121px of English prompt prose visible.

Local evidence (ignored output; not committed):

- `.impeccable/review/circuit-workspace/results.json`
- `.impeccable/review/circuit-workspace/desktop-expanded-he-light.png`
- `.impeccable/review/circuit-workspace/desktop-fullscreen-he-light.png`
- `.impeccable/review/circuit-workspace/desktop-expanded-en-dark.png`
- `.impeccable/review/circuit-workspace/desktop-fullscreen-en-dark.png`
- `.impeccable/review/circuit-workspace/mobile-question-he-light.png`
- `.impeccable/review/circuit-workspace/mobile-canvas-he-light.png`
- `.impeccable/review/circuit-workspace/mobile-question-en-dark.png`
- `.impeccable/review/circuit-workspace/mobile-canvas-en-dark.png`
- `.impeccable/review/circuit-workspace/mobile-question-canvas-he-light.png`
- `.impeccable/review/circuit-workspace/mobile-question-canvas-en-dark.png`

The incumbent visual comparison is `.impeccable/review/ion-production/circuit-light-desktop.png`.

To reproduce, keep the local preview server running on port 3212 and run from the repository root:

```powershell
node apps/web/tools/screenshots/circuit-workspace.mjs --url 'http://localhost:3212/site-preview?style=ion-adaptive' --out .impeccable/review/circuit-workspace
```

The runner uses an isolated temporary headless Edge profile and an existing local shared preview. It does not exercise an authenticated live backend. Mobile device emulation does not replace testing on a physical iPhone. Automated evidence covers representative preview content; authenticated questions with real figures, resource failures, long content, and interview flows still require the manual checks below. This handoff does not assert deployment completion; the delivery owner records the final deployment separately.

## בדיקה ידנית באתר החי

1. היכנסו לאתר החי עם החשבון הרגיל. פתחו את **היום** ובחרו פריט תרגול, או לחצו על **מאגר** ואז על שורת שאלה לפי הכותרת שלה (בשורה מופיע **לתרגול** או **תרגלתם בעבר**). באזור התשובה פתחו **שרטוט מעגל לוגי**.
2. הוסיפו שער **AND**, גררו אותו למיקום שקל לזהות ובחרו אותו. בצעו ביטול שינוי ואז ביצוע מחדש כדי לוודא שהשער חוזר.
3. לחצו על **הרחבת הלוח**. ודאו שהלוח גדל ושנוסח השאלה מופיע לצד אזור השרטוט במחשב. בשאלה עם תמונה או אפשרויות תשובה, ודאו שגם הן מופיעות ושפתרון השאלה אינו מוצג בחלונית.
4. גללו את חלונית השאלה ואת אזור העריכה בנפרד. ודאו שאפשר להגיע לכל התוכן ולכפתור **חזרה לתשובה**, בלי גלילה אופקית של העמוד.
5. לחצו על **הסתרת השאלה**, ואז על **הצגת השאלה**. ודאו שהשער, המיקום והבחירה נשמרו. בדקו גם את כפתור סגירת חלונית השאלה ופתיחתה מחדש.
6. לחצו על **מסך מלא**. ודאו שהסביבה ממלאת את חלון הדפדפן. עברו אל **חלון מוגדל** ובחזרה; ודאו שהשרטוט נשמר. אין צורך שהדפדפן עצמו יעבור למסך מלא.
7. לחצו על **חזרה לתשובה**. ודאו שהשרטוט והמיקום נשמרו ושאפשר שוב לגלול בעמוד. בדקו שביטול שינוי וביצוע מחדש עדיין עובדים.
8. פתחו שוב את **הרחבת הלוח**, ואז לחצו על **Esc** במקלדת. ודאו שחזרתם לתשובה עם אותו שרטוט ושהמיקוד חזר לכפתור ההרחבה.
9. חזרו על הבדיקה בעברית ובאנגלית, במצב בהיר ובמצב כהה. בדקו שטקסט השאלה קריא ושכיוון הטקסט, השערים והחיבורים תקין. אם משתמשים בראיון, חזרו על פתיחת השאלה והשרטוט גם שם.
10. בטלפון אמיתי, ובפרט ב־iPhone, בדקו את שני מצבי ההרחבה. השאלה אמורה להופיע מעל העורך; גללו אותה בנפרד, הסתירו אותה כדי לפנות מקום ללוח, ובדקו שכפתורי היציאה נגישים גם ליד שולי המסך ובסיבוב המכשיר.

השלבים האלה הם הוראות לאימות ידני; הם אינם דיווח שבוצעה בדיקה בחשבון חי או ב־iPhone פיזי. שמירת השרטוט בין מצבי תצוגה אינה הבטחה לשמירה לאחר רענון או יציאה מהשאלה; התנהגות השמירה הקיימת של התרגול ממשיכה לקבוע זאת.
