"""실제 자료의 연결 자격만 감사한다. 모델을 학습하거나 입력을 승인하지 않는다."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rentlab.national_sources import population_before_month, rate_before_day, AmbiguousPopulationError
from rentlab.runtime import atomic_json, now


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''): result.update(chunk)
    return result.hexdigest()


def read_source(folder):
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    source = (folder/manifest['data_path']).resolve(strict=True)
    if not source.is_relative_to(folder.resolve()) or manifest['status'] != 'acquired_current_snapshot':
        raise ValueError('원천 경로/취득 상태 오류')
    if digest(source) != manifest['data_sha256']: raise ValueError('원천 해시 오류')
    for raw in manifest['raw_responses']:
        path = (folder/raw['path']).resolve(strict=True)
        if not path.is_relative_to(folder.resolve()) or digest(path) != raw['sha256']:
            raise ValueError('원응답 해시 오류')
    with source.open(encoding='utf-8-sig', newline='') as stream: rows = list(csv.DictReader(stream))
    if len(rows) != manifest['rows']: raise ValueError('원천 행 수 오류')
    return rows, manifest


def audit(project, output):
    project = Path(project).resolve(); output = Path(output).resolve()
    if output.exists(): raise ValueError('새 감사 파일 필요')
    population = []; source_receipts = []; quality = Counter()
    for year in range(2020, 2026):
        rows, receipt = read_source(project/f'외부 자료/2차/MOIS_{year}')
        population.extend(rows); source_receipts.append(receipt)
        quality.update(r['quality_status'] for r in rows)
    rates, receipt = read_source(project/'외부 자료/2차/BOK'); source_receipts.append(receipt)
    rates = [dict(decision_date=r['decision_date'], base_rate=float(r['base_rate'])) for r in rates]
    index = defaultdict(list); prior = {}
    for r in population:
        index[r['month']].append(r)
        key = (r['region_code'], r['month'])
        if key in prior: raise ValueError('지역 코드×월 중복')
        prior[key] = r
    # 입력의 원본 SHA/행수까지 검사한 후 캐시된 지역×계약월 연결만 집계한다.
    input_folder = project/'실제 실험/확장 입력 1차'
    manifest = json.loads((input_folder/'자료_manifest.json').read_text(encoding='utf-8-sig'))
    counts = defaultdict(Counter); provinces = defaultdict(Counter); cache = {}; files = []; rows_all = 0
    rate_counts = Counter(); examples = {}; resolution = Counter(); invalid_dates = 0
    for entry in manifest['files']:
        path = (input_folder/entry['path']).resolve(strict=True)
        if not path.is_relative_to(input_folder.resolve()) or digest(path) != entry['sha256']:
            raise ValueError('계약 입력 경로/해시 오류')
        n = 0
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                n += 1; rows_all += 1
                if row['계약구분'].strip() not in {'신규', '신규계약'}: continue
                ym = row['계약년월']; region = ' '.join(row['시군구'].split())
                try:
                    if len(ym) != 6 or not ym.isdigit(): raise ValueError('계약월 오류')
                    day = date(int(ym[:4]), int(ym[4:]), int(row['계약일'])).isoformat()
                except ValueError:
                    invalid_dates += 1; continue
                key = (region, ym)
                if key not in cache:
                    serial = int(ym[:4])*12+int(ym[4:])-3; yr, mo = divmod(serial, 12)
                    reference = f'{yr:04}-{mo+1:02}'
                    status = 'unmatched'
                    try:
                        matched = population_before_month(index[reference], region, day)
                    except AmbiguousPopulationError:
                        matched = None; status = 'ambiguous_hierarchy'
                    yoy = False
                    if matched:
                        status = 'local' if len(matched['region_name'].split()) >= 2 else 'province'
                        previous = prior.get((matched['region_code'], f'{yr-1:04}-{mo+1:02}'))
                        yoy = bool(previous and previous['quality_status'] == 'valid' and int(previous['population']) > 0)
                    cache[key] = (status, yoy, matched)
                status, yoy, matched = cache[key]
                counts[ym[:4]]['new_raw_rows_valid_date'] += 1
                counts[ym[:4]][status] += 1
                counts[ym[:4]]['same_code_yoy_available'] += int(yoy)
                provinces[region.split()[0]][status] += 1
                if status == 'unmatched' and len(examples) < 20: examples.setdefault(region, ym)
                if matched: resolution[matched['region_name']] += 1
                rate_counts['matched' if rate_before_day(rates, day) is not None else 'unmatched'] += 1
        if n != entry['rows'] or digest(path) != entry['sha256']: raise ValueError('계약 행수/처리 중 파일 변경')
        files.append(dict(path=entry['path'], rows=n, sha256=entry['sha256']))
        print(path.name, n, flush=True)
    result = dict(created_at=now(), status='audit_only_not_feature_approval', model_training_executed=False,
                  raw_contract_rows=rows_all, input_files=files, population_rows=len(population),
                  population_quality=dict(quality), rate_history_rows=len(rates), sources=source_receipts,
                  population_rule='계약월-2개월; 이름의 토큰 경계를 지킨 최장 접두사; 시군구 미일치 시 시도 연결 구분',
                  publication_rule_status='lag_assumption_not_verified_historical_publication',
                  rate_rule='결정일 < 계약일 (당일 변경 제외)', by_year={k:dict(v) for k,v in counts.items()},
                  by_province={k:dict(v) for k,v in provinces.items()}, rates=dict(rate_counts),
                  unmatched_examples=examples, invalid_new_contract_dates=invalid_dates,
                  historical_availability_proven=False, feature_ready=False,
                  limitations=['집계 대상은 원문 신규 계약이며 면적/가격/건축연도 정제 전. 최종 분석 표본과 다름.',
                               '공간 이름 정확 일치는 경계 불변/법정동과 행정동의 완전한 일치를 보증하지 않음.',
                               '시도 대체 연결은 세부 지역 특성 아님. 임의 행정구역 명칭 교정/보간 없음.',
                               '과거 통계의 현재 제공본이며 당시 발표 원본/수정 빈티지 증명 없음.',
                               '월 지연 2개월은 연구상 가정이며 공식 발표일을 생성하지 않음.',
                               '본 감사는 주택별 좌표·건물 자료와 통합한 최종 특징 스냅샷이 아님.'])
    atomic_json(output, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(); result = audit(args.project, args.output)
    print(json.dumps({k:result[k] for k in ['raw_contract_rows','population_rows','population_quality','by_year','rates']}, ensure_ascii=False, indent=2))
