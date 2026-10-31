# PREP-212 — רשימה מקושרת כטיפוס נתונים מופשט ואטום בשפת C

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-18.png](../sources/2026-10-31-batch20-18.png)

## נוסח המקור / Original wording

מימוש רשימה מקושרת באמצעות Abstract Data Types ב-C כולל פונקציות createNode, listContains ופונקציה להוספת node במקום כלשהו ברשימה

## עברית

ממשו ב־C רשימה חד־כיוונית באמצעות טיפוס נתונים מופשט: createNode ליצירת צומת עם מטען int, listContains לבדיקת קיום ערך, ו־insertNode להכנסת צומת קיים במיקום נתון. הציגו ממשק ציבורי אטום ומימוש פרטי, הסבירו בעלות על זיכרון והוכיחו שהפעולות משמרות רשימה סופית ללא מעגלים.

השלמות עריכה: האינדקסים מתחילים באפס, ומותר להכניס בכל מיקום 0..length כולל הוספה לסוף. createNode יוצר צומת מנותק בבעלות הקורא. הבעלות עוברת לרשימה רק בהכנסה מוצלחת; כישלון או מיקום לא תקין אינם משנים את הרשימה או את הצומת. יש לדחות צומת שכבר שייך לכל רשימה, גם אם הוא זנב עם next=NULL. API התמיכה המוצהר כולל listInit, listDestroy, destroyDetachedNode וכן listLength/listGet לקריאה בלבד. כישלון הקצאה מחזיר NULL, ולא משנה רשימה קיימת. ההכנסה עצמה אינה מקצה זיכרון. מניחים שימוש בכתובות חיות שהוחזרו מה־API, ללא גישות מקבילות; אין שימוש בידית אחרי שחרורה.

### רמזים / Hints

1. אילו פרטים צריכים להופיע בקובץ הכותרת כדי שמשתמש יוכל להחזיק ידיות בלי לשנות קישורים?
2. הכנסה בראש משנה את head, והכנסה באמצע משנה next של קודמו. אפשר לתאר את שני המקרים כעדכון הכתובת של קישור אחד.
3. החזיקו Node **link, שמתחיל בכתובת head ומתקדם אל כתובת next. בדקו טווח ובעלות לפני שינוי; next=NULL לבדו אינו מוכיח שהצומת מנותק.

### הצעה לפתרון / Proposed solution

### הפרדת הממשק מן הייצוג
בקובץ הכותרת נכריז typedef על struct List ועל struct Node, בלי לחשוף שדות. הקורא מחזיק מצביעים אטומים; רק קובץ המימוש מכיר את head, length ואת שדות הצומת value,next,owner. כך הלקוח אינו יכול לשנות next ישירות במסגרת ה־API. ה־owner הוא NULL בצומת מנותק ומצביע לרשימה אחרי העברת בעלות. בדיקת next לבדה אינה מספיקה: גם הזנב של רשימה תקינה מצביע ל־NULL.

listInit מקצה רשימה ריקה. createNode מקצה צומת ומאתחל את שלושת שדותיו; אם malloc נכשל הוא מחזיר NULL בלי לכתוב למקום לא תקף. listContains עובר על הצמתים ומשווה את המטען, ולא את כתובת הצומת. ערכים כפולים מותרים. destroyDetachedNode משחרר רק צומת ללא בעלים; listDestroy משחרר כל צומת שבבעלות הרשימה ואת הידית עצמה. אחרי השחרור כל מצביע שאול לצומת או לרשימה אינו תקף.

### הכנסה באמצעות כתובת של קישור
ראשית נדחה ידיות NULL, צומת עם owner שאינו NULL, צומת עם next שאינו NULL, מיקום גדול מהאורך ומקרה של גלישת מונה length. עד כאן לא השתנה דבר. נציב link=&list->head. אחרי position צעדים, link הוא כתובת הקישור שצריך להפנות אל הצומת החדש: כתובת head בהכנסה לראש, או כתובת next של הקודם בהכנסה באמצע ובסוף. נשמור node->next=*link, נרשום owner, נפנה *link אל node ונגדיל אורך. אין הקצאה בתוך insertNode, ולכן אין כשל הקצאה באמצע חיבור הקישורים.

