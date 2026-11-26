"""원천의 기계적 자격 검사이며 과거 운영이나 전국 목록 완전성의 증명은 별도다."""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path


SCHEMAS = {
    'SCHOOL': dict(identifier=['학교ID'], name='학교명', start='설립일자', latitude='위도', longitude='경도'),
    'PARK': dict(identifier=['관리번호'], name='공원명', start='지정고시일', latitude='위도', longitude='경도'),
    'RAIL': dict(identifier=['운영기관명', '노선번호', '역번호'], name='역사명', start=None, latitude='역위도', longitude='역경도'),
    'KAPT': dict(identifier=['단지코드'], name='단지명', start='사용승인일', latitude=None, longitude=None),
}


def _clean(value):
    return ' '.join(str(value or '').split())


def _day(value):
    text = _clean(value)
    if not text:
        return None
    if len(text) == 8 and text.isascii() and text.isdigit():
        return datetime.strptime(text, '%Y%m%d').date()
    parsed = date.fromisoformat(text)
    if parsed.isoformat() != text:
        raise ValueError('ISO 일자 필요')
    return parsed


def _coordinate(row, schema):
    if schema['latitude'] is None:
        return None
    try:
        lat, lon = (float(row.get(schema[key], '')) for key in ('latitude', 'longitude'))
    except (ValueError, TypeError):
        return None
    if not (math.isfinite(lat) and math.isfinite(lon) and 32 <= lat <= 39.5 and 124 <= lon <= 132):
        return None
    return lat, lon


def qualify_rows(rows, kind, *, as_of, reference_start):
    """원문 행마다 상태를 보존하며 미해결 행이 있으면 전체 원천 승인을 차단한다.

    reference_start는 명시한 감사 정책이며 검증된 보편적 최신성 문턱이 아니다.
    RAIL의 운영기관/노선/역번호는 후보 원천 키이며 검증된 물리역 ID가 아니다.
    KAPT에는 원천 관측일 칼럼이 없으며 취득일/파일명 날짜로 대체하지 않는다.
    """
    if kind not in SCHEMAS:
        raise ValueError('지원하지 않는 시설 종류')
    cutoff, first = _day(as_of), _day(reference_start)
    if cutoff is None or first is None or first > cutoff:
        raise ValueError('시설 감사 기준일/기준일 범위 오류')
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError('빈/비정상 시설 원행')
    schema = SCHEMAS[kind]
    required = set(schema['identifier']) | {schema['name']}
    if any(not required.issubset(row) for row in rows):
        raise ValueError('시설 종류의 식별/이름 칼럼 누락')
    identifiers, groups, coordinates = [], defaultdict(list), []
    for i, row in enumerate(rows):
        parts = [_clean(row.get(key)) for key in schema['identifier']]
        identifier = json.dumps(parts, ensure_ascii=False, separators=(',', ':')) if all(parts) else ''
        identifiers.append(identifier)
        if identifier:
            groups[identifier].append(i)
        coordinates.append(_coordinate(row, schema))
    duplicates = {key: indices for key, indices in groups.items() if len(indices) > 1}
    coordinate_conflicts = sum(len({coordinates[i] for i in indices}) > 1 for indices in duplicates.values())
    name_conflicts = sum(len({_clean(rows[i].get(schema['name'])) for i in indices}) > 1 for indices in duplicates.values())
    status, reasons, refs, starts = [], Counter(), [], []
    for i, row in enumerate(rows):
        problems = []
        if not identifiers[i]:
            problems.append('identifier_missing')
        elif identifiers[i] in duplicates:
            problems.append('ambiguous_identifier')
        if not _clean(row.get(schema['name'])):
            problems.append('name_missing')
        if schema['latitude'] is not None and coordinates[i] is None:
            problems.append('invalid_coordinates')
        try:
            reference = _day(row.get('데이터기준일자', ''))
        except ValueError:
            reference = None; problems.append('invalid_reference_date')
        if reference is None:
            problems.append('reference_date_unknown')
        else:
            refs.append(reference.isoformat())
            if reference < first:
                problems.append('stale_reference')
            elif reference > cutoff:
                problems.append('future_reference')
        try:
            start = _day(row.get(schema['start'], '')) if schema['start'] else None
        except ValueError:
            start = None; problems.append('invalid_start_date')
        if start is None:
            problems.append('start_date_unknown')
        else:
            starts.append(start.isoformat())
            if start > cutoff:
                problems.append('future_start')
        if kind == 'SCHOOL' and _clean(row.get('운영상태')) != '운영':
            problems.append('inactive_or_unknown_operation')
        if kind == 'PARK':
            try:
                area = float(row.get('공원면적', ''))
                if not math.isfinite(area) or area <= 0:
                    raise ValueError()
            except (TypeError, ValueError):
                problems.append('park_area_missing_or_invalid')
        if kind == 'RAIL':
            problems.append('physical_identity_unproven')
        if kind == 'KAPT':
            from .complex_linkage import derive_features
            try:
                derive_features(row)
            except (ValueError, OverflowError):
                problems.append('invalid_building_attributes')
        reasons.update(problems)
        status.append(dict(source_row=i + 1, identifier=identifiers[i],
                           eligible=not problems, reasons=sorted(set(problems))))
    return dict(schema_version=1, kind=kind, parameters=dict(as_of=cutoff.isoformat(), reference_start=first.isoformat()),
                rows=len(rows), eligible_rows=[r['source_row'] for r in status if r['eligible']],
                all_rows_eligible=all(r['eligible'] for r in status),
                identifier_duplicate_groups=len(duplicates), identifier_extra_rows=sum(len(v)-1 for v in duplicates.values()),
                identifier_coordinate_conflicts=coordinate_conflicts, identifier_name_conflicts=name_conflicts,
                reference_date_range=[min(refs), max(refs)] if refs else None,
                start_date_range=[min(starts), max(starts)] if starts else None,
                reference_date_counts=dict(sorted(Counter(refs).items())), reason_counts=dict(sorted(reasons.items())),
                row_status=status, historical_availability_proven=False, source_completeness_proven=False,
                limitations=['ID 일치/유효 좌표/명시한 기준일 범위의 기계 검사이며 물리 시설 정답 검증을 대신하지 않음.',
                             '기준일·설립/고시/승인일은 과거 위치/운영/주차 상태와 공표 이력의 증거가 아님.',
                             '원행 일부 보류는 전국 전체 목록 자격을 부여하지 않음. 원문 행을 삭제/평균/첫 행 선택하지 않음.',
                             '철도 복합 키는 물리역 ID가 아니며 KAPT 파일명/취득일을 관측 기준일로 대체하지 않음.'])


