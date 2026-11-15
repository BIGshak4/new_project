# PREP-351 — תכנון רגרסיה להשוואת דוחות תזמון

פתרון מוצע.

[מקור פנימי](../sources/2026-11-15-batch20b-14.png)

## he

תכננו רגרסיה להשוואת שתי גרסאות של כלי STA או שתי תוכנות, למשל Fusion Compiler ו־PrimeTime. הגדירו מה יש לקבע, אילו דוחות ונתוני כיסוי לאסוף, כיצד להתאים מסלולים ומה ייחשב שינוי מהותי. ספקו מימוש קטן המשווה דוחות מנורמלים.

חוזה המימוש שנבחר הוא JSON, ללא הרצת כלים מסחריים. כל שורה היא התוצאה הגרועה של שאילתה מפורשת בזהות הכוללת תרחיש, setup/hold, נקודת התחלה וסיום, שני שעונים, שתי חזיתות ומעבר rise/fall. החזיתות הן מזהי חזית לפי ההגדרה, לא זמני הגעה הנמדדים להשוואה. כל דוח מציין יחידה ps/ns, כיסוי מלא של קבוצת השאילתות הנבחרת וגיבובי netlist,constraints,libraries,parasitics,analysis. הגיבוב האחרון כולל אפשרויות ניתוח, OCV/derates, CPPR והגדרת השאילתות. סף שינוי מטרי הוא 10 ps, ושינוי סימן slack תמיד מדווח.

1. האם קובץ netlist זהה לבדו מספיק כדי שההשוואה תהיה הוגנת?
2. הפרידו בין שינוי מספרי, שינוי כיסוי ושינוי הקשר הניתוח. סדר שורות או יחידות אינם זהות מסלול.
3. נרמלו יחידות, בנו מפתח מלא לשאילתה, בדקו קבוצות מפתחות ואז השוו arrival,required,slack בנפרד. אל תחליפו ערך חסר באפס.

### חוזה השוואה בר־שחזור
מקפיאים תכנון, ספריות ופינות, constraints וחריגים, שעונים וחזיתות, parasitics, מצב case analysis ואפשרויות ניתוח. מתעדים גם גרסאות כלים, פקודות, שגיאות ואזהרות. שינוי מודע של הקשר דורש השוואה חדשה שסיבתה מתועדת. שני הכלים עלולים להשתמש בברירות מחדל שונות.

### כיסוי לפני מספרים
אוספים setup וגם hold, קבוצות מסלולים, שעונים/אוגרים ללא אילוצים, קשתות מושבתות וחריגי תזמון. מגדירים מראש קבוצת שאילתות מלאה. דוח שמחזיר רק N מסלולים גרועים אינו מוכיח היעדר מסלול אחר. מתאם ייעודי לכל כלי מוציא את ה־JSON ובודק סיום תקין. מזהי מקרים ותרחישים נשמרים גם כשאין מסלול, בדוח כיסוי משלים. השוואת הדוגמה דוחה דוח חלקי או הקשר שונה, ומדווחת מפתחות חסרים או נוספים. הסימון complete הוא התחייבות המתאם שצריך לאמת, ולא הוכחה שמתקבלת מן המספרים.

### נרמול והשוואה
ממירים ל־ps, משווים קבוצות זהויות, וממיינים רק לצורך פלט קבוע. בבדיקת setup נדרש slack=required−arrival; ב־hold החוזה משתמש ב־arrival−required. לא קושרים מזהה מסלול לזמן הגעה ולא לטקסט עמודות. בודקים גם שדות נפרדים כדי ששינויים ב־arrival וב־required לא יבטלו זה את זה ב־slack. מעבר slack מ־חיובי לשלילי מדווח גם כשההפרש קטן מ־10 ps. סף רגרסיה הוא מדיניות השוואה ואינו אישור לסגירת תזמון.

לדוגמה arrival=1000 ps,required=1100 ps נותנים slack=100 ps. דוח אחר עם 1.020 ns ו־1.100 ns נותן 80 ps ומדווח שינוי 20 ps. אם שני המספרים זזים יחד ב־20 ps וה־slack נשאר 100 ps, עדיין מדווחים שני שינויים. אחרי כישלון משווים clocks,exceptions,derates,קשתות ותאי המסלול לפני קביעה שיש באג בכלי.

דפי AMD מתעדים אפשרויות סינון מסלולים וחריגי תזמון כעקרונות STA. מתאמי כלי Synopsys והפקודות המדויקות דורשים אימות מול גרסת הכלי. [דוחות מסלולים](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_timing) · [קשתות תזמון מושבתות](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_disable_timing).