דוגמה: ברשימה 10→20→30, הכנסת צומת 99 במיקום 1 מעדכנת קודם 99.next=20 ואחר כך 10.next=99; מתקבלת 10→99→20→30. במיקום 0 הקישור הוא head, ובמיקום 3 ברשימה המקורית הקישור הוא next של 30. מיקום 4 ברשימה המקורית נדחה, והצומת נשאר מנותק בבעלות הקורא. אפשר לנסות אותו במיקום תקין או לשחרר אותו באמצעות destroyDetachedNode.

### נכונות וניהול חיים
אינווריאנט הייצוג: head מוביל לשרשרת סופית ללא מעגלים, length שווה למספר צמתיה, וכל צומת בשרשרת בעל owner של אותה רשימה. רשימה ריקה מקיימת זאת. חיפוש וקריאה אינם משנים דבר. להכנסה מגיע צומת מנותק שאינו שייך לשום שרשרת; הוא מקשר אל סיומת קיימת, וקישור אחד מצביע אליו. אף צומת קיים אינו נמחק או משנה סדר, ולחדש לא הייתה דרך להגיע לעצמו. לכן אין מעגל או שיתוף חדש, והאורך והבעלות מתעדכנים יחד. דחיית צומת בעל owner מונעת שימוש כפול גם באותה רשימה וגם ברשימה אחרת.

הבטחת “אין שינוי בכישלון” נשענת על כך שכל בדיקות הכישלון קודמות לכתיבות, והתקדמות link תקפה בגלל אינווריאנט האורך והבדיקה position≤length. בממשק הזה מצביע לא תקף או מצביע שכבר שוחרר אינו קלט חוקי; בדיקת NULL אינה בדיקת תקפות כללית של זיכרון ב־C. בהשמדה נשמור next לפני free ונעבור אליו; סדר זה מונע קריאה מן הצומת אחרי ששוחרר. אין כאן API הסרה או העברת צומת מרשימה קיימת, ולכן אין צורך להמציא חוזה בעלות לפעולות כאלה.

### עלות, בדיקה והמשך
יצירת צומת ואתחול רשימה מבצעים מספר קבוע של פעולות מלבד עלות המקצה. חיפוש הוא O(n) זמן ו־O(1) מקום נוסף; הכנסה במיקום p היא O(p+1), ובמקרה הגרוע O(n), עם O(1) מקום נוסף; הכנסה לראש O(1). השמדה O(n). מונה אורך מאפשר לדחות מיקום לא תקין מייד, אך אינו נותן גישה אקראית לצומת האמצעי. אין טענה שהמקצה עצמו בעל זמן קבוע במקרה הגרוע.

רתמת C נפרדת משתמשת רק ב־API הציבורי לבדיקה: כל מיקום הכנסה עבור אורכים אפס עד שמונה, מיקום לא תקין, סדר המטענים, חיפוש, דחיית זנב שכבר בבעלות, דחיית בעלות בין שתי רשימות ושחרור זיכרון. היא מזריקה כשלי הקצאה ל־listInit ול־createNode, ובודקת שהכנסה אינה מקצה גם כאשר ההקצאה הבאה חסומה. הרתמה קוּמפלה והורצה בפועל בשירות הרצה מבודד: עברו 54 תרחישי הכנסה ו־2,264 בדיקות assert, ולא נותרו בלוקים חיים לפי מונה ההקצאות של הרתמה. זהו מעבר של הרתמה העצמאית, ולא אישור מקצועי אנושי או בדיקת sanitizer. זהות וגרסת המהדר לא הוחזרו בשירות; הראיות המלאות נשמרו בקובץ הבדיקות.

תשובה קצרה: “אסתיר את המבנים, אגדיר בעלות מפורשת, ואכניס באמצעות מצביע לכתובת קישור אחרי כל הבדיקות. owner מונע הכנסה כפולה גם לזנב. הבעלות עוברת רק בהצלחה.” בהמשך אפשר להוסיף הסרה שמחזירה צומת מנותק: יש לעדכן קישורים ואורך, לאפס next ו־owner ולהעביר אחריות שחרור לקורא.

#### ממשק ציבורי: `prep_212_linked_list_adt.h`

