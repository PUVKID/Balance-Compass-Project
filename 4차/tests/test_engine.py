"""금액·자료 보존·분할 누수·유한표본 구간의 경계 검증."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from rentlab.engine import (COLUMNS, PURPOSES, conformal_radius, fit_target, main, metrics,
                            normalize_money, prepare, preprocessor, read_manifest, run, split_data, synthetic_data)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, frame=None):
        source = self.folder / "source.csv"
        (synthetic_data() if frame is None else frame).to_csv(source, index=False, encoding="utf-8-sig")
        document = {"files": [{"path": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                               "rows": len(synthetic_data() if frame is None else frame), "source_url": "https://rt.molit.go.kr/pt/xls/xls.do",
                               "acquired_at": "2026-11-26T10:00:00+09:00", "snapshot_id": "test-snapshot"}]}
        path = self.folder / "manifest.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path, document, source

    def test_rust_exact_won(self):
        self.assertEqual(normalize_money(["12,345.6789", "0", "001.5"]), [123456789, 0, 15000])

    def test_rust_rejects_malformed(self):
        with self.assertRaisesRegex(ValueError, "Rust 금액 검증 실패"):
            normalize_money(["1,23"])

    def test_rust_rejects_embedded_newline(self):
        with self.assertRaises(ValueError):
            normalize_money(["1\n2"])

    def test_manifest_source_unchanged(self):
        path, _, source = self.manifest()
        before = source.read_bytes()
        raw, provenance = read_manifest(path)
        self.assertEqual(len(raw), 288)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(len(provenance["sources"]), 1)

    def test_manifest_utf8_strict_priority(self):
        path, _, _ = self.manifest()
        _, provenance = read_manifest(path)
        self.assertEqual(provenance["sources"][0]["encoding"], "utf-8-sig")

    def test_manifest_cp949_preserves_original_bytes(self):
        path, document, source = self.manifest()
        original = synthetic_data().to_csv(index=False).encode("cp949", errors="strict")
        source.write_bytes(original)
        document["files"][0]["sha256"] = hashlib.sha256(original).hexdigest()
        path.write_text(json.dumps(document), encoding="utf-8")
        frame, provenance = read_manifest(path)
        self.assertEqual(frame.iloc[0]["시군구"], "합성시 지역0")
        self.assertEqual(provenance["sources"][0]["encoding"], "cp949")
        self.assertEqual(provenance["sources"][0]["verified_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(source.read_bytes(), original)

    def test_manifest_invalid_encoding_cli_exit2(self):
        path, document, source = self.manifest()
        source.write_bytes(b"\xff\xff")
        document["files"][0]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "UTF-8 또는 CP949"):
            read_manifest(path)
        self.assertEqual(main(["validate", "--manifest", str(path)]), 2)

    def test_manifest_hash_failure(self):
        path, document, _ = self.manifest()
        document["files"][0]["sha256"] = "0" * 64
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            read_manifest(path)

    def test_duplicate_source_rejected(self):
        path, document, _ = self.manifest()
        document["files"].append(dict(document["files"][0]))
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "중복"):
            read_manifest(path)

    def test_overlapping_scope_rejected(self):
        path, document, _ = self.manifest()
        other = synthetic_data().iloc[:1].copy()
        other["층"] = "99"
        file = self.folder / "other.csv"
        other.to_csv(file, index=False, encoding="utf-8-sig")
        document["files"].append({**document["files"][0], "path": file.name, "rows": 1,
                                   "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "범위 중복"):
            read_manifest(path)

    def test_empty_manifest_is_not_real_success(self):
        path = self.folder / "empty.json"
        path.write_text('{"files": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "실측 자료가 없습니다"):
            read_manifest(path)

    def test_contract_audit(self):
        raw = synthetic_data().iloc[:4].copy()
        raw.loc[0, "계약구분"] = "갱신"
        raw.loc[1, "전용면적(㎡)"] = "-1"
        raw.loc[2, "계약일"] = "99"
        data, audit = prepare(raw)
        self.assertEqual(audit["included_rows"], 1)
        self.assertEqual(set(audit["excluded_by_reason"]), {"not_new_contract", "invalid_area", "invalid_date"})
        self.assertEqual(data.deposit.dtype.kind, "i")

    def test_fixed_time_boundaries(self):
        data, _ = prepare(synthetic_data())
        splits = split_data(data)
        self.assertTrue(splits["train"].date.dt.year.isin([2022, 2023]).all())
        self.assertTrue(splits["validation"].date.dt.month.le(6).all())
        self.assertTrue(splits["calibration"].date.dt.month.ge(7).all())
        self.assertTrue(splits["test"].date.dt.year.eq(2025).all())
        self.assertEqual(sum(len(v) for v in splits.values()), len(data))

    def test_region_holdout_all_prior_splits(self):
        data, _ = prepare(synthetic_data())
        splits = split_data(data, "합성시 지역1")
        for name in ["train", "validation", "calibration"]:
            self.assertFalse(splits[name].region.eq("합성시 지역1").any())
        self.assertTrue(splits["test"].region.eq("합성시 지역1").all())

    def test_unknown_holdout_rejected(self):
        data, _ = prepare(synthetic_data())
        with self.assertRaises(ValueError):
            split_data(data, "없는지역")

    def test_empty_split_rejected(self):
        data, _ = prepare(synthetic_data().iloc[:36])
        with self.assertRaisesRegex(ValueError, "빈 자료"):
            split_data(data)

    def test_finite_sample_rank(self):
        self.assertEqual(conformal_radius(np.arange(1, 10)), 9)
        self.assertEqual(conformal_radius(np.arange(1, 20)), 18)

    def test_insufficient_calibration_is_json_null(self):
        self.assertIsNone(conformal_radius([1, 2]))
        self.assertEqual(json.dumps({"radius": conformal_radius([])}, allow_nan=False), '{"radius": null}')

    def test_invalid_residual_rejected(self):
        for residual in [[float("nan")], [-1], [float("inf")]]:
            with self.assertRaises(ValueError):
                conformal_radius(residual)

    def test_interval_score(self):
        result = metrics([0, 4], [1, 1], radius=1)
        self.assertEqual(result["coverage"], 0.5)
        self.assertEqual(result["width"], 2)
        self.assertEqual(result["interval_score"], 22)

    def test_existing_output_preserved(self):
        output = self.folder / "existing"
        output.mkdir()
        marker = output / "keep.txt"
        marker.write_text("보존", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "덮어쓰지"):
            run(output, synthetic=True)
        self.assertEqual(marker.read_text(encoding="utf-8"), "보존")

    def test_output_failure_atomic(self):
        output = self.folder / "failed"
        with patch("rentlab.engine.fit_target", return_value=({"split_counts": {}}, pd.DataFrame(), {})), patch("rentlab.engine.write_artifacts", side_effect=ValueError("의도한 출력 실패")):
            with self.assertRaisesRegex(ValueError, "의도한 출력 실패"):
                run(output, synthetic=True)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_registry_distinct_purposes(self):
        self.assertGreaterEqual(len(PURPOSES), 30)
        self.assertEqual(len(PURPOSES), len({name for name, _ in PURPOSES}))

    def test_model_selection_never_test(self):
        data, _ = prepare(synthetic_data())
        jeonse = data.loc[data.rent.eq(0)].copy()
        first, _, _ = fit_target(jeonse, "jeonse", None)
        jeonse.loc[jeonse.date.dt.year.eq(2025), "deposit"] = 999999999
        second, _, _ = fit_target(jeonse, "jeonse", None)
        self.assertEqual(first["selected_model"], second["selected_model"])
        self.assertEqual(first["validation"], second["validation"])
        self.assertEqual(first["conformal_radius_won"], second["conformal_radius_won"])

    def test_preprocessing_train_only_and_unknown_region(self):
        processor = preprocessor(["area"])
        processor.fit(pd.DataFrame({"area": [10.0, 20.0, np.nan], "region": ["훈련지역"] * 3}))
        self.assertEqual(processor.named_transformers_["numeric"].named_steps["impute"].statistics_[0], 15)
        result = processor.transform(pd.DataFrame({"area": [np.nan], "region": ["새지역"]}))
        self.assertTrue(np.isfinite(result).all())
        self.assertEqual(processor.named_transformers_["category"].categories_[0].tolist(), ["훈련지역"])


if __name__ == "__main__":
    unittest.main()
