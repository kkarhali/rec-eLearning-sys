#!/usr/bin/env python3
"""Align the frontend mock data (src/frontend/mock/*.json) with the frozen hybrid that the live service serves
(docs/defense/session2/app-impact-review.md, item ت-4).

The mock files date from the design stage: they carried a four-component hybrid (recent_pop, wrmf, sknn, assess_prox),
the risk cuts 28/56/112 as model cuts, and a "snapshot" day ≠ the requested day. This script rewrites, deterministically
and without touching any key that the live contract tests compare (``assertCovers`` in src/backend/tests/test_api_live.py):

1. components = ``hybrid_frozen.json["components"]`` (C7_ClusterPop → ``similar_pop``, B5_SKNN → ``sknn``) with the weights
   ``initial_weights_modal`` (0.75/0.25), in meta.json, recommendations.json and explanations.json. Each component's
   contribution = weight × r_tilde; the relevance is their sum; items are re-sorted (ties keep the old order) and re-ranked;
   the main sentence is the template of the largest contribution and the secondary one the template of the second
   if it exceeds a third of the score (the rule of ``serving.Engine.recommend``); sentences come from ``serving.TEMPLATES``.
   learner-details.json ``top_recs`` = the first three re-ranked items.
2. ``cutoffs`` = ``settings.MODEL_CUTS`` (70, 126, 182) in meta.json and presentations.json, and ``provenance.model_cut``
   = the nearest model cut ≤ the requested day (null before 70), as in the live service. Risk cuts (``cut_day``) are kept.
3. ``snapshot_day`` = the requested day (the live service computes at t itself).

Derivation rule for values the old files do not have (stated here as the review requires): the old items have no r_tilde
for ``similar_pop``; it is taken from the nearest component in the file, ``recent_pop`` (the other windowed-popularity
count), and so is its count evidence (n, window), marked ``scope = "similar"``. A component absent from an old
explanation had a zero contribution, so its r_tilde is 0 and it has no evidence. The ``sknn`` r_tilde and item evidence
are kept. Once aligned, the files are a fixed point: a second run changes nothing (``--check`` exits 1 if it would).
The mock numbers stay synthetic and the UI labels them «وضع المحاكاة».

Usage:  python3 scripts/align_mock.py [--check]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backend.services.labels import comp_id, comp_label, fix_ar  # noqa: E402
from src.backend.settings import MODEL_CUTS  # noqa: E402
from src.ml.serving import TEMPLATES  # noqa: E402

MOCK = ROOT / "src" / "frontend" / "mock"
FROZEN = json.loads((ROOT / "results" / "dev2013" / "hybrid_frozen.json").read_text(encoding="utf-8"))
COMPS = list(FROZEN["components"])                       # serving ids, frozen order
WEIGHTS = {m: float(FROZEN["initial_weights_modal"][m]) for m in COMPS}
IDS = {m: comp_id(m) for m in COMPS}
# where an old file lacks a frozen component, take the nearest one present in it (see the module docstring)
NEAREST = {"similar_pop": "recent_pop"}


def load(name):
    return json.loads((MOCK / name).read_text(encoding="utf-8"))


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1)  # the files' own format (indent 1, no trailing newline)


def model_cut(day):
    cs = [c for c in MODEL_CUTS if c <= day]
    return max(cs) if cs else None


def components_info():
    return [{"id": IDS[m], "label": comp_label(m), "weight": round(WEIGHTS[m], 4)} for m in COMPS]


def source_component(old: dict, cid: str):
    """The old explanation component for a frozen id: itself if already aligned, else its nearest stand-in."""
    return old.get(cid) or old.get(NEAREST.get(cid, ""))


def evidence_for(cid: str, old: dict):
    c = source_component(old, cid)
    if not c or not c.get("evidence"):
        return None
    ev = dict(c["evidence"])
    if cid == "similar_pop" and ev.get("type") == "count":
        return {"type": "count", "n": int(ev["n"]), "window": int(ev["window"]), "scope": "similar"}
    return ev


def align_item(expl: dict):
    """(per-component rows, relevance, main sentence, secondary sentence) from an old explanation entry."""
    old = {c["id"]: c for c in expl["components"]}
    rows = []
    for m in COMPS:
        cid = IDS[m]
        src = source_component(old, cid)
        rt = float(src["r_tilde"]) if src else 0.0
        rows.append({"m": m, "id": cid, "weight": WEIGHTS[m], "r_tilde": rt, "contribution": WEIGHTS[m] * rt,
                     "evidence": evidence_for(cid, old) if src else None})
    relevance = sum(r["contribution"] for r in rows)
    tot = relevance or 1.0
    ranked = sorted(rows, key=lambda r: -r["contribution"])          # stable: ties keep the frozen order
    main = fix_ar(TEMPLATES[ranked[0]["m"]])
    secondary = fix_ar(TEMPLATES[ranked[1]["m"]]) if len(ranked) > 1 and ranked[1]["contribution"] > tot / 3 else None
    return rows, ranked, relevance, main, secondary


def main(check: bool = False) -> int:
    files = {n: load(n) for n in ("meta.json", "presentations.json", "recommendations.json", "explanations.json",
                                   "learner-details.json", "overview.json", "clusters.json", "learners.json")}
    before = {n: dump(o) for n, o in files.items()}

    meta = files["meta.json"]
    meta["components"] = components_info()
    meta["cutoffs"] = list(MODEL_CUTS)
    for p in files["presentations.json"]:
        p["cutoffs"] = list(MODEL_CUTS)

    recs, expls = files["recommendations.json"], files["explanations.json"]
    for reg, r in recs.items():
        day = int(r["requested_day"])
        r["snapshot_day"] = day
        r["components"] = components_info()
        r["provenance"]["model_cut"] = model_cut(day)
        new = []
        for pos, it in enumerate(r["items"]):
            key = f"{reg}|{it['id_site']}"
            e = expls[key]
            rows, ranked, rel, main_s, sec_s = align_item(e)
            new.append((-round(rel, 4), pos, it, e, rows, ranked, rel, main_s, sec_s))
        new.sort(key=lambda x: (x[0], x[1]))
        items = []
        for rank, (_, _, it, e, rows, ranked, rel, main_s, sec_s) in enumerate(new, start=1):
            items.append({"rank": rank, "id_site": it["id_site"], "activity_type": it["activity_type"],
                          "relevance": round(rel, 4),
                          "contributions": {x["id"]: round(x["contribution"], 4) for x in rows},
                          "reason": main_s, "reason_secondary": sec_s})
            e["relevance"] = round(rel, 4)
            e["snapshot_day"] = int(e["day"])
            e["provenance"]["model_cut"] = model_cut(int(e["day"]))
            e["components"] = [{"id": x["id"], "label": comp_label(x["m"]), "weight": round(x["weight"], 4),
                                "r_tilde": round(x["r_tilde"], 4), "contribution": round(x["contribution"], 4),
                                "evidence": x["evidence"], "sentence": fix_ar(TEMPLATES[x["m"]])} for x in ranked]
        r["items"] = items

    for reg, d in files["learner-details.json"].items():
        d["snapshot_day"] = int(d["day"])
        d["provenance"]["model_cut"] = model_cut(int(d["day"]))
        rec = recs.get(reg)
        if rec is not None and d.get("top_recs"):
            d["top_recs"] = [{"rank": i["rank"], "id_site": i["id_site"], "activity_type": i["activity_type"],
                              "reason": i["reason"]} for i in rec["items"][:3]]

    for name in ("overview.json", "clusters.json"):
        o = files[name]
        o["snapshot_day"] = int(o["requested_day"])
        o["provenance"]["model_cut"] = model_cut(int(o["requested_day"]))
    lr = files["learners.json"]
    lr["provenance"]["model_cut"] = model_cut(int(files["overview.json"]["requested_day"]))

    changed = [n for n, o in files.items() if dump(o) != before[n]]
    if not check:
        for n in changed:
            (MOCK / n).write_text(dump(files[n]), encoding="utf-8")
    print(("would change: " if check else "changed: ") + (", ".join(changed) or "nothing"))
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
