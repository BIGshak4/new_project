# PREP-352 — למה מסלול תזמון מופיע בהרצה אחת ונעלם באחרת?

פתרון מוצע.

[מקור פנימי](../sources/2026-11-15-batch20b-15.png)

## he

מסלול בין שני אוגרים מופיע בהרצת STA אחת ואינו מופיע באחרת. הציעו אבחון מסודר שמבדיל בין שינוי תכנון, שינוי אילוצים/מצב ניתוח ושינוי שאילתת הדוח. אילו ראיות צריך לאסוף לפני שמכריזים שהמסלול אינו קיים?

הניחו שתי הרצות תקינות. אין נתון שמוכיח שכולן משתמשות באותו netlist,mode,corner,סוג check או פילטר. אל תסירו חריגי תזמון כדי לקבל תוצאה רצויה. מודל Python המצורף מקבל תצפיות בוליאניות מפורשות ומחזיר גורמים אפשריים; הוא אינו קורא בסיס נתונים של STA.

1. האם היעדר שורה בדוח מצביע בהכרח על היעדר חיבור חשמלי?
2. בדקו תחילה זהות אובייקטים וכיסוי שאילתה, ואז clocks,חריגים וקשתות פעילות.
3. התמקדו ב־from/to ותרחיש מפורשים, ודרשו דוחות ראיות לנתיב הנתונים ולסיבה שבגללה לא נותח.

### שלושה סוגי היעלמות
ראשית משווים גיבובים וגרסאות, טוענים את התכנון והתרחיש הנכונים ומוודאים ששמות שני האוגרים נפתרים לאובייקטים יחידים. סינתזה עלולה למחוק אוגר, לשנות שמות או להפוך ענף לקבוע. בודקים fanin/fanout כדי להבחין בין חיבור נתונים ממשי לבין השערה לפי שמות.

שנית מאמתים מה נשאל בדוח. top-N,סף slack,מסלול גרוע יחיד לכל endpoint,מעבר rise/fall,קבוצת שעון,פינת ניתוח,setup מול hold ודרך־ביניים מסוימת יכולים להסתיר שורה בלי למחוק מסלול. מבקשים שאילתה ממוקדת עם אותם start/end,שעונים וחזיתות בשתי ההרצות. בהשוואת setup ו־hold עשויות להיות קשתות שונות, ולכן אין להשוות אותן כאילו הן אותו check.

שלישית בודקים clocks ואילוצים. שעון או generated clock חסר, או ממשק I/O ללא אילוצים, עלולים להשאיר מסלול מחוץ לדוח הרגיל. false path ו־clock groups יכולים להוציא מסלולים מהניתוח. case analysis והתפשטות קבועים עשויים לחסום קשת לוגית; set_disable_timing או ספרייה שאין בה קשת נדרשת עשויים לנתק את גרף התזמון. מצב test/functional והפעלת clock-gating משנים קשתות פעילות. multicycle משנה בחירת חזיתות ובדיקות, ואינו כשלעצמו הוכחה שמסלול נמחק.

לכל כיוון שומרים ראיה כמו אובייקט שנעלם, חריג שפגע בו או שאילתה שמחזירה אותו כשהסינון משתנה. כמה גורמים יכולים להתקיים יחד. המודל מחזיר רשימה, וכשכל הבדיקות המבניות והאנליטיות עברו אך השורה עדיין חסרה הוא מפנה לכיסוי/שאילתת הדוח. בלי תצפיות כאלה התשובה היא רשימת השערות ותכנית איסוף, ולא אבחנה ודאית.

[אפשרויות דיווח וסינון](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_timing) · [קשתות תזמון מושבתות](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_disable_timing). דפי היצרן מתעדים מנגנונים בכלי AMD; שמות פקודות ותמיכה בכלי אחר נבדקים בגרסתו.