```c
#ifndef PREP_212_LINKED_LIST_ADT_H
#define PREP_212_LINKED_LIST_ADT_H

#include <stdbool.h>
#include <stddef.h>

/* Opaque handles. Only this module changes links or ownership. */
typedef struct List List;
typedef struct Node Node;

/* Support API: a successful init returns an empty list; NULL = allocation failure. */
List *listInit(void);
void listDestroy(List *list); /* frees every owned node and the list; NULL is fine */
Node *createNode(int value);  /* detached on success; NULL = allocation failure */
bool destroyDetachedNode(Node *node); /* rejects owned nodes; NULL is harmless */

bool listContains(const List *list, int value); /* NULL list => false */
/* Valid positions are 0..length inclusive. Ownership transfers only on true.
   Failure never changes the list or the node. Insertion itself allocates nothing. */
bool insertNode(List *list, Node *node, size_t position);

/* Read-only support API, also used by the independent C test harness. */
size_t listLength(const List *list); /* NULL => 0 */
bool listGet(const List *list, size_t position, int *out_value);

#endif
```

#### מימוש פרטי: `prep_212_linked_list_adt.c`

```c
#include "prep_212_linked_list_adt.h"

#include <stdint.h>
#include <stdlib.h>

#ifndef LIST_MALLOC
#define LIST_MALLOC malloc
#endif
#ifndef LIST_FREE
#define LIST_FREE free
#endif

struct Node {
    int value;
    struct Node *next;
    struct List *owner;
};

struct List {
    Node *head;
    size_t length;
};

List *listInit(void) {
    List *list = LIST_MALLOC(sizeof *list);
    if (list == NULL) return NULL;
    list->head = NULL;
    list->length = 0;
    return list;
}

Node *createNode(int value) {
    Node *node = LIST_MALLOC(sizeof *node);
    if (node == NULL) return NULL;
    node->value = value;
    node->next = NULL;
    node->owner = NULL;
    return node;
}

bool destroyDetachedNode(Node *node) {
    if (node == NULL) return true;
    if (node->owner != NULL) return false;
    LIST_FREE(node);
    return true;
}

bool listContains(const List *list, int value) {
    if (list == NULL) return false;
    for (const Node *node = list->head; node != NULL; node = node->next) {
        if (node->value == value) return true;
    }
    return false;
}

bool insertNode(List *list, Node *node, size_t position) {
    if (list == NULL || node == NULL || node->owner != NULL ||
        node->next != NULL || position > list->length || list->length == SIZE_MAX) {
        return false;
    }
    Node **link = &list->head;
    for (size_t i = 0; i < position; ++i) link = &(*link)->next;
    node->next = *link;
    node->owner = list;
    *link = node;
    ++list->length;
    return true;
}

size_t listLength(const List *list) {
    return list == NULL ? 0 : list->length;
}

bool listGet(const List *list, size_t position, int *out_value) {
    if (list == NULL || out_value == NULL || position >= list->length) return false;
    const Node *node = list->head;
    for (size_t i = 0; i < position; ++i) node = node->next;
    *out_value = node->value;
    return true;
}

void listDestroy(List *list) {
    if (list == NULL) return;
    Node *node = list->head;
    while (node != NULL) {
        Node *next = node->next;
        LIST_FREE(node);
        node = next;
    }
    LIST_FREE(list);
}
```


### assumptions

[
  "רשימה חד־כיוונית סופית ללא מעגלים עם מטען int; ידיות אטומות חיות ושימוש מסודר ללא מקביליות.",
  "מיקום 0..length; צומת מנותק בבעלות הקורא עד הכנסה מוצלחת. אין שימוש אחרי listDestroy או שחרור צומת.",
  "listInit/listDestroy ודאגת הקורא לצומת מנותק הם API תמיכה מוצהר; insertNode אינו מקצה."
]

### optimality

"חיפוש והשמדה O(n); הכנסה במיקום p עולה O(p+1), לראש O(1), עם O(1) מקום נוסף. יצירה מבצעת מספר קבוע של פעולות מלבד עלות malloc; אין טענת אופטימליות בין כל מבני הנתונים."

### verification

"רתמת C קוּמפלה והורצה בפועל בשירות מבודד: עברו 54 תרחישי הכנסה ו־2,264 בדיקות assert, כולל דחיית זנב ובעלות כפולה, שמירת הסדר והזרקת כשלי הקצאה; מונה הבלוקים החיים הסתיים באפס. אין דיווח גרסת מהדר או בדיקת sanitizer. הראיות ב־checks/prep-212-verification.json; ביקורת אנושית ממתינה."

