"""보존된 시설 취득 스냅숏을 검사한다. 학습·다운로드·원문 수정을 수행하지 않는다."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rentlab.facility_quality import source_report
from rentlab.runtime import atomic_json, now
from audit_national_sources import read_source, digest


def audit(project, output, *, as_of, reference_start, historical_cutoff='2025-12-31'):
    project, output = Path(project).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('새 시설 감사 출력 폴더 필요')
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.facility-audit-', dir=output.parent))
    try:
        records = []
        for kind, relative in [('SCHOOL', '외부 자료/1차/학교'), ('PARK', '외부 자료/1차/공원'),
                               ('RAIL', '외부 자료/1차/철도역'), ('KAPT', '외부 자료/2차/KAPT_검증취득')]:
            folder = project / relative
            manifest_bytes = (folder/'manifest.json').read_bytes()
            rows, manifest = read_source(folder)  # 원응답 해시, CSV 해시와 행 수를 확인한다.
            source = (folder/manifest['data_path']).resolve(strict=True)
            for label, cutoff, first in [('snapshot_policy', as_of, reference_start),
                                          ('research_end', historical_cutoff, historical_cutoff[:4]+'-01-01')]:
                report = source_report(source, source_id=manifest['source_id'], kind=kind,
                                       as_of=cutoff, reference_start=first)
                if report['source_sha256'] != manifest['data_sha256'] or report['rows'] != len(rows):
                    raise ValueError('감사 원천 SHA/행수 불일치')
                name = f'{kind}_{label}.json'
                atomic_json(stage/name, report)
                records.append(dict(kind=kind, claim=label, path=name, sha256=digest(stage/name),
                                    source_id=manifest['source_id'], source_sha256=report['source_sha256'],
                                    rows=report['rows'], eligible_rows=len(report['eligible_rows']),
                                    all_rows_eligible=report['all_rows_eligible'],
                                    reason_counts=report['reason_counts'],
                                    identifier_duplicate_groups=report['identifier_duplicate_groups'],
                                    identifier_coordinate_conflicts=report['identifier_coordinate_conflicts']))
            if digest(source) != manifest['data_sha256'] or (folder/'manifest.json').read_bytes() != manifest_bytes:
                raise ValueError('시설 원자료/manifest가 감사 중 변경됨')
        summary = dict(created_at=now(), status='audited_not_feature_or_historical_approval',
                       model_training_executed=False, raw_sources_modified=False,
                       historical_availability_proven=False, source_completeness_proven=False,
                       policy=dict(as_of=as_of, reference_start=reference_start, historical_cutoff=historical_cutoff,
                                   note='명시한 감사 기준일 범위이며 보편적인 최신성 보장 기준이 아님'),
                       reports=records)
        atomic_json(stage/'manifest.json', summary)
        stage.rename(output)
        return summary
    except BaseException:
        if stage.resolve().parent != output.parent.resolve() or not stage.name.startswith('.facility-audit-'):
            raise RuntimeError('감사 임시 폴더 경계 오류')
        shutil.rmtree(stage)
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--as-of', required=True); p.add_argument('--reference-start', required=True)
    p.add_argument('--historical-cutoff', default='2025-12-31')
    a = p.parse_args()
    try:
        print(json.dumps(audit(a.project, a.output, as_of=a.as_of, reference_start=a.reference_start,
                               historical_cutoff=a.historical_cutoff), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as error:
        print(f'시설 감사 실패: {error}', file=sys.stderr)
        raise SystemExit(2)
