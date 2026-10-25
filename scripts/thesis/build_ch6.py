#!/usr/bin/env python3
"""Rebuild chapter 6 from its recorded text at tag freeze-03.

Allowed changes only: delete non-applicable branches, fill «[نتيجة 2014]», and add post-result
paragraphs that start with «**بعد النتيجة.**». The diff against the recorded text is verified
mechanically at the end (the run fails on any other change).

The recorded text is templates/ch6_freeze03.md, a byte copy of
`git show freeze-03:docs/working/06-thesis/ch6-discussion.md`. Pass --verify-tag to check that
copy against the tag (read-only git call).

Usage:  python3 scripts/thesis/build_ch6.py [--verify-tag]
"""
import os, re, sys, difflib, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TAGFILE = os.path.join(HERE, "templates", "ch6_freeze03.md")
TAGTEXT = open(TAGFILE, encoding="utf-8").read()
if "--verify-tag" in sys.argv:
    ref = subprocess.run(["git", "-C", ROOT, "show", "freeze-03:docs/working/06-thesis/ch6-discussion.md"],
                         capture_output=True, text=True, check=True).stdout
    if ref != TAGTEXT:
        raise SystemExit("templates/ch6_freeze03.md differs from the freeze-03 recorded text")
    print("recorded text verified against freeze-03")
sys.path.insert(0, HERE)
from refmap import apply_citations, load_map
REFMAP = load_map(ROOT)  # original unified citation number -> thesis number (after renumber.py), or None
if REFMAP:
    TAGTEXT = apply_citations(TAGTEXT, REFMAP)
TAG = TAGTEXT.split("\n")
OUTP = os.path.join(ROOT, "docs", "working", "06-thesis", "ch6-discussion.md")
PH = "«[نتيجة 2014]»"
AFTER = "**بعد النتيجة.**"

DELETE = {25, 27, 40, 41, 53, 54, 55, 67, 68}
# line -> list of replacements, applied in order to successive placeholder occurrences
FILL = {
    5: ["«النتيجة»"],
    19: ["«غير حاسمة»", "−0.0006", "[−0.0166، +0.0204]", "0.9429"],
    33: ["«مؤكَّدة» (بهامش)", "+0.0497", "[+0.0352، +0.0659]"],
    39: ["(الفصل الخامس، الجدول 5-21)"],
    47: ["«مدحوضة للتفوق»", "−0.0100", "[−0.0349، +0.0123]"],
    61: ["«مدحوضة عملياً»", "+0.0083", "[+0.0019، +0.0144]", "موجب في الربعين"],
    71: ["(+0.041 [+0.019، +0.085] في الربع الأقل تاريخاً، و+0.017 في الأعلى)"],
    97: ["(وقد جاءت فيها نماذج الخطر بترتيب السلّم نفسه، وصفاً بلا فاصل لأنها عرضان فقط؛ الفصل الخامس، الجدول 5-22-ج)"],
    101: ["(لم تغيّر إعادة النوع `page` إلى الكتالوج اتجاه الفروق ولا حجمها تقريباً، في حين غيّر ترك صفحات التنقل المقارنات بين النماذج؛ الفصل الخامس، الجدول 5-8-د)"],
    105: ["(فبقي فاصل H2-أ كله فوق الصفر، وشمل فاصل H4-أ الصفر مع سبع وحدات فقط؛ الفصل الخامس، الجدول 5-8-هـ)"],
    135: ["(وقد تكرر فيه النمط: معدل السلب الكاذب لمصنِّف الخطر أعلى لدى الإناث منه لدى الذكور بفاصلين لا يتداخلان، وأعلى في الفئتين العمريتين الأكبر، وجاءت جودة التوصية أعلى لدى الإناث وأدنى في فئة 55 عاماً فأكثر الصغيرة؛ الفصل الخامس، الجدولان 5-8-ح و5-8-ط)"],
}
# partial branch deletion inside line 71 (the non-applicable «if unclear» clause)
PARTIAL = {71: ("؛ وإن لم يتضح بقي العنقود أداة وصف للمدرّس.", ".")}