### edge_cases

[
  "רשימה ריקה; הכנסה לראש/אמצע/סוף; position=length+1; ידיות NULL.",
  "ערכים כפולים; INT_MIN ו־INT_MAX; כשל malloc; צומת זנב בבעלות עם next=NULL; הכנסה לאותה רשימה ולרשימה אחרת.",
  "שחרור צומת מנותק; ניסיון שחרור צומת בבעלות; שמירת next לפני שחרור בהשמדה."
]

### common_mistakes

[
  "לחשוף שדות ב־header ולכנות את הממשק אטום.",
  "לזהות צומת מנותק רק לפי next=NULL ולפספס זנב בבעלות.",
  "לשנות קישורים לפני בדיקת המיקום; לשכוח לעדכן head או מונה אורך.",
  "לאבד בעלות בכישלון; לשחרר צומת פעמיים; לקרוא next אחרי free; להתייחס למצביע משוחרר כקלט שניתן לאמת."
]

### interview_answer

"אשתמש בטיפוסים אטומים, בשדה owner ובמצביע לכתובת קישור. כל בדיקות הכישלון קודמות לחיבור; רק הצלחה מעבירה בעלות. השמדה משחררת את שרשרת הבעלות, והקורא משחרר צומת שנשאר מנותק."

### source_ambiguities

[
  "המקור מונה פעולות אך אינו מגדיר כיוון, טיפוס מטען, אינדוקס, בעלות, טיפול בכשל או API מחזור חיים; כל אלה הוגדרו כהשלמות עריכה.",
  "לא נוספה פעולת הסרה למימוש הנדרש; היא נידונה כהמשך בלבד. הנוסח המקורי נשמר בנפרד."
]

### solution_extensions

{
  "question": "כיצד תסירו צומת במיקום נתון ותחזירו אותו לקורא בלי לשחררו?",
  "direction": "בדקו טווח קודם; מצאו את כתובת הקישור, עקפו את הצומת, הקטינו length ואפסו next ו־owner. רק אז העבירו לקורא בעלות על צומת מנותק.",
  "integration": "מוכן בתוכן; לא מחובר לתור המשך אינטראקטיבי."
}

## English

Implement a singly linked list in C as an abstract data type: createNode creates a node holding an int, listContains tests value membership, and insertNode inserts an existing node at a requested position. Provide an opaque public interface and private implementation, explain memory ownership, and show that operations preserve a finite acyclic list.

Editorial completions: positions are zero-based;0..length inclusive permits insertion at the end. createNode returns a detached node owned by the caller. Ownership transfers only on successful insertion; failure or an invalid position changes neither list nor node. Reject a node already owned by any list, including a tail whose next=NULL. The declared support API includes listInit, listDestroy, destroyDetachedNode and read-only listLength/listGet. Allocation failure returns NULL without changing an existing list. Insertion itself does not allocate. Callers supply live handles from this API, access is serialized, and handles are not reused after destruction.

### רמזים / Hints

1. What belongs in the header so callers can hold handles without changing links?
2. Head insertion changes head; middle insertion changes a predecessor’s next. Both update one link location.
3. Use Node **link, starting at the address of head and advancing to an address of next. Check position and ownership before mutation; next=NULL alone does not prove detachment.

### הצעה לפתרון / Proposed solution

### Separate interface from representation
The header declares typedefs for struct List and struct Node without exposing their fields. Callers hold opaque pointers; only the implementation sees head,length and node fields value,next,owner. Clients cannot modify next through the public API. owner is NULL for a detached node and points to the list after ownership transfer. Checking next alone is insufficient: a legitimate list tail also has next=NULL.

listInit allocates an empty list. createNode allocates and initializes all three node fields; a failed malloc returns NULL without writing through an invalid pointer. listContains traverses and compares payload values rather than node addresses; duplicates are allowed. destroyDetachedNode frees only an unowned node, while listDestroy frees all owned nodes and the list handle. All borrowed node/list pointers become invalid after their objects are freed.

### Insert through the address of a link
First reject NULL handles, non-NULL owner, non-NULL next, positions beyond length and length-counter overflow. No state has changed. Set link=&list->head. After position steps, link is the address of the link that should target the new node: the head field for head insertion, or the predecessor’s next field in the middle and at the end. Set node->next=*link, record owner, set *link=node and increment length. insertNode allocates nothing, so allocation cannot fail halfway through rewiring.

