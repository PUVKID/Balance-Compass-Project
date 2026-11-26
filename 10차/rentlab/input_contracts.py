"""저장 표 구조와 홀드아웃 고정 실행 조건의 공통 계약."""
import csv
import io
import pandas as pd


def strict_csv(raw, *, required=(), encoding='utf-8-sig', dtype=str):
    """같은 바이트의 원문 열·행 수를 확인하고 문자열 값을 보존한다."""
    try:
        text=raw.decode(encoding)
        if '\x00' in text:raise ValueError('CSV NUL 문자로 인한 셀 잘림 위험')
        reader=csv.reader(io.StringIO(text,newline=''),strict=True)
        header=next(reader,None)
        if (not header or any(not name.strip() for name in header)
                or len(set(header))!=len(header) or not set(required).issubset(header)):
            raise ValueError('CSV 머리글 중복/공란/필수 칼럼 누락')
        for number,row in enumerate(reader,2):
            if len(row)!=len(header):raise ValueError(f'CSV {number}번째 논리 행의 칼럼 수 불일치/빈 행')
    except (csv.Error,UnicodeError,LookupError) as error:
        raise ValueError('CSV 인코딩/인용 구조 오류') from error
    # 검사를 위해 원행 목록을 복제하지 않는다. 같은 바이트를 읽어 문자열 ID를 보존한다.
    return pd.read_csv(io.BytesIO(raw),encoding=encoding,dtype=dtype,keep_default_na=False)


def validate_holdout_settings(ordinary, held):
    """고정 버전/추정기 인자는 같아야 하며 학습된 선택값/반복수는 비교하지 않는다."""
    targets=ordinary.get('targets');other_targets=held.get('targets')
    if not isinstance(targets,dict) or not isinstance(other_targets,dict) or set(targets)!=set(other_targets):
        raise ValueError('일반/홀드아웃 목표 집합 불일치')
    for name,metadata in targets.items():
        other=other_targets[name]
        if not isinstance(metadata,dict) or not isinstance(other,dict):raise ValueError('목표별 메타데이터 형식 오류')
        for field in ('versions','estimator_details','no_deposit_estimator_details'):
            left,right=metadata.get(field,{}),other.get(field,{})
            if not isinstance(left,dict) or not isinstance(right,dict):raise ValueError('실행 버전/설정 형식 오류')
            if field=='versions':
                if left!=right:raise ValueError('일반/홀드아웃 실행 라이브러리 버전 불일치')
            else:
                if any(not isinstance(v,dict) or not isinstance(v.get('parameters'),dict) for v in list(left.values())+list(right.values())):
                    raise ValueError('추정기 고정 설정 근거 누락/오류')
                if {k:v['parameters'] for k,v in left.items()}!={k:v['parameters'] for k,v in right.items()}:
                    raise ValueError('일반/홀드아웃 추정기 설정 불일치')
        if ordinary.get('mode')=='REAL' and (not metadata.get('versions') or not metadata.get('estimator_details')):
            raise ValueError('REAL 홀드아웃 실행 버전/고정 설정 근거 누락')
