"""Baselines B1–B9 and the reference B10 EASE behind one interface (see base.Recommender)."""
from .base import Recommender, grid, sample_space
from .cbf import CBF
from .ease import EASE
from .knn import SKNN, ItemKNN
from .markov import Markov
from .simple import Pop, PersonalRepeat, RandomRec, RecentPop
from .wrmf import WRMF

BASELINES = {
    "B1_Random": RandomRec,
    "B2_Pop": Pop,
    "B3_RecentPop": RecentPop,
    "B4_ItemKNN": ItemKNN,
    "B5_SKNN": SKNN,
    "B6_Markov": Markov,
    "B7_WRMF": WRMF,
    "B8_PersonalRepeat": PersonalRepeat,
    "B9_CBF": CBF,
    "B10_EASE": EASE,      # reference only (D-37)
}

__all__ = ["Recommender", "grid", "sample_space", "BASELINES", "RandomRec", "Pop", "RecentPop",
           "ItemKNN", "SKNN", "Markov", "WRMF", "PersonalRepeat", "CBF", "EASE"]
