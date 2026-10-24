"""Synthetic presentations for unit tests (no raw data needed)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.ml.data import PresentationData

MINI_TYPES = {1: "oucontent", 2: "quiz", 3: "forumng", 4: "resource", 5: "url"}


def make_presentation(events, types: dict[int, str], name: str = "AAA_2013J", length: int = 300,
                      assessment_dates=(19, 54, 117)) -> PresentationData:
    """events: iterable of (id_student, id_site, date, clicks)."""
    ev = pd.DataFrame(list(events), columns=["id_student", "id_site", "date", "clicks"])
    ev = ev.groupby(["id_student", "id_site", "date"], as_index=False)["clicks"].sum()
    ev["n_rows"] = 1
    ev["activity_type"] = ev["id_site"].map(types).astype("category")
    ev["week_from"] = np.nan
    ev["week_to"] = np.nan
    ev = ev.astype({"id_student": np.int32, "id_site": np.int32, "date": np.int16, "clicks": np.int32})
    items = pd.DataFrame({"id_site": list(types), "activity_type": list(types.values()),
                          "week_from": np.nan, "week_to": np.nan})
    asm = pd.DataFrame({"id_assessment": range(len(assessment_dates)), "assessment_type": "TMA",
                        "date": list(assessment_dates), "weight": 10.0})
    students = pd.DataFrame({"id_student": sorted(ev["id_student"].unique())})
    return PresentationData(name=name, events=ev, items=items, assessments=asm, students=students,
                            registrations=students.copy(), length=length)


def mini_example_events():
    """Table 11 of the draft (number of access days, L1): u1..u4 × i1..i5, all before day 50."""
    days = {(1, 1): 3, (1, 2): 1, (1, 4): 2,
            (2, 1): 2, (2, 3): 1, (2, 5): 1,
            (3, 2): 2, (3, 4): 3, (3, 5): 1,
            (4, 1): 2, (4, 4): 1}
    ev = []
    for (u, i), n in days.items():
        for k in range(n):
            ev.append((u, i, 10 + 3 * k + i, 1))
    return ev


def random_presentation(seed: int = 0, n_students: int = 60, n_items: int = 40, length: int = 260,
                        nav_items: int = 5) -> PresentationData:
    rng = np.random.default_rng(seed)
    types = {}
    kinds = ["oucontent", "quiz", "forumng", "resource", "url"]
    for i in range(1, n_items + 1):
        types[1000 + i] = kinds[i % len(kinds)]
    for j in range(nav_items):
        types[5000 + j] = ["homepage", "subpage", "page", "folder", "sharedsubpage"][j % 5]
    ev = []
    sites = list(types)
    for u in range(1, n_students + 1):
        for _ in range(rng.integers(30, 120)):
            ev.append((10_000 + u, sites[rng.integers(len(sites))], int(rng.integers(-10, length)),
                       int(rng.integers(1, 20))))
    return make_presentation(ev, types, length=length)
