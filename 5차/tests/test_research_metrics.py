import unittest
import numpy as np
import pandas as pd
from rentlab.research_metrics import interval_score, finite_radius, balance_score, evaluate_frames, AnalysisConfig


class ResearchFormulaTests(unittest.TestCase):
    def test_interval_score_known_values(self):
        np.testing.assert_allclose(interval_score([0, 2, 4], [1, 1, 1], [3, 3, 3], .1), [22, 2, 22])

    def test_finite_order_statistic_and_insufficiency(self):
        self.assertEqual(finite_radius(np.arange(1, 10), .1), 9)
        self.assertIsNone(finite_radius(np.arange(1, 9), .1))

    def test_composite_units_and_no_propriety_claim(self):
        self.assertAlmostEqual(balance_score(10, 20, .01, 100, .1), .125)
        with self.assertRaises(ValueError):
            balance_score(10, 20, .01, 0, .1)

    def test_eight_hypotheses_with_missing_inputs_not_zero(self):
        frame = pd.DataFrame({"actual_won": [100.] * 12, "prediction_won": [100.] * 12,
                              "region": ["A"] * 12, "date": ["2025-01-01"] * 12})
        result = evaluate_frames({"jeonse": frame}, {}, {"jeonse": {}}, config=AnalysisConfig(bootstrap_replicates=99))
        self.assertEqual({r["id"] for r in result["hypotheses"]}, {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"})
        h5 = [r for r in result["hypotheses"] if r["id"] == "H5"][0]
        self.assertIsNone(h5["effect"])
        self.assertEqual(h5["status"], "unmeasured")
        self.assertTrue(all(r["decision"] != "support" for r in result["hypotheses"]))

    def test_rejects_nonfinite_and_crossed_intervals(self):
        for args in [([1], [2], [1], .1), ([np.nan], [0], [2], .1), ([1], [0], [2], 0)]:
            with self.assertRaises(ValueError):
                interval_score(*args)

    @staticmethod
    def frames():
        y = np.arange(100., 140.)
        f = pd.DataFrame({"actual_won": y, "prediction_won": y - 1,
                          "prediction_ai_won": y - 1, "prediction_global_median_won": y - 10,
                          "prediction_region_median_won": y - 12, "prediction_no_deposit_won": y - 4,
                          "source_row_id": [str(i) for i in range(40)],
                          "cluster_id": [str(i % 20) for i in range(40)],
                          "region": ["A" if i % 2 else "B" for i in range(40)],
                          "date": ["2025-02-01"] * 20 + ["2025-09-01"] * 20})
        cal = pd.DataFrame({"actual_won": np.arange(20.) + 100, "prediction_won": np.arange(20.) + 97,
                            "region": ["A", "B"] * 10, "date": ["2024-08-01"] * 20})
        meta = {"validation": {"global_median": {"mae": 10}, "region_median": {"mae": 12}},
                "train_target_median_won": 120, "train_price_edges_won": [90, 110, 120, 125, 130, 150]}
        return f, cal, meta

    def test_known_effects_and_missing_holdout(self):
        f, cal, meta = self.frames()
        config = AnalysisConfig(bootstrap_replicates=99, minimum_group_n=2, minimum_group_clusters=2, regional_calibration_min=2)
        result = evaluate_frames({"jeonse": f, "monthly": f}, {"jeonse": cal, "monthly": cal}, {"jeonse": meta, "monthly": meta}, config=config)
        self.assertEqual(len(result["hypotheses"]), 15)
        effects = {(r["id"], r["target"]): r for r in result["hypotheses"]}
        self.assertEqual(effects["H1", "jeonse"]["effect"], 9)
        self.assertEqual(effects["H2", "monthly"]["effect"], 3)
        self.assertAlmostEqual(effects["H3", "jeonse"]["effect"], .1)
        self.assertEqual(effects["H7", "monthly"]["effect"], 0)
        self.assertEqual(effects["H8", "monthly"]["effect"], 0)
        self.assertEqual(effects["H1", "monthly"]["ci"], [9., 9.])
        self.assertNotEqual(effects["H1", "monthly"]["decision"], "support")

    def test_calibration_cannot_use_test_dates(self):
        f, cal, meta = self.frames()
        cal["date"] = "2025-02-01"
        with self.assertRaises(ValueError):
            evaluate_frames({"jeonse": f}, {"jeonse": cal}, {"jeonse": meta}, config=AnalysisConfig(bootstrap_replicates=99))

    def test_holdout_same_identifier_wrong_date_rejected(self):
        f, cal, meta = self.frames()
        held = f.copy()
        held.loc[0, "date"] = "2025-03-01"
        with self.assertRaises(ValueError):
            evaluate_frames({"jeonse": f}, {}, {"jeonse": meta}, holdout_frames={"jeonse": held}, config=AnalysisConfig(bootstrap_replicates=99))

    def test_missing_test_date_rejected(self):
        f, cal, meta = self.frames()
        with self.assertRaises(ValueError):
            evaluate_frames({"jeonse": f.drop(columns="date")}, {}, {"jeonse": meta}, config=AnalysisConfig(bootstrap_replicates=99))

    def test_inactive_regional_calibration_is_unmeasured(self):
        f, cal, meta = self.frames()
        result = evaluate_frames({"jeonse": f}, {"jeonse": cal}, {"jeonse": meta}, config=AnalysisConfig(bootstrap_replicates=99, minimum_group_n=2, minimum_group_clusters=2))
        row = next(r for r in result["hypotheses"] if r["id"] == "H7" and r["target"] == "jeonse")
        self.assertEqual(row["status"], "unmeasured")
        self.assertIsNone(row["effect"])

    def test_weights_must_have_exactly_three_components(self):
        for weights in ((.5, .5), (.5, .2, .2, .1)):
            with self.assertRaises(ValueError):
                balance_score(10, 20, .01, 100, weights=weights)

    def test_h6_does_not_reconstruct_quantiles_from_deduplicated_edges(self):
        f, cal, meta = self.frames()
        meta["train_price_edges_won"] = [90, 110, 130, 150]
        result = evaluate_frames({"jeonse": f}, {}, {"jeonse": meta}, config=AnalysisConfig(bootstrap_replicates=99))
        row = next(r for r in result["hypotheses"] if r["id"] == "H6" and r["target"] == "jeonse")
        self.assertIsNone(row["effect"])


if __name__ == "__main__":
    unittest.main()
