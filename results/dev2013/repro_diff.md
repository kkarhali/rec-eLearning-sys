# repro_diff — إعادة إنتاج نتائج التطوير من ذاكرة مؤقتة فارغة (D-62 ش5)

**الحالة: مطابق** · بدأ 2026-10-25 18:42:03 · commit `20eeb9824030187de6f7ba847b4273dfaefb8144` · المدة 47.8 دقيقة

المقارنة حرفية بعد حجب الحقول المتقلبة وحدها (الأزمنة، والتواريخ، وhash الـcommit، والذاكرة، والسرعة): أعمدة CSV ['fit_score_seconds', 'maxrss_mb', 'seconds', 'seconds_total']، ومفاتيح JSON ['command', 'cpu_seconds', 'cpu_seconds_test', 'cpu_seconds_tune', 'date', 'git_commit', 'git_commit_at_freeze_run', 'git_commit_when_written', 'maxrss_mb', 'positions_per_second', 'seconds', 'seconds_total', 'wall_seconds'].

| الملف | النتيجة |
|---|---|
| `dev2013/ablation_meta.json` | مطابق |
| `dev2013/ablation_signals.csv` | مطابق |
| `dev2013/ablation_tuning.csv` | مطابق |
| `dev2013/baselines.csv` | مطابق |
| `dev2013/eda.md` | مطابق |
| `dev2013/eda_peer_repro.csv` | مطابق |
| `dev2013/eda_presentations.csv` | مطابق |
| `dev2013/eda_totals.csv` | مطابق |
| `dev2013/eda_windows.csv` | مطابق |
| `dev2013/folds.csv` | مطابق |
| `dev2013/gru.csv` | مطابق |
| `dev2013/gru_meta.json` | مطابق |
| `dev2013/gru_sanity.json` | مطابق |
| `dev2013/gru_sanity.md` | مطابق |
| `dev2013/gru_tuning.csv` | مطابق |
| `dev2013/h1_decomposition.csv` | مطابق |
| `dev2013/h4b.csv` | مطابق |
| `dev2013/hybrid.csv` | مطابق |
| `dev2013/hybrid_acceptance.md` | مطابق |
| `dev2013/hybrid_frozen.json` | مطابق |
| `dev2013/hybrid_meta.json` | مطابق |
| `dev2013/learner_analysis.md` | مطابق |
| `dev2013/learner_auc.csv` | مطابق |
| `dev2013/learner_clusters.csv` | مطابق |
| `dev2013/learner_fairness.csv` | مطابق |
| `dev2013/learner_h4a_summary.csv` | مطابق |
| `dev2013/learner_meta.json` | مطابق |
| `dev2013/mde80.json` | مطابق |
| `dev2013/mde80.md` | مطابق |
| `dev2013/repro_meta.json` | مطابق |
| `dev2013/run_meta.json` | مطابق |
| `dev2013/summary.md` | مطابق |
| `dev2013/timing.csv` | مطابق |
| `dev2013/tuning.csv` | مطابق |
| `frozen/freeze03_config.json` | مطابق |
| `frozen/risk_final.json` | مطابق |