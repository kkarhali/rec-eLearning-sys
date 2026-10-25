# التشغيل الجاف مقابل نتائج التطوير

| file | metric | rows_compared | max_abs_diff | note |
|---|---|---|---|---|
| baselines.csv | NDCG@10 | 3780 | 0.0000 | nan |
| baselines.csv | HR@10 | 3780 | 0.0000 | nan |
| gru.csv | NDCG@10 | 1080 | 0.0000 | nan |
| gru.csv | HR@10 | 1080 | 0.0000 | nan |
| hybrid.csv HYB* A | NDCG@10 | 27 | 0.0000 | nan |
| hybrid.csv HYB* B | NDCG@10 | 27 | 0.0000 | nan |
| hybrid.csv HYB_accept_only A | NDCG@10 | 27 | 0.0000 | nan |
| hybrid.csv HYB_accept_only B | NDCG@10 | 27 | 0.0000 | nan |
| hybrid.csv HYB_nominal_floor A | NDCG@10 | 27 | 0.0000 | nan |
| ablation_signals.csv | NDCG@10 | 3240 | 0.0000 | nan |
| h4a_auc.csv vs learner_auc.csv (day 56) | ROC_AUC | 45 | 0.0036 | dev: λ chosen by nested inner LOPO per held-out presentation; dry run: frozen λ (D-58) |