For 10→20→30, inserting a node with value 99 at position 1 first links 99 to 20 and then links 10 to 99, producing 10→99→20→30. At position 0 the link is head; at position 3 in the original list it is the next field of node 30. Position 4 in the original list is rejected and leaves the node detached and caller-owned. The caller can retry a valid position or use destroyDetachedNode.

### Correctness and lifetimes
Representation invariant: head reaches a finite acyclic chain, length equals its node count, and each reachable node has this list as owner. An empty list satisfies it. Search and reads do not change it. Insertion receives a detached node outside every chain; it points to an existing suffix, and exactly one existing link is redirected to it. Existing nodes remain in order, and the new node had no path back to itself. No cycle or new shared ownership is introduced; count and owner update consistently. Rejecting non-NULL owner prevents duplicate insertion both within one list and across lists.

The failure-no-change guarantee follows because every rejection precedes every write. Advancing link is valid by the length invariant and position≤length. Invalid or already-freed addresses are outside the contract; NULL checking is not general pointer-validity checking in C. Destruction saves next before free and follows the saved pointer, avoiding a read through the freed node. This interface does not offer removal or transfer of an already-owned node, so those operations have no invented ownership behavior.

### Cost, verification and continuation
Node creation and list initialization perform a constant number of operations apart from allocator cost. Membership takes O(n) time and O(1) extra space. Insertion at p takes O(p+1), worst-case O(n), with O(1) extra space; head insertion is O(1). Destruction is O(n). Cached length immediately rejects an invalid position but does not provide random access to a middle node. No worst-case constant-time claim is made for the allocator itself.

A separate C harness observes only the public API: every insertion position for initial lengths 0..8, an invalid position, payload order, search, rejection of an already-owned tail, cross-list ownership rejection and cleanup. It injects allocation failures into listInit and createNode and checks that insertion allocates nothing even when the next allocation is blocked. The harness was actually compiled and executed by an isolated C service: all 54 insertion scenarios and 2,264 assertions passed, with zero live blocks according to the harness allocation tracker. This is an independent harness pass, not human professional approval or sanitizer execution. The service did not return compiler identity/version; full evidence is preserved in the verification report.

Short answer: “Hide the structures, define ownership, and insert through a pointer to a link after validating everything. owner prevents double insertion even for a tail; ownership moves only on success.” A follow-up adds removal returning a detached node: update links/count, clear next and owner, and return cleanup responsibility to the caller.

#### Public interface: `prep_212_linked_list_adt.h`

```c
#ifndef PREP_212_LINKED_LIST_ADT_H
#define PREP_212_LINKED_LIST_ADT_H

#include <stdbool.h>
#include <stddef.h>

/* Opaque handles. Only this module changes links or ownership. */
typedef struct List List;
typedef struct Node Node;

/* Support API: a successful init returns an empty list; NULL = allocation failure. */
List *listInit(void);
void listDestroy(List *list); /* frees every owned node and the list; NULL is fine */
Node *createNode(int value);  /* detached on success; NULL = allocation failure */
bool destroyDetachedNode(Node *node); /* rejects owned nodes; NULL is harmless */

bool listContains(const List *list, int value); /* NULL list => false */
/* Valid positions are 0..length inclusive. Ownership transfers only on true.
   Failure never changes the list or the node. Insertion itself allocates nothing. */
bool insertNode(List *list, Node *node, size_t position);

/* Read-only support API, also used by the independent C test harness. */
size_t listLength(const List *list); /* NULL => 0 */
bool listGet(const List *list, size_t position, int *out_value);

#endif
```

#### Private implementation: `prep_212_linked_list_adt.c`