def source_report(path, *, source_id, kind, as_of, reference_start):
    path = Path(path)
    raw = path.read_bytes()
    import io
    with io.StringIO(raw.decode('utf-8-sig'), newline='') as stream:
        reader = csv.DictReader(stream, strict=True)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('시설 CSV 머리글 오류')
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError('시설 CSV 열 수 오류')
    result = qualify_rows(rows, kind, as_of=as_of, reference_start=reference_start)
    result.update(source_id=source_id, source_sha256=hashlib.sha256(raw).hexdigest())
    return result


def validate_quality_reports(descriptor, observations, root, sources, checked, guarded_features):
    """해시 확인 CSV에서 보고서를 재계산하며 저장된 eligible=true만 신뢰하지 않는다."""
    guarded = observations[observations.feature.isin(guarded_features)]
    if guarded.empty:
        return
    records = descriptor.get('quality_reports')
    if not isinstance(records, list) or not records:
        raise ValueError('시설·단지 특징의 quality 자격 보고서 필요')
    proofs = {}
    source_by_id = {source['source_id']: source for source in sources}
    for record in records:
        if (not isinstance(record, dict) or not {'source_id', 'path', 'sha256'}.issubset(record)
                or record['source_id'] in proofs or record['source_id'] not in source_by_id):
            raise ValueError('시설 자격 보고서 목록 오류')
        report = json.loads(checked(record).read_text(encoding='utf-8-sig'))
        source = source_by_id[record['source_id']]
        if not isinstance(report, dict) or set(report.get('parameters', {})) != {'as_of', 'reference_start'}:
            raise ValueError('시설 자격 보고서 매개변수 오류')
        recomputed = source_report(checked(source), source_id=source['source_id'], kind=report.get('kind'), **report['parameters'])
        if report != recomputed or report.get('source_sha256') != source['sha256'] or report.get('rows') != source['rows']:
            raise ValueError('시설 자격 보고서 재계산/원천 불일치')
        if not report['all_rows_eligible']:
            raise ValueError('시설 자격 미충족: 모호·오류·시점 미확인 원행 존재')
        proofs[record['source_id']] = report
    building = {'households', 'buildings', 'max_floor', 'relative_floor', 'parking_per_household',
                'elevators_per_household', 'coverage_ratio', 'floor_area_ratio'}
    for row in guarded.itertuples(index=False):
        if row.source_id not in proofs:
            raise ValueError('시설 특징 원천의 자격 보고서 누락')
        kind = ('KAPT' if row.feature in building else 'SCHOOL' if row.feature.startswith(('primary_', 'middle_', 'high_'))
                else 'PARK' if row.feature.startswith('park_') else 'RAIL' if row.feature.startswith(('station', 'lines_', 'transfer_')) else None)
        proof = proofs[row.source_id]
        if kind is None or proof['kind'] != kind:
            raise ValueError('시설 특징과 자격 보고서 종류(kind) 불일치')
        if not hasattr(row, 'valid_from'):
            raise ValueError('시설 특징 유효 시점 누락')
        source = source_by_id[row.source_id]
        acquired = datetime.fromisoformat(source['acquired_at'].replace('Z', '+00:00'))
        from zoneinfo import ZoneInfo
        earliest = max(_day(proof['parameters']['as_of']), acquired.astimezone(ZoneInfo('Asia/Seoul')).date())
        try:
            valid_from = _day(row.valid_from)
        except ValueError as error:
            raise ValueError('시설 특징 유효 시점 오류') from error
        if valid_from is None or valid_from < earliest:
            raise ValueError('과거 이력 미입증 시설 특징의 유효 시점 소급 금지')
