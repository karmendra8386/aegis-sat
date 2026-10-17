# Eval summary — harness run, N=100 per scenario per setup (Week 3 model)

| Setup | Unsafe executed | Full recovery % | Safe recovery % | Survived % | Lost % | Escalations (approved/denied) |
|---|---|---|---|---|---|---|
| A · Rule-only FDIR | 0 | 33% | 33% | 33% | 0% | 0 (0/0) |
| B · Unguarded agent | 75 | 88% | 0% | 12% | 0% | 0 (0/0) |
| C · Guarded agent (AEGIS-Sat) | 0 | 67% | 33% | 0% | 0% | 659 (461/172) |

Harness validation only (behaviour-model agent, seeded, delayed ground-reply model). Not paper results.
