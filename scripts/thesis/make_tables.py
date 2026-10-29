#!/usr/bin/env python3
"""Generate the Markdown tables of thesis section 5-8 and appendix D from results/conf2014/.

Every number printed here is read from a result file; nothing is typed by hand.
Each table title names its source file(s) and its provenance tag (locked / phase 2).
results/ is read only. Output: deliverables/06-final-thesis/tables/ (one .md per table,
figures.txt with figure blocks, CHECKS.txt with the cross-checks).

Usage (from anywhere):  python3 scripts/thesis/make_tables.py
"""
import hashlib, json, os, re, sys
from collections import defaultdict
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = os.path.join(ROOT, "results", "conf2014")
DEV = os.path.join(ROOT, "results", "dev2013")
OUT = os.path.join(ROOT, "deliverables", "06-final-thesis", "tables")
os.makedirs(OUT, exist_ok=True)
CHECKS = []

MODEL_AR = {
    "B1_Random": "B1 العشوائي", "B2_Pop": "B2 الشعبية", "B3_RecentPop": "B3 الشعبية الآنية",
    "B4_ItemKNN": "B4 التصفية بالعناصر", "B5_SKNN": "B5 الجيران على السلال", "B6_Markov": "B6 ماركوف",
    "B7_WRMF": "B7 WRMF", "B8_PersonalRepeat": "B8 الإعادة الشخصية", "B9_CBF": "B9 التصفية بالمحتوى",
    "B10_EASE": "B10 EASE (مرجعي)", "GRU_lite": "GRU-lite", "HYB*": "الهجين المجمَّد HYB\\*",
    "HYB_accept_only": "الهجين بقاعدة القبول وحدها", "HYB_nominal_floor": "الهجين بالأرضية الاسمية",
    "C7_ClusterPop": "شعبية العنقود", "M0": "M0 (مجموع النقرات)", "M1": "M1 (ملامح السلوك)",
    "M2": "M2 (السلوك والأكاديميا)", "CART_M2": "CART على ملامح M2", "majority": "الفئة الغالبة",
    "M2 (appendix)": "M2 (السلوك والأكاديميا)",
}
HYP_AR = {"H1": "H1", "H2-a": "H2-أ", "H3": "H3", "H4-a": "H4-أ"}
ATTR_AR = {"gender": "الجنس", "disability": "الإعاقة", "imd_band": "مؤشر الحرمان", "age_band": "الفئة العمرية"}
GROUP_AR = {"F": "أنثى", "M": "ذكر", "N": "لا", "Y": "نعم", "0-35": "0–35", "35-55": "35–55", "55<=": "55 فأكثر"}
VARIANT_AR = {"L0": "L0 ثنائية", "L1": "L1 عدد الأيام", "L2": "L2 الأيام مع الحداثة",
              "L3": "L3 مع الشدة المطبَّعة", "Wstar": "W\\* العائلة الموزونة"}


def num(x, d=4, sign=False):
    if x is None or (isinstance(x, float) and pd.isna(x)) or x == "":
        return "—"
    x = float(x)
    s = f"{abs(x):.{d}f}"
    if x != 0 and float(s) == 0:  # avoid printing ±0.0000 for tiny non-zero values
        s = f"{abs(x):.{d + 1}f}"
    if x < 0:
        return "−" + s
    return ("+" + s) if sign else s


def ci(lo, hi, d=4, sign=True):
    return f"[{num(lo, d, sign)}، {num(hi, d, sign)}]"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


LOCKED = set(json.load(open(os.path.join(R, "LOCK")))["files"])
TAG_LOCKED = "(مقفل)"
TAG_P2 = "(ثانوي، الطور الثاني؛ مرجعه إيداع النتائج)"
TAG_META = "(سجل التشغيل، خارج القفل؛ مرجعه إيداع النتائج)"
SOURCES = {
    "t-5-8-1a": None, "t-5-8-1b": ["folds.csv"], "t-5-8-1c": ["hybrid_2014.json"], "t-D-1": ["hybrid_2014.json"],
    "t-5-18": ["verdicts.csv"], "t-5-19": ["per_presentation.csv"], "t-5-20a": ["h1_decomposition.csv"],
    "t-5-20b": ["per_origin.csv"], "t-5-21": ["ablation_signals.csv"],
    "t-5-22a": ["summary.md", "h4a_auc.csv"], "t-5-22b": ["secondary.csv"], "t-5-22c": ["secondary.csv"],
    "t-5-23": ["h4b.csv"], "t-5-24a": ["summary.md", "baselines.csv", "gru.csv", "hybrid.csv"],
    "t-5-24b": ["summary.md", "baselines.csv", "gru.csv", "hybrid.csv"],
    "t-5-8-8a": ["sensitivity_E4.csv", "sensitivity_none.csv"], "t-5-8-8b": ["sensitivity_other.csv"],
    "t-5-8-8c": ["ablation_components.csv"], "t-5-8-8d": ["protocol_sampled.csv"],
    "t-D-2": ["intervals_appendix.csv"], "t-5-8-9a": ["fairness.csv"], "t-5-8-9b": ["fairness.csv"],
    "t-D-3": ["fairness.csv"], "t-D-4": ["fairness.csv"],
}


def prov(files):
    if files is None:
        return TAG_META
    return TAG_LOCKED if all(f in LOCKED for f in files) else TAG_P2


def write(name, title, body, note=None):
    if name == "t-D-2":
        title = title.replace(" (المصدر:", " (عمود الحكم مقفل؛ الفاصلان البديلان ثانويان، الطور الثاني؛ مرجعهما إيداع النتائج) (المصدر:", 1)
    elif name in SOURCES:
        tag = prov(SOURCES[name])
        m = re.search(r"\(ثانوي[،]? ?([^)]*)\)", title)
        if tag == TAG_P2 and m:
            rest = m.group(1).strip("، ")
            merged = "(ثانوي، الطور الثاني؛ مرجعه إيداع النتائج" + (f"؛ {rest}" if rest else "") + ")"
            title = title.replace(m.group(0), merged, 1)
        else:
            title = title.replace(" (المصدر:", f" {tag} (المصدر:", 1)
    elif name == "t-D-5":
        title = title.replace(" (المصدر:", " (حالة كل صف في عمود القفل) (المصدر:", 1)
    text = f"**{title}**\n\n{body}\n"
    if note:
        text += f"\n{note}\n"
    with open(os.path.join(OUT, name + ".md"), "w", encoding="utf-8") as f:
        f.write(text)


def check(label, a, b, tol=5e-5):
    ok = abs(float(a) - float(b)) <= tol
    CHECKS.append(f"{'OK ' if ok else 'BAD'} {label}: {a} vs {b}")
    if not ok:
        raise SystemExit(f"cross-check failed: {label}: {a} vs {b}")


def agg(df, value, by=("model",)):
    """Mean over seeds within (presentation, cut), then over cuts, then over presentations."""
    by = list(by)
    a = df.groupby(by + ["presentation", "cut"], dropna=False)[value].mean().reset_index()
    a = a.groupby(by + ["presentation"], dropna=False)[value].mean().reset_index()
    return a


