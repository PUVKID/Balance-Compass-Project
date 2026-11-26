# 문서 수정 전체 비교

기준 커밋: `e079767e4c799d6ebde7fa99d81751b8d1a537bc`. 실행 코드·이전 원문 diff·배포 자산은 변경하지 않았습니다. 이 비교 문서 자체는 자기참조를 피하기 위해 diff에서 제외합니다.

~~~~~diff
diff --git a/docs/changes/2026-11-27-round9-navigation.md b/docs/changes/2026-11-27-round9-navigation.md
new file mode 100644
index 0000000..52d8646
--- /dev/null
+++ b/docs/changes/2026-11-27-round9-navigation.md
@@ -0,0 +1,7 @@
+# 9차 영어 차수 목록과 소스 연결
+
+영어 개요의 전체 연구 차수 표에 9차를 추가하고 영어 설명 범위를 4–9차로 맞췄습니다. 다섯 영어 수준 안내에서는 이전 8차 소스를 8차 폴더로 연결하고 최신 9차 소스는 9차 설명 아래에 배치했습니다. 코드·171개 검사 근거·실제 학습 중지·연구 한계·이전 차수 원문은 보존했습니다.
+
+[수정한 문서 전체 비교](2026-11-27-round9-navigation-full.md)
+
+차수별 소스 이름도 Round 8·Round 9로 명시해 다음 차수의 최신 소스 변경과 이전 차수 연결을 구분합니다.
diff --git a/en/README.md b/en/README.md
index 4dd4b74..cede286 100644
--- a/en/README.md
+++ b/en/README.md
@@ -40,8 +40,9 @@ Balance Compass studies **apartment lease deposits, monthly rent, and prediction
 | 6 | Saved-prediction identity/split/mode validation, complete Seoul H5, dashboard consistency and facility eligibility | [Round 6 · English](docs/round6.md) | [5 → 6 · Korean](../6차/docs/차수비교.md) |
 | 7 | Strict CSV/feature validation, fixed-condition evidence and a model-free preflight CLI; training stopped | [Round 7 · English](docs/round7.md) | [6 → 7 · Korean](../7차/docs/차수비교.md) |
 | 8 | Full 48-month lineage audit, selected-manifest execution and analysis completion guards, cluster diagnostics and partial historical evidence | [Round 8 · English](docs/round8.md) | [7 → 8 · Korean](../8차/docs/차수비교.md) |
+| 9 | Bind both saved summaries before combined analysis; match the exact non-Seoul calibration population and observations while allowing different predictions and row order | [Round 9 · English](docs/round9.md) | [8 → 9 · Korean](../9차/docs/차수비교.md) |
 
