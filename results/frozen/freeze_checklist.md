# قائمة شروط وسم freeze-03 (D-62) — مولَّدة بـ`python3 -m src.ml.experiments.freeze_config --checklist`

الوقت: 2026-10-24 23:20:04

| # | الشرط | الحالة | الدليل | المسؤول |
|---|---|---|---|---|
| ش1 | run_hybrid بأرضية D-51 افتراضياً + الملفات | ✓ | results/dev2013/hybrid_frozen.json (floor_rule)، hybrid_acceptance.md | مهندس ML |
| ش2 | MDE80 لـH1 بالـHYB* الجديد | ✓ | results/dev2013/mde80.md (H1 = 0.0375) | مهندس ML |
| ش3 | الهجين على B؛ M1 افتراضياً؛ وسم «منحلّ»؛ H2-ب غير منطبقة | ✓ | hybrid.csv (task B)، serving.py (risk_model="M1")، stats.cluster_bootstrap_t + اختبار، hybrid_frozen.json (H2b) | مهندس ML |
| ش4 | نماذج الخطر النهائية | ✓ | results/frozen/risk_final.json | مهندس ML |
| ش5 | reproduce_dev + repro_diff.md | ✗ | results/dev2013/repro_diff.md | مهندس ML |
| ش6 | freeze03_config.json + SHA-256 | ✓ | results/frozen/freeze03_config.json | مهندس ML |
| ش7 | run_confirmatory + تشغيل جاف كامل على 2013 | ✗ | src/ml/experiments/run_confirmatory.py، results/dryrun2013/ | مهندس ML |
| ش8 | مراجعة الزميل وتوقيعه | ✗ | docs/meetings/*peer* | الزميل الباحث |
| ش9 | تحديث الوثيقة 02 بالملحق ب وREADME | ✓ | docs/working/02-hypotheses-algorithms.md، src/ml/README.md | مصمّم الفرضيات + مهندس ML |
| ش10 | تحقق المشرف وتوقيعه ثم الوسم | ✗ | §8 من محضر الاجتماع 03؛ git tag freeze-03 | المشرف ← مهندس ML |

## SHA-256
- `freeze03_config.json`: `74af801381404e92c7f855c1373b1d6f81c5ab2017187f9371edd055e8dbd535`
- `mde80.json`: `607468aeab296da35fae7e047b502d52c1ee919b26cb00cf8415cb6a9b81e88a`
- `hybrid_frozen.json`: `de7960ac999f2585c2cb8b7ca15d43e405e4757794dee7656f6d2d7c1389a3b9`
- `risk_final.json`: `d8b188be0c58f08a9371f87f9bbd637ac8de1ad952d7c08f31c1e60a1511e841`