def mean_over_pres(df, value, by=("model",)):
    return agg(df, value, by).groupby(list(by), dropna=False)[value].agg(["mean", "std", "count"])


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# ---------------------------------------------------------------- 5-8-1 run properties
meta = json.load(open(os.path.join(R, "run_meta.json")))
lock = json.load(open(os.path.join(R, "LOCK")))
dev_text = open(os.path.join(R, "deviations.md"), encoding="utf-8").read()
dev_body = [l.strip() for l in dev_text.splitlines() if l.strip() and not l.startswith("#")]
rows = [
    ("وسم نسخة التجميد ونسخة الشيفرة", f"`{meta['tag']}`، `{meta['commit'][:7]}`"),
    ("حالة التشغيل", meta["status"]),
    ("العروض", f"{len(meta['presentations'])} عرضاً من 2014"),
    ("بصمة SHA-256 لملف الإعداد المجمَّد", f"`{meta['frozen_config_sha256'][:12]}…`"),
    ("مطابقة بصمات MD5 للجداول الخام السبعة للقيم المجمَّدة", "نعم" if meta["raw_md5_match_frozen"] else "لا"),
    ("الملفات المقفلة في نهاية الطور الأول", f"{len(lock['files'])} ملفاً"),
    ("بصمة SHA-256 لملف القفل نفسه", f"`{sha256(os.path.join(R, 'LOCK'))[:8]}…`"),
    ("بصمة SHA-256 لتقرير الأحكام", f"`{lock['verdicts_md_sha256'][:8]}…`"),
    ("بصمة SHA-256 لجدول الأحكام", f"`{lock['verdicts_csv_sha256'][:8]}…`"),
    ("وقت كتابة القفل", lock.get("time", "—").replace("T", " ")),
    ("زمن الطور الأول (الأحكام)", f"{meta['phase1_seconds']/60:.1f} دقيقة"),
    ("زمن الطور الثاني (الثانوي والاستكشافي)", f"{meta['phase2_seconds']/60:.1f} دقيقة"),
    ("الزمن الكلي في استدعاء واحد", f"{meta['wall_seconds']/60:.1f} دقيقة"),
    ("وقت الاكتمال", meta["date"]),
    ("سجل الانحرافات", " ".join(dev_body)),
    ("استئناف", "لا" if "resume" not in meta else "نعم"),
    ("الإصدارات", f"Python {meta['python']}، numpy {meta['numpy']}، pandas {meta['pandas']}، {meta['workers']} عمليات"),
]
write("t-5-8-1a", "جدول 5-8-أ: خصائص التشغيل التأكيدي (المصدر: run_meta.json وLOCK وdeviations.md)",
      table(["الخاصية", "القيمة"], rows))

folds = pd.read_csv(os.path.join(R, "folds.csv"))
g = folds.groupby("presentation")
rows = []
for p, d in g:
    rows.append((p, f"{int(d.catalogue.min())}–{int(d.catalogue.max())}", num(d.density.mean(), 3),
                 f"{int(d.n_eval_A.sum()):,}", f"{int(d.n_eval_B.sum()):,}", num(d.unreachable_share.max(), 3)))
rows.append(("المجموع / المدى", f"{int(folds.catalogue.min())}–{int(folds.catalogue.max())}",
             f"{num(folds.density.min(),3)}–{num(folds.density.max(),3)}", f"{int(folds.n_eval_A.sum()):,}",
             f"{int(folds.n_eval_B.sum()):,}", num(folds.unreachable_share.max(), 3)))
write("t-5-8-1b", f"جدول 5-8-ب: خصائص الطيّات لكل عرض على نقاط القطع الثلاث، {len(folds)} طيّة (المصدر: folds.csv)",
      table(["العرض", "حجم الكتالوج (مدى)", "متوسط الكثافة", "المقيَّمون، المهمة A", "المقيَّمون، المهمة B",
             "أعلى حصة أهداف غير قابلة للوصول"], rows))

hyb = json.load(open(os.path.join(R, "hybrid_2014.json")))
wf = hyb["weights_by_fold"]
cnt = defaultdict(int)
for k, w in wf.items():
    cnt[tuple(sorted(w.items()))] += 1
rows = []
for w, c in sorted(cnt.items(), key=lambda kv: -kv[1]):
    d = dict(w)
    rows.append((num(d.get("C7_ClusterPop", 0), 2), num(d.get("B5_SKNN", 0), 2), c))
write("t-5-8-1c", f"جدول 5-8-ج: توزيع أوزان الهجين المضبوطة على الطيّات الـ{len(wf)} داخل الفضاء المجمَّد (المصدر: hybrid_2014.json)",
      table(["وزن شعبية العنقود", "وزن الجيران على السلال (الأرضية ≥ 0.25)", "عدد الطيّات"], rows))
rows = [(k.rsplit("_", 1)[0], k.rsplit("_", 1)[1], num(w.get("C7_ClusterPop", 0), 2), num(w.get("B5_SKNN", 0), 2))
        for k, w in wf.items()]
write("t-D-1", f"جدول د-1: الأوزان المضبوطة للهجين لكل (عرض، نقطة قطع)، {len(wf)} طيّة (المصدر: hybrid_2014.json)",
      table(["العرض", "نقطة القطع", "وزن شعبية العنقود", "وزن الجيران على السلال"], rows))

# ---------------------------------------------------------------- 5-18 verdicts
v = pd.read_csv(os.path.join(R, "verdicts.csv"))
def verdict_ar(r):
    if r.verdict == "confirmed":
        return "**مؤكَّدة** (بهامش)" if str(r.confirmed_with_margin) == "True" else "**مؤكَّدة**"
    if r.verdict == "inconclusive":
        return "**غير حاسمة**"
    if r.verdict == "refuted":
        return "**مدحوضة للتفوق**¹" if r.hypothesis == "H3" else "**مدحوضة عملياً** (استُبعد أثر ≥ δ)"
    if r.verdict == "refuted_reverse":
        return "**مدحوضة عكسياً**"
    return r.verdict
rows = []
for r in v.itertuples():
    rows.append((HYP_AR[r.hypothesis], r.n, num(r.mean_delta, 4, True), ci(r.ci_lo, r.ci_hi),
                 "نعم" if str(r.degenerate) == "True" else "لا", num(r.p, 4), num(r.p_holm, 4),
                 f"{r.n_delta_pos}/{r.n}", num(r.p_margin, 4), num(r.delta, 2), verdict_ar(r)))
d48 = v[v.D48_text.notna()]
note = "¹ يطبع تقرير الأحكام لهذا الصف النص العام «مدحوضة عملياً (استُبعد أثر ≥ δ)»، والشرط واحد: الحد الأعلى < δ."
for r in d48.itertuples():
    note += f"\n\nالنص المسجل الملحق بـ{HYP_AR[r.hypothesis]}: «{r.D48_text}»."
write("t-5-18", "جدول 5-18: أحكام الفرضيات الرئيسية على عروض 2014، عائلة هولم بأربع فرضيات (المصدر: verdicts.csv)",
      table(["الفرضية", "n", "متوسط الفرق Δ̄", "فاصل bootstrap-t 95%", "فاصل منحلّ", "p الخام (قلب الإشارات)",
             "p بعد هولم", "عروض Δ > 0", "p الهامش (Δ − δ)", "δ", "الحكم"], rows), note)

# ---------------------------------------------------------------- 5-19 per presentation
pp = pd.read_csv(os.path.join(R, "per_presentation.csv"))
hyps = [c for c in pp.columns if c != "presentation"]
rows = [[r["presentation"]] + [num(r[h], 4, True) for h in hyps] for _, r in pp.iterrows()]
rows.append(["عروض Δ > 0"] + [f"{int((pp[h] > 0).sum())}/{len(pp)}" for h in hyps])
rows.append(["المتوسط"] + [num(pp[h].mean(), 4, True) for h in hyps])
for h in hyps:
    check(f"per_presentation mean {h}", pp[h].mean(), v.set_index("hypothesis").loc[h, "mean_delta"], 2e-6)
write("t-5-19", "جدول 5-19: الفرق لكل عرض للفرضيات الأربع، 2014 (المصدر: per_presentation.csv)",
      table(["العرض"] + [HYP_AR[h] + (" (AUC)" if h == "H4-a" else " (NDCG@10)") for h in hyps], rows))

# ---------------------------------------------------------------- 5-20 secondary H1
dec = pd.read_csv(os.path.join(R, "h1_decomposition.csv"))
DEC_AR = {"(a)": "(أ) الهجين المجمَّد − الهجين غير الشخصي (الشعبية الآنية وقرب التقييم)",
          "(b)": "(ب) شعبية العنقود منفردة − الشعبية الآنية [مكسب التقسيم]",
          "(c)": "(ج) الهجين المجمَّد − شعبية العنقود منفردة [مكسب الشخصنة]",
          "(d)": "(د) الهجين بالأرضية الاسمية − الشعبية الآنية"}
rows = [(DEC_AR[r.component[:3]], num(r.mean, 4, True), ci(r.ci_lo, r.ci_hi), num(r.p, 4), f"{r.n_pos}/{r.n}")
        for r in dec.itertuples()]
write("t-5-20a", "جدول 5-20-أ: التفكيك الوصفي لفرق H1، 2014 (ثانوي، خارج عائلة هولم، p غير مصحَّحة) (المصدر: h1_decomposition.csv)",
      table(["المكوّن", "متوسط الفرق", "فاصل bootstrap-t 95%", "p غير مصحَّحة", "عروض الفرق فيها موجب"], rows))
po = pd.read_csv(os.path.join(R, "per_origin.csv"))
piv = po.pivot(index="cut", columns="hypothesis", values="mean_delta")
rows = [[f"اليوم {c}"] + [num(piv.loc[c, h], 4, True) for h in piv.columns] for c in piv.index]
write("t-5-20b", "جدول 5-20-ب: متوسط الفرق لكل نقطة قطع منفردة، 2014 (ثانوي وصفي، بلا فاصل) (المصدر: per_origin.csv)",
      table(["نقطة القطع"] + [HYP_AR[h] for h in piv.columns], rows))

# ---------------------------------------------------------------- 5-21 signal ablation
def ablation(path):
    a = pd.read_csv(path)
    a = a[(a.slice == "all") & (a.task == "A")]
    s = agg(a, "NDCG@10", ("model", "variant"))
    return s
ab14 = ablation(os.path.join(R, "ablation_signals.csv"))
ab13 = ablation(os.path.join(DEV, "ablation_signals.csv"))
fig3 = pd.read_csv(os.path.join(R, "figures", "fig3_signal_ablation.csv"))
rows = []
for model in ["B7_WRMF", "B4_ItemKNN"]:
    for var in ["L0", "L1", "L2", "L3", "Wstar"]:
        x14 = ab14[(ab14.model == model) & (ab14.variant == var)].set_index("presentation")["NDCG@10"]
        x13 = ab13[(ab13.model == model) & (ab13.variant == var)].set_index("presentation")["NDCG@10"]
        l014 = ab14[(ab14.model == model) & (ab14.variant == "L0")].set_index("presentation")["NDCG@10"]
        l013 = ab13[(ab13.model == model) & (ab13.variant == "L0")].set_index("presentation")["NDCG@10"]
        d14 = (x14 - l014)
        if model == "B7_WRMF":
            f = fig3[(fig3.series == "WRMF target") & (fig3.x == var)].y.iloc[0]
            check(f"ablation WRMF {var} 2014 vs fig3", x14.mean(), f, 2e-6)
            f = fig3[(fig3.series == "WRMF dev 2013") & (fig3.x == var)].y.iloc[0]
            check(f"ablation WRMF {var} 2013 vs fig3", x13.mean(), f, 2e-6)
        rows.append((MODEL_AR[model], VARIANT_AR[var], num(x13.mean(), 4), num(x14.mean(), 4),
                     "—" if var == "L0" else num(d14.mean(), 4, True),
                     "—" if var == "L0" else f"{int((d14 > 0).sum())}/{len(d14)}",
                     "—" if var == "L0" else num((x13 - l013).mean(), 4, True)))
check("H2-a pair = WRMF Wstar − L0 (ablation file)",
      (ab14[(ab14.model == "B7_WRMF") & (ab14.variant == "Wstar")].set_index("presentation")["NDCG@10"]
       - ab14[(ab14.model == "B7_WRMF") & (ab14.variant == "L0")].set_index("presentation")["NDCG@10"]).mean(),
      v.set_index("hypothesis").loc["H2-a", "mean_delta"], 2e-6)
write("t-5-21", "جدول 5-21: استئصال الإشارة الضمنية في WRMF والتصفية بالعناصر، المهمة A، NDCG@10، 2014 مقابل التطوير (ثانوي، خارج عائلة هولم، وصفي بلا فاصل) (المصدر: ablation_signals.csv في 2014 والتطوير)",
      table(["النموذج", "المستوى", "التطوير 2013", "التأكيد 2014", "الفرق عن L0، 2014", "عروض الفرق موجب، 2014", "الفرق عن L0، التطوير"], rows))

# ---------------------------------------------------------------- 5-22 H4-a
auc = pd.read_csv(os.path.join(R, "h4a_auc.csv"))
a56 = auc[auc.cut == 56]
summ = open(os.path.join(R, "summary.md"), encoding="utf-8").read()
sec = summ.split("## H4-أ")[1]
srows = {}
for line in sec.splitlines():
    m = re.match(r"\|\s*(\w+)\s*\|\s*([\d.]+|nan)\s*\|\s*([\d.]+|nan)\s*\|\s*([\d.]+|nan)\s*\|", line)
    if m:
        srows[m.group(1)] = [float(m.group(i)) for i in (2, 3, 4)]
