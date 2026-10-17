# OPS-SAT-AD telemetry anchoring (ESA OPS-SAT, real telemetry)

- Dataset: OPSSAT-AD, Zenodo DOI 10.5281/zenodo.12588359 — 2,123 segments over 9 telemetry channels (434 anomalous / 1689 nominal), plus 303,493 labelled points from the anomalous segments.
- Anomalous segment duration: median 266s, max 1115s — real faults persist for minutes, which is why the harness uses multi-step episodes with delayed ground replies rather than single-shot decisions.

## Simple explainable detector (logistic regression, 8 segment features)

- Trained on the dataset's train split only (1594 segments), tested on its test split (529).
- Test AUC: 0.887
- At threshold 0.5: detection 66/113 anomalous segments (58%), false alarms 9/416 nominal (2.2%).

Reading: a one-page, fully explainable detector already separates
most expert-labelled anomalies on real telemetry. AEGIS-Sat's claim
is not the detector — it is what happens after detection: policy
tiers, the context-adaptive envelope, ground escalation, and the
tamper-evident audit ledger.