```python
"""Compare complete, tool-adapted timing manifests; this does not invoke an STA tool."""
from math import isfinite


CONTEXT = ("netlist", "constraints", "libraries", "parasitics", "analysis")
IDENTITY = (
    "scenario", "check", "startpoint", "endpoint", "launch_clock",
    "capture_clock", "launch_edge", "capture_edge", "transition",
)
METRICS = ("arrival", "required", "slack")
UNIT_PS = {"ps": 1.0, "ns": 1000.0}


def normalized(run):
    if run.get("complete") is not True:
        raise ValueError("an exhaustive chosen-query manifest is required")
    if set(run.get("context", {})) != set(CONTEXT):
        raise ValueError("all context fingerprints are required")
    if any(not isinstance(v, str) or not v for v in run["context"].values()):
        raise ValueError("context fingerprints must be nonempty strings")
    if run.get("unit") not in UNIT_PS:
        raise ValueError("only explicit ps or ns units are supported")
    scale = UNIT_PS[run["unit"]]
    result = {}
    for row in run["paths"]:
        identity = tuple(row[name] for name in IDENTITY)
        if any(not isinstance(v, str) or not v for v in identity):
            raise ValueError("explicit nonempty path identity fields are required")
        if identity in result:
            raise ValueError("duplicate query identity")
        if row["check"] not in ("setup", "hold"):
            raise ValueError("unsupported check")
        values = {}
        for metric in METRICS:
            value = row[metric]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("numeric finite metrics required")
            value = float(value) * scale
            if not isfinite(value):
                raise ValueError("numeric finite metrics required")
            values[metric] = value
        expected_slack = (values["required"] - values["arrival"]
                          if row["check"] == "setup"
                          else values["arrival"] - values["required"])
        if abs(values["slack"] - expected_slack) > 1e-6:
            raise ValueError("inconsistent arrival/required/slack convention")
        result[identity] = values
    return result


def compare_runs(reference, candidate, tolerance_ps=10.0):
    if (isinstance(tolerance_ps, bool) or not isinstance(tolerance_ps, (int, float))
            or not isfinite(tolerance_ps) or tolerance_ps < 0):
        raise ValueError("nonnegative finite tolerance required")
    left, right = normalized(reference), normalized(candidate)
    if reference["context"] != candidate["context"]:
        raise ValueError("the frozen comparison context differs")
    missing, added = sorted(left.keys() - right.keys()), sorted(right.keys() - left.keys())
    changed, sign_changed = [], []
    for identity in sorted(left.keys() & right.keys()):
        for metric in METRICS:
            difference = right[identity][metric] - left[identity][metric]
            if abs(difference) > tolerance_ps:
                changed.append({"identity": identity, "metric": metric,
                                "delta_ps": difference})
        if (left[identity]["slack"] < 0) != (right[identity]["slack"] < 0):
            sign_changed.append(identity)
    return {"passed": not (missing or added or changed or sign_changed),
            "missing": missing, "added": added, "changed": changed,
            "sign_changed": sign_changed}
```

## en

Design a regression comparing two STA tool versions or two tools, such as Fusion Compiler and PrimeTime. Define frozen inputs, reports and coverage evidence, path matching and meaningful changes. Implement a small comparison of normalized reports.

The chosen executable contract is JSON without invoking commercial tools. Each row is the worst result of an explicit query identified by scenario, setup/hold, startpoint/endpoint, both clocks, both edge identities and rise/fall transition. Edge identities are declared clock edges, not measured arrival times being compared. Every run states ps/ns units, completeness for the chosen query set and netlist,constraints,libraries,parasitics,analysis fingerprints. The last fingerprint covers analysis settings, OCV/derates, CPPR and query definitions. Metric tolerance is 10 ps, and every slack-sign change is reported.

1. Is an identical netlist enough for a fair comparison?
2. Separate numeric changes, coverage changes and changed analysis context. Row order or units are not path identity.
3. Normalize units, key each query completely, compare key sets and then arrival,required,slack separately. Do not replace missing data with zero.

### Reproducible comparison context
Freeze the design, libraries/corners, constraints/exceptions, clocks/edges, parasitics, case analysis and analysis settings. Record tool versions, commands, warnings and errors. An intentional context change needs its own documented comparison. Different tools can have different defaults.