INSERT = {
    5: f"{AFTER} أُبقي في هذا الفصل لكل فرضية الفرع المنطبق وحده بنصه المسجل، وحُذفت الفروع الأخرى. التفسيرات الشرطية الكاملة مسجلة في نسخة الوسم `freeze-03` (`eb34d6a`).",
    15: f"{AFTER} قد يجتمع في فرضية واحدة أثر دالّ إحصائياً وحكم «مدحوضة عملياً»، ولا تناقض في ذلك. فالدلالة الإحصائية تجيب عن سؤال «هل الأثر غير صفري؟»، والعتبة العملية تجيب عن سؤال «هل هو بحجم يستحق؟». وقد صيغت الفرضيات بالسؤال الثاني، فالحكم بالعتبة، وتُذكر الدلالة معه في موضعه. وفي H3، التي تُقرأ بجدول سداسي يميّز التفوق من التأخر، يُسمّى الحكم «مدحوضة» بوسمه المسجل «مدحوضة للتفوق».",
    29: f"{AFTER} لم يتحقق هذا التوقع: جاء الفرق −0.0006 والحكم غير حاسمة بالإجراء المسجل. فلم يتفوق الهجين السلوكي على الشعبية الآنية (0.5692 مقابل 0.5698، الفصل الخامس، الجدول 5-18)، ولا يكشف التصميم بقوة 80% أثراً أصغر من 0.0375. ونفصح أن الحد الأعلى للفاصل (0.0204) يزيد على العتبة بـ0.0004 فقط، وهو فرق في حدود خطأ المحاكاة، وأن الفاصلين البديلين في الملحق يقعان دونها. والطريقة والبذرة مثبتتان قبل البيانات، فلا يُعاد التصنيف، ولا يُقرأ الحكم استبعاداً للأثر ولا دليلاً عليه (الملحق د، القسم د-2).\n\n"
        f"{AFTER} وانعكس التفكيك على 2014: فقد جاء مكسب التقسيم إلى عناقيد، أي شعبية العنقود منفردة ناقص الشعبية الآنية، −0.0103 بفاصل [−0.0256، +0.0058]، وجاء مكسب الشخصنة، أي الهجين ناقص شعبية العنقود منفردة، +0.0097 بفاصل [+0.0028، +0.0156]، موجباً في اثني عشر عرضاً من ثلاثة عشر (الفصل الخامس، الجدول 5-20-أ). والتفكيك غير مصحَّح، ويُعرض وصفاً. فشعبية العنقود منفردةً جاءت دون الشعبية الآنية في 2014، والهجين جاء أعلى وصفاً من الجيران على السلال وحدهم في H4-ب الاستكشافية (القسم 6-6). ويتسق ذلك مع أن العنقود يعمل سياقاً شعبياً مكمّلاً للجيران، لا شخصنة تتجاوز الجدول، ولا يُبنى على ذلك ادعاء. وفي التأكيد جاءت الشعبية الآنية والهجين متقاربين على مهمة الموارد الجديدة (0.5698 و0.5692، الفصل الخامس، الجدول 5-24-أ).",
    43: f"{AFTER} جاء الحكم مؤكَّداً لأن الأثر تجاوز ضعف العتبة: فقيمة p بعد هولم 0.0010، والفرق موجب في العروض الثلاثة عشر كلها، والحد الأدنى لفاصله فوق العتبة. وحدد الاستئصال على 2014، وصفاً، الحداثة مستوى يحمل أكثر الأثر كما في التطوير: فعدد الأيام وحده أضاف +0.0035، ورفع اضمحلال الحداثة الفرق إلى +0.0406، وأضافت الشدة بعده قليلاً. **وحدود هذا الحكم** أنه يخص WRMF على اكتشاف الموارد الجديدة، في عروض السنة التالية من OULAD. فلا يمتد إلى النظام المقترح، لأن H2-ب غير منطبقة؛ ولا إلى نماذج أخرى، فاستئصال التصفية بالعناصر ثانوي يُعرض وصفاً؛ ولا إلى منصات أو مؤسسات أخرى. ولا يجعل WRMF المرجَّح نموذجاً منافساً، فقد بلغ 0.27 مقابل 0.57 لأقوى خط أساس.",
    51: f"{AFTER} لم يُسجَّل لحكم «مدحوضة للتفوق» فرع صريح، فيُكتب من تعريف القسم 6-2: وقع الحد الأعلى لفاصل الثقة دون العتبة، أي أن البيانات تستبعد أثراً بحجم العتبة أو أكبر. استُبعد تفوّق GRU-lite على SKNN بمقدار ≥ 0.02. ولا تكافؤ، لأن الحد الأدنى −0.035 أقل من −0.02. فلم يتفوق GRU-lite على SKNN بالقدر المسجل، فالفاصل يستبعد تفوقاً لا يقل عن 0.02. ولا يُقرأ الحكم تأخراً لـGRU-lite، لأن الفاصل يشمل الصفر. والحكم مقيّد بهذا التنفيذ: GRU-lite مكتوب بمكتبة numpy، ببُعد حالة 64، وبضبط محدود؛ فلا تعميم على الشبكات المتكررة عامة.",
    57: f"{AFTER} وتتسق نتيجة التأكيد مع ما وجدته [42] و[43]: فلم تتفوق الشبكة المتكررة على طريقة الجيران هنا أيضاً.",
    73: f"{AFTER} أضافت ملامح السلوك إلى مجموع النقرات أثراً موجباً ودالاً (+0.0083 AUC، p بعد هولم = 0.044، وموجب في 11 من 13 عرضاً). لكن الحد الأعلى لفاصله (0.0144) دون أصغر أثر ذي قيمة عملية سُجّل مسبقاً (0.02)، فالفرضية كما صيغت، أي تحسّن لا يقل عن 0.02، مدحوضة عملياً. والنتيجة متسقة مع التطوير (+0.014، دون العتبة). ويُقرأ الفرع المسجل أعلاه مع هذه الجملة: فالأثر غير صفري، لكنه دون الحجم الذي عُدّ ذا قيمة. وفي المقارنات الثانوية تقدّم النموذج M2، الذي يضيف الملامح الأكاديمية، على M1 بـ+0.064 [+0.040، +0.079] (الفصل الخامس، الجدول 5-22-ب)، وهو يتسق مع أن الملامح الأكاديمية أقوى المنبئات. وبناء درجة اللوحة على M1 قيد معلن (القسم 6-9).",
    81: f"{AFTER} وعلى 2014 جاءت الشعبية الآنية والجيران على السلال أعلى خطوط الأساس كما في التطوير، ولم يتفوق الهجين على الشعبية الآنية (غير حاسمة)، ولم يتفوق GRU-lite على الجيران على السلال (مدحوضة للتفوق). وبيّن تحليل البروتوكول على 2014 أن الترتيب بين عشرين سالبة معيَّنة يضخّم معدل الإصابة ويغيّر ترتيب النماذج (الفصل الخامس، الجدول 5-8-ز). وجاء حكم H2-أ «مؤكَّدة» داخل WRMF، في حدود التعميم المبينة في القسم 6-4.",
    97: f"{AFTER} ولا تُعرض عروض 2014 في الواجهة، وفتحها مؤجَّل إلى عمل مستقبلي؛ وسجل الإذن المكتوب بعد التحقق المستقل سجلٌّ لا يقرؤه الكود.",
    105: f"{AFTER} ومع ذلك جاءت H2-أ مؤكَّدة لأن أثرها تجاوز ضعف العتبة، وH3 مدحوضة للتفوق لأن الحد الأعلى لفاصلها وقع دون العتبة.",
    131: f"{AFTER} أضاف التشغيل التأكيدي قيدين:\n\n19. **درجة الخطر في اللوحة مبنية على ملامح السلوك (M1)** لأن السلوك موضوع الفرضية، مع أن النموذج الذي يضيف الملامح الأكاديمية أقوى تنبؤاً.\n20. **عروض 2014 لا تُعرض في الواجهة**، وفتحها مؤجَّل إلى عمل مستقبلي.",
    143: f"{AFTER} ثبّت الفصل لكل فرضية حكمها التأكيدي: H2-أ مؤكَّدة بهامش داخل WRMF، وH1 غير حاسمة لم يتفوق فيها الهجين على الشعبية الآنية، وH3 مدحوضة للتفوق، وH4-أ مدحوضة عملياً مع أثر موجب دال دون العتبة؛ وأضاف التشغيل التأكيدي قيدين فصارت القيود عشرين.",
}

