"""OULAD loading and preprocessing (ADR-001: D-04, D-05, D-06, D-07, D-09, D-21).

Responsibilities
----------------
* read the seven OULAD tables from ``data/raw/oulad/``;
* aggregate duplicated ``studentVle`` rows on (registration, id_site, date) by summing
  ``sum_click`` (D-06) — 19.1 % of groups have > 1 row in the exploratory check;
* join ``id_site`` → ``activity_type``, ``week_from``, ``week_to`` (``vle``);
* the learner is the registration (code_module, code_presentation, id_student) (D-04);
  since every model is fitted per presentation (D-05), ``id_student`` identifies the
  registration *inside* a :class:`PresentationData` object;
* exclusion sets for the recommendation target (D-07) incl. the sensitivity variants;
* unordered day baskets (D-06);
* a cache in ``data/cache/`` (parquet if pyarrow is importable, else pickle).

Guard for D-09: the 13 presentations of 2014 are the confirmatory set and are only
run once after the freeze. Every loader refuses them unless ``allow_confirmatory=True``
is passed explicitly; the experiments in this round never pass it.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "oulad"
CACHE_DIR = REPO_ROOT / "data" / "cache"
RESULTS_DIR = REPO_ROOT / "results"

# --- presentations (D-09) -------------------------------------------------------------
DEV_PRESENTATIONS: tuple[str, ...] = (
    "AAA_2013J", "BBB_2013B", "BBB_2013J", "DDD_2013B", "DDD_2013J",
    "EEE_2013J", "FFF_2013B", "FFF_2013J", "GGG_2013J",
)
CONF_PRESENTATIONS: tuple[str, ...] = (
    "AAA_2014J", "BBB_2014B", "BBB_2014J", "CCC_2014B", "CCC_2014J", "DDD_2014B", "DDD_2014J",
    "EEE_2014B", "EEE_2014J", "FFF_2014B", "FFF_2014J", "GGG_2014B", "GGG_2014J",
)

# --- exclusion sets (D-07) -------------------------------------------------------------
E5 = frozenset({"homepage", "subpage", "sharedsubpage", "folder", "page"})
EXCLUSION_SETS: dict[str, frozenset[str]] = {
    "E5": E5,                                   # main analysis (D-07)
    "E4": E5 - {"page"},                        # sensitivity 1: E \ {page}
    "none": frozenset(),                        # sensitivity 2: no exclusion
    # definition used in the exploratory checks of the supervisor and the peer (3 types);
    # only used to reproduce those numbers (T1), never in the main protocol
    "nav3": frozenset({"homepage", "subpage", "page"}),
}

# columns that must never enter a model (D-21); kept only for fairness analysis
SENSITIVE_COLUMNS = ("gender", "disability", "imd_band", "age_band", "region", "highest_education")


class ConfirmatoryAccessError(RuntimeError):
    """Raised when a 2014 (confirmatory) presentation is requested before the freeze (D-09)."""


def split_name(name: str) -> tuple[str, str]:
    module, pres = name.split("_")
    return module, pres


def assert_allowed(names, allow_confirmatory: bool = False) -> None:
    for n in names:
        if n in CONF_PRESENTATIONS and not allow_confirmatory:
            raise ConfirmatoryAccessError(
                f"{n} belongs to the 2014 confirmatory set (D-09); it may only be run once after "
                "the freeze, with allow_confirmatory=True.")
        if n not in DEV_PRESENTATIONS and n not in CONF_PRESENTATIONS:
            raise ValueError(f"unknown presentation {n}")


# --- cache helpers ----------------------------------------------------------------------
def _has_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        return False


def _cache_path(stem: str) -> Path:
    return CACHE_DIR / (stem + (".parquet" if _has_pyarrow() else ".pkl"))


def _cache_read(stem: str) -> pd.DataFrame | None:
    p = _cache_path(stem)
    if not p.exists():
        return None
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_pickle(p)


def _cache_write(stem: str, df: pd.DataFrame) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _cache_path(stem)
    if p.suffix == ".parquet":
        df.to_parquet(p, index=False)
    else:
        df.to_pickle(p)


def raw_fingerprint() -> str:
    """Cheap fingerprint of the raw files (size + mtime) used to invalidate the cache."""
    h = hashlib.md5()
    for name in ("studentVle.csv", "vle.csv"):
        p = RAW_DIR / name
        st = p.stat()
        h.update(f"{name}:{st.st_size}".encode())
    return h.hexdigest()[:10]


# --- table loaders -------------------------------------------------------------------------
def load_vle() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "vle.csv")
    df["presentation"] = df["code_module"] + "_" + df["code_presentation"]
    return df[["id_site", "presentation", "activity_type", "week_from", "week_to"]]


def load_assessments() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "assessments.csv")
    df["presentation"] = df["code_module"] + "_" + df["code_presentation"]
    return df[["presentation", "id_assessment", "assessment_type", "date", "weight"]]


def load_courses() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "courses.csv")
    df["presentation"] = df["code_module"] + "_" + df["code_presentation"]
    return df[["presentation", "module_presentation_length"]]


def load_student_info(include_sensitive: bool = False) -> pd.DataFrame:
    """studentInfo; sensitive columns are dropped unless explicitly requested (fairness only, D-21)."""
    df = pd.read_csv(RAW_DIR / "studentInfo.csv")
    df["presentation"] = df["code_module"] + "_" + df["code_presentation"]
    if not include_sensitive:
        df = df.drop(columns=list(SENSITIVE_COLUMNS))
    return df.drop(columns=["code_module", "code_presentation"])


def load_registrations() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "studentRegistration.csv")
    df["presentation"] = df["code_module"] + "_" + df["code_presentation"]
    return df.drop(columns=["code_module", "code_presentation"])


def _read_student_vle(presentations: tuple[str, ...]) -> pd.DataFrame:
    t = time.time()
    df = pd.read_csv(
        RAW_DIR / "studentVle.csv",
        dtype={"code_module": "category", "code_presentation": "category", "id_student": np.int32,
               "id_site": np.int32, "date": np.int16, "sum_click": np.int32},
    )
    n_raw = len(df)
    pres = df["code_module"].astype(str) + "_" + df["code_presentation"].astype(str)
    keep = pres.isin(presentations).to_numpy()
    df = df.loc[keep, ["id_student", "id_site", "date", "sum_click"]].copy()
    df["presentation"] = pres[keep].astype("category").to_numpy()
    print(f"[data] read studentVle.csv: {n_raw:,} rows ({time.time() - t:.1f}s); kept {len(df):,}")
    return df


def load_daily_events(role: str = "dev", allow_confirmatory: bool = False,
                      use_cache: bool = True) -> pd.DataFrame:
    """Aggregated daily interactions c_uid for all presentations of a role.

    Returns columns: presentation (category), id_student, id_site, date, clicks, n_rows,
    activity_type (category), week_from, week_to.
    One row per (registration, id_site, date): duplicated raw rows are summed (D-06);
    ``n_rows`` keeps the number of raw rows that were merged (for the EDA).
    """
    if role == "dev":
        pres = DEV_PRESENTATIONS
    elif role == "conf":
        assert_allowed(CONF_PRESENTATIONS, allow_confirmatory)
        pres = CONF_PRESENTATIONS
    else:
        raise ValueError(role)
    stem = f"daily_events_{role}_{raw_fingerprint()}"
    if use_cache:
        cached = _cache_read(stem)
        if cached is not None:
            return cached
    raw = _read_student_vle(pres)
    agg = (raw.groupby(["presentation", "id_student", "id_site", "date"], observed=True, sort=True)
           ["sum_click"].agg(["sum", "size"]).reset_index()
           .rename(columns={"sum": "clicks", "size": "n_rows"}))
    agg["clicks"] = agg["clicks"].astype(np.int32)
    agg["n_rows"] = agg["n_rows"].astype(np.int16)
    vle = load_vle()[["id_site", "activity_type", "week_from", "week_to"]]
    agg = agg.merge(vle, on="id_site", how="left", validate="many_to_one")
    if agg["activity_type"].isna().any():
        raise ValueError("studentVle contains id_site values missing from vle.csv")
    agg["activity_type"] = agg["activity_type"].astype("category")
    agg["presentation"] = agg["presentation"].astype("category")
    if use_cache:
        _cache_write(stem, agg)
    return agg


# --- per-presentation container --------------------------------------------------------------
@dataclass
class PresentationData:
    """Everything known about one presentation (D-05: one independent model per presentation)."""

    name: str
    events: pd.DataFrame          # daily aggregated events (all activity types)
    items: pd.DataFrame           # vle rows of this presentation: id_site, activity_type, week_from, week_to
    assessments: pd.DataFrame     # published assessment schedule (allowed context, ADR-002 §3.6.10)
    students: pd.DataFrame        # studentInfo without sensitive columns
    registrations: pd.DataFrame   # studentRegistration
    length: int                   # module_presentation_length
    meta: dict = field(default_factory=dict)

    @property
    def module(self) -> str:
        return split_name(self.name)[0]


def load_presentation(name: str, events: pd.DataFrame | None = None,
                      allow_confirmatory: bool = False) -> PresentationData:
    assert_allowed([name], allow_confirmatory)
    if events is None:
        events = load_daily_events("dev" if name in DEV_PRESENTATIONS else "conf",
                                   allow_confirmatory=allow_confirmatory)
    ev = events[events["presentation"] == name].drop(columns=["presentation"]).reset_index(drop=True)
    vle = load_vle()
    items = vle[vle["presentation"] == name].drop(columns=["presentation"]).reset_index(drop=True)
    asm = load_assessments()
    asm = asm[asm["presentation"] == name].drop(columns=["presentation"]).reset_index(drop=True)
    info = load_student_info()
    info = info[info["presentation"] == name].drop(columns=["presentation"]).reset_index(drop=True)
    reg = load_registrations()
    reg = reg[reg["presentation"] == name].drop(columns=["presentation"]).reset_index(drop=True)
    courses = load_courses()
    length = int(courses.loc[courses["presentation"] == name, "module_presentation_length"].iloc[0])
    return PresentationData(name=name, events=ev, items=items, assessments=asm, students=info,
                            registrations=reg, length=length)


def load_dev_presentations(names=DEV_PRESENTATIONS) -> dict[str, PresentationData]:
    assert_allowed(names)
    ev = load_daily_events("dev")
    return {n: load_presentation(n, events=ev) for n in names}


# --- generic helpers ------------------------------------------------------------------------------
def target_mask(activity_type: pd.Series, exclusion: str = "E5") -> np.ndarray:
    """True for recommendable (non-excluded) items under the chosen exclusion set."""
    return ~activity_type.astype(str).isin(EXCLUSION_SETS[exclusion]).to_numpy()


def day_baskets(events: pd.DataFrame, user_col: str = "id_student", item_col: str = "id_site",
                day_col: str = "date") -> pd.Series:
    """Unordered day baskets S_{u,d} = {i : c_uid > 0} (D-06), indexed by (user, day)."""
    return events.groupby([user_col, day_col], sort=True)[item_col].agg(lambda s: frozenset(s.tolist()))


def next_assessment_gap(days: np.ndarray, assessment_dates) -> np.ndarray:
    """a(d) = min{date_k - d : date_k >= d} over published, non-missing dates.

    Missing dates are ignored (3.6 of the hypotheses draft); days after the last known
    date get +inf (they fall in the "> 14" bin).
    """
    dates = np.sort(np.asarray([x for x in assessment_dates if pd.notna(x)], dtype=float))
    days = np.asarray(days, dtype=float)
    if dates.size == 0:
        return np.full(days.shape, np.inf)
    pos = np.searchsorted(dates, days, side="left")
    out = np.full(days.shape, np.inf)
    ok = pos < dates.size
    out[ok] = dates[pos[ok]] - days[ok]
    return out


PROXIMITY_BINS = ((0, 3), (4, 7), (8, 14), (15, np.inf))


def proximity_bin(gap: np.ndarray) -> np.ndarray:
    """Bins {0–3, 4–7, 8–14, >14} of the days-to-next-assessment context feature."""
    gap = np.asarray(gap, dtype=float)
    return np.select([gap <= 3, gap <= 7, gap <= 14], [0, 1, 2], default=3).astype(np.int8)
