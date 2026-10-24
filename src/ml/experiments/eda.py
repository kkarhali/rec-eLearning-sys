"""Descriptive statistics of the development presentations (2013) + official reproduction of the
exploratory checks cited in the meeting records (task T1).

    python3 -m src.ml.experiments.eda

Outputs (results/dev2013/):
  eda_presentations.csv  one row per presentation (registrations, catalogue sizes, navigation
                         click share, duplicate rows, density, long tail, assessments)
  eda_windows.csv        per presentation × origin t ∈ {70,126,182} × exclusion set: repeat share
                         and unreachable share of the test window (t, t+14], density at t
  eda_peer_repro.csv     peer check 0.2 (FFF_2013J, cut day 100, 14-day window, Pop / Recent-Pop(14)
                         / Item-kNN cosine binary) under the peer's definitions and under the protocol's
  eda.md                 human-readable tables generated from the CSVs

The 2014 parts of the original checks (DDD_2014B, the 13 presentations of 2014) are *not*
reproduced: D-09 forbids touching the confirmatory presentations before the freeze.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from .. import data, metrics, splits
from ..models import ItemKNN, Pop, RecentPop
from ..signals import SignalSpec

OUT = data.RESULTS_DIR / "dev2013"
NAV3 = data.EXCLUSION_SETS["nav3"]


def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float("nan")
    cum = np.cumsum(x)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def presentation_row(p: data.PresentationData) -> dict:
    ev = p.events
    at = ev["activity_type"].astype(str)
    nav3 = at.isin(NAV3).to_numpy()
    e5 = at.isin(data.E5).to_numpy()
    e4 = at.isin(data.EXCLUSION_SETS["E4"]).to_numpy()
    clicks = ev["clicks"].to_numpy()
    tgt = ev.loc[~e5]
    pairs = tgt[["id_student", "id_site"]].drop_duplicates()
    U, I = pairs["id_student"].nunique(), pairs["id_site"].nunique()
    item_pop = pairs.groupby("id_site").size().sort_values(ascending=False).to_numpy()
    top = max(1, int(round(0.2 * len(item_pop))))
    a = p.assessments
    return {
        "presentation": p.name,
        "registrations": len(p.students),
        "registrations_with_vle": ev["id_student"].nunique(),
        "withdrawn_share": float((p.students["final_result"] == "Withdrawn").mean()),
        "sites_in_vle_table": len(p.items),
        "sites_with_logs": ev["id_site"].nunique(),
        "sites_nonnav_nav3": ev.loc[~nav3, "id_site"].nunique(),
        "sites_nonnav_E4": ev.loc[~e4, "id_site"].nunique(),
        "sites_nonnav_E5": I,
        "click_share_nav3": float(clicks[nav3].sum() / clicks.sum()),
        "click_share_E5": float(clicks[e5].sum() / clicks.sum()),
        "dup_group_share": float((ev["n_rows"] > 1).mean()),
        "dup_group_max_rows": int(ev["n_rows"].max()),
        "raw_rows": int(ev["n_rows"].sum()),
        "daily_rows": len(ev),
        "learners_E5": U,
        "density_full_E5": len(pairs) / (U * I),
        "top20pct_items_pair_share": float(item_pop[:top].sum() / item_pop.sum()),
        "gini_item_popularity": gini(item_pop),
        "assessments": len(a),
        "assessment_dates_missing": int(a["date"].isna().sum()),
        "length_days": p.length,
    }


def window_rows(p: data.PresentationData, cuts=splits.CUTS) -> list[dict]:
    rows = []
    for exclusion in ("E5", "E4", "none", "nav3"):
        for cut in cuts:
            tr, tg = splits.make_fold(p, cut, "test", exclusion)
            # peer definition: pairs of training learners on catalogue items
            reach = tg.target
            repeat = (reach & tr.seen).sum() / max(reach.sum(), 1)
            rows.append({"presentation": p.name, "exclusion": exclusion, "cut": cut,
                         "catalogue": tr.n_items, "learners_train": tr.n_users,
                         "density_at_t": float(tr.seen.mean()),
                         "window_pairs": tg.n_window_pairs,
                         "repeat_share": float(repeat),
                         "unreachable_share": tg.n_window_pairs_unreachable / max(tg.n_window_pairs, 1),
                         "evaluated_A": int(tg.task("A")[3].sum()), "evaluated_B": int(tg.task("B")[3].sum()),
                         "window_learners": tg.n_window_learners})
    return rows


PEER_REPORTED = {  # docs/meetings/2026-10-24-peer-position-dataset-and-algorithms.md §0.2 (FFF_2013J)
    ("none", "B"): {"Pop": (0.999, 0.603), "RecentPop14": (0.999, 0.629), "ItemKNN": (0.728, 0.164)},
    ("nav3", "B"): {"Pop": (0.768, 0.171), "RecentPop14": (0.941, 0.357), "ItemKNN": (0.723, 0.155)},
    ("nav3", "A"): {"Pop": (0.446, 0.119), "RecentPop14": (0.864, 0.418), "ItemKNN": (0.504, 0.141)},
}


def peer_reproduction(p: data.PresentationData, cut: int = 100) -> list[dict]:
    rows = []
    models = {"Pop": Pop(), "RecentPop14": RecentPop(w=14),
              "ItemKNN": ItemKNN(k=None, shrink=0.0, signal=SignalSpec("L0"))}
    for exclusion, task in (("none", "B"), ("nav3", "B"), ("nav3", "A"), ("E5", "B"), ("E5", "A")):
        tr, tg = splits.make_fold(p, cut, "test", exclusion)
        tgt, cand, unreach, ev = tg.task(task)
        rep = (tg.target & tr.seen).sum() / max(tg.target.sum(), 1)
        for name, m in models.items():
            S = m.fit(tr).score()
            for variant, un in (("protocol", unreach), ("peer_ignore_unreachable", np.zeros_like(unreach))):
                evm = ev if variant == "protocol" else tgt.any(axis=1)
                res = metrics.evaluate(S, cand, tgt, un, evm, tr.tiebreak, ks=(10,))
                s = metrics.summarize(res)
                reported = PEER_REPORTED.get((exclusion, task), {}).get(name, (np.nan, np.nan))
                rows.append({"presentation": p.name, "cut": cut, "exclusion": exclusion, "task": task,
                             "model": name, "evaluation": variant, "n_eval": res["n_eval"],
                             "catalogue": tr.n_items, "density": float(tr.seen.mean()),
                             "repeat_share": float(rep),
                             "unreachable_share": tg.n_window_pairs_unreachable / max(tg.n_window_pairs, 1),
                             "HR@10": s["HR@10"], "NDCG@10": s["NDCG@10"], "R@10": s["R@10"],
                             "peer_HR@10": reported[0], "peer_NDCG@10": reported[1]})
    return rows


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in r.values) + " |")
    return "\n".join(out)


def write_markdown(pres: pd.DataFrame, win: pd.DataFrame, peer: pd.DataFrame, out: Path) -> None:
    allc = pres.copy()
    md = ["# EDA — عروض التطوير 2013 (مولَّد آلياً بـ`python3 -m src.ml.experiments.eda`)\n",
          "> لا تُلمس عروض 2014 (D-09)، فلا يُعاد هنا الجزء الخاص بـDDD_2014B من فحص الزميل ولا عروض 2014 "
          "من فحص المشرف.\n",
          "## 1. لكل عرض\n",
          _md(allc[["presentation", "registrations", "registrations_with_vle", "withdrawn_share",
                    "sites_with_logs", "sites_nonnav_nav3", "sites_nonnav_E5", "click_share_nav3",
                    "click_share_E5", "dup_group_share", "density_full_E5", "top20pct_items_pair_share",
                    "gini_item_popularity", "assessment_dates_missing"]]) + "\n",
          "## 2. مجاميع 2013\n"]
    md.append(f"- تسجيلات لها سجلات VLE: {int(pres['registrations_with_vle'].sum()):,}.")
    md.append(f"- موارد غير تنقلية (تعريف المشرف nav3): {int(pres['sites_nonnav_nav3'].min())}–"
              f"{int(pres['sites_nonnav_nav3'].max())}؛ وبتعريف E الخماسي: {int(pres['sites_nonnav_E5'].min())}–"
              f"{int(pres['sites_nonnav_E5'].max())}.")
    md.append(f"- حصة نقرات التنقل (nav3) لكل عرض: {pres['click_share_nav3'].min():.1%}–"
              f"{pres['click_share_nav3'].max():.1%}؛ (E5): {pres['click_share_E5'].min():.1%}–"
              f"{pres['click_share_E5'].max():.1%} (المجموع المرجّح بالنقرات في القسم 5).")
    md.append(f"- كثافة مصفوفة (متعلم × مورد E5) على العرض كاملاً: {pres['density_full_E5'].min():.1%}–"
              f"{pres['density_full_E5'].max():.1%}.")
    md.append(f"- مجموعات (تسجيل، مورد، يوم) بأكثر من صف: {pres['dup_group_share'].min():.1%}–"
              f"{pres['dup_group_share'].max():.1%} (حتى {int(pres['dup_group_max_rows'].max())} صفوف).\n")
    w = win.groupby(["exclusion", "cut"])[["repeat_share", "unreachable_share", "density_at_t"]].agg(["mean", "min", "max"])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    md.append("## 3. نوافذ الاختبار (t, t+14] — متوسط/أدنى/أعلى عبر العروض التسعة\n")
    md.append(_md(w.reset_index()) + "\n")
    md.append("`repeat_share` = حصة أزواج (متعلم، مورد) في نافذة الاختبار التي زارها المتعلم قبل t "
              "(بين متعلمي التدريب وموارد الكتالوج، كتعريف الزميل).\n")
    md.append("## 4. إعادة إنتاج فحص الزميل 0.2 (FFF_2013J، قطع اليوم 100)\n")
    md.append(_md(peer[["exclusion", "task", "model", "evaluation", "n_eval", "catalogue", "repeat_share",
                        "HR@10", "NDCG@10", "peer_HR@10", "peer_NDCG@10"]]) + "\n")
    md.append("`exclusion`: none = كل الأنشطة؛ nav3 = استبعاد {homepage, subpage, page} كما في الفحص؛ "
              "E5 = تعريف البروتوكول. `task`: B = أي وصول، A = موارد جديدة. "
              "`evaluation`: protocol = الأهداف خارج الكتالوج إخفاق وكسر تعادل بمفاتيح ثابتة؛ "
              "peer_ignore_unreachable = تُهمل الأهداف خارج الكتالوج كما في سكربت الزميل.\n")
    (out / "eda.md").write_text("\n".join(md), encoding="utf-8")


def main():
    t = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    pres = data.load_dev_presentations()
    prow = pd.DataFrame([presentation_row(p) for p in pres.values()])
    # click-weighted totals over the nine presentations
    ev = data.load_daily_events("dev")
    at = ev["activity_type"].astype(str)
    tot = {
        "registrations_with_vle": int(ev.groupby("presentation", observed=True)["id_student"].nunique().sum()),
        "click_share_nav3": float(ev.loc[at.isin(NAV3), "clicks"].sum() / ev["clicks"].sum()),
        "click_share_E5": float(ev.loc[at.isin(data.E5), "clicks"].sum() / ev["clicks"].sum()),
        "dup_group_share": float((ev["n_rows"] > 1).mean()),
    }
    win = pd.DataFrame([r for p in pres.values() for r in window_rows(p)])
    peer = pd.DataFrame(peer_reproduction(pres["FFF_2013J"]))
    prow.to_csv(OUT / "eda_presentations.csv", index=False, float_format="%.6f")
    pd.DataFrame([tot]).to_csv(OUT / "eda_totals.csv", index=False, float_format="%.6f")
    win.to_csv(OUT / "eda_windows.csv", index=False, float_format="%.6f")
    peer.to_csv(OUT / "eda_peer_repro.csv", index=False, float_format="%.6f")
    write_markdown(prow, win, peer, OUT)
    with (OUT / "eda.md").open("a", encoding="utf-8") as f:
        f.write("\n## 5. eda_totals (مرجّح بالنقرات على عروض 2013 التسعة)\n\n")
        f.write(_md(pd.DataFrame([tot])) + "\n")
    print(f"[eda] done in {time.time() - t:.1f}s → {OUT}")


if __name__ == "__main__":
    main()