```python
"""Evidence-based toy path visibility, separate from licensed STA tools."""


def explain_visibility(evidence):
    """Evidence booleans describe one selected scenario/check and explicit path."""
    required = (
        "same_design", "start_exists", "end_exists", "physical_route",
        "clocked", "exception_cut", "arc_disabled", "constant_cut",
        "reported",
    )
    if set(evidence) != set(required) or any(type(v) is not bool for v in evidence.values()):
        raise ValueError("all nine explicit boolean observations are required")
    causes = []
    if not evidence["same_design"]:
        causes.append("different_design")
    if not evidence["start_exists"] or not evidence["end_exists"]:
        causes.append("missing_object")
    if not evidence["physical_route"]:
        causes.append("no_data_route")
    if not evidence["clocked"]:
        causes.append("unconstrained_clock_or_io")
    if evidence["exception_cut"]:
        causes.append("timing_exception")
    if evidence["arc_disabled"]:
        causes.append("disabled_timing_arc")
    if evidence["constant_cut"]:
        causes.append("case_or_constant_propagation")
    if not causes and not evidence["reported"]:
        causes.append("report_query_or_coverage")
    return causes
```

## en

A path between two registers appears in one STA run and is absent from another. Design a diagnosis distinguishing design changes, constraint/analysis changes and report-query changes. What evidence is needed before declaring that the path does not exist?

Assume both runs complete successfully. Nothing establishes identical netlist,mode,corner,check type or filters. Do not remove timing exceptions merely to obtain a desired result. The attached Python model accepts explicit Boolean observations and returns possible causes; it does not read an STA database.

1. Does an absent report row establish that a physical connection is absent?
2. First check object identity and query coverage, then clocks, exceptions and active arcs.
3. Query explicit from/to objects and scenario, and collect evidence for both physical connectivity and the reason timing was omitted.

### Three kinds of disappearance
First compare fingerprints/versions, load the correct design/scenario and establish that both names resolve uniquely. Synthesis can remove registers, rename them or fold a branch to a constant. Trace fanin/fanout to distinguish real connectivity from a guess based on names.

Second establish the report query. Top-N,slack cutoffs,one worst path per endpoint,rise/fall selection,clock groups,corners,setup versus hold and through-point filters can suppress a row without removing a path. Query matching explicit start/end objects,clocks and edges in both runs. Setup and hold can select different arcs; they are different checks.

Third inspect clocks and constraints. Missing clocks/generated clocks or unconstrained I/O can omit paths from ordinary reports. False paths and clock-group exclusions can cut analysis. Case analysis and constant propagation can block logical arcs. Disabled timing arcs or missing library timing data can disconnect the timing graph. Test/functional modes and clock-gating state change active arcs. Multicycle changes edge selection/checks and does not by itself prove a path was removed.

Retain evidence for each explanation, such as a missing object, an affecting exception or a focused query recovering the row. Multiple causes can coexist. The model returns a list, and when structural/analysis observations pass but the row remains absent it points to query/coverage. Without those observations the result is a hypothesis list and evidence plan rather than a definite diagnosis.

[Reporting and filtering](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_timing) · [Disabled timing arcs](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_disable_timing). These vendor pages document AMD mechanisms; exact commands and support in another tool require that tool's versioned documentation.

```python
"""Evidence-based toy path visibility, separate from licensed STA tools."""


def explain_visibility(evidence):
    """Evidence booleans describe one selected scenario/check and explicit path."""
    required = (
        "same_design", "start_exists", "end_exists", "physical_route",
        "clocked", "exception_cut", "arc_disabled", "constant_cut",
        "reported",
    )
    if set(evidence) != set(required) or any(type(v) is not bool for v in evidence.values()):
        raise ValueError("all nine explicit boolean observations are required")
    causes = []
    if not evidence["same_design"]:
        causes.append("different_design")
    if not evidence["start_exists"] or not evidence["end_exists"]:
        causes.append("missing_object")
    if not evidence["physical_route"]:
        causes.append("no_data_route")
    if not evidence["clocked"]:
        causes.append("unconstrained_clock_or_io")
    if evidence["exception_cut"]:
        causes.append("timing_exception")
    if evidence["arc_disabled"]:
        causes.append("disabled_timing_arc")
    if evidence["constant_cut"]:
        causes.append("case_or_constant_propagation")
    if not causes and not evidence["reported"]:
        causes.append("report_query_or_coverage")
    return causes
```

[Executable reference](../solutions/sta_path_visibility1115b.py)
[Checks](../checks/check_sta1115b.py)
[Verification](../checks/sta1115b-verification.json)
[he diagram](../diagrams/prep-352-sta-solution-1115b-he.png)
[en diagram](../diagrams/prep-352-sta-solution-1115b-en.png)
