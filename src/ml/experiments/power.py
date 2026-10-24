"""MDE80 per hypothesis from its own development pair (D-46, D-48) → results/dev2013/mde80.md (+ .json).

    python3 -m src.ml.experiments.power

σ = SD across the nine development presentations of Δ_p for the actual pair, on the 2013 test windows:
  H1   HYB* (frozen) − B_np*                         (hybrid_meta.json)
  H2-a WRMF(W*) − WRMF(binary)                      (ablation_signals.csv)
  H3   GRU-lite − S* (best non-neural sequential)    (gru.csv, baselines.csv)
  H4-a AUC(M1) − AUC(M0), leave-one-presentation-out (learner_h4a_summary.csv)
MDE80 = smallest true mean with confirmation probability ≥ 0.8 under the full one-sided rule on 13
confirmatory presentations with the strictest Holm factor (4) — ``stats.mde80``. σ from 9 units is approximate.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .. import data, stats

OUT = data.RESULTS_DIR / "dev2013"
DELTA = 0.02


def pres_means(df, model, metric="NDCG@10", **filt):
    r = df[(df["model"] == model) & (df["task"] == "A") & (df["slice"] == "all")]
    for k, v in filt.items():
        r = r[r[k] == v]
    return r.groupby(["presentation", "cut"])[metric].mean().groupby("presentation").mean().sort_index()


def main():
    rows = []
    hm = json.loads((OUT / "hybrid_meta.json").read_text()) if (OUT / "hybrid_meta.json").exists() else None
    if hm:
        rows.append(("H1", "HYB* (floor ≥ 1/4, D-51) − B_np* = B3", hm["sd_H1"], hm["H1"]["mean"]))
    if (OUT / "ablation_signals.csv").exists():
        ab = pd.read_csv(OUT / "ablation_signals.csv")
        d = (pres_means(ab, "B7_WRMF", variant="Wstar") - pres_means(ab, "B7_WRMF", variant="L0")).to_numpy()
        rows.append(("H2-a", "WRMF(W*) − WRMF(binary)", float(np.std(d, ddof=1)), float(d.mean())))
    if (OUT / "gru.csv").exists():
        g, b = pd.read_csv(OUT / "gru.csv"), pd.read_csv(OUT / "baselines.csv")
        nn = max(("B5_SKNN", "B6_Markov"), key=lambda m: pres_means(b, m).mean())
        d = (pres_means(g, "GRU_lite") - pres_means(b, nn)).to_numpy()
        rows.append(("H3", f"GRU-lite − {nn}", float(np.std(d, ddof=1)), float(d.mean())))
    if (OUT / "learner_meta.json").exists():
        lm = json.loads((OUT / "learner_meta.json").read_text())
        s = pd.read_csv(OUT / "learner_h4a_summary.csv")
        r = s[(s["cut"] == 56) & s["overlap_excluded"] & (s["comparison"] == "M1 − M0")].iloc[0]
        rows.append(("H4-a", "AUC(M1) − AUC(M0)", float(lm["sigma_H4a"]), float(r["delta"])))
    out = []
    for h, pair, sd, dev_mean in rows:
        m80 = stats.mde80(sd, n=13, delta=DELTA, n_sim=1000, n_boot=2000)
        out.append({"hypothesis": h, "pair": pair, "sigma_dev": sd, "dev_mean_delta": dev_mean, "MDE80": m80,
                    "MDE80_over_delta": m80 / DELTA, "MDE80_gt_2delta": bool(m80 > 2 * DELTA),
                    "power_at_delta": stats.confirmation_power(DELTA, sd, n=13),
                    "power_at_1.5delta": stats.confirmation_power(1.5 * DELTA, sd, n=13),
                    "power_at_2delta": stats.confirmation_power(2 * DELTA, sd, n=13)})
    df = pd.DataFrame(out)
    (OUT / "mde80.json").write_text(json.dumps(out, indent=2))
    md = ["# MDE80 لكل فرضية (D-46، D-48) — مولَّد بـ`python3 -m src.ml.experiments.power`\n",
          "σ = انحراف Δ_p عبر عروض التطوير التسعة لزوج الفرضية الفعلي على نوافذ اختبار 2013 (H4-أ: AUC بترك عرض خارج "
          "التدريب). MDE80 = أصغر أثر حقيقي باحتمال تأكيد ≥ 0.8 بالقاعدة الكاملة (Δ̄ ≥ δ، حد bootstrap-t الأدنى > 0، "
          "4·p < 0.05) على 13 عرضاً تأكيدياً (`stats.mde80`، 1000 محاكاة × 2000 إعادة). σ مقدَّر من 9 وحدات فهو تقريبي. "
          "δ = 0.02 (δ_AUC = 0.02 لـH4-أ) **لا يتغير** (D-48).\n",
          "| الفرضية | الزوج | σ (تطوير) | Δ̄ تطوير | MDE80 | MDE80/δ | قوة عند δ | عند 1.5δ | عند 2δ | MDE80 > 2δ |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in out:
        md.append(f"| {r['hypothesis']} | {r['pair']} | {r['sigma_dev']:.4f} | {r['dev_mean_delta']:+.4f} | "
                  f"**{r['MDE80']:.4f}** | {r['MDE80_over_delta']:.2f} | {r['power_at_delta']:.2f} | "
                  f"{r['power_at_1.5delta']:.2f} | {r['power_at_2delta']:.2f} | {'نعم' if r['MDE80_gt_2delta'] else 'لا'} |")
    md += ["", "**النص المسجل مسبقاً لحكم «غير حاسمة» (D-48):** «غير حاسمة: لا يكشف التصميم بقوة 80% أثراً أصغر من "
           "MDE80 = x»، حيث x من هذا الجدول للفرضية المعنية. وحيث MDE80 > 2δ يُكتب صراحة أن التصميم لا يكشف إلا آثاراً كبيرة.",
           "", "يُكتب هذا الجدول قبل التجميد، ولا أثر له على δ أو قاعدة الحكم (D-61). للسجل: قيمة H1 بالأرضية الاسمية قبل "
           "D-51 كانت 0.0375 (σ = 0.0344) وأُبطلت. بديل B5−B3 التوضيحي لا يدخل هنا (D-46). ممنوع إعادة حسابه من بيانات 2014."]
    (OUT / "mde80.md").write_text("\n".join(md), encoding="utf-8")
    print(df.to_string())


if __name__ == "__main__":
    main()
