"""Explain Fibonacci indexing with a complete small recursion tree."""
import json
import shutil
from pathlib import Path
from prep_024_grasshopper_stairs import count_ways
root=Path(__file__).resolve().parents[1]
source='sources/prep-024-fibonacci-index-clarification.png'
tree='''W(4) = 5
├── W(3) = 3
│   ├── W(2) = 2
│   │   ├── W(1) = 1
│   │   └── W(0) = 1
│   └── W(1) = 1
└── W(2) = 2
    ├── W(1) = 1
    └── W(0) = 1'''
he='''### מה פירוש W(n)=F(n+1), ומה עץ הרקורסיה סופר?

בצילום ההסבר המצורף הנוסחה עלולה להיראות משובשת בגלל ערבוב עברית ומתמטיקה. הסימון המדויק משמאל לימין הוא `W(n) = F(n + 1)`. W(n) הוא מספר הדרכים לשלב n; F(k) הוא האיבר במקום k בסדרת פיבונאצ׳י עם F(0)=0,F(1)=1. אין הכוונה ל־F(n)+1 ואין הכוונה להוסיף שלב לסולם: זו רק התאמה בין שתי סדרות עם מספור שונה.

| n | F(n) | W(n) |
|---|---|---|
| 0 | 0 | 1 |
| 1 | 1 | 1 |
| 2 | 1 | 2 |
| 3 | 2 | 3 |
| 4 | 3 | 5 |
| 5 | 5 | 8 |

לדוגמה, W(4)=5=F(5), ו־W(5)=8=F(6). שתי הסדרות מקיימות אותו חיבור שני קודמים, אך מקרי הבסיס של W הם 1,1 ולא 0,1.

**התשובה הסופית הכללית:** W(0)=1, W(1)=1, W(n)=W(n−1)+W(n−2) עבור n≥2. שקול ל־W(n)=F(n+1). מאחר שלא ניתן n מספרי, אין תשובה מספרית אחת. לדוגמה, אם n=4 התשובה 5, ואם n=10 התשובה 89.

**עץ רקורסיה לדוגמה n=4:**

```text
'''+tree+'''
```

כל צומת מתפצל לפי שתי האפשרויות לקפיצה האחרונה: קפיצה של 1 נותנת ילד W(n−1), וקפיצה של 2 נותנת ילד W(n−2). ערך האב הוא סכום ערכי הילדים. עוצרים ב־W(1)=1 או W(0)=1, ולכן בכל עלה נספרת דרך אחת. בעץ הזה יש חמישה עלים, ולכן W(4)=5. W(1) כעלה אומר שנותרה השלמה יחידה בקפיצה של 1; W(0) אומר שכבר הושלם המרחק וההמשך הריק אפשרי בדרך אחת. קריאת הענפים מהשורש מתארת קפיצות אחרונות לאחור; היא אינה רשימת צעדים כרונולוגית מהקרקע.

חמש הדרכים הן (1,1,1,1), (1,1,2), (1,2,1), (2,1,1), (2,2). העץ מסביר את הספירה אבל מחשב W(2) פעמיים, ולכן בנייה נאיבית שלו אינה המימוש היעיל. לחישוב משתמשים בקוד הלולאה עם שני משתנים שכבר נשמר. עץ יכול לתת מספר מדויק לכל n נתון, אך גודלו גדל במהירות; הנסיגה מאפשרת לחשב בלי לבנות את העץ.
'''
en='''Index clarification: W(n)=F(n+1), not F(n)+1. F uses base values 0,1; W uses 1,1, so W(4)=5=F(5). With unspecified n there is no single numeric answer: the exact general answer is W(0)=W(1)=1 and W(n)=W(n-1)+W(n-2), equivalently F(n+1). Examples: n=4 gives 5 and n=10 gives 89.

The complete W(4) recursion tree splits into W(3) and W(2), stopping at W(1) and W(0), each worth one. It has five leaves. W(1) represents the unique remaining one-step completion, while W(0) represents the empty completion. Branches describe final jumps in reverse chronological order. The tree's repeated W(2) illustrates why naive recursion is inefficient; bottom-up iteration avoids repeated subproblems. The tree explains exact counting, not a need to enumerate the tree to compute the answer.'''
assert count_ways(4)==5 and count_ways(5)==8 and count_ways(10)==89
def leaves(n):
    return 1 if n<=1 else leaves(n-1)+leaves(n-2)
assert leaves(4)==5
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-024"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
assert all(x['path']!=source for x in q['sources'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-7a2882fc-6d69-4eaf-b52c-df40fc375c9a.png',root/source)
q['sources'].append({'type':'user_supplied_image','path':source,'received_on':'2026-09-28','role':'clarification_of_previous_explanation','note':'Screenshot of Fibonacci index explanation, not a new problem or company source.'})
q['media_assets'].append({'type':'source_image','path':source,'description':'User-supplied screenshot requesting clarification of the Fibonacci index offset.'})
q.setdefault('solution_extensions',[]).append({'key':'fibonacci-index-and-recursion-tree','content_he':he,'content_en':en,'recursion_tree_text':tree,'verification':'Examples W(4)=5, W(5)=8, W(10)=89 and five leaves checked in update_prep_024_recursion_tree.py.'})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==24 and all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-024')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n![צילום ההסבר שלגביו התבקשה הבהרה](../'+source+')\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
print('PREP-024 indexing explanation and full recursion tree saved; numeric examples and leaf count checked.')
