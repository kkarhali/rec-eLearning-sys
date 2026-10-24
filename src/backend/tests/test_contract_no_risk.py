"""D-22/NFR-09/D-21: لا خطر ولا عنقود ولا سمات حساسة ولا final_result في عقود المتعلم؛ وقائمة بيضاء للمدرّس."""
import unittest

from pydantic import BaseModel

from src.backend import schemas

FORBIDDEN_LEARNER = {"risk", "score", "probability", "cluster", "final_result", "gender", "disability", "imd_band", "age_band",
                     "region", "highest_education", "threshold", "youden_threshold", "above_threshold", "factors"}
SENSITIVE = {"gender", "disability", "imd_band", "age_band", "region", "highest_education", "final_result"}


def field_names(model, seen=None):
    """أسماء كل الحقول تكرارياً عبر النماذج المتداخلة (بما فيها Union وlist وdict)."""
    seen = seen if seen is not None else set()
    out = set()

    def walk_type(t):
        for a in getattr(t, "__args__", ()) or ():
            walk_type(a)
        if isinstance(t, type) and issubclass(t, BaseModel) and t not in seen:
            seen.add(t)
            for name, f in t.model_fields.items():
                out.add(name)
                walk_type(f.annotation)
    walk_type(model)
    return out


class TestContractNoRisk(unittest.TestCase):
    def test_learner_models_have_no_risk_or_sensitive_fields(self):
        for m in schemas.LEARNER_MODELS:
            bad = field_names(m) & FORBIDDEN_LEARNER
            self.assertFalse(bad, f"{m.__name__}: {bad}")

    def test_instructor_models_have_no_sensitive_fields(self):
        for m in schemas.INSTRUCTOR_MODELS:
            bad = field_names(m) & SENSITIVE
            self.assertFalse(bad, f"{m.__name__}: {bad}")

    def test_no_outcome_field_anywhere(self):
        for m in schemas.LEARNER_MODELS + schemas.INSTRUCTOR_MODELS:
            self.assertNotIn("outcome", field_names(m), m.__name__)

    def test_no_evaluation_numbers_fields(self):
        names = set()
        for m in schemas.LEARNER_MODELS + schemas.INSTRUCTOR_MODELS:
            names |= field_names(m)
        self.assertFalse(names & {"ndcg", "hit_rate", "precision", "recall", "mrr", "ndcg@10"})

    def test_model_cut_is_in_provenance(self):
        self.assertIn("model_cut", schemas.Provenance.model_fields)

    def test_every_day_dependent_response_carries_provenance_model_cut(self):
        """D-49 (6): كل نماذج الاستجابة المعتمدة على اليوم وناتج النموذج تحوي provenance من النوع Provenance."""
        self.assertGreaterEqual(len(schemas.PROVENANCE_MODELS), 5)
        for m in schemas.PROVENANCE_MODELS:
            f = m.model_fields.get("provenance")
            self.assertIsNotNone(f, m.__name__)
            self.assertIs(f.annotation, schemas.Provenance, m.__name__)
        self.assertEqual(set(schemas.Provenance.model_fields), {"run_id", "role", "model_cut"})


if __name__ == "__main__":
    unittest.main()