rows = []
for model in ["majority", "M0", "M1", "M2", "CART_M2"]:
    d = a56[a56.model == model].groupby("presentation")[["ROC_AUC", "PR_AUC", "Brier", "balanced_accuracy", "F1", "FNR", "FPR"]].mean()
    m = d.mean()
    check(f"H4-a {model} ROC_AUC vs summary.md", round(m.ROC_AUC, 4), srows[model][0], 1e-4)
    rows.append((MODEL_AR[model], num(m.ROC_AUC), num(m.PR_AUC), num(m.Brier), num(m.balanced_accuracy, 3),
                 num(m.F1, 3), num(m.FNR, 3), num(m.FPR, 3)))
write("t-5-22a", "جدول 5-22-أ: نماذج الخطر عند اليوم 56، متوسط العروض الثلاثة عشر، عتبة يودن المجمَّدة (المصدر: summary.md وh4a_auc.csv)",
      table(["النموذج", "ROC-AUC", "PR-AUC", "Brier", "الدقة المتوازنة", "F1 للفئة المعرّضة", "FNR", "FPR"], rows))
sc = pd.read_csv(os.path.join(R, "secondary.csv"))
SEC_AR = {"M2 − M1 (AUC, day 56)": "M2 − M1، اليوم 56", "M2 − M0 (AUC, day 56)": "M2 − M0، اليوم 56",
          "CART_M2 − M0 (AUC, day 56)": "CART على ملامح M2 − M0، اليوم 56",
          "M1 − M0 (AUC, day 28)": "M1 − M0، اليوم 28", "M1 − M0 (AUC, day 112)": "M1 − M0، اليوم 112"}
rows = []
for r in sc.itertuples():
    key = r.comparison.replace("H4-a secondary ", "")
    if key in SEC_AR:
        rows.append((SEC_AR[key], num(r.mean, 4, True), ci(r.ci_lo, r.ci_hi), num(r.p, 4), int(r.n)))
write("t-5-22b", "جدول 5-22-ب: المقارنات الثانوية لنماذج الخطر، فرق ROC-AUC (ثانوي، خارج عائلة هولم، p غير مصحَّحة) (المصدر: secondary.csv)",
      table(["المقارنة", "متوسط الفرق", "فاصل bootstrap-t 95%", "p غير مصحَّحة", "العروض"], rows))
rows = []
for r in sc.itertuples():
    if "CCC unseen-course slice" in r.comparison:
        model = r.comparison.split("slice, ")[1].replace(" mean AUC", "")
        rows.append((MODEL_AR[model], num(r.mean, 4), int(r.n)))
write("t-5-22c", "جدول 5-22-ج: شريحة المقرر الذي لا عرض له في التطوير (CCC)، متوسط ROC-AUC عند اليوم 56 (ثانوي، وصف بلا فاصل لأن n = 2) (المصدر: secondary.csv)",
      table(["النموذج", "متوسط ROC-AUC", "العروض"], rows))
h2b = sc[sc.comparison == "H2-b"]
CHECKS.append(f"INFO H2-b row status: {h2b.status.iloc[0]}")

# ---------------------------------------------------------------- 5-23 H4-b
h4b = pd.read_csv(os.path.join(R, "h4b.csv"))
SL = {"cold_q1": "الربع الأقل تاريخاً", "top_q4": "الربع الأعلى تاريخاً"}
rows = [(SL[r.slice], num(r.mean, 4, True), ci(r.ci_lo, r.ci_hi), num(r.p, 4), r.n) for r in h4b.itertuples()]
write("t-5-23", "جدول 5-23: الهجين المجمَّد − الجيران على السلال منفرداً في ربعي طول التاريخ، NDCG@10، 2014 (استكشافي: يولّد فرضية ولا يختبرها) (المصدر: h4b.csv)",
      table(["الشريحة", "متوسط الفرق", "فاصل bootstrap-t 95%", "p غير مصحَّحة", "العروض"], rows))

# ---------------------------------------------------------------- 5-24 all models
base = pd.read_csv(os.path.join(R, "baselines.csv"))
gru = pd.read_csv(os.path.join(R, "gru.csv"))
hy = pd.read_csv(os.path.join(R, "hybrid.csv"))
srow = {}
for line in summ.split("## H4-أ")[0].splitlines():
    m = re.match(r"\|\s*([AB])\s*\|\s*(\S+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+|nan)\s*\|", line)
    if m:
        srow[(m.group(1), m.group(2))] = (float(m.group(3)), float(m.group(4)), float(m.group(5)))
order = ["B3_RecentPop", "HYB*", "HYB_nominal_floor", "HYB_accept_only", "B5_SKNN", "GRU_lite", "B8_PersonalRepeat",
         "B6_Markov", "B4_ItemKNN", "B7_WRMF", "B10_EASE", "B2_Pop", "B9_CBF", "B1_Random"]
companions = ["HR@10", "MRR@10", "Coverage@10", "PopBias@10"]
for task in ["A", "B"]:
    rows = []
    for model in order:
        if (task, model) not in srow:
            continue
        mean, sd, devv = srow[(task, model)]
        if model.startswith("HYB"):
            src = hy[(hy.task == task) & (hy.model == model)].copy()
            src["seed"] = 0
            sl = src
        else:
            src = gru if model == "GRU_lite" else base
            sl = src[(src.task == task) & (src.model == model) & (src.slice == "all")]
        m = mean_over_pres(sl, "NDCG@10")
        check(f"5-24 {task} {model} NDCG@10 vs summary.md", round(m["mean"].iloc[0], 4), mean, 1e-4)
        comp = []
        for c in companions:
            if c in sl.columns and sl[c].notna().any():
                comp.append(num(mean_over_pres(sl, c)["mean"].iloc[0], 3))
            else:
                comp.append("—")
        rows.append((mean, [MODEL_AR[model], f"{num(mean)} ± {num(sd)}"] + comp + [num(devv) if devv == devv else "—"]))
    rows = [r for _, r in sorted(rows, key=lambda t: -t[0])]
    note524 = ("لا يحمل ملف الملخص قيمة تطوير للهجين ونسخه في هذا العمود، ونتائج تطوير الهجين معروضة وصفاً في القسم 5-7-3."
               + (" ولا يحمل ملف الهجين على هذه المهمة المقاييس المرافقة، فتُركت خاناتها فارغة، وهي محسوبة تحليلاً لاحقاً في الملحق هـ (الجدول هـ-3)." if task == "A" else
                  " ولا يحمل ملف الهجين التغطية وانحياز الشعبية، فتُركت خانتاهما فارغتين."))
    write(f"t-5-24{'a' if task == 'A' else 'b'}",
          f"جدول 5-24-{'أ' if task == 'A' else 'ب'}: كل النماذج على مهمة {'الموارد الجديدة (A)' if task == 'A' else 'أي وصول (B)'}، 2014، المتوسط ± الانحراف عبر العروض، مع عمود التطوير (وصفي) (المصدر: summary.md وbaselines.csv وgru.csv وhybrid.csv)",
          table(["النموذج", "NDCG@10 (2014)", "HR@10", "MRR@10", "Coverage@10", "PopBias@10", "NDCG@10 (التطوير)"], rows), note524)