### Coverage before metrics
Collect setup and hold, path groups, unconstrained clocks/registers, disabled arcs and exceptions. Declare a complete query set. A top-N worst-path report does not establish that another path is absent. A tool-specific adapter emits the JSON and checks successful execution. A separate coverage artifact retains query identities and scenarios even when no path is returned. The sample rejects incomplete or incompatible-context runs and reports missing/added keys. The complete flag is an adapter obligation to verify, rather than proof inferred from numeric rows.

### Normalize and compare
Convert to ps, compare identity sets and sort only for deterministic output. Setup uses slack=required−arrival; this hold contract uses arrival−required. Do not identify a query by measured arrival or human-formatted columns. Compare individual metrics so arrival/required changes cannot cancel inside slack. A positive-to-negative slack change is reported even below 10 ps. A regression tolerance is comparison policy and does not approve timing closure.

For example arrival=1000 ps,required=1100 ps gives slack=100 ps. Another run with 1.020 ns and 1.100 ns gives 80 ps, flagging a 20 ps change. If both times shift by 20 ps while slack stays 100 ps, both metrics still differ. Investigate clocks,exceptions,derates,arcs and cells before concluding that a tool has a defect.

AMD documents path filtering and disabled arcs as general STA mechanisms. Synopsys-specific adapters and commands must be checked for their installed tool version. [Path reporting](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_timing) · [Disabled timing arcs](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_disable_timing).

```python
"""Compare complete, tool-adapted timing manifests; this does not invoke an STA tool."""
from math import isfinite


CONTEXT = ("netlist", "constraints", "libraries", "parasitics", "analysis")
IDENTITY = (
    "scenario", "check", "startpoint", "endpoint", "launch_clock",
    "capture_clock", "launch_edge", "capture_edge", "transition",
)
METRICS = ("arrival", "required", "slack")
UNIT_PS = {"ps": 1.0, "ns": 1000.0}


def normalized(run):
    if run.get("complete") is not True:
        raise ValueError("an exhaustive chosen-query manifest is required")
    if set(run.get("context", {})) != set(CONTEXT):
        raise ValueError("all context fingerprints are required")
    if any(not isinstance(v, str) or not v for v in run["context"].values()):
        raise ValueError("context fingerprints must be nonempty strings")
    if run.get("unit") not in UNIT_PS:
        raise ValueError("only explicit ps or ns units are supported")
    scale = UNIT_PS[run["unit"]]
    result = {}
    for row in run["paths"]:
        identity = tuple(row[name] for name in IDENTITY)
        if any(not isinstance(v, str) or not v for v in identity):
            raise ValueError("explicit nonempty path identity fields are required")
        if identity in result:
            raise ValueError("duplicate query identity")
        if row["check"] not in ("setup", "hold"):
            raise ValueError("unsupported check")
        values = {}
        for metric in METRICS:
            value = row[metric]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("numeric finite metrics required")
            value = float(value) * scale
            if not isfinite(value):
                raise ValueError("numeric finite metrics required")
            values[metric] = value
        expected_slack = (values["required"] - values["arrival"]
                          if row["check"] == "setup"
                          else values["arrival"] - values["required"])
        if abs(values["slack"] - expected_slack) > 1e-6:
            raise ValueError("inconsistent arrival/required/slack convention")
        result[identity] = values
    return result


def compare_runs(reference, candidate, tolerance_ps=10.0):
    if (isinstance(tolerance_ps, bool) or not isinstance(tolerance_ps, (int, float))
            or not isfinite(tolerance_ps) or tolerance_ps < 0):
        raise ValueError("nonnegative finite tolerance required")
    left, right = normalized(reference), normalized(candidate)
    if reference["context"] != candidate["context"]:
        raise ValueError("the frozen comparison context differs")
    missing, added = sorted(left.keys() - right.keys()), sorted(right.keys() - left.keys())
    changed, sign_changed = [], []
    for identity in sorted(left.keys() & right.keys()):
        for metric in METRICS:
            difference = right[identity][metric] - left[identity][metric]
            if abs(difference) > tolerance_ps:
                changed.append({"identity": identity, "metric": metric,
                                "delta_ps": difference})
        if (left[identity]["slack"] < 0) != (right[identity]["slack"] < 0):
            sign_changed.append(identity)
    return {"passed": not (missing or added or changed or sign_changed),
            "missing": missing, "added": added, "changed": changed,
            "sign_changed": sign_changed}
```

[Executable reference](../solutions/sta_normalized_regression1115b.py)
[Checks](../checks/check_sta1115b.py)
[Verification](../checks/sta1115b-verification.json)
[he diagram](../diagrams/prep-351-sta-solution-1115b-he.png)
[en diagram](../diagrams/prep-351-sta-solution-1115b-en.png)
