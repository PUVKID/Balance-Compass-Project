"""사전에 정한 가설에 저장된 예측을 적용한다. 이 모듈은 모델을 학습하지 않는다."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import math

import numpy as np
import pandas as pd

TITLES = {
    "H1": "미래 계약에서 AI와 중앙값 기준의 오차 차이",
    "H2": "관측 보증금의 월세 예측 기여",
    "H3": "명목 90% 예측구간과 실제 포함률의 동등성",
    "H4": "지역 동일 가중 포함률 편차",
    "H5": "미학습 지역으로 이동할 때의 오차 증가",
    "H6": "학습기 가격 구간에 따른 정규화 오차 차이",
    "H7": "지역별 보정에 따른 포함률 편차 감소",
    "H8": "지역 구성을 맞춘 상·하반기 포함률 감소",
}
FORMULAS = {"H1": "MAE(검증 선택 기준모델) − MAE(검증 선택 AI)",
            "H2": "MAE(보증금 제외 AI) − MAE(보증금 포함 AI)",
            "H3": "실제 포함률 − (1 − α), 동등성 범위 ±ε",
            "H4": "mean_g |coverage_g − (1−α)| − ε",
            "H5": "MAE(지역 홀드아웃) − MAE(일반 시간분할)",
            "H6": "[MAE(학습기 상위 가격구간) − MAE(하위 구간)] / median_train(y)",
            "H7": "macro_gap(전체 보정) − macro_gap(지역 보정)",
            "H8": "mean_g [coverage_g,상반기 − coverage_g,하반기]"}
SOURCES = [
    {"id": "Lei2018", "title": "Distribution-Free Predictive Inference for Regression", "url": "https://doi.org/10.1080/01621459.2017.1307116", "use": "분할 conformal의 순위와 구간"},
    {"id": "Gneiting2007", "title": "Strictly Proper Scoring Rules, Prediction, and Estimation", "url": "https://doi.org/10.1198/016214506000001437", "use": "예측구간 폭과 미포함 벌점을 결합한 interval score"},
    {"id": "Vovk2012", "title": "Conditional Validity of Inductive Conformal Predictors", "url": "https://proceedings.mlr.press/v25/vovk12.html", "use": "조건부·그룹별 보정의 근거와 한계"},
    {"id": "Cameron2008", "title": "Bootstrap-Based Improvements for Inference with Clustered Errors", "url": "https://www.nber.org/papers/t0344", "use": "군집 의존성 고려의 동기. 논문의 bootstrap-t를 그대로 구현한 것은 아님"},
]


@dataclass(frozen=True)
class AnalysisConfig:
    alpha: float = .1
    coverage_tolerance: float = .02
    confidence: float = .95
    family_size: int = 15
    bootstrap_replicates: int = 9999
    minimum_clusters: int = 20
    minimum_group_n: int = 30
    minimum_group_clusters: int = 5
    regional_calibration_min: int = 100
    seed: int = 20261126

    def __post_init__(self):
        if not 0 < self.alpha < 1 or not 0 < self.confidence < 1:
            raise ValueError("alpha와 신뢰수준은 0과 1 사이여야 합니다")
        if not 0 < self.coverage_tolerance < 1 or self.family_size != 15:
            raise ValueError("동등성 허용오차와 고정 15개 평가 가족을 확인하십시오")
        if self.bootstrap_replicates < 99 or self.minimum_clusters < 2 or self.minimum_group_clusters < 2:
            raise ValueError("부트스트랩 반복·군집 조건이 부족합니다")
        if self.minimum_group_n < 1 or self.regional_calibration_min < 1:
            raise ValueError("최소 표본 수는 양수여야 합니다")


def interval_score(actual, lower, upper, alpha=.1):
    y, lo, hi = [np.asarray(v, dtype=float) for v in (actual, lower, upper)]
    if y.shape != lo.shape or y.shape != hi.shape or not 0 < alpha < 1:
        raise ValueError("구간 점수의 모양 또는 alpha 오류")
    if not all(np.isfinite(v).all() for v in (y, lo, hi)) or (lo > hi).any():
        raise ValueError("구간 점수에는 유한한 값과 올바른 하한·상한이 필요합니다")
    return hi - lo + 2 / alpha * np.maximum(lo - y, 0) + 2 / alpha * np.maximum(y - hi, 0)


def finite_radius(residuals, alpha=.1):
    values = np.asarray(residuals, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or (values < 0).any() or not 0 < alpha < 1:
        raise ValueError("보정 잔차 또는 alpha 오류")
    rank = math.ceil((len(values) + 1) * (1 - alpha))
    return None if rank > len(values) or not len(values) else float(np.partition(values, rank - 1)[rank - 1])


def balance_score(mae, mean_interval_score, macro_gap, train_scale, alpha=.1, weights=(.5, .25, .25)):
    """연구용 제안 지표. proper score나 검증된 신규 통계량이라고 주장하지 않는다."""
    if len(weights) != 3:
        raise ValueError("균형 손실은 정확히 3개 가중치가 필요합니다")
    values = np.asarray([mae, mean_interval_score, macro_gap, train_scale, alpha, *weights], dtype=float)
    if not np.isfinite(values).all() or train_scale <= 0 or not 0 < alpha < 1:
        raise ValueError("균형 손실의 척도와 입력은 유효해야 합니다")
    if min(mae, mean_interval_score, macro_gap, *weights) < 0 or not np.isclose(sum(weights), 1):
        raise ValueError("음수가 아닌 손실과 합계 1인 가중치가 필요합니다")
    return float(weights[0] * mae / train_scale + weights[1] * mean_interval_score / train_scale + weights[2] * macro_gap / alpha)


def _numbers(frame, column):
    if column not in frame:
        return None
    values = pd.to_numeric(frame[column], errors="raise").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"유한하지 않은 예측·정답 칼럼: {column}")
    return values


def _blank(hypothesis, target, reason="필요한 입력 또는 비교 결과가 없습니다"):
    return {"id": hypothesis, "target": target, "title": TITLES[hypothesis], "formula": FORMULAS[hypothesis],
            "status": "unmeasured", "effect": None, "ci": None, "decision": "unmeasured", "reason": reason,
            "n": None, "clusters": None, "unit": "원" if hypothesis in {"H1", "H2", "H5"} else "무차원"}


def _interval(samples, config):
    values = np.asarray(samples, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < math.ceil(.8 * config.bootstrap_replicates):
        return None
    tail = (1 - config.confidence) / config.family_size / 2
    return [float(v) for v in np.quantile(values, [tail, 1 - tail])]


def _finish(row, value, samples, config, n, clusters, reason=""):
    if not np.isfinite(value):
        return row
    row.update(status="measured", effect=float(value), n=int(n), clusters=clusters, reason=reason)
    row["bootstrap_requested"] = config.bootstrap_replicates
    row["bootstrap_valid"] = int(np.isfinite(samples).sum()) if samples is not None else 0
    row["ci"] = _interval(samples, config) if samples is not None else None
    row["decision"] = "inconclusive"
    if row["ci"] is None:
        row["status"] = "partial"
        row["reason"] = (reason + " · " if reason else "") + "군집 식별·표본·유효 재표집이 부족하여 신뢰구간과 확정 판정은 미산출"
    elif config.bootstrap_replicates < 9999:
        row["status"] = "partial"
        row["reason"] = "기술 확인용 축소 반복수입니다. 논문용 확정 판정에 사용하지 않습니다"
    elif row["id"] == "H3":
        lo, hi = row["ci"]
        eps = config.coverage_tolerance
        row["decision"] = "support" if lo > -eps and hi < eps else "not_support" if lo > eps or hi < -eps else "inconclusive"
    else:
        lo, hi = row["ci"]
        row["decision"] = "support" if lo > 0 else "not_support" if hi <= 0 else "inconclusive"
    return row


def _target_analysis(frame, calibration, metadata, target, config):
    ids = [h for h in TITLES if h not in {"H5"} and (h != "H2" or target == "monthly")]
    rows = {h: _blank(h, target) for h in ids}
    if frame.empty or "actual_won" not in frame or "prediction_won" not in frame or "region" not in frame:
        return list(rows.values()), {}
    if "date" not in frame:
        raise ValueError("가설 테스트의 계약일이 없어 고정 2025년 분리를 확인할 수 없습니다")
    y, prediction = _numbers(frame, "actual_won"), _numbers(frame, "prediction_won")
    if (y <= 0).any() or frame.region.isna().any() or frame.region.astype(str).str.strip().eq("").any():
        raise ValueError("가설 평가에는 양수 정답과 관측 지역이 필요합니다")
    n = len(frame)
    regions = frame.region.astype(str).to_numpy()
    region_codes, region_labels = pd.factorize(regions, sort=True)
    gcount = len(region_labels)
    cluster_available = "cluster_id" in frame and frame.cluster_id.notna().all() and frame.cluster_id.astype(str).str.strip().ne("").all()
    cluster_labels = frame.cluster_id.astype(str).to_numpy() if cluster_available else regions
    cluster_codes, cluster_names = pd.factorize(cluster_labels, sort=True)
    k = len(cluster_names)
    mapping = pd.DataFrame({"cluster": cluster_codes, "region": region_codes}).groupby("cluster").region
    if mapping.nunique().gt(1).any():
        raise ValueError("같은 단지 식별자가 여러 지역에 연결되었습니다")
    cluster_regions = mapping.first().to_numpy()
    # 열: 표본, AI오차, 기준오차, 보증금제외오차, 전체/지역포함, 전체/지역구간점수,
    # 하위가격표본/오차, 상위가격표본/오차, 상반기표본/포함, 하반기표본/포함, 선택모델오차.
    features = np.zeros((n, 17), dtype=float)
    features[:, 0] = 1
    features[:, 16] = np.abs(y - prediction)
    available = set()
    ai = _numbers(frame, "prediction_ai_won")
    baseline_name = metadata.get("best_baseline_model")
    if not baseline_name:
        validation = metadata.get("validation", {})
        names = [name for name in ("global_median", "region_median") if name in validation]
        baseline_name = min(names, key=lambda name: (validation[name]["mae"], name)) if names else None
    baseline = _numbers(frame, f"prediction_{baseline_name}_won") if baseline_name else None
    if ai is not None:
        features[:, 1] = np.abs(y - ai)
    if ai is not None and baseline is not None:
        features[:, 2] = np.abs(y - baseline)
        available.add("H1")
    no_deposit = _numbers(frame, "prediction_no_deposit_won")
    if target == "monthly" and ai is not None and no_deposit is not None:
        features[:, 3] = np.abs(y - no_deposit)
        available.add("H2")
    global_radius = None
    radii = {}
    region_radius = None
    if not calibration.empty and {"actual_won", "prediction_won", "region"}.issubset(calibration):
        if "date" not in calibration:
            raise ValueError("보정 자료의 계약일이 없어 시간 분리를 확인할 수 없습니다")
        cal_dates = pd.to_datetime(calibration.date, errors="raise")
        if cal_dates.isna().any() or not cal_dates.between("2024-07-01", "2024-12-31").all():
            raise ValueError("보정 자료는 고정된 2024년 하반기 계약만 허용합니다")
        if "source_row_id" in calibration and "source_row_id" in frame and set(calibration.source_row_id) & set(frame.source_row_id):
            raise ValueError("같은 계약 행을 보정과 테스트에 중복 사용할 수 없습니다")
        residuals = np.abs(_numbers(calibration, "actual_won") - _numbers(calibration, "prediction_won"))
        global_radius = finite_radius(residuals, config.alpha)
    if global_radius is not None:
        lo, hi = prediction - global_radius, prediction + global_radius
        features[:, 4] = (lo <= y) & (y <= hi)
        features[:, 6] = interval_score(y, lo, hi, config.alpha)
        available.update(["H3", "H4", "H8"])
        for region, positions in calibration.groupby("region", sort=False).indices.items():
            if len(positions) >= config.regional_calibration_min:
                radius = finite_radius(residuals[positions], config.alpha)
                if radius is not None:
                    radii[str(region)] = radius
        region_radius = np.asarray([radii.get(region, global_radius) for region in regions])
        features[:, 5] = (prediction - region_radius <= y) & (y <= prediction + region_radius)
        features[:, 7] = interval_score(y, prediction - region_radius, prediction + region_radius, config.alpha)
        if any(region in radii for region in regions):
            available.add("H7")
        else:
            rows["H7"]["reason"] = "테스트 지역에 지역별 보정이 적용되지 않아 비교 효과는 미산출"
    scale = metadata.get("train_target_median_won")
    scale = float(scale) if scale is not None else float("nan")
    edges = metadata.get("train_price_quantiles_won", metadata.get("train_price_edges_won", []))
    if np.isfinite(scale) and scale > 0 and len(edges) == 6 and np.isfinite(edges).all() and np.all(np.diff(edges) >= 0) and edges[1] < edges[-2]:
        low, high = y <= edges[1], y > edges[-2]
        features[:, 8], features[:, 9] = low, low * features[:, 16]
        features[:, 10], features[:, 11] = high, high * features[:, 16]
        if low.any() and high.any():
            available.add("H6")
    if "date" in frame:
        dates = pd.to_datetime(frame.date, errors="raise")
        if dates.isna().any() or not dates.dt.year.eq(2025).all():
            raise ValueError("가설 테스트는 고정된 2025년 계약만 허용합니다")
        first = dates.dt.month.le(6).to_numpy()
        features[:, 12], features[:, 13] = first, first * features[:, 4]
        features[:, 14], features[:, 15] = ~first, (~first) * features[:, 4]
    else:
        available.discard("H8")
    aggregate = np.zeros((k, features.shape[1]), dtype=float)
    np.add.at(aggregate, cluster_codes, features)
    base_group_n = np.bincount(region_codes, minlength=gcount)
    group_clusters = np.bincount(cluster_regions, minlength=gcount)
    price_clusters = {"low": int((aggregate[:, 8] > 0).sum()), "high": int((aggregate[:, 10] > 0).sum())} if cluster_available else {"low": 0, "high": 0}
    eligible = (base_group_n >= config.minimum_group_n) & (group_clusters >= config.minimum_group_clusters) if cluster_available else np.zeros(gcount, dtype=bool)
    calibrated_eligible = set(region_labels[eligible]) & set(radii)
    if not calibrated_eligible:
        available.discard("H7")
        rows["H7"]["reason"] = "적격 테스트 지역에 지역별 보정이 적용되지 않아 비교 효과는 미산출"
    temporal_eligible = eligible.copy()
    for column in (12, 14):
        ns = np.bincount(cluster_regions, weights=aggregate[:, column], minlength=gcount)
        cs = np.bincount(cluster_regions, weights=(aggregate[:, column] > 0), minlength=gcount)
        temporal_eligible &= (ns >= config.minimum_group_n) & (cs >= config.minimum_group_clusters)

    def estimates(weights):
        total = weights @ aggregate
        out = {}
        for h, numerator in (("H1", total[2] - total[1]), ("H2", total[3] - total[1])):
            out[h] = numerator / total[0]
        out["H3"] = total[4] / total[0] - (1 - config.alpha)
        out["H6"] = (total[11] / total[10] - total[9] / total[8]) / scale if min(total[8], total[10]) > 0 and scale > 0 else np.nan
        gn = np.bincount(cluster_regions, weights=weights * aggregate[:, 0], minlength=gcount)
        gc = np.bincount(cluster_regions, weights=weights * aggregate[:, 4], minlength=gcount)
        gr = np.bincount(cluster_regions, weights=weights * aggregate[:, 5], minlength=gcount)
        if eligible.any() and (gn[eligible] > 0).all():
            gap = np.mean(np.abs(gc[eligible] / gn[eligible] - (1 - config.alpha)))
            r_gap = np.mean(np.abs(gr[eligible] / gn[eligible] - (1 - config.alpha)))
            out["H4"], out["H7"] = gap - config.coverage_tolerance, gap - r_gap
        else:
            out["H4"], out["H7"] = np.nan, np.nan
        temporal = []
        for count_column, covered_column in ((12, 13), (14, 15)):
            tn = np.bincount(cluster_regions, weights=weights * aggregate[:, count_column], minlength=gcount)
            tc = np.bincount(cluster_regions, weights=weights * aggregate[:, covered_column], minlength=gcount)
            temporal.append(tc[temporal_eligible] / tn[temporal_eligible] if temporal_eligible.any() and (tn[temporal_eligible] > 0).all() else np.array([np.nan]))
        out["H8"] = float(np.mean(temporal[0] - temporal[1]))
        return out

    base = estimates(np.ones(k))
    samples = {h: [] for h in ids}
    can_bootstrap = cluster_available and k >= config.minimum_clusters
    if can_bootstrap:
        rng = np.random.default_rng(config.seed + (0 if target == "jeonse" else 1))
        strata = [np.flatnonzero(cluster_regions == region) for region in np.flatnonzero(eligible)]
        for _ in range(config.bootstrap_replicates):
            weights = rng.multinomial(k, np.full(k, 1 / k)).astype(float)
            values = estimates(weights)
            for h in ("H1", "H2", "H3", "H6"):
                if h in samples:
                    samples[h].append(values[h])
            # 지역 구성을 고정하는 지표는 각 지역 안에서 단지 군집을 재표집한다.
            weights = np.zeros(k)
            for positions in strata:
                weights[positions] = rng.multinomial(len(positions), np.full(len(positions), 1 / len(positions)))
            regional = estimates(weights) if strata else {}
            for h in ("H4", "H7", "H8"):
                samples[h].append(regional.get(h, np.nan))
    for h in ids:
        if h not in available:
            continue
        used_n = int(base_group_n[temporal_eligible if h == "H8" else eligible].sum()) if h in {"H4", "H7", "H8"} else n
        reason = "지역 지표는 사전에 정한 최소 표본·단지 군집 조건을 충족한 지역만 평가" if h in {"H4", "H7", "H8"} else ""
        used_clusters = int(group_clusters[temporal_eligible if h == "H8" else eligible].sum()) if h in {"H4", "H7", "H8"} else k
        sufficient = can_bootstrap and used_clusters >= config.minimum_clusters
        if h == "H6":
            sufficient &= min(price_clusters.values()) >= config.minimum_clusters
            rows[h]["subgroup_clusters"] = price_clusters
        _finish(rows[h], base[h], samples[h] if sufficient else None, config, used_n, used_clusters if cluster_available else None, reason)
    supplementary = {"cluster_available": bool(cluster_available), "eligible_regions": int(eligible.sum()),
                     "temporal_eligible_regions": int(temporal_eligible.sum()), "total_regions": gcount,
                     "baseline_selected_on_validation": baseline_name,
                     "regional_calibration_fallback": "표본 부족 지역은 전체 보정 반경 사용", "balance_score": None}
    supplementary["regional_calibration"] = {"calibrated_test_regions": len(set(regions) & set(radii)),
        "calibrated_eligible_regions": len(calibrated_eligible),
        "fallback_n": int(sum(region not in radii for region in regions)) if global_radius is not None else None,
        "fallback_rate": float(np.mean([region not in radii for region in regions])) if global_radius is not None else None}
    if global_radius is not None and scale > 0 and eligible.any():
        total = aggregate.sum(axis=0)
        gap = base["H4"] + config.coverage_tolerance
        supplementary["balance_score"] = balance_score(total[16] / n, total[6] / n, gap, scale, config.alpha)
        supplementary["balance_score_status"] = "검증 전 제안 요약지표 · 모델 선택에 사용하지 않음"
        supplementary["weight_sensitivity"] = [{"weights": list(w), "value": balance_score(total[16] / n, total[6] / n, gap, scale, config.alpha, w)} for w in ((.5, .25, .25), (.25, .5, .25), (.25, .25, .5))]
    return list(rows.values()), supplementary


def evaluate_frames(test_frames, calibration_frames, target_metadata, *, config=None, holdout_frames=None):
    config = config or AnalysisConfig()
    hypotheses, supplementary = [], {}
    for target in ("jeonse", "monthly"):
        frame = test_frames.get(target, pd.DataFrame())
        rows, extra = _target_analysis(frame, calibration_frames.get(target, pd.DataFrame()), target_metadata.get(target, {}), target, config)
        hypotheses.extend(rows)
        supplementary[target] = extra
        h5 = _blank("H5", target, "같은 계약 행의 지역 홀드아웃 비교 결과가 없습니다")
        held = (holdout_frames or {}).get(target)
        if held is not None and not held.empty and not frame.empty and "source_row_id" in frame and "source_row_id" in held:
            if not {"date", "region"}.issubset(frame) or not {"date", "region"}.issubset(held):
                raise ValueError("홀드아웃 비교의 날짜·지역 근거가 없습니다")
            if frame.source_row_id.duplicated().any() or held.source_row_id.duplicated().any():
                raise ValueError("홀드아웃 비교의 원행 식별자가 중복됩니다")
            pair = frame.merge(held, on="source_row_id", suffixes=("_seen", "_held"), validate="one_to_one")
            if len(pair) != len(held) or pair.empty or not np.array_equal(_numbers(pair, "actual_won_seen"), _numbers(pair, "actual_won_held")):
                raise ValueError("홀드아웃 비교의 계약 행·정답이 일치하지 않습니다")
            for field in ("date", "region", "cluster_id"):
                if f"{field}_seen" in pair and f"{field}_held" in pair and not pair[f"{field}_seen"].astype(str).equals(pair[f"{field}_held"].astype(str)):
                    raise ValueError(f"홀드아웃 비교의 {field} 값이 일치하지 않습니다")
            delta = np.abs(_numbers(pair, "actual_won_seen") - _numbers(pair, "prediction_won_held")) - np.abs(_numbers(pair, "actual_won_seen") - _numbers(pair, "prediction_won_seen"))
            boot, clusters = None, None
            if "cluster_id_seen" in pair and pair.cluster_id_seen.notna().all() and pair.cluster_id_seen.astype(str).str.strip().ne("").all():
                stats = pd.DataFrame({"id": pair.cluster_id_seen, "loss": delta, "n": 1}).groupby("id")[["loss", "n"]].sum().to_numpy()
                clusters = len(stats)
                if clusters >= config.minimum_clusters:
                    rng = np.random.default_rng(config.seed + 5)
                    boot = []
                    for _ in range(config.bootstrap_replicates):
                        values = stats[rng.integers(0, clusters, size=clusters)].sum(axis=0)
                        boot.append(values[0] / values[1])
            _finish(h5, float(delta.mean()), boot, config, len(pair), clusters)
        hypotheses.append(h5)
    hypotheses.sort(key=lambda row: (int(row["id"][1:]), row["target"]))
    return {"config": asdict(config), "hypotheses": hypotheses, "supplementary": supplementary, "sources": SOURCES,
            "inference": {"method": "단지 군집 percentile bootstrap; 지역 지표는 지역 내 군집 재표집", "family_size": 15,
                          "marginal_interval_confidence": 1 - (1 - config.confidence) / 15,
                          "target_family_confidence": config.confidence,
                          "warning": "근사적·학습된 모델 조건부 추론입니다. 시간 이동·군집 간 의존·작은 표본에서 보장하지 않습니다. 유의확률은 산출하지 않습니다."}}


def write_research_results(output: Path, summary: dict, *, config=None, holdout_result=None):
    output = Path(output)
    tests, calibrations, held = {}, {}, {}
    if holdout_result is not None:
        held_summary = json.loads((Path(holdout_result) / "summary.json").read_text(encoding="utf-8"))
        if summary.get("holdout_region") or not held_summary.get("holdout_region") or held_summary.get("mode") != summary.get("mode"):
            raise ValueError("일반 시간분할과 명시된 지역 홀드아웃 실행만 비교할 수 있습니다")
        def fingerprints(value):
            sources = value.get("provenance", {}).get("sources", [])
            result = []
            for s in sources:
                digest = str(s.get("verified_sha256", s.get("sha256", "")))
                raw_snapshot = s.get("snapshot_id")
                snapshot = raw_snapshot.strip() if isinstance(raw_snapshot, str) else ""
                count = s.get("rows")
                if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest) or not snapshot or isinstance(count, bool) or not isinstance(count, int) or count <= 0:
                    raise ValueError("홀드아웃 비교의 입력 스냅숏 근거가 유효하지 않습니다")
                result.append((digest.lower(), snapshot, count))
            return sorted(result)
        if not fingerprints(summary) or fingerprints(summary) != fingerprints(held_summary):
            raise ValueError("홀드아웃 비교의 입력 스냅숏 근거가 없거나 서로 다릅니다")
    for target in ("jeonse", "monthly"):
        for source, name in ((tests, f"{target}_predictions.csv"), (calibrations, f"{target}_calibration_predictions.csv")):
            path = output / name
            if path.is_file():
                source[target] = pd.read_csv(path, keep_default_na=False)
        if holdout_result is not None:
            path = Path(holdout_result) / f"{target}_predictions.csv"
            if path.is_file():
                held[target] = pd.read_csv(path, keep_default_na=False)
                if "region" not in held[target] or not held[target].region.astype(str).str.split().str[0].eq(held_summary["holdout_region"]).all():
                    raise ValueError("홀드아웃 예측 행의 지역이 선언한 제외 지역과 다릅니다")
    result = evaluate_frames(tests, calibrations, summary.get("targets", {}), config=config, holdout_frames=held)
    result["mode"] = summary.get("mode")
    result["analysis_code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if summary.get("mode") == "SYNTHETIC":
        for row in result["hypotheses"]:
            row["decision"] = "inconclusive" if row["effect"] is not None else "unmeasured"
            row["reason"] = "합성 기술 검증이며 논문 가설의 실측 지지 근거가 아닙니다. " + row["reason"]
    records = [{**row, "ci": json.dumps(row["ci"], ensure_ascii=False)} for row in result["hypotheses"]]
    pd.DataFrame(records).to_csv(output / "hypothesis_results.csv", index=False, encoding="utf-8-sig")
    (output / "hypothesis_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    result["artifacts"] = [{"id": "hypothesis_results", "title": "8개 가설의 15개 목표별 평가", "status": "measured", "csv": "hypothesis_results.csv", "png": None}]
    return result
