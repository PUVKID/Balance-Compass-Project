"""모델을 불러오거나 학습하지 않고 외부 특징 스냅숏의 입력 자격을 확인한다."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from .feature_store import validate_feature_manifest


def inspect_snapshot(manifest=None):
    """입력 기술 검사이며 표본·연결 정답·역사·자원·학습 승인 검증을 대신하지 않는다."""
    report=dict(schema_version=1,checked_at=datetime.now(timezone.utc).isoformat(),
                status='missing_input',scope='feature_input_validation_only',training_started=False,
                experiment_readiness='not_evaluated',historical_availability_proven=False,
                source_completeness_proven=False,manifest_sha256=None,observations=None,
                feature_profile={},errors=[],limitations=[
                    '형식·해시·원천 자격 검사를 통과해도 실제 학습 실행 승인이 아니다.',
                    '계약과의 실제 결합·분할별 결측·독립 연결 정답·표본 선택 편향·자원 사용은 별도 검증해야 한다.',
                    '원천의 과거 운영·공표 이력과 전국 목록 완전성은 이 보고서가 입증하지 않는다.'])
    report['validation_code_sha256']={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
        for name in ('input_contracts.py','feature_store.py','facility_quality.py','feature_preflight.py')}
    if manifest is None:
        report['errors']=[dict(type='MissingInput',message='승인할 외부 특징 manifest가 제공되지 않았습니다.')]
        return report
    try:
        path=Path(manifest).resolve(strict=True);raw=path.read_bytes()
        report['manifest_sha256']=hashlib.sha256(raw).hexdigest()
        descriptor=json.loads(raw.decode('utf-8-sig'))
        observations=validate_feature_manifest(descriptor,path.parent)
        for feature,part in observations.groupby('feature',sort=True):
            values=part.value.astype(float)
            report['feature_profile'][feature]=dict(rows=len(part),entities=int(part.entity_key.nunique()),
                sources=int(part.source_id.nunique()),value_min=float(values.min()),value_max=float(values.max()),
                valid_from_range=[part.valid_from.min(),part.valid_from.max()],
                open_ended_rows=int(part.valid_to.eq('').sum()))
        report.update(status='validated_input_only',observations=len(observations),features=len(descriptor['features']),
                      source_count=len(descriptor['sources']),key_column=descriptor['key_column'],
                      observation_sha256=descriptor['sha256'])
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        report.update(status='invalid_input',feature_profile={},observations=None)
        report['errors']=[dict(type=type(error).__name__,message=str(error))]
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features',type=Path,help='검사할 외부 특징 manifest; 미제공 시 미준비 보고서')
    parser.add_argument('--output',type=Path,help='새 JSON 보고서 파일; 기존 파일을 덮어쓰지 않음')
    args=parser.parse_args(argv)
    report=inspect_snapshot(args.features)
    text=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)
    try:
        if args.output:
            with args.output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text+'\n')
        else:print(text)
    except OSError as error:
        print('사전 검사 보고서 저장 실패: '+type(error).__name__)
        return 2
    return 0 if report['status']=='validated_input_only' else 2


if __name__=='__main__':raise SystemExit(main())