# ---------------------------------------------------------------- 5-8-8 sensitivities
def hyp_deltas(df):
    # hybrid rows carry no slice/seed (already averaged over five seeds), as in hybrid.csv
    df = df[((df.slice == "all") | df.slice.isna()) & (df.task == "A")].copy()
    df["seed"] = df["seed"].fillna(0)
    out = {}
    def per(model, source=None, variant=None):
        d = df[df.model == model]
        if source is not None:
            d = d[d.source == source]
        if variant is not None:
            d = d[d.variant == variant]
        return agg(d, "NDCG@10").set_index("presentation")["NDCG@10"]
    out["H1"] = per("HYB*", "hybrid") - per("B3_RecentPop", "baselines")
    out["H2-a"] = per("B7_WRMF", "h2a_pair", "Wstar") - per("B7_WRMF", "h2a_pair", "L0")
    out["H3"] = per("GRU_lite", "gru") - per("B5_SKNN", "baselines")
    lvl = {"B3": per("B3_RecentPop", "baselines").mean(), "HYB": per("HYB*", "hybrid").mean()}
    return out, lvl
rows = []
main = {h: pp.set_index("presentation")[h] for h in ["H1", "H2-a", "H3"]}
main_lvl = (srow[("A", "B3_RecentPop")][0], srow[("A", "HYB*")][0])
rows.append(["الاستبعاد المسجل (خمسة أنواع تنقلية)", num(main_lvl[0]), num(main_lvl[1])] +
            [f"{num(main[h].mean(), 4, True)} ({int((main[h] > 0).sum())}/{len(main[h])})" for h in main])
for fname, label in [("sensitivity_E4.csv", "إعادة `page` إلى الكتالوج"), ("sensitivity_none.csv", "دون استبعاد")]:
    s = pd.read_csv(os.path.join(R, fname))
    d, lvl = hyp_deltas(s)
    rows.append([label, num(lvl["B3"]), num(lvl["HYB"])] +
                [f"{num(d[h].mean(), 4, True)} ({int((d[h] > 0).sum())}/{len(d[h])})" for h in ["H1", "H2-a", "H3"]])
write("t-5-8-8a", "جدول 5-8-د: حساسية تعريف الأنواع المستبعدة، المهمة A، NDCG@10 (ثانوي، وصفي بلا فاصل؛ بين القوسين عروض الفرق الموجب) (المصدر: sensitivity_E4.csv وsensitivity_none.csv وsummary.md وper_presentation.csv)",
      table(["تعريف الاستبعاد", "B3 الشعبية الآنية", "الهجين المجمَّد", "فرق H1", "فرق H2-أ", "فرق H3"], rows))

so = pd.read_csv(os.path.join(R, "sensitivity_other.csv"))
SO_AR = {"course-level bootstrap (robustness, D-31)": "إعادة السحب على المقررات السبعة",
         "nominal floor (D-51), H1 pair": "الأرضية الاسمية، زوج H1",
         "H4-a full training": "تدريب كامل دون حذف المتداخلين",
         "H4-a deployable training": "تدريب قابل للنشر"}
rows = []
for r in so.itertuples():
    if r.analysis in SO_AR:
        rows.append((SO_AR[r.analysis], HYP_AR[r.hypothesis], num(r.mean, 4, True), ci(r.ci_lo, r.ci_hi), num(r.p, 4), int(r.n_units)))
write("t-5-8-8b", "جدول 5-8-هـ: تحليلات المتانة الأخرى (ثانوي، خارج عائلة هولم، p غير مصحَّحة) (المصدر: sensitivity_other.csv)",
      table(["التحليل", "الفرضية", "متوسط الفرق", "فاصل bootstrap-t 95%", "p غير مصحَّحة", "الوحدات"], rows))

ac = pd.read_csv(os.path.join(R, "ablation_components.csv"))
AC_AR = {"HYB* − C7_ClusterPop": "حذف شعبية العنقود (يبقى الجيران على السلال)",
         "HYB* − B5_SKNN": "حذف الجيران على السلال (تبقى شعبية العنقود)"}
rows = [(AC_AR[r.ablation], num(getattr(r, "_2"), 4), num(r.delta_full_minus_without, 4, True), ci(r.ci_lo, r.ci_hi), num(r.p, 4))
        for r in ac.itertuples()]
write("t-5-8-8c", "جدول 5-8-و: استئصال مكوّنات الهجين المجمَّد، المهمة A، NDCG@10 (ثانوي، خارج عائلة هولم، p غير مصحَّحة) (المصدر: ablation_components.csv)",
      table(["المكوّن المحذوف", "NDCG@10 بعد الحذف", "الهجين الكامل − بعد الحذف", "فاصل bootstrap-t 95%", "p غير مصحَّحة"], rows))

ps = pd.read_csv(os.path.join(R, "protocol_sampled.csv"))
ps["seed"] = 0
samp = mean_over_pres(ps, "HR@10_sampled20")["mean"]
rows = []
full = {}
for model in ["B3_RecentPop", "HYB*", "B5_SKNN", "GRU_lite"]:
    if model == "HYB*":
        continue
    src = gru if model == "GRU_lite" else base
    sl = src[(src.task == "A") & (src.model == model) & (src.slice == "all")]
    full[model] = mean_over_pres(sl, "HR@10")["mean"].iloc[0]
# the hybrid's full-catalogue HR@10 is not in the locked hybrid file; it comes from the post-hoc
# companion metrics (appendix E, table E-3), marked as such
cm = pd.read_csv(os.path.join(ROOT, "results", "posthoc", "a4_3_companion_metrics.csv"))
hyb_hr = cm[(cm.year == 2014) & (cm.model == "HYB*")]["HR@10"].iloc[0]
rank_s = samp.sort_values(ascending=False).index.tolist()
for model in rank_s:
    fcell = num(full[model], 3) if model in full else (num(hyb_hr, 3) + " (لاحق، الجدول هـ-3)" if model == "HYB*" else "—")
    rows.append((MODEL_AR[model], num(samp[model], 3), fcell, rank_s.index(model) + 1))
write("t-5-8-8d", "جدول 5-8-ز: أثر البروتوكول، HR@10 بالترتيب بين عشرين سالبة معيَّنة مقابل الترتيب على الكتالوج الكامل، المهمة A (ثانوي، وصفي) (المصدر: protocol_sampled.csv وbaselines.csv وgru.csv)",
      table(["النموذج", "HR@10 بالسوالب المعيَّنة", "HR@10 على الكتالوج الكامل", "الرتبة بالسوالب المعيَّنة"], rows),
      "لا يحمل ملف الهجين المقفل على المهمة A عمود HR@10 على الكتالوج الكامل، فأُخذت قيمته من الحساب اللاحق في الملحق هـ (الجدول هـ-3).")

ia = pd.read_csv(os.path.join(R, "intervals_appendix.csv"))
rows = []
for r in ia.itertuples():
    vv = v.set_index("hypothesis").loc[r.hypothesis]
    rows.append((HYP_AR[r.hypothesis], ci(vv.ci_lo, vv.ci_hi), ci(r.percentile_lo, r.percentile_hi), ci(r.t_lo, r.t_hi)))
