# repro_diff — إعادة إنتاج نتائج التطوير من ذاكرة مؤقتة فارغة (D-62 ش5)

**الحالة: فروق** · بدأ 2026-10-24 22:26:26 · commit `62e26519276340f54a13f4d8baaafcede2486ed0` (شجرة src غير مُودَعة: يُعاد على commit نظيف قبل الوسم) · المدة 53.6 دقيقة

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
| `dev2013/hybrid_acceptance.md` | line 106: ¦ C7_ClusterPop + B5_SKNN ¦ 0.5560 ¦ 0.0004 ¦ → ¦ C7_ClusterPop + B7_WRMF ¦ 0.5529 ¦ 0.0005 ¦<br>line 107: ¦ C7_ClusterPop + B7_WRMF ¦ 0.5529 ¦ 0.0005 ¦ → ¦ C7_ClusterPop + B9_CBF ¦ 0.5480 ¦ 0.0007 ¦<br>line 108: ¦ C7_ClusterPop + B9_CBF ¦ 0.5480 ¦ 0.0007 ¦ → ¦ C7_ClusterPop + B5_SKNN ¦ 0.5560 ¦ 0.0004 ¦ |
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
| `dev2013/run_meta.json` | مطابق |
| `dev2013/summary.md` | line 166: ¦ B10_EASE ¦ 1.5 ¦ 5.9 ¦ 7.4 ¦ 550.0 ¦ → ¦ B10_EASE ¦ 2.0 ¦ 9.3 ¦ 11.3 ¦ 535.0 ¦<br>line 167: ¦ B1_Random ¦ 5.2 ¦ 1.0 ¦ 6.2 ¦ 550.0 ¦ → ¦ B1_Random ¦ 7.4 ¦ 1.6 ¦ 9.0 ¦ 535.0 ¦<br>line 168: ¦ B2_Pop ¦ 1.0 ¦ 0.9 ¦ 1.9 ¦ 550.0 ¦ → ¦ B2_Pop ¦ 1.4 ¦ 1.5 ¦ 2.9 ¦ 535.0 ¦<br>line 169: ¦ B3_RecentPop ¦ 1.0 ¦ 4.7 ¦ 5.7 ¦ 550.0 ¦ → ¦ B3_RecentPop ¦ 1.5 ¦ 7.1 ¦ 8.6 ¦ 535.0 ¦<br>line 170: ¦ B4_ItemKNN ¦ 1.5 ¦ 24.7 ¦ 26.2 ¦ 550.0 ¦ → ¦ B4_ItemKNN ¦ 2.0 ¦ 36.6 ¦ 38.6 ¦ 535.0 ¦<br>line 171: ¦ B5_SKNN ¦ 20.0 ¦ 162.6 ¦ 182.6 ¦ 550.0 ¦ → ¦ B5_SKNN ¦ 29.9 ¦ 233.7 ¦ 263.6 ¦ 535.0 ¦ |
| `dev2013/timing.csv` | مطابق |
| `dev2013/tuning.csv` | مطابق |
| `frozen/freeze03_config.json` | json content differs (non-volatile keys) |
| `frozen/risk_final.json` | json content differs (non-volatile keys) |