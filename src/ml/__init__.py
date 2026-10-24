"""Experimental harness for the thesis «نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم».

Package layout (see src/ml/README.md):
    data      — OULAD loading, duplicate aggregation (D-06), exclusion set E (D-07), day baskets
    signals   — nested implicit-signal family L0 ⊂ L1 ⊂ L2 ⊂ L3 and WRMF confidence (ADR-002 §3.2)
    splits    — global temporal cuts t ∈ {70,126,182}, tune/test phases, tasks A/B (D-14)
    metrics   — P/R/HR/NDCG/MRR@K, Coverage@K, PopBias@K on the full catalogue
    models/   — baselines B1–B9 behind one interface (fit / score / recommend)
    hybrid    — linear rank fusion of ≤ 4 components + acceptance rule (D-11)
    stats     — cluster bootstrap, exact sign-flip test, Holm, D-15 verdict
    experiments/ — eda, run_baselines (development presentations 2013 only; D-09)

Everything is numpy/pandas only and deterministic (fixed seeds).
"""

__version__ = "0.1.0"
