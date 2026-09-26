# Performance and multi-user night — 26 September 2026

Working notes, filled in as the night goes; `backend/STATUS.md` §5n has the summary.

## 1. Before any change (`scripts/latency_bench.py --label before`, commit a9d8643)

Real model (Opus 5 evaluator, Sonnet 5 prose, tip polished), real database from Shaked's machine (Supabase
Session pooler, one connection, everything rolled back), production rules. Five answers: an English weak answer
that gets a follow-up, the follow-up answer, an English strong answer, a Hebrew strong answer, a Python answer
run against its code tests.

```
  en weak (follow-up)              band WEAK     grade  17.8 s   all  17.8 s   progress  4259 ms   (28 + 33 statements)
  en weak (follow-up) → follow-up  band WEAK     grade   7.9 s   all   7.9 s   progress  1813 ms   (24 + 20 statements)
  en strong                        band PARTIAL  grade  16.4 s   all  16.4 s   progress  1900 ms   (30 + 20 statements)
  he strong                        band STRONG   grade  37.0 s   all  37.0 s   progress  1922 ms   (29 + 20 statements)
  code (python)                    band STRONG   grade  16.8 s   all  16.8 s   progress  1893 ms   (27 + 20 statements)
```

### before: 5 answers

| stage | median | max | n |
|---|---:|---:|---:|
| load | 0.67 s | 1.15 s | 5 |
| accept+save | 0.45 s | 0.60 s | 5 |
| check | 0.07 s | 0.14 s | 2 |
| evaluator | 5.01 s | 5.96 s | 5 |
| card | 6.92 s | 12.19 s | 4 |
| tip | 0.00 s | 2.21 s | 5 |
| follow-up | 7.96 s | 27.80 s | 4 |
| next question | 1.11 s | 1.28 s | 5 |
| outcome save | 1.29 s | 2.58 s | 5 |
| grade known | 16.80 s | 36.97 s | 5 |
| all feedback | 16.80 s | 36.97 s | 5 |
| progress | 1.90 s | 4.26 s | 5 |
| program | 1.01 s | 1.09 s | 5 |
| db statements (submit) | 28 | 30 | 5 |
| db statements (progress) | 20 | 33 | 5 |

| answer | band | grade known | all feedback | evaluator | progress |
|---|---|---:|---:|---:|---:|
| en weak (follow-up) | WEAK | 17.8 s | 17.8 s | 5.0 s | 4259 ms |
| en weak (follow-up) → follow-up | WEAK | 7.9 s | 7.9 s | 4.7 s | 1813 ms |
| en strong | PARTIAL | 16.4 s | 16.4 s | 5.6 s | 1900 ms |
| he strong | STRONG | 37.0 s | 37.0 s | 6.0 s | 1922 ms |
| code (python) | STRONG | 16.8 s | 16.8 s | 4.6 s | 1893 ms |
