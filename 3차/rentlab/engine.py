"""스냅숏 검증, 시간 분할, 비교 모델 및 예측구간 평가."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["시군구", "전용면적(㎡)", "계약년월", "계약일", "보증금(만원)", "월세금(만원)", "층", "건축년도", "계약구분"]
NUMERIC = ["area", "floor", "age", "month"]
CATEGORICAL = ["region"]


def rust_binary() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    path = ROOT / "rust_money" / "target" / "release" / ("bc-money" + suffix)
    if not path.is_file():
        raise ValueError(f"Rust 금액 엔진이 없습니다. rust_money에서 cargo build --release 실행 필요: {path}")
    return path


def normalize_money(values: list[str]) -> list[int]:
    # 모든 금액을 한 번의 실제 Rust 프로세스로 보내며 Python 실수로 변환하지 않는다.
    if any("\n" in str(v) or "\r" in str(v) for v in values):
        raise ValueError("금액 내부 개행은 허용되지 않습니다")
    completed = subprocess.run([str(rust_binary())], input="\n".join(values) + "\n", text=True,
                               encoding="utf-8", capture_output=True, timeout=120, check=False)
    if completed.returncode:
        raise ValueError(f"Rust 금액 검증 실패(exit={completed.returncode}): {completed.stderr.strip()}")
    result = [int(v) for v in completed.stdout.splitlines()]
    if len(result) != len(values):
        raise ValueError("Rust 출력 행 수가 입력과 다릅니다")
    return result


def read_manifest(path: Path) -> tuple[pd.DataFrame, dict]:
    path = path.resolve(strict=True)
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest 최상위는 객체여야 합니다")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("전국 실측 자료가 없습니다: manifest.files에 원본 CSV가 필요합니다")
    seen_paths, seen_hashes, frames, sources = set(), set(), [], []
    scopes = []
    for entry in entries:
        required = {"path", "sha256", "rows", "source_url", "acquired_at", "snapshot_id"}
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise ValueError(f"파일 manifest 필수 필드: {sorted(required)}")
        for field in ("path", "sha256", "source_url", "acquired_at", "snapshot_id"):
            if not isinstance(entry[field], str) or not entry[field].strip():
                raise ValueError(f"manifest {field}는 비어 있지 않은 문자열이어야 합니다")
        if not __import__("re").fullmatch(r"[0-9a-fA-F]{64}", entry["sha256"]):
            raise ValueError("manifest SHA-256 형식 오류")
        if isinstance(entry["rows"], bool) or not isinstance(entry["rows"], int) or entry["rows"] < 1:
            raise ValueError("manifest rows는 양의 정수여야 합니다")
        source = (path.parent / entry["path"]).resolve(strict=True)
        original_bytes = source.read_bytes()
        digest = hashlib.sha256(original_bytes).hexdigest()
        if source in seen_paths or digest in seen_hashes:
            raise ValueError("중복 경로 또는 동일 원본 파일의 범위 중복입니다")
        if digest.lower() != str(entry["sha256"]).lower():
            raise ValueError(f"원본 SHA-256 불일치: {source.name}")
        if not str(entry["source_url"]).startswith("https://") or not entry["snapshot_id"]:
            raise ValueError("출처 HTTPS URL과 snapshot_id가 필요합니다")
        datetime.fromisoformat(str(entry["acquired_at"]).replace("Z", "+00:00"))
        # 해시를 검사한 같은 바이트에 엄격 UTF-8을 우선 적용하고 디코딩 실패일 때만 CP949를 시도한다.
        encoding = "utf-8-sig"
        try:
            original_bytes.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            encoding = "cp949"
            try:
                original_bytes.decode(encoding, errors="strict")
            except UnicodeDecodeError as error:
                raise ValueError(f"CSV 인코딩 오류: UTF-8 또는 CP949로 저장한 공식 CSV가 필요합니다: {source.name}") from error
        frame = pd.read_csv(io.BytesIO(original_bytes), dtype=str, encoding=encoding, encoding_errors="strict", keep_default_na=False)
        if isinstance(entry["rows"], bool) or not isinstance(entry["rows"], int) or entry["rows"] != len(frame):
            raise ValueError(f"원본 행 수 불일치: {source.name}")
        if frame.empty or not set(COLUMNS).issubset(frame.columns):
            raise ValueError(f"빈 자료 또는 공식 CSV 필수 칼럼 누락: {source.name}")
        # 내용상 같은 지역·계약월을 포함하는 파일은 신고 범위가 겹칠 수 있어 병합을 거부한다.
        scope = set(zip(frame["시군구"].str.strip(), frame["계약년월"].str.strip()))
        if any(scope & previous for previous in scopes):
            raise ValueError("파일 사이 시군구·계약년월 범위 중복: 원본 범위를 분리해 제출하십시오")
        scopes.append(scope)
        seen_paths.add(source)
        seen_hashes.add(digest)
        if "source_file" not in frame:
            frame["source_file"] = str(source)
        if "source_row" not in frame:
            frame["source_row"] = np.arange(1, len(frame) + 1)
        frames.append(frame)
        sources.append({**entry, "resolved_path": str(source), "verified_sha256": digest, "encoding": encoding})
    return pd.concat(frames, ignore_index=True), {"manifest": str(path), "sources": sources}


def prepare(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    data = raw.copy()
    if not set(COLUMNS).issubset(data.columns):
        raise ValueError("공식 CSV 필수 칼럼 누락")
    if "source_file" not in data:
        data["source_file"] = "in_memory"
    if "source_row" not in data:
        data["source_row"] = data.groupby("source_file", sort=False).cumcount() + 1
    if "source_row_id" not in data:
        data["source_row_id"] = data["source_file"].astype(str) + ":" + data["source_row"].astype(str)
    if "cluster_id" not in data:
        data["cluster_id"] = pd.NA
    data["cluster_id"] = data["cluster_id"].replace("", pd.NA)
    money = normalize_money(data["보증금(만원)"].tolist() + data["월세금(만원)"].tolist())
    n = len(data)
    data["deposit"] = money[:n]
    data["rent"] = money[n:]
    data["region"] = data["시군구"].str.strip()
    data["area"] = pd.to_numeric(data["전용면적(㎡)"], errors="coerce")
    floor_text = data["층"].fillna("").astype(str).str.strip()
    data["floor"] = pd.to_numeric(floor_text, errors="coerce")
    built = pd.to_numeric(data["건축년도"], errors="coerce")
    year_month = data["계약년월"].fillna("").astype(str).str.strip()
    day = data["계약일"].fillna("").astype(str).str.strip()
    valid_shape = year_month.str.fullmatch(r"[0-9]{6}") & day.str.fullmatch(r"[0-9]{1,2}")
    dates = pd.to_datetime((year_month + day.str.zfill(2)).where(valid_shape), format="%Y%m%d", errors="coerce")
    data["date"] = dates
    data["month"] = dates.dt.month
    data["age"] = dates.dt.year - built
    reasons = pd.Series("", index=data.index, dtype=str)
    def reject(mask, label):
        reasons.loc[mask & reasons.eq("")] = label
    reject(~data["계약구분"].str.strip().isin(["신규", "신규계약"]), "not_new_contract")
    cancellation_observed = data["해제사유발생일"].notna() if "해제사유발생일" in data else pd.Series(False, index=data.index)
    if "해제사유발생일" in data:
        reject(cancellation_observed & data["해제사유발생일"].fillna("").str.strip().ne(""), "cancelled")
    reject(dates.isna(), "invalid_date")
    reject(data["region"].eq(""), "missing_region")
    reject(~np.isfinite(data["area"]) | (data["area"] <= 0), "invalid_area")
    reject(floor_text.ne("") & (~np.isfinite(data["floor"]) | data["floor"].mod(1).ne(0)), "invalid_floor")
    reject(built.isna() | ~np.isfinite(built) | built.mod(1).ne(0) | (built < 1800) | (built > dates.dt.year), "invalid_build_year")
    reject((data["deposit"] <= 0) & (data["rent"] == 0), "invalid_amount")
    reject(~dates.dt.year.between(2022, 2025), "outside_protocol")
    data["exclusion_reason"] = reasons
    audit = {"input_rows": n, "included_rows": int(reasons.eq("").sum()),
             "excluded_by_reason": {str(k): int(v) for k, v in reasons[reasons.ne("")].value_counts().items()},
             "projected_duplicate_rows_retained": int(raw.duplicated(subset=COLUMNS).sum()),
             "duplicate_definition": "필수 학습 9열 투영 일치; 공개 원행 중복과 다름; 삭제하지 않음",
             "missing_floor_rows": int(floor_text.eq("").sum()),
             "cancellation_observability": {"observed_rows": int(cancellation_observed.sum()), "unobserved_rows": int((~cancellation_observed).sum()), "status": "observed" if cancellation_observed.all() else "partial" if cancellation_observed.any() else "unavailable"},
             "cluster_observability": {"available_rows": int(data.cluster_id.notna().sum()), "unavailable_rows": int(data.cluster_id.isna().sum())},
             "contract_categories_by_year": [{"year": str(year), "category": str(category), "n": int(len(group)), "included_n": int(group.exclusion_reason.eq("").sum())} for (year, category), group in data.groupby([year_month.str[:4], "계약구분"], dropna=False)],
             "contract_categories": {str(k): int(v) for k, v in raw["계약구분"].value_counts().items()}}
    return data, audit


def split_data(data: pd.DataFrame, holdout_region: str | None = None) -> dict[str, pd.DataFrame]:
    dates = data["date"]
    masks = {"train": dates.between("2022-01-01", "2023-12-31"),
             "validation": dates.between("2024-01-01", "2024-06-30"),
             "calibration": dates.between("2024-07-01", "2024-12-31"),
             "test": dates.between("2025-01-01", "2025-12-31")}
    if holdout_region:
        held = data["region"].eq(holdout_region) | data["region"].str.startswith(holdout_region + " ")
        if not held.any():
            raise ValueError(f"홀드아웃 지역이 없습니다: {holdout_region}")
        for name in ("train", "validation", "calibration"):
            masks[name] &= ~held
        masks["test"] &= held
    result = {name: data.loc[mask].copy() for name, mask in masks.items()}
    if any(frame.empty for frame in result.values()):
        raise ValueError(f"프로토콜 분할에 빈 자료가 있습니다: { {k:len(v) for k,v in result.items()} }")
    return result


def conformal_radius(residuals, alpha=0.1):
    values = np.asarray(residuals, dtype=float)
    if not 0 < alpha < 1 or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("보정 잔차와 alpha가 유효하지 않습니다")
    rank = math.ceil((len(values) + 1) * (1 - alpha))
    if rank > len(values) or not len(values):
        return None
    return float(np.partition(values, rank - 1)[rank - 1])


def metrics(actual, predicted, radius=None, alpha=0.1):
    y, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    error = y - p
    result = {"n": len(y), "mae": float(np.abs(error).mean()), "rmse": float(np.sqrt(np.mean(error ** 2))),
              "coverage": None, "width": None, "interval_score": None}
    if radius is not None:
        low, high = p - radius, p + radius
        result.update(coverage=float(np.mean((low <= y) & (y <= high))), width=float(2 * radius),
                      interval_score=float(np.mean(2 * radius + 2 / alpha * np.maximum(low-y, 0) + 2 / alpha * np.maximum(y-high, 0))))
    return result


class HierarchicalRegions(BaseEstimator, TransformerMixin):
    """학습 시점과 무관한 지역명 분해로 상위 행정구역을 보존한다."""
    def fit(self, x, y=None):
        return self

    def transform(self, x):
        result = x.copy()
        parts = result["region"].fillna("").str.split()
        result["province"] = parts.str[0].fillna("")
        result["district"] = parts.map(lambda value: " ".join(value[:2]))
        return result


def preprocessor(numeric, *, sparse=False, hierarchical=False):
    transformers = [
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median", keep_empty_features=True)), ("scale", StandardScaler())]), numeric),
        ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=sparse, max_categories=64 if hierarchical else None), CATEGORICAL)]
    if hierarchical:
        transformers.append(("hierarchy", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["province", "district"]))
    return ColumnTransformer(transformers, sparse_threshold=1.0 if sparse else 0)


def ai_candidates(numeric):
    # Ridge는 전체 지역 희소 표현, HGB는 전체 상위 계층과 세부지역 상한을 사용한다.
    return {
        "ridge": Pipeline([("prepare", preprocessor(numeric, sparse=True)), ("model", Ridge(alpha=10, solver="lsqr"))]),
        "hist_gradient_boosting": Pipeline([("regions", HierarchicalRegions()), ("prepare", preprocessor(numeric, hierarchical=True)), ("model", HistGradientBoostingRegressor(max_iter=80, max_leaf_nodes=15, min_samples_leaf=10, early_stopping=False, random_state=42))])}


def fit_target(data: pd.DataFrame, target: str, holdout: str | None):
    if target not in {"jeonse", "monthly"}:
        raise ValueError("목표는 jeonse 또는 monthly여야 합니다")
    frames = split_data(data, holdout)
    numeric = NUMERIC + (["deposit"] if target == "monthly" else [])
    features = numeric + CATEGORICAL
    response = "rent" if target == "monthly" else "deposit"
    train = frames["train"]
    x, y = train[features], train[response]
    candidates = {"global_median": DummyRegressor(strategy="median"), **ai_candidates(numeric)}
    predictions, validation, estimators = {}, {}, {}
    for name, model in candidates.items():
        model.fit(x if name != "global_median" else np.zeros((len(x), 1)), y)
        predictions[name] = {key: model.predict(frame[features] if name != "global_median" else np.zeros((len(frame), 1))) for key, frame in frames.items() if key != "train"}
        validation[name] = metrics(frames["validation"][response], predictions[name]["validation"])
        estimator = model.named_steps["model"] if isinstance(model, Pipeline) else model
        iterations = getattr(estimator, "n_iter_", None)
        estimators[name] = {"parameters": estimator.get_params(), "actual_n_iter": np.asarray(iterations).tolist() if iterations is not None else None}
    medians, fallback = train.groupby("region")[response].median(), float(y.median())
    predictions["region_median"] = {key: frame["region"].map(medians).fillna(fallback).to_numpy() for key, frame in frames.items() if key != "train"}
    validation["region_median"] = metrics(frames["validation"][response], predictions["region_median"]["validation"])
    selected = min(validation, key=lambda key: (validation[key]["mae"], key))
    best_ai = min(ai_candidates(numeric), key=lambda key: (validation[key]["mae"], key))
    no_deposit_best = None
    no_deposit_predictions = {}
    no_deposit_validation = {}
    no_deposit_estimators = {}
    if target == "monthly":
        for name, model in ai_candidates(NUMERIC).items():
            model.fit(train[NUMERIC + CATEGORICAL], y)
            estimator = model.named_steps["model"]
            iterations = getattr(estimator, "n_iter_", None)
            no_deposit_estimators[name] = {"parameters": estimator.get_params(), "actual_n_iter": np.asarray(iterations).tolist() if iterations is not None else None}
            no_deposit_predictions[name] = {key: model.predict(frame[NUMERIC + CATEGORICAL]) for key, frame in frames.items() if key != "train"}
            no_deposit_validation[name] = metrics(frames["validation"][response], no_deposit_predictions[name]["validation"])
        no_deposit_best = min(no_deposit_validation, key=lambda key: (no_deposit_validation[key]["mae"], key))
    radii = {name: conformal_radius(np.abs(frames["calibration"][response].to_numpy() - values["calibration"])) for name, values in predictions.items()}
    radius = radii[selected]
    for key in ("validation", "calibration", "test"):
        frame = frames[key]
        frame["actual_won"] = frame[response]
        frame["prediction_won"] = predictions[selected][key]
        frame["lower_won"] = frame.prediction_won - radius if radius is not None else np.nan
        frame["upper_won"] = frame.prediction_won + radius if radius is not None else np.nan
        for name, values in predictions.items():
            frame[f"prediction_{name}_won"] = values[key]
        frame["prediction_ai_won"] = predictions[best_ai][key]
        if target == "monthly":
            frame["prediction_no_deposit_won"] = no_deposit_predictions[no_deposit_best][key]
    test = frames["test"]
    groups = [{"region": str(region), **metrics(group.actual_won, group.prediction_won, radius)} for region, group in test.groupby("region")]
    return {"selected_model": selected, "best_ai_model": best_ai, "no_deposit_best_ai_model": no_deposit_best,
            "no_deposit_validation": no_deposit_validation, "no_deposit_estimator_details": no_deposit_estimators,
            "validation": validation, "candidate_test_metrics": {name: metrics(test.actual_won, values["test"], radii[name]) for name, values in predictions.items()},
            "metrics": metrics(test.actual_won, test.prediction_won, radius), "groups": groups,
            "train_target_median_won": fallback, "train_price_edges_won": np.unique(np.quantile(y, [0, .2, .4, .6, .8, 1])).tolist(),
            "train_price_quantiles_won": np.quantile(y, [0, .2, .4, .6, .8, 1]).tolist(),
            "estimator_details": estimators, "versions": {"numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__, "python": sys.version.split()[0]},
            "region_representation": {"ridge": "전체 세부 지역 one-hot, 희소 행렬, 상한 없음", "hist_gradient_boosting": "전체 시도·시군구 one-hot + 세부 지역 최대 64; 학습 범주만 추정, target encoding 없음", "hgb_fine_region_max_categories": 64, "train_fine_region_count": int(train.region.nunique())},
            "conformal_radius_won": radius, "interval_status": "available" if radius is not None else "insufficient_calibration",
            "split_counts": {key: len(frame) for key, frame in frames.items()},
            "interpretation": "관측 보증금을 조건으로 한 월세 예측" if target == "monthly" else "전세 보증금 예측"}, test, frames


PURPOSES = [
    ("split_counts", "시간 분할별 표본 수"), ("audit", "제외 사유별 표본 수"),
    ("target_counts", "전세·월세 표본 수"), ("region_counts", "지역별 표본 수"),
    ("year_counts", "연도별 표본 수"), ("month_counts", "월별 계절 분포"),
    ("area_distribution", "전용면적 분포"), ("age_distribution", "건물 연령 분포"),
    ("floor_distribution", "층수 분포"), ("deposit_distribution", "분석 포함 전체 계약의 보증금 분포"),
    ("rent_distribution", "분석 포함 전체 계약의 월세 분포(전세 0 포함)"), ("validation_mae", "검증 모델별 MAE"),
    ("validation_rmse", "검증 모델별 RMSE"), ("test_mae", "목표별 테스트 MAE"),
    ("test_rmse", "목표별 테스트 RMSE"), ("coverage", "목표별 구간 포함률"),
    ("width", "목표별 구간 폭"), ("interval_score", "목표별 구간 점수"),
    ("regional_mae", "지역별 테스트 MAE"), ("regional_coverage", "지역별 구간 포함률"),
    ("regional_counts", "지역별 테스트 표본 수"), ("residual_distribution", "테스트 절대오차 분포"),
    ("prediction_distribution", "테스트 예측값 분포"), ("actual_distribution", "테스트 실제값 분포"),
    ("monthly_test_mae", "계약월별 테스트 MAE"), ("area_test_mae", "면적 구간별 테스트 MAE"),
    ("age_test_mae", "연령 구간별 테스트 MAE"), ("floor_test_mae", "층 구간별 테스트 MAE"),
    ("regional_macro_mae", "지역 동일 가중 MAE"), ("price_test_mae", "가격 구간별 테스트 MAE"),
    ("cluster_bootstrap", "단지 군집 부트스트랩"), ("regional_conformal", "지역별 별도 보정 비교"),
    ("quantile_interval", "분위수 모델 구간 비교"), ("report_delay", "신고 지연 민감도"),
    ("renewal_sensitivity", "갱신 계약 민감도")]


def write_artifacts(output, summary, data, tests):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font_path = ROOT / "web" / "NanumGothic-Bold.ttf"
    if not font_path.is_file():
        raise ValueError(f"그래프용 나눔고딕700 파일이 없습니다: {font_path}")
    font_manager.fontManager.addfont(str(font_path))
    plt.rcParams.update({"font.family": font_manager.FontProperties(fname=str(font_path)).get_name(),
                         "font.weight": "bold", "axes.unicode_minus": False})
    tables = {}
    tables["split_counts"] = pd.DataFrame([{"label": f"{target}/{split}", "value": count} for target, counts in summary["split_counts"].items() for split, count in counts.items()])
    tables["audit"] = pd.DataFrame([{"label": reason, "value": count} for reason, count in summary["audit"]["excluded_by_reason"].items()] or [{"label": "excluded", "value": 0}])
    tables["target_counts"] = pd.DataFrame([{"label": "jeonse", "value": int(data.rent.eq(0).sum())}, {"label": "monthly", "value": int(data.rent.gt(0).sum())}])
    for name, series in [("region_counts", data.region), ("year_counts", data.date.dt.year), ("month_counts", data.date.dt.month)]:
        tables[name] = series.value_counts().sort_index().rename_axis("label").reset_index(name="value")
    for name, column in [("area_distribution", "area"), ("age_distribution", "age"), ("floor_distribution", "floor"), ("deposit_distribution", "deposit"), ("rent_distribution", "rent")]:
        counts = pd.cut(data[column], bins=10, duplicates="drop").value_counts(sort=False)
        tables[name] = pd.DataFrame({"label": counts.index.astype(str), "value": counts.values})
    for score in ["mae", "rmse"]:
        tables[f"validation_{score}"] = pd.DataFrame([{"target": target, "label": model, "value": scores[score]} for target, result in summary["targets"].items() for model, scores in result["validation"].items()])
    for score in ["mae", "rmse", "coverage", "width", "interval_score"]:
        tables["test_" + score if score in ["mae", "rmse"] else score] = pd.DataFrame([{"target": target, "label": target, "value": result["metrics"][score]} for target, result in summary["targets"].items()])
    all_test = pd.concat([frame.assign(target=target) for target, frame in tests.items()], ignore_index=True)
    all_test["absolute_error"] = (all_test.actual_won-all_test.prediction_won).abs()
    for name, column in [("residual_distribution", "absolute_error"), ("prediction_distribution", "prediction_won"), ("actual_distribution", "actual_won")]:
        distributions = []
        for target, group in all_test.groupby("target"):
            counts = pd.cut(group[column], bins=10, duplicates="drop").value_counts(sort=False)
            distributions.append(pd.DataFrame({"target": target, "label": counts.index.astype(str), "value": counts.values}))
        tables[name] = pd.concat(distributions, ignore_index=True)
    for name, score in [("regional_mae", "mae"), ("regional_coverage", "coverage"), ("regional_counts", "n")]:
        tables[name] = pd.DataFrame([{"target": target, "label": group["region"], "value": group[score], "n": group["n"], "coverage": group["coverage"]} for target, result in summary["targets"].items() for group in result["groups"]])
    tables["regional_macro_mae"] = pd.DataFrame([{"target": target, "label": target, "value": float(np.mean([g["mae"] for g in result["groups"]]))} for target, result in summary["targets"].items()])
    for name, column in [("monthly_test_mae", "month"), ("area_test_mae", "area"), ("age_test_mae", "age"), ("floor_test_mae", "floor"), ("price_test_mae", "actual_won")]:
        rows = []
        for target, group in all_test.groupby("target"):
            if name == "price_test_mae":
                frozen = summary["targets"][target]["train_price_edges_won"]
                # 학습 범위를 벗어난 미래 가격도 바깥 구간에 포함한다.
                edges = [-np.inf, *frozen[1:-1], np.inf]
                bins = pd.cut(group[column], bins=edges, include_lowest=True)
            else:
                bins = group[column] if column == "month" else pd.cut(all_test[column], bins=5, duplicates="drop").loc[group.index]
            for label, subgroup in group.groupby(bins, observed=True):
                valid_interval = subgroup.lower_won.notna() & subgroup.upper_won.notna()
                coverage = float(((subgroup.actual_won >= subgroup.lower_won) & (subgroup.actual_won <= subgroup.upper_won)).loc[valid_interval].mean()) if valid_interval.any() else None
                rows.append({"target": target, "label": str(label), "value": float(subgroup.absolute_error.mean()), "n": len(subgroup), "interval_n": int(valid_interval.sum()), "coverage": coverage})
        tables[name] = pd.DataFrame(rows)
    artifacts = []
    for name, title in PURPOSES:
        item = {"id": name, "title": title, "status": "unmeasured", "csv": None, "png": None}
        table = tables.get(name)
        if table is not None and not table.empty and table["value"].notna().any():
            table.to_csv(output / f"{name}.csv", index=False, encoding="utf-8-sig")
            panels = list(table.groupby("target", sort=False)) if "target" in table else [(None, table)]
            fig, axes = plt.subplots(len(panels), 1, figsize=(10, 4 * len(panels)), squeeze=False)
            displayed = 0
            panel_metadata = []
            for axis, (target, panel) in zip(axes[:, 0], panels):
                plot = panel.dropna(subset=["value"]).head(50)
                displayed += len(plot)
                eligible = int(panel.value.notna().sum())
                panel_metadata.append({"target": target, "displayed_rows": len(plot), "total_rows": len(panel), "eligible_rows": eligible, "row_limit": 50, "truncated": eligible > 50})
                axis.bar(np.arange(len(plot)), plot.value, color="#4168D6")
                axis.set_xticks(np.arange(len(plot)), plot.label.astype(str), rotation=75, fontsize=7)
                target_title = {"jeonse": "전세 보증금", "monthly": "월세(관측 보증금 조건부)"}.get(target, "")
                axis.set_title(title + (f" · {target_title}" if target else "") + (" [합성 검증]" if summary["mode"] == "SYNTHETIC" else "") + f"\n표시 {len(plot)}/{len(panel)}행 · 패널당 최대 50행 · 전체 CSV 제공")
                x_unit = {"area_distribution": "전용면적 구간(㎡)", "age_distribution": "건물 연령 구간(년)",
                          "floor_distribution": "층수 구간(층)", "deposit_distribution": "보증금 구간(원)",
                          "rent_distribution": "월세 구간(원)", "residual_distribution": "절대오차 구간(원)",
                          "prediction_distribution": "예측값 구간(원)", "actual_distribution": "실제값 구간(원)",
                          "area_test_mae": "전용면적 구간(㎡)", "age_test_mae": "건물 연령 구간(년)",
                          "floor_test_mae": "층수 구간(층)", "price_test_mae": "실제 가격 구간(원)",
                          "monthly_test_mae": "계약월"}.get(name, "분석 구분")
                axis.set_xlabel(x_unit)
                if plot.empty:
                    axis.text(0.5, 0.5, "보정 표본 부족: 미산출", ha="center", transform=axis.transAxes)
                unit = "포함률(0–1)" if "coverage" in name else "금액(원)" if any(key in name for key in ["mae", "rmse", "width", "score"]) else "표본 수(건)"
                axis.set_ylabel(unit)
            fig.tight_layout()
            fig.savefig(output / f"{name}.png", dpi=120)
            plt.close(fig)
            item.update(status="measured", csv=f"{name}.csv", png=f"{name}.png", displayed_rows=displayed, total_rows=len(table), row_limit_per_panel=50, panels=panel_metadata)
        else:
            item["reason"] = "필요한 입력 또는 구현이 없어 미측정"
        artifacts.append(item)
    return artifacts


def synthetic_data():
    rows = []
    for year, months in [(2022, [1, 7]), (2023, [1, 7]), (2024, [1, 7]), (2025, [1, 7])]:
        for month in months:
            for i in range(36):
                monthly = i % 2 == 0
                rows.append(dict(zip(COLUMNS, [f"합성시 지역{i%3}", str(40+i), f"{year}{month:02}", str(1+i%27), str(1000+i*30), str(30+i if monthly else 0), str(1+i%20), str(1990+i%25), "신규"])))
    return pd.DataFrame(rows)


def run(output: Path, manifest: Path | None = None, holdout_region=None, synthetic=False):
    created_at = datetime.now(timezone.utc).isoformat()
    output = output.resolve()
    if output.exists():
        raise ValueError(f"기존 출력은 덮어쓰지 않습니다: {output}")
    if synthetic:
        raw, provenance = synthetic_data(), {"manifest": None, "sources": [], "generator": "deterministic_smoke_v1"}
    else:
        if manifest is None:
            raise ValueError("전국 원본 manifest가 필요합니다. 합성 검증은 smoke를 사용하십시오")
        raw, provenance = read_manifest(manifest)
    prepared, audit = prepare(raw)
    data = prepared.loc[prepared.exclusion_reason.eq("")].copy()
    if data.empty:
        raise ValueError("주분석 신규계약이 없습니다")
    summary = {"mode": "SYNTHETIC" if synthetic else "REAL", "status": "running", "created_at": created_at,
               "rows": len(raw), "audit": audit, "provenance": {**provenance, "rust_binary": str(rust_binary()), "rust_sha256": hashlib.sha256(rust_binary().read_bytes()).hexdigest()},
               "holdout_region": holdout_region, "split_counts": {}, "targets": {},
               "limitations": ["실거래 공개 스냅숏이며 전국 임차가구 모집단이 아닙니다", "전국 지역 완전성은 별도 공식 코드 목록과 대조되지 않았습니다", "시간·지역 이동에서 90% 포함률을 보장하지 않습니다", "모델 선택은 2024 상반기 검증 MAE만 사용합니다", "월세는 관측 보증금 조건부 예측입니다", "가설별 계산·군집 불확실성·지역 보정 가능 여부는 research 상태를 확인하십시오", "분위수 비교·신고 지연·갱신 민감도는 미측정입니다"]}
    tests, evaluation_frames = {}, {}
    for target, mask in [("jeonse", data.rent.eq(0)), ("monthly", data.rent.gt(0))]:
        result, test, frames = fit_target(data.loc[mask], target, holdout_region)
        summary["targets"][target] = result
        summary["split_counts"][target] = result["split_counts"]
        tests[target] = test
        evaluation_frames[target] = frames
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rentlab-", dir=output.parent))
    try:
        prepared.to_csv(stage / "audit_rows.csv", index=False, encoding="utf-8-sig")
        for target, test in tests.items():
            test.to_csv(stage / f"{target}_predictions.csv", index=False, encoding="utf-8-sig")
            for split in ("validation", "calibration"):
                if split in evaluation_frames[target]:
                    evaluation_frames[target][split].to_csv(stage / f"{target}_{split}_predictions.csv", index=False, encoding="utf-8-sig")
        summary["artifacts"] = write_artifacts(stage, summary, data, tests)
        from rentlab.research_metrics import write_research_results
        summary["research"] = write_research_results(stage, summary)
        summary["research_hypotheses"] = summary["research"]["hypotheses"]
        summary["artifacts"].extend(summary["research"].get("artifacts", []))
        summary["status"] = "completed"
        summary["completed_at"] = datetime.now(timezone.utc).isoformat()
        (stage / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        if output.exists():
            raise ValueError("출력 경로가 실행 중 생성되어 보존합니다")
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="전국 아파트 임대료 연구 CPU 엔진")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--manifest", type=Path, required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--manifest", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--holdout-region")
    smoke = sub.add_parser("smoke")
    smoke.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            raw, provenance = read_manifest(args.manifest)
            _, audit = prepare(raw)
            print(json.dumps({"status": "validated", "rows": len(raw), "audit": audit, "provenance": provenance}, ensure_ascii=False, allow_nan=False))
        else:
            result = run(args.output, getattr(args, "manifest", None), getattr(args, "holdout_region", None), args.command == "smoke")
            print(json.dumps({"mode": result["mode"], "status": result["status"], "output": str(args.output.resolve())}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f"연구 실행 실패: {error}", file=sys.stderr)
        return 2