```c
#include "prep_212_linked_list_adt.h"

#include <stdint.h>
#include <stdlib.h>

#ifndef LIST_MALLOC
#define LIST_MALLOC malloc
#endif
#ifndef LIST_FREE
#define LIST_FREE free
#endif

struct Node {
    int value;
    struct Node *next;
    struct List *owner;
};

struct List {
    Node *head;
    size_t length;
};

List *listInit(void) {
    List *list = LIST_MALLOC(sizeof *list);
    if (list == NULL) return NULL;
    list->head = NULL;
    list->length = 0;
    return list;
}

Node *createNode(int value) {
    Node *node = LIST_MALLOC(sizeof *node);
    if (node == NULL) return NULL;
    node->value = value;
    node->next = NULL;
    node->owner = NULL;
    return node;
}

bool destroyDetachedNode(Node *node) {
    if (node == NULL) return true;
    if (node->owner != NULL) return false;
    LIST_FREE(node);
    return true;
}

bool listContains(const List *list, int value) {
    if (list == NULL) return false;
    for (const Node *node = list->head; node != NULL; node = node->next) {
        if (node->value == value) return true;
    }
    return false;
}

bool insertNode(List *list, Node *node, size_t position) {
    if (list == NULL || node == NULL || node->owner != NULL ||
        node->next != NULL || position > list->length || list->length == SIZE_MAX) {
        return false;
    }
    Node **link = &list->head;
    for (size_t i = 0; i < position; ++i) link = &(*link)->next;
    node->next = *link;
    node->owner = list;
    *link = node;
    ++list->length;
    return true;
}

size_t listLength(const List *list) {
    return list == NULL ? 0 : list->length;
}

bool listGet(const List *list, size_t position, int *out_value) {
    if (list == NULL || out_value == NULL || position >= list->length) return false;
    const Node *node = list->head;
    for (size_t i = 0; i < position; ++i) node = node->next;
    *out_value = node->value;
    return true;
}

void listDestroy(List *list) {
    if (list == NULL) return;
    Node *node = list->head;
    while (node != NULL) {
        Node *next = node->next;
        LIST_FREE(node);
        node = next;
    }
    LIST_FREE(list);
}
```


### assumptions

[
  "Finite acyclic singly linked list with int payloads; live opaque handles and serialized access.",
  "Positions 0..length; the caller owns a detached node until successful insertion. Never reuse a freed list/node handle.",
  "listInit/listDestroy and detached-node cleanup are declared support APIs; insertNode does not allocate."
]

### optimality

"Search/destruction O(n); insertion at p is O(p+1), head insertion O(1), with O(1) extra space. Creation performs constant work apart from malloc; no optimality claim across all data structures."

### verification

"A C harness actually compiled and ran in an isolated service: 54 insertion scenarios and 2,264 assertions passed, including tail/double-ownership rejection, order preservation and allocation-failure injection; tracked live blocks ended at zero. No compiler version was returned and no sanitizer run is claimed. Evidence: checks/prep-212-verification.json; human review pending."

### edge_cases

[
  "Empty list; head/middle/tail insertion; position=length+1; NULL handles.",
  "Duplicate payloads; INT_MIN/INT_MAX; malloc failure; an owned tail with next=NULL; reinsertion into the same and another list.",
  "Detached cleanup; rejecting cleanup of an owned node; save next before free during destruction."
]

### common_mistakes

[
  "Exposing fields in the header while calling the interface opaque.",
  "Treating next=NULL as proof of detachment and accepting an owned tail.",
  "Mutating links before position validation; forgetting head or length updates.",
  "Losing ownership on failure; double freeing; reading next after free; assuming arbitrary dangling pointers can be validated."
]

### interview_answer

"Use opaque types, an owner field and a pointer to a link. Validate before rewiring; transfer ownership only on success. Destruction frees the owned chain, while callers clean up nodes still detached."

### source_ambiguities

[
  "The source names operations but omits direction, payload type, indexing, ownership, failure behavior and lifetime APIs; these are explicit editorial completions.",
  "Removal is discussed only as a follow-up, not added to the required implementation. Original text is preserved separately."
]

### solution_extensions

{
  "question": "How would removal return a node to the caller without freeing it?",
  "direction": "Validate position, locate the link, bypass the node, decrement length and clear next/owner. Then transfer a detached node back to the caller.",
  "integration": "Prepared in content; not connected to an interactive follow-up queue."
}

## קבצים / Files

- [solutions/prep_212_linked_list_adt.c](../solutions/prep_212_linked_list_adt.c)
- [solutions/prep_212_linked_list_adt.h](../solutions/prep_212_linked_list_adt.h)
- [diagrams/prep-212-algorithms-batch20-he.png](../diagrams/prep-212-algorithms-batch20-he.png)
- [diagrams/prep-212-algorithms-batch20-en.png](../diagrams/prep-212-algorithms-batch20-en.png)
