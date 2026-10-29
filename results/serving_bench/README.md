# results/serving_bench: زمن استجابة الخدمة (ت-5، شرط اللجنة ب-2)

قياس واحد لكل حال من أحوال الخادم الثلاث، بالأوامر أدناه حرفياً، ولم يُعَد أي تشغيل ولم يُنتقَ. ومنها يولّد
`scripts/thesis/make_tables.py` الجدول 5-6 وأرقام القسم 5-6-3 وخانة حالة NFR-01 في الملحق ج وجملة «بعد النتيجة» عن القيد 16 في الفصل 6،
ويوقف التشغيل عند أي اختلاف (انظر `scripts/thesis/README.md`). والأيام الباردة والأحوال محددة سلفاً في
`docs/meetings/2026-10-29-meeting-t5-serving-bench.md` قبل أي قياس. وهذه الأرقام زمن آلة بعينها، فتتغير بتغيّر الآلة؛ ولا تُعدَّل بها حدود NFR-01.

| الملف | ما فيه |
|---|---|
| `cold.json` | `bench.py --state cold`: خادم بلا `--warm`، وذاكرة اختيار العناقيد `data/cache/serving_clusters` منقولة جانباً (فلا حساب مسبق)، اليوم 75 ثم الأيام الباردة |
| `precompute.txt` | ناتج `python3 -m src.backend.precompute` من ذاكرة فارغة (مدة الحساب المسبق لأيام FFF_2013J كلها) |
| `warm.json` | `bench.py --state warm`: خادم بـ`--warm` بعد اكتمال التسخين (`server_health_at_start.warm` يحمل أزمنة التسخين)، اليوم 75 |
| `precomputed.json` | `bench.py --state precomputed`: الخادم المسخَّن نفسه، والحساب المسبق كامل، اليوم 75 ثم الأيام الباردة نفسها |

كل ملف JSON يحمل في `meta`: `git_commit` و`git_dirty_paths` عند بدء القياس، والتاريخ (UTC)، و`platform` و`cpu_count`،
و`loadavg_at_start`، والعرض واليوم وn والمتعلم، والأمر نفسه، و`cluster_cache_days_at_start` (عدد أيام الذاكرة الدائمة على الآلة)،
وحال الخادم من `/api/health`. ولكل صف الطلب الأول ووسيط n طلباً تالياً وأقصاها وعيّناتها، ولكل يوم بارد زمن أول طلب.

## الآلة والنسخة

- الآلة: Linux 6.18.44 (x86_64، glibc 2.39)، Intel Xeon @ 2.80GHz، 4 أنوية، 15 GiB ذاكرة؛ Python 3.13.17. حاوية سحابية.
- النسخة: commit `6c56acf` (رأس الفرع عند القياس) مع تعديلات ت-5 غير الملتزمة (`src/backend/bench.py`، والاختبار، والمحضر).
  وقد أُقلع خادم حال `cold` عند `ed14dfc` (`run_id` في الملف)، والتُزم `6c56acf` أثناء القياس من جلسة أخرى، وفرقه عن `ed14dfc`
  ملف واحد خارج الشيفرة (`docs/working/07-presentation/deck-content.md`)، فالشيفرة المخدومة واحدة في الأحوال الثلاث. وأُقلع خادم
  `warm` و`precomputed` عند `6c56acf`. والتعديلات غير الملتزمة عند كل قياس في `git_dirty_paths`، وليس فيها ملف Python مخدوم
  (يفحص ذلك `make_tables.py`).
- الحمل قبل البدء: `uptime` 06:39 UTC: `load average: 0.28, 0.42, 0.29`، و06:46: `0.05, 0.15, 0.20`؛ ولا عملية أخرى ثقيلة
  (`ps aux --sort=-%cpu`). والحمل عند بدء كل تشغيل في `loadavg_at_start` بكل ملف؛ وفي `warm` و`precomputed` بقية حمل الحساب المسبق
  الذي انتهى قبلهما بدقيقة (المتوسط المتحرك لدقيقة ثم خمس دقائق)، ولا عملية أخرى تعمل.

## الأوامر (من جذر المستودع، 2026-10-29)

```bash
# 1) cold: نقل ذاكرة العناقيد جانباً، وخادم بلا تسخين
mv data/cache/serving_clusters data/cache/serving_clusters.bak-t5
python3 -m src.backend --port 8100 &
python3 -m src.backend.bench http://127.0.0.1:8100 --state cold --out results/serving_bench/cold.json \
  --cold-day 63 --cold-day 77 --cold-day 91 --cold-day 105 --cold-day 119 --cold-day 133 --cold-day 147 \
  --cold-day 161 --cold-day 175 --cold-day 189 --cold-day 203 \
  --cold-overview-day 66 --cold-overview-day 94 --cold-overview-day 122 --cold-overview-day 150 --cold-overview-day 178
# إيقاف الخادم. ملفات العناقيد السبعة عشر التي كتبها طابقت النسخة المنقولة جانباً مصفوفةً مصفوفة، ثم حُذفت

# 2) الحساب المسبق من ذاكرة فارغة (الناتج كاملاً في precompute.txt)
rm -rf data/cache/serving_clusters
python3 -m src.backend.precompute --presentation FFF_2013J --jobs 4 >> results/serving_bench/precompute.txt 2>&1
# الذاكرة الناتجة (269 ملفاً) طابقت النسخة المنقولة جانباً مصفوفةً مصفوفة، فحُذفت النسخة المنقولة

# 3) warm ثم precomputed على خادم واحد بتسخين
python3 -m src.backend --warm --port 8100 &
# انتظار /api/health حتى warm.state = done
python3 -m src.backend.bench http://127.0.0.1:8100 --state warm --out results/serving_bench/warm.json
python3 -m src.backend.bench http://127.0.0.1:8100 --state precomputed --out results/serving_bench/precomputed.json \
  --cold-day 63 --cold-day 77 --cold-day 91 --cold-day 105 --cold-day 119 --cold-day 133 --cold-day 147 \
  --cold-day 161 --cold-day 175 --cold-day 189 --cold-day 203 \
  --cold-overview-day 66 --cold-overview-day 94 --cold-overview-day 122 --cold-overview-day 150 --cold-overview-day 178
```