write("t-D-2", "جدول د-2: فاصل bootstrap-t المسجل (أساس الحكم) والفاصلان البديلان للشفافية وحدها (المصدر: verdicts.csv وintervals_appendix.csv)",
      table(["الفرضية", "bootstrap-t 95% (الحكم؛ مقفل)", "الفاصل المئيني 95% (الطور الثاني)", "فاصل t 95% (الطور الثاني)"], rows))

# ---------------------------------------------------------------- 5-8-9 fairness
fa = pd.read_csv(os.path.join(R, "fairness.csv"))
def grp(a, g):
    if pd.isna(g) or str(g) == "nan":
        return "غير مسجَّل"
    return GROUP_AR.get(g, g) if a in ("gender", "disability", "age_band") else g
def fair_rec(metric, name, title):
    rec = fa[(fa.part == "recommendation") & (fa.metric == metric)]
    rows = []
    for (a, gname), d in rec.groupby(["attribute", "group"], sort=False, dropna=False):
        b3 = d[d.model == "B3_RecentPop"].iloc[0]
        hb = d[d.model == "HYB*"].iloc[0]
        rows.append((ATTR_AR[a], grp(a, gname), f"{int(hb.n):,}" + (" (صغيرة)" if str(hb.small_group) == "True" else ""),
                     f"{num(b3.value, 3)} {ci(b3.ci_lo, b3.ci_hi, 3, False)}", f"{num(hb.value, 3)} {ci(hb.ci_lo, hb.ci_hi, 3, False)}"))
    write(name, title, table(["السمة", "المجموعة", "العدد", "B3 الشعبية الآنية [فاصل 95%]", "الهجين المجمَّد [فاصل 95%]"], rows))
fair_rec("NDCG@10", "t-5-8-9a", "جدول 5-8-ح: الإنصاف الوصفي للتوصية، NDCG@10 بحسب المجموعات، المهمة A، 2014 (ثانوي، وصفي) (المصدر: fairness.csv)")
fair_rec("HR@10", "t-D-3", "جدول د-3: الإنصاف الوصفي للتوصية، HR@10 بحسب المجموعات، المهمة A، 2014 (المصدر: fairness.csv)")
def fair_clf(model, name, title):
    c = fa[(fa.part == "classifier") & (fa.model == model)]
    rows = [(ATTR_AR[r.attribute], grp(r.attribute, r.group), f"{int(r.n):,}" + (" (صغيرة)" if str(r.small_group) == "True" else ""),
             f"{num(r.FNR, 3)} {ci(r.FNR_ci_lo, r.FNR_ci_hi, 3, False)}", f"{num(r.FPR, 3)} {ci(r.FPR_ci_lo, r.FPR_ci_hi, 3, False)}")
            for r in c.itertuples()]
    write(name, title, table(["السمة", "المجموعة", "العدد", "FNR [فاصل 95%]", "FPR [فاصل 95%]"], rows))
fair_clf("M1", "t-5-8-9b", "جدول 5-8-ط: معدلا السلب والإيجاب الكاذبين لمصنِّف الخطر M1 عند اليوم 56 بعتبة يودن، 2014 (ثانوي، وصفي) (المصدر: fairness.csv)")
fair_clf("M2 (appendix)", "t-D-4", "جدول د-4: معدلا السلب والإيجاب الكاذبين لمصنِّف الخطر M2 عند اليوم 56 بعتبة يودن، 2014 (المصدر: fairness.csv)")

# ---------------------------------------------------------------- figures (derived copies, captions)
FIGS = [("fig1_forest", "5-5", "الفرق المتوسط وفاصل bootstrap-t للفرضيات الأربع مع خطي الصفر والعتبة",
         "يجمع المحور وحدتين: فروق NDCG@10 للفرضيات H1 وH2-أ وH3، وفرق AUC للفرضية H4-أ، وخط العتبة واحد لأن العتبتين متساويتان عدداً (0.02)."),
        ("fig2_per_presentation", "5-6", "الفرق لكل عرض للفرضيات الأربع",
         "يجمع المحور وحدتين: فروق NDCG@10 للفرضيات H1 وH2-أ وH3، وفرق AUC للفرضية H4-أ."),
        ("fig3_signal_ablation", "5-7", "استئصال الإشارة في WRMF، التطوير مقابل التأكيد",
         "المحور الرأسي لا يبدأ من الصفر، كما في الأصل، دون قص لأي قيمة."),
        ("fig4_models_dev_vs_target", "5-10", "NDCG@10 لكل نموذج على المهمة A، التطوير مقابل التأكيد",
         "المحور لا يبدأ من الصفر، كما في الأصل، دون قص لأي قيمة."),
        ("fig5_roc", "5-8", "منحنيات ROC لنماذج الخطر عند اليوم 56",
         "لا يعرض الشكل AUC مجمَّعاً، لأن الحكم على H4-أ بمتوسط الفرق لكل عرض؛ وقيم AUC في الجدول 5-22-أ (h4a_auc.csv)."),
        ("fig6_h4b", "5-9", "فرق الهجين عن الجيران على السلال في ربعي طول التاريخ",
         "استكشافي، خارج عائلة هولم."),
        ("fig7_fairness", "5-11", "NDCG@10 للهجين المجمَّد بحسب المجموعات بفواصل 95%", "")]
DERIVED = "deliverables/06-final-thesis/figures/derived"
rows, caps = [], []
for name, num_, title, fnote in FIGS:
    rel = f"figures/{name}.csv"
    h = sha256(os.path.join(R, rel))
    locked = rel in lock["files"]
    if locked and lock["files"][rel] != h:
        raise SystemExit(f"LOCK mismatch for {rel}")
    status = "مقفل" if locked else "من نواتج الطور الثاني، خارج القفل"
    rows.append((f"الشكل {num_}", f"`results/conf2014/figures/{name}.png`", f"`{DERIVED}/{name}.png`",
                 f"`{name}.csv`", f"`{h[:12]}…`", status))
    if locked:
        cap = f"أُعيد رسمه من `{name}.csv` المقفل (SHA-256 `{h[:12]}…`)؛ الأصل في `results/conf2014/figures/`"
    else:
        cap = f"أُعيد رسمه من `{name}.csv` من نواتج الطور الثاني (خارج القفل؛ مرجعه إيداع النتائج `86c0885`؛ SHA-256 `{h[:12]}…`)؛ الأصل في `results/conf2014/figures/`"
    tag = TAG_LOCKED if locked else TAG_P2
    caps.append(f"<!--FIG:{name}-->\n![الشكل {num_}: {title} {tag}]({DERIVED}/{name}.png)\n\n*الشكل {num_}: {title} {tag}. {fnote + " " if fnote else ""}{cap}.*\n")
    CHECKS.append(f"FIG {name}: sha256 {h[:12]} locked={locked}")
