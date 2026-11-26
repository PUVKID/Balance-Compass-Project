"""등록된 외부 수치 특징의 날짜·공표시점 결합. 계약 원행을 복제하지 않는다."""
from __future__ import annotations
from datetime import datetime
import hashlib
import csv
from pathlib import Path
import numpy as np
import pandas as pd

# 원자료의 정답이나 임의 칼럼을 특징 이름으로 주입할 수 없다.
FEATURES={
 'building':['households','buildings','max_floor','relative_floor','parking_per_household',
             'elevators_per_household','coverage_ratio','floor_area_ratio'],
 'access':['station_distance_m','stations_500m','stations_1000m','lines_1000m','transfer_distance_m',
           'primary_distance_m','middle_distance_m','high_distance_m','primary_count_1000m',
           'park_distance_m','park_area_1000m','hospital_distance_m','hospital_count_1000m'],
 'supply_demand':['population','resident_households','population_yoy','households_yoy',
                  'persons_per_household','unsold','completed_unsold'],
 'market':['base_rate','lending_rate','cpi','jeonse_index','monthly_index','jeonse_index_yoy','monthly_index_yoy'],
 'lagged_prices':['rent_count_90d','rent_count_180d','jeonse_median_per_m2','monthly_median_per_m2',
                  'sale_count_180d','sale_median_per_m2','days_from_published_contract']}
ALLOWED={x for group in FEATURES.values() for x in group}
MODES={'strict_asof','retrospective_snapshot'}


def validate_feature_manifest(descriptor, root):
    """해시·행수·등록 특징·원천 파일 근거 확인. 날짜의 역사적 사실성 자체를 인증하지 않는다."""
    root=Path(root).resolve()
    required={'path','sha256','rows','features','sources','status','key_column'}
    if not required.issubset(descriptor) or descriptor['status']!='verified_feature_snapshot':
        raise ValueError('특징 스냅숏 명세 누락/미검증')
    if not descriptor['features'] or len(descriptor['features'])!=len(set(descriptor['features'])) or not set(descriptor['features']).issubset(ALLOWED):
        raise ValueError('특징 목록 오류')
    if descriptor['key_column'] not in {'cluster_id','region'}:raise ValueError('허용하지 않는 결합키')
    def checked(record):
        p=(root/record['path']).resolve(strict=True)
        if not p.is_relative_to(root):raise ValueError('특징/원천 파일 범위 이탈')
        digest=hashlib.sha256()
        with p.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        if digest.hexdigest()!=record['sha256']:raise ValueError('특징/원천 해시 불일치')
        return p
    sources=descriptor['sources']
    if not isinstance(sources,list) or not sources:raise ValueError('원천 증거 없음')
    identifiers=set()
    for source in sources:
        if not {'path','sha256','source_id','source_url','acquired_at','status','rows'}.issubset(source):raise ValueError('원천 명세 누락')
        if source['status']!='acquired_current_snapshot' or not source['source_url'].startswith('https://'):
            raise ValueError('격리/미취득 원천 또는 출처 오류')
        try:acquired=datetime.fromisoformat(str(source['acquired_at']).replace('Z','+00:00'))
        except ValueError as e:raise ValueError('원천 취득 시각 오류') from e
        if acquired.tzinfo is None:raise ValueError('원천 취득 시각 시간대 누락')
        p=checked(source)
        if p.suffix.lower()!='.csv':raise ValueError('원천 표준 CSV만 지원: 원 JSON도 별도 보존 필요')
        with p.open(encoding=source.get('encoding','utf-8-sig'),newline='') as stream:
            reader=csv.reader(stream,strict=True);header=next(reader,None);count=0
            if not header or len(set(header))!=len(header):raise ValueError('원천 머리글 오류')
            for row in reader:
                if len(row)!=len(header):raise ValueError('원천 칼럼 수 오류')
                count+=1
        if isinstance(source['rows'],bool) or not isinstance(source['rows'],int) or source['rows']!=count:
            raise ValueError('원천 행 수 불일치')
        identifiers.add(source['source_id'])
    path=checked(descriptor)
    obs=pd.read_csv(path,dtype=str,keep_default_na=False)
    if not isinstance(descriptor['rows'],int) or isinstance(descriptor['rows'],bool) or len(obs)!=descriptor['rows']:
        raise ValueError('특징 행 수 불일치')
    if not {'feature','source_id'}.issubset(obs) or set(obs.feature)!=set(descriptor['features']) or not set(obs.source_id).issubset(identifiers):
        raise ValueError('특징/원천 목록 불일치')
    return obs