-Rounds 1–3 remain in Korean and are explicitly labeled. Rounds 4–8 and the five current reading guides have English explanations.
+Rounds 1–3 remain in Korean and are explicitly labeled. Rounds 4–9 and the five current reading guides have English explanations.
 
 [Current source](../9차/) · [Current execution and remaining conditions](docs/round9.md#user-content-reading-level-3) · [Formulas and interpretation · Korean](../4차/docs/확장분석_수식과해석.md)
 
diff --git a/en/docs/levels/level1.md b/en/docs/levels/level1.md
index d0a7809..eea7f8e 100644
--- a/en/docs/levels/level1.md
+++ b/en/docs/levels/level1.md
@@ -66,7 +66,7 @@ Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics an
 |---|---|---|
 | Input lineage and completion | Full 48-month audit, selected manifest and post-analysis hash checks | Data integrity is not independent location truth, historical-vintage approval or measured performance |
 
-[Round 8 at this level](../round8.md#user-content-reading-level-1) · [Current source](../../../9차/)
+[Round 8 at this level](../round8.md#user-content-reading-level-1) · [Round 8 source](../../../8차/)
 
 
 Revision 9 validates both saved summaries before combined analysis and checks holdout calibration contract identity against the ordinary non-Seoul subset. 171 controlled tests pass; real training remains stopped. Round 9 is available in Korean and English. [Revision 9 · Korean](../../../9차/docs/차수설명.md#user-content-reading-level-1).
@@ -82,4 +82,4 @@ A result file and its saved description must tell the same story. Before compari
 | A different contract is substituted | Contract identity | Reject the comparison |
 | A new model predicts a different amount | Observed contract is unchanged | Allow the comparison |
 
-[Round 9 at this level](../round9.md#user-content-reading-level-1) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-1)
+[Round 9 at this level](../round9.md#user-content-reading-level-1) · [Round 9 source](../../../9차/) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-1)
diff --git a/en/docs/levels/level2.md b/en/docs/levels/level2.md
index 3eebd3b..0ac320e 100644
--- a/en/docs/levels/level2.md
+++ b/en/docs/levels/level2.md
@@ -67,7 +67,7 @@ Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics an
 |---|---|---|
 | Input lineage and completion | Full 48-month audit, selected manifest and post-analysis hash checks | Data integrity is not independent location truth, historical-vintage approval or measured performance |
 
-[Round 8 at this level](../round8.md#user-content-reading-level-2) · [Current source](../../../9차/)
+[Round 8 at this level](../round8.md#user-content-reading-level-2) · [Round 8 source](../../../8차/)
 
 
 Revision 9 validates both saved summaries before combined analysis and checks holdout calibration contract identity against the ordinary non-Seoul subset. 171 controlled tests pass; real training remains stopped. Round 9 is available in Korean and English. [Revision 9 · Korean](../../../9차/docs/차수설명.md#user-content-reading-level-2).
@@ -83,4 +83,4 @@ Start with ordinary calibration contracts and remove Seoul. The remaining source
 | Ordinary to holdout observations | Amount, date, region and cluster | Model prediction |
 | Saved summary to preserved copy | JSON values, types and validated bytes | Filename for the analysis result |
 
-[Round 9 at this level](../round9.md#user-content-reading-level-2) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-2)
+[Round 9 at this level](../round9.md#user-content-reading-level-2) · [Round 9 source](../../../9차/) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-2)
diff --git a/en/docs/levels/level3.md b/en/docs/levels/level3.md
index 879acd2..0e99db8 100644
--- a/en/docs/levels/level3.md
+++ b/en/docs/levels/level3.md
@@ -67,7 +67,7 @@ Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics an
 |---|---|---|
 | Input lineage and completion | Full 48-month audit, selected manifest and post-analysis hash checks | Data integrity is not independent location truth, historical-vintage approval or measured performance |
 
-[Round 8 at this level](../round8.md#user-content-reading-level-3) · [Current source](../../../9차/)
+[Round 8 at this level](../round8.md#user-content-reading-level-3) · [Round 8 source](../../../8차/)
 
 
 Revision 9 validates both saved summaries before combined analysis and checks holdout calibration contract identity against the ordinary non-Seoul subset. 171 controlled tests pass; real training remains stopped. Round 9 is available in Korean and English. [Revision 9 · Korean](../../../9차/docs/차수설명.md#user-content-reading-level-3).
@@ -84,4 +84,4 @@ Use Python 3.12, the fixed dependencies and the Rust money parser. Run python -B
 | Calibration check | Calibration prediction CSVs | Reject changed row population or observations |
 | Traceability | 입력검증.json and 일반원본_summary.json | Preserve originals separately |
 
-[Round 9 at this level](../round9.md#user-content-reading-level-3) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-3)
+[Round 9 at this level](../round9.md#user-content-reading-level-3) · [Round 9 source](../../../9차/) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-3)
diff --git a/en/docs/levels/level4.md b/en/docs/levels/level4.md
index 7de28e3..59fc968 100644
--- a/en/docs/levels/level4.md
+++ b/en/docs/levels/level4.md
@@ -67,7 +67,7 @@ Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics an
 |---|---|---|
 | Input lineage and completion | Full 48-month audit, selected manifest and post-analysis hash checks | Data integrity is not independent location truth, historical-vintage approval or measured performance |
 
-[Round 8 at this level](../round8.md#user-content-reading-level-4) · [Current source](../../../9차/)
+[Round 8 at this level](../round8.md#user-content-reading-level-4) · [Round 8 source](../../../8차/)
 
 
 Revision 9 validates both saved summaries before combined analysis and checks holdout calibration contract identity against the ordinary non-Seoul subset. 171 controlled tests pass; real training remains stopped. Round 9 is available in Korean and English. [Revision 9 · Korean](../../../9차/docs/차수설명.md#user-content-reading-level-4).
@@ -84,4 +84,4 @@ combine_results validates both saved JSON summaries against returned summaries b
 | Observation fields | Three string fields and numeric actual amount | date, region, cluster_id, actual_won |
 | Learned outputs | No forced equality | Different prediction_won values remain valid |
 
-[Round 9 at this level](../round9.md#user-content-reading-level-4) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-4)
+[Round 9 at this level](../round9.md#user-content-reading-level-4) · [Round 9 source](../../../9차/) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-4)
diff --git a/en/docs/levels/level5.md b/en/docs/levels/level5.md
index cef21bc..1894e36 100644
--- a/en/docs/levels/level5.md
+++ b/en/docs/levels/level5.md
@@ -67,7 +67,7 @@ Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics an
 |---|---|---|
 | Input lineage and completion | Full 48-month audit, selected manifest and post-analysis hash checks | Data integrity is not independent location truth, historical-vintage approval or measured performance |
 
-[Round 8 at this level](../round8.md#user-content-reading-level-5) · [Current source](../../../9차/)
+[Round 8 at this level](../round8.md#user-content-reading-level-5) · [Round 8 source](../../../8차/)
 
 
 Revision 9 validates both saved summaries before combined analysis and checks holdout calibration contract identity against the ordinary non-Seoul subset. 171 controlled tests pass; real training remains stopped. Round 9 is available in Korean and English. [Revision 9 · Korean](../../../9차/docs/차수설명.md#user-content-reading-level-5).
@@ -84,4 +84,4 @@ This change strengthens H5 input traceability; it does not change the estimand,
 | Uncertainty | Existing cluster bootstrap and 15-evaluation rules retained | Coverage guarantees under dependence or shift |
 | Outcome claims | 171 controlled tests pass | Real performance, supported hypotheses or completed paper |
 
-[Round 9 at this level](../round9.md#user-content-reading-level-5) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-5)
+[Round 9 at this level](../round9.md#user-content-reading-level-5) · [Round 9 source](../../../9차/) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-5)
~~~~~