if REFMAP:
    INSERT = {k: apply_citations(v, REFMAP) for k, v in INSERT.items()}
    FILL = {k: [apply_citations(x, REFMAP) for x in v] for k, v in FILL.items()}

out = []
for i, line in enumerate(TAG, 1):
    if i in DELETE:
        assert line.startswith("- **إن جاءت"), (i, line[:40])
        continue
    if i in FILL:
        assert line.count(PH) == len(FILL[i]), (i, line.count(PH))
        for rep in FILL[i]:
            line = line.replace(PH, rep, 1)
    if i in PARTIAL:
        old, new = PARTIAL[i]
        assert line.count(old) == 1
        line = line.replace(old, new)
    out.append(line)
    if i in INSERT:
        out.append("")
        out.append(INSERT[i])
text = "\n".join(out)
text = re.sub(r"\n{3,}", "\n\n", text)
# deleted branches leave blank-line runs collapsed above
assert PH not in text
open(OUTP, "w", encoding="utf-8").write(text)

# ---- mechanical verification against the tag
new = text.split("\n")
sm = difflib.SequenceMatcher(a=TAG, b=new, autojunk=False)
report = {"deleted_branch": 0, "filled": 0, "after_result": 0, "other": []}
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op == "equal":
        continue
    olds, news = TAG[a1:a2], new[b1:b2]
    for l in olds:
        if l.startswith("- **إن جاءت"):
            report["deleted_branch"] += 1
        elif l.strip() == "":
            pass
        else:
            # must be a filled line: rebuilding the recorded text by turning fills back into placeholders
            idx = TAG.index(l) + 1
            if idx in FILL or idx in PARTIAL:
                report["filled"] += 1
            else:
                report["other"].append(("old", idx, l[:60]))
    for l in news:
        if l.strip() == "" or l.startswith(AFTER) or re.match(r"^(19|20)\. ", l):
            if l.startswith(AFTER):
                report["after_result"] += 1
            continue
        # filled lines appear here too: check that they map back to a tag line
        cand = [k for k in list(FILL) + list(PARTIAL)]
        ok = False
        for k in cand:
            t = TAG[k - 1]
            s2 = l
            if k in PARTIAL:
                s2 = s2.replace(PARTIAL[k][1] if s2.endswith(PARTIAL[k][1]) and False else "", "")
            r = TAG[k - 1]
            if k in PARTIAL:
                r = r.replace(PARTIAL[k][0], PARTIAL[k][1])
            for rep in FILL.get(k, []):
                r = r.replace(PH, rep, 1)
            if r == l:
                ok = True
                break
        if not ok:
            report["other"].append(("new", l[:60]))
print(report)