write("t-D-5", "جدول د-5: مقابلة كل شكل أصلي في نتائج التأكيد بنسخته المشتقة المعروضة في الأطروحة (المصدر: LOCK وملفات figures/*.csv)",
      table(["الشكل", "الأصل", "النسخة المشتقة", "ملف القيم", "SHA-256 لملف القيم", "حالة القفل"], rows))
with open(os.path.join(OUT, "figures.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(caps))

# ---------------------------------------------------------------- 5-6 serving latency (results/serving_bench/, ت-5)
# Table 5-6 and the latency numbers of section 5-6-3, of the NFR-01 status cell (appendix C) and of the post-result
# sentence on the cold request in chapter 6 come from the three bench files (one run per server state, written by
# `src/backend/bench.py --out --state`) and from the saved output of the cluster precompute. The NFR-01 bounds are the
# requirement itself (appendix C, chapter 4); they are compared with the measurement here and never adjusted.
SB = os.path.join(ROOT, "results", "serving_bench")
NFR01 = {"warm_learner_ms": 200.0, "warm_dash_ms": 1000.0, "cold_rec_s": 5.0, "cold_dash_s": 8.0}
DASH = {"instructor/overview", "instructor/clusters", "instructor/learners"}
EP_AR = {"health": "فحص الحالة", "meta": "البيانات الوصفية", "presentations": "قائمة العروض",
         "registrations": "قائمة التسجيلات", "recommendations": "التوصيات", "explanations": "تفسير مورد",
         "history": "سجل المتعلم", "instructor/overview": "النظرة العامة للمدرّس", "instructor/clusters": "العناقيد",
         "instructor/learners": "جدول المتعلمين", "instructor/learner": "ملف المتعلم في لوحة المدرّس"}


def sb_fail(msg):
    raise SystemExit(f"serving_bench check failed: {msg}")


def sb_load(state):
    p = os.path.join(SB, f"{state}.json")
    if not os.path.exists(p):
        sb_fail(f"missing results/serving_bench/{state}.json")
    d = json.load(open(p, encoding="utf-8"))
    if d.get("schema") != "serving_bench/1" or d["meta"].get("state") != state:
        sb_fail(f"{state}.json: schema {d.get('schema')} / state {d['meta'].get('state')}")
    import statistics
    for r in d["rows"]:
        s = r.get("samples_ms")
        if r["first_ms"] is None or r["note"] or not s or len(s) != d["meta"]["n"]:
            sb_fail(f"{state}.json row {r['endpoint']}: failed request or {len(s or [])} samples != n")
        if abs(statistics.median(s) - r["median_ms"]) > 1e-9 or abs(max(s) - r["max_ms"]) > 1e-9:
            sb_fail(f"{state}.json row {r['endpoint']}: median/max differ from its samples")
    for c in d["cold_days"]:
        if c["first_ms"] is None or c["note"]:
            sb_fail(f"{state}.json cold day {c['endpoint']} {c['day']}: {c['note']}")
    CHECKS.append(f"OK  serving_bench {state}.json: {len(d['rows'])} rows (median/max = samples), "
                  f"{len(d['cold_days'])} cold days, commit {str(d['meta']['git_commit'])[:7]}")
    return d


SBD = {s: sb_load(s) for s in ("cold", "warm", "precomputed")}
for key in ("presentation", "day", "n", "registration", "cpu_count", "platform"):
    vals = {SBD[s]["meta"][key] for s in SBD}
    if len(vals) != 1:
        sb_fail(f"meta.{key} differs between the three files: {vals}")
CHECKS.append("OK  serving_bench: presentation, day, n, registration, cpu_count, platform equal in the three files")
# served code = the recorded commit: no uncommitted Python change in src/ml/ or src/backend/ (bench.py and tests aside)
for s in SBD:
    dirty = [p for p in SBD[s]["meta"].get("git_dirty_paths", [])
             if p.startswith(("src/ml/", "src/backend/")) and (p.endswith(".py") or p.endswith("/"))
             and p != "src/backend/bench.py" and not p.startswith("src/backend/tests/")]
    if dirty:
        sb_fail(f"{s}.json was measured with uncommitted serving code: {dirty}")
# the state each file claims is the state the server was in
hc, hw, hp = (SBD[s]["meta"]["server_health_at_start"] or {} for s in ("cold", "warm", "precomputed"))
if hc.get("warm", {}).get("enabled") is not False or SBD["cold"]["meta"]["cluster_cache_days_at_start"] not in (None, 0) \
        or any(c["cluster_cached_at_start"] for c in SBD["cold"]["cold_days"]):
    sb_fail("cold.json: server warmed or cluster precompute present")
if hw.get("warm", {}).get("state") != "done" or hp.get("warm", {}).get("state") != "done":
    sb_fail("warm.json/precomputed.json: warm-up not done when the run started")
if not SBD["precomputed"]["cold_days"] or not all(c["cluster_cached_at_start"] for c in SBD["precomputed"]["cold_days"]):
    sb_fail("precomputed.json: a measured cold day had no precomputed cluster selection")
pairs = {s: [(c["endpoint"], c["day"]) for c in SBD[s]["cold_days"]] for s in ("cold", "precomputed")}
if pairs["cold"] != pairs["precomputed"]:
    sb_fail("cold days differ between cold.json and precomputed.json")
CHECKS.append("OK  serving_bench: cold = unwarmed and no cluster cache; warm/precomputed = warm-up done; "
              "precomputed cold days all cached; same cold days in cold and precomputed")
ptxt = open(os.path.join(SB, "precompute.txt"), encoding="utf-8").read()
pm = re.findall(r"^(\S+): (\d+) يوماً؛ حُسب (\d+) وكان (\d+) محسوباً؛ (\d+) عمليات؛ (\d+) ث$", ptxt, re.M)
if len(pm) != 1 or "# exit: 0" not in ptxt:
    sb_fail("precompute.txt: no single summary line or non-zero exit")
pre_pres, pre_days, pre_comp, pre_cached, pre_jobs, pre_sec = pm[0][0], *map(int, pm[0][1:])
if pre_pres != SBD["cold"]["meta"]["presentation"] or pre_comp != pre_days or pre_cached != 0:
    sb_fail(f"precompute.txt: {pre_pres}, computed {pre_comp} of {pre_days}, {pre_cached} already cached")
CHECKS.append(f"OK  serving_bench precompute.txt: {pre_pres} {pre_days} days computed from an empty cache, "
              f"{pre_jobs} jobs, {pre_sec} s")


def ms_ar(x):
    return f"{x:,.0f} مللي ثانية" if x >= 1000 else f"{x:.1f} مللي ثانية"


def s1(ms):
    return f"{ms / 1000:.1f}"


def count_ar(n, one, two, few, many):
    return one if n == 1 else two if n == 2 else f"{n} {few}" if 3 <= n <= 10 else f"{n} {many}"


def days_ar(n):
    return count_ar(n, "يوم واحد", "يومين", "أيام", "يوماً")


def and_ar(items):
    return " و".join(str(i) for i in items)


row = {s: {r["endpoint"]: r for r in SBD[s]["rows"]} for s in ("cold", "warm")}
m0 = SBD["warm"]["meta"]
P_, DAY_, N_ = m0["presentation"], m0["day"], m0["n"]
dates = sorted({SBD[s]["meta"]["date"][:10] for s in SBD})
commits = sorted({str(SBD[s]["meta"]["git_commit"])[:7] for s in SBD})
rows = [("دون تسخين: أول طلب توصيات", row["cold"]["recommendations"]),
        ("دون تسخين: أول طلب للنظرة العامة للمدرّس", row["cold"]["instructor/overview"]),
        ("دون تسخين: أول طلب لقائمة التسجيلات¹", row["cold"]["registrations"]),
        ("بعد التسخين: أول طلب توصيات", row["warm"]["recommendations"]),
        ("بعد التسخين: أول طلب للنظرة العامة", row["warm"]["instructor/overview"])]
write("t-5-6",
      f"جدول 5-6: زمن الاستجابة المقاس للخدمة، العرض {P_} عند اليوم {DAY_}، الطلب الأول ثم {N_} طلباً تالياً "
      f"(آلة بـ{count_ar(m0['cpu_count'], 'نواة واحدة', 'نواتين', 'أنوية', 'نواة')}؛ قياس {and_ar(dates)}، commit `{and_ar(commits)}`) "
      f"(المصدر: results/serving_bench/cold.json وwarm.json)",
      table(["الحالة", "الطلب الأول", "الطلبات التالية (الوسيط)", "الطلبات التالية (الأقصى)"],
            [(lab, ms_ar(r["first_ms"]), ms_ar(r["median_ms"]), ms_ar(r["max_ms"])) for lab, r in rows]),
      "¹ يسبق القياسَ في كل حال طلبٌ واحد لقائمة التسجيلات تختار به أداة القياس المتعلم، فهذا الصف طلبها الثاني.")
for lab, r in rows:
    CHECKS.append(f"OK  t-5-6 {lab}: first {r['first_ms']:.1f} median {r['median_ms']:.1f} max {r['max_ms']:.1f} ms (file)")

# warm state: every path, bound per NFR-01 (every subsequent request, i.e. the max, against the bound)
wrows = SBD["warm"]["rows"]
over = [r for r in wrows if r["max_ms"] > (NFR01["warm_dash_ms"] if r["endpoint"] in DASH else NFR01["warm_learner_ms"])]
wmax = max(wrows, key=lambda r: r["max_ms"])
warm_bound = ("فلم يتجاوز أي طلب حدّه في NFR-01: 200 مللي ثانية لمسارات المتعلم وملف المتعلم، وثانية للنظرة العامة "
              "والعناقيد وجدول المتعلمين" if not over else
              "وتجاوز حدَّه في NFR-01 (200 مللي ثانية لمسارات المتعلم وملف المتعلم، وثانية للوحة) أقصى " +
              and_ar(f"{EP_AR[r['endpoint']]} ({ms_ar(r['max_ms'])})" for r in over))
hwarm = hw["warm"]
cum, day_ready = hwarm.get("serving_warm_seconds", 0.0), None
for d in hwarm["done"]:
    cum += d["seconds"]
    if d["day"] == DAY_:
        day_ready = cum
if day_ready is None:
    sb_fail(f"warm.json: day {DAY_} is not among the warmed days")


def cold_range(state, endpoint):
    xs = [c["first_ms"] for c in SBD[state]["cold_days"] if c["endpoint"] == endpoint]
    return min(xs), max(xs), len(xs), [c["day"] for c in SBD[state]["cold_days"] if c["endpoint"] == endpoint]


cr, co, pr, po = (cold_range(s, e) for s in ("cold", "precomputed") for e in ("recommendations", "instructor/overview"))
pre_over = ([f"أول طلب توصية في اليوم {c['day']} ({s1(c['first_ms'])} ثانية)" for c in SBD["precomputed"]["cold_days"]
             if c["endpoint"] == "recommendations" and c["first_ms"] > NFR01["cold_rec_s"] * 1000] +
            [f"أول نظرة عامة في اليوم {c['day']} ({s1(c['first_ms'])} ثانية)" for c in SBD["precomputed"]["cold_days"]
             if c["endpoint"] == "instructor/overview" and c["first_ms"] > NFR01["cold_dash_s"] * 1000])
VALS = {
    "presentation": P_, "day": DAY_, "n": N_, "date": and_ar(dates), "commit": and_ar(commits),
    "cpu_ar": count_ar(m0["cpu_count"], "نواة واحدة", "نواتين", "أنوية", "نواة"),
    "warm_days": and_ar(d["day"] for d in hwarm["done"]),
    "warm_total_s": f"{hwarm['seconds']:.0f}", "warm_day_ready_s": f"{day_ready:.0f}",
    "warm_med_min": f"{min(r['median_ms'] for r in wrows):.1f}", "warm_med_max": f"{max(r['median_ms'] for r in wrows):.1f}",
    "warm_max": f"{wmax['max_ms']:.1f}", "warm_max_label": EP_AR[wmax["endpoint"]], "warm_bound_phrase": warm_bound,
    "nfr_warm_status": "منفّذ ومقاس" if not over else "منفّذ، وتجاوزه القياس في " + and_ar(EP_AR[r["endpoint"]] for r in over),
    "rec_days_ar": days_ar(pr[2]), "ov_days_ar": days_ar(po[2]),
    "rec_days_list": and_ar(pr[3]), "ov_days_list": and_ar(po[3]),
    "cold_rec_min": s1(cr[0]), "cold_rec_max": s1(cr[1]), "cold_ov_min": s1(co[0]), "cold_ov_max": s1(co[1]),
    "pre_rec_min": s1(pr[0]), "pre_rec_max": s1(pr[1]), "pre_ov_min": s1(po[0]), "pre_ov_max": s1(po[1]),
    "pre_bound_phrase": ("أي دون حدّي NFR-01: خمس ثوانٍ لأول طلب توصية، وثماني ثوانٍ لأول نظرة عامة" if not pre_over else
                         "وتجاوز حدَّي NFR-01 (خمس ثوانٍ لأول طلب توصية، وثماني ثوانٍ لأول نظرة عامة) " + and_ar(pre_over)),
    "nfr_cold_status": "مستوفى" if not pre_over else "غير مستوفى في القياس",
    "pre_minutes": f"{pre_sec / 60:.0f}", "pre_jobs_ar": count_ar(pre_jobs, "عملية واحدة", "عمليتين", "عمليات", "عملية"),
    "pre_days": pre_days,
}
with open(os.path.join(OUT, "serving_bench_values.json"), "w", encoding="utf-8") as f:
    json.dump(VALS, f, ensure_ascii=False, indent=1, sort_keys=True)
    f.write("\n")
CHECKS.append(f"INFO serving_bench NFR-01: warm over-bound {[r['endpoint'] for r in over]}; precomputed cold over-bound {pre_over}")

with open(os.path.join(OUT, "CHECKS.txt"), "w") as f:
    f.write("\n".join(CHECKS) + "\n")
print("\n".join(CHECKS))
print("tables written:", sorted(os.listdir(OUT)))
