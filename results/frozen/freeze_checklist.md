# قائمة شروط وسم freeze-03 (D-62) — مولَّدة بـ`python3 -m src.ml.experiments.freeze_config --checklist`

الوقت: 2026-10-25 14:58:35

| # | الشرط | الحالة | الدليل | المسؤول |
|---|---|---|---|---|
| ش1 | run_hybrid بأرضية D-51 افتراضياً + الملفات | ✓ | results/dev2013/hybrid_frozen.json (floor_rule)، hybrid_acceptance.md | مهندس ML |
| ش2 | MDE80 لـH1 بالـHYB* الجديد | ✓ | results/dev2013/mde80.md (H1 = 0.0375) | مهندس ML |
| ش3 | الهجين على B؛ M1 افتراضياً؛ وسم «منحلّ»؛ H2-ب غير منطبقة | ✓ | hybrid.csv (task B)، serving.py (risk_model="M1")، stats.cluster_bootstrap_t + اختبار، hybrid_frozen.json (H2b) | مهندس ML |
| ش4 | نماذج الخطر النهائية | ✓ | results/frozen/risk_final.json | مهندس ML |
| ش5 | reproduce_dev + repro_diff.md على commit نظيف | ✗ | results/dev2013/repro_diff.md، repro_meta.json (commit 62e2651927، src_dirty=True) | مهندس ML |
| ش6 | freeze03_config.json + SHA-256 | ✓ | results/frozen/freeze03_config.json | مهندس ML |
| ش7 | run_confirmatory + تشغيل جاف كامل على 2013 | ✗ | results/dryrun2013/run_meta.json (status=None، audit_2014.ok=None، guard_rehearsal=None، resume_simulation.ok=None، commit None)، dryrun_vs_dev max |Δ| = None (≤ 1e-6، عدا λ) | مهندس ML |
| ش8 | مراجعة الزميل وتوقيعه | ✗ | docs/meetings/*peer* | الزميل الباحث |
| ش9 | تحديث الوثيقة 02 بالملحق ب وREADME | ✓ | docs/working/02-hypotheses-algorithms.md، src/ml/README.md | مصمّم الفرضيات + مهندس ML |
| ش10 | تحقق المشرف وتوقيعه ثم الوسم | ✗ | §8 من محضر الاجتماع 03؛ git tag freeze-03 | المشرف ← مهندس ML |

## SHA-256
- `freeze03_config.json`: `d80ad472e015da8f190fb96e0b761aa0726d435aabb940758166447d9ec4d2c4`
- `mde80.json`: `607468aeab296da35fae7e047b502d52c1ee919b26cb00cf8415cb6a9b81e88a`
- `hybrid_frozen.json`: `cdfb3b553a8ebc1ef555da0247b8f482708f4fdd77bc8df7f9ea80dc668a0c0e`
- `risk_final.json`: `76857226775c233b67cb67057ae3bf0c70ed11ff1622ec48dcdde1ef37c2a189`