def join_features(contracts, observations, mode='strict_asof', key_column='cluster_id'):
    if mode not in MODES:raise ValueError('평가 모드 오류')
    required={'source_row_id','date',key_column}
    if not required.issubset(contracts):raise ValueError('계약 식별/날짜/결합키 누락')
    if contracts.source_row_id.isna().any() or contracts.source_row_id.astype(str).str.strip().eq('').any() or contracts.source_row_id.duplicated().any():
        raise ValueError('계약 원행 ID 중복/누락')
    required_obs={'entity_key','feature','value','valid_from','valid_to','published_at','source_id','record_id'}
    if not required_obs.issubset(observations):raise ValueError('외부 관측 명세 누락')
    obs=observations.copy()
    for col in ('entity_key','feature','source_id','record_id'):
        if obs[col].isna().any() or obs[col].astype(str).str.strip().eq('').any():raise ValueError(f'{col} 누락')
    if not set(obs.feature).issubset(ALLOWED):raise ValueError('등록되지 않은 특징 또는 정답 파생 입력')
    if set(obs.feature)&set(contracts.columns):raise ValueError('기존 계약 칼럼 충돌')
    obs['value']=pd.to_numeric(obs.value,errors='coerce')
    if not np.isfinite(obs.value).all():raise ValueError('비수치/무한대 특징')
    for col in ('valid_from','valid_to'):
        original=obs[col].fillna('').astype(str)
        obs[col]=pd.to_datetime(original,format='%Y-%m-%d',errors='coerce')
        if (original.ne('')&obs[col].isna()).any():raise ValueError(f'{col} 날짜 오류')
    if obs.valid_from.isna().any() or (obs.valid_to.notna()&(obs.valid_to<=obs.valid_from)).any():
        raise ValueError('유효기간 누락/역전')
    for value in obs.published_at:
        try:parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        except ValueError as e:raise ValueError('공표시점 형식 오류') from e
        if parsed.tzinfo is None:raise ValueError('공표시점에 시간대 필요')
    obs['published_at']=pd.to_datetime(obs.published_at,utc=True,errors='coerce',format='mixed')
    if obs.published_at.isna().any():raise ValueError('공표시점 누락/오류')
    if obs.duplicated(['entity_key','feature','valid_from','published_at']).any():raise ValueError('동일 시점 관측 중복/모호')
    if obs.duplicated(['source_id','record_id']).any():raise ValueError('원 관측 ID 중복')
    dates=pd.to_datetime(contracts.date,errors='coerce')
    if dates.isna().any():raise ValueError('계약일 누락/오류')
    if dates.dt.tz is not None:raise ValueError('계약일은 현지 달력 날짜여야 합니다')
    dates=dates.dt.normalize()
    cutoffs=dates.dt.tz_localize('Asia/Seoul').dt.tz_convert('UTC')
    frame=contracts.copy();audit={'mode':mode,'input_rows':len(frame),'output_rows':len(frame),
      'historical_availability_proven':False,'features':{},
      'availability_note':'관측의 공표/유효시점 조건만 검사. 원천 이력 증거 및 학습 정답 시점은 별도 검증 필요.'}
    # 같은 키·계약일을 묶어 계산량을 줄인다. 모호한 일대다를 펼치지 않고 정확히 한 값을 선택한다.
    queries=pd.DataFrame({'key':frame[key_column].fillna('').astype(str),'date':dates,'cutoff':cutoffs})
    for feature,part in obs.groupby('feature',sort=True):
        values={};lineage={}
        by_key={str(k):v for k,v in part.groupby('entity_key')}
        for key,day,cutoff in queries.drop_duplicates().itertuples(index=False,name=None):
            group=by_key.get(key)
            if group is None:continue
            eligible=group[(group.valid_from<=day)&(group.valid_to.isna()|(day<group.valid_to))]
            if mode=='strict_asof':eligible=eligible[eligible.published_at<cutoff]
            if eligible.empty:continue
            # 서로 다른 유효기간이 겹치고 최신 공표시점도 같다면 임의 선택하지 않는다.
            latest=eligible[eligible.published_at.eq(eligible.published_at.max())]
            if len(latest)!=1:raise ValueError('重複する有効期間の候補が曖昧')
            row=latest.iloc[0];values[(key,day)]=float(row.value)
            lineage[(key,day)]=str(row.source_id)+':'+str(row.record_id)
        pairs=list(zip(queries.key,queries.date))
        frame[feature]=[values.get(pair,np.nan) for pair in pairs]
        frame[feature+'__record']=[lineage.get(pair,'') for pair in pairs]
        frame[feature+'__missing']=frame[feature].isna().astype(int)
        audit['features'][feature]={'matched_rows':int(frame[feature].notna().sum()),
                                  'unmatched_rows':int(frame[feature].isna().sum()),'source_ids':sorted(set(part.source_id))}
    if len(frame)!=len(contracts) or frame.source_row_id.tolist()!=contracts.source_row_id.tolist():
        raise ValueError('결합 후 계약 원행 변경')
    return frame,audit
