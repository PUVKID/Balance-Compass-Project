"""원본 학습 없이 저장 요약·보정 집합의 불일치를 재현한다."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import test_runtime_v3 as runtime_cases
import test_research_input_validation as research_cases
from rentlab.experiment_runner import combine_results


class ResultBindingTests(unittest.TestCase):
    def test_both_saved_summaries_must_match_before_analysis_folder(self):
        for role in ("결과", "홀드아웃결과"):
            for damage in ("missing", "changed", "changed_type"):
                with self.subTest(role=role, damage=damage), tempfile.TemporaryDirectory() as tmp:
                    fixture = runtime_cases.HoldoutExecutionTests()
                    root = fixture.root(tmp)
                    run, _ = fixture.controlled(root)
                    ordinary = run(root/"결과", root/"자료_manifest.json")
                    held = run(root/"홀드아웃결과", root/"자료_manifest.json", "서울특별시")
                    path = root/role/"summary.json"
                    if damage == "missing":
                        path.unlink()
                    else:
                        value=json.loads(path.read_text(encoding="utf8"))
                        if damage == "changed_type":value["targets"]["jeonse"]["split_counts"]["validation"]=True
                        else:value["rows"]=999
                        path.write_text(json.dumps(value),encoding="utf8")
                    writer=Mock()
                    with self.assertRaisesRegex(ValueError, "summary"):
                        combine_results(root,ordinary,held,root/"자료_manifest.json","서울특별시",writer=writer)
                    writer.assert_not_called()
                    self.assertFalse((root/"가설통합결과").exists())

    def test_holdout_calibration_requires_exact_non_seoul_rows(self):
        for damage in ("replace", "remove", "actual_won", "region", "date", "cluster_id"):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as tmp:
                fixture=research_cases.PersistedResearchTests();root=Path(tmp)
                _,_,summary=fixture.fixture(root/"ordinary")
                _,cal,hs=fixture.fixture(root/"held",region="서울특별시")
                if damage=="replace":cal.loc[0,"source_row_id"]="foreign:row"
                elif damage=="remove":
                    cal=cal.iloc[1:]
                    hs["targets"]["jeonse"]["split_counts"]["calibration"]=len(cal)
                    (root/"held/summary.json").write_text(json.dumps(hs),encoding="utf8")
                else:cal.loc[0,damage]={"actual_won":101.,"region":"대구광역시 중구","date":"2024-08-02","cluster_id":"foreign:cluster"}[damage]
                cal.to_csv(root/"held/jeonse_calibration_predictions.csv",index=False)
                with self.assertRaisesRegex(ValueError,"보정"):
                    fixture.run_writer(root/"ordinary",summary,root/"held")
                self.assertFalse((root/"ordinary/hypothesis_results.json").exists())

    def test_holdout_calibration_allows_new_predictions_and_reordering(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture=research_cases.PersistedResearchTests();root=Path(tmp)
            _,_,summary=fixture.fixture(root/"ordinary")
            _,cal,_=fixture.fixture(root/"held",region="서울특별시")
            cal["prediction_won"]=95.
            cal.iloc[::-1].to_csv(root/"held/jeonse_calibration_predictions.csv",index=False)
            result=fixture.run_writer(root/"ordinary",summary,root/"held")
            self.assertEqual(len(result["hypotheses"]),15)

if __name__=="__main__":unittest.main()
