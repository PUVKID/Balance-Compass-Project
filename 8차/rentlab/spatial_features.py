"""신뢰된 물리역 ID의 직선거리 산술만 수행한다.

원문 철도 CSV의 노선별 역번호를 facility_id로 자동 변환하지 않는다.
이 저수준 함수는 자료를 승인하지 않으며, 실험의 외부 특징 입력은
feature_store.validate_feature_manifest의 원천 자격 검사를 별도로 통과해야 한다.
과거 시설 운영/전국 역망 완전성/보행거리를 입증하지 않는다.
"""
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

EARTH_RADIUS_M=6371008.8


def station_features(origins, facilities):
    required={'latitude','longitude'}
    if not required.union({'cluster_id'}).issubset(origins) or not required.union({'facility_id','line'}).issubset(facilities):
        raise ValueError('좌표/식별자/노선 칼럼 누락')
    if origins.cluster_id.isna().any() or origins.cluster_id.astype(str).str.strip().eq('').any() or origins.cluster_id.duplicated().any():
        raise ValueError('단지 좌표 키 중복/누락')
    fac=facilities.copy()
    if fac.facility_id.isna().any() or fac.facility_id.astype(str).str.strip().eq('').any():raise ValueError('시설 ID 누락')
    if fac.line.isna().any() or fac.line.astype(str).str.strip().eq('').any():raise ValueError('노선 미상은 노선 수0으로 처리하지 않음')
    def coordinates(frame):
        xy=frame[['latitude','longitude']].apply(pd.to_numeric,errors='coerce')
        # 연구 대상의 넉넉한 대한민국 범위. 국경 판정·행정 경계 검사가 아니다.
        valid=xy.latitude.between(32,39.5)&xy.longitude.between(124,132)
        return xy,valid
    xy,valid=coordinates(origins);fxy,fvalid=coordinates(fac)
    if not fvalid.all() or not len(fac):raise ValueError('시설 좌표 오류/빈 목록: 시설을 조용히 제외하지 않음')
    fac[['latitude','longitude']]=fxy
    if (fac.groupby('facility_id')[['latitude','longitude']].nunique()>1).any().any():
        raise ValueError('같은 시설 ID의 좌표 충돌')
    unique=fac.drop_duplicates('facility_id').reset_index(drop=True)
    tree=BallTree(np.radians(unique[['latitude','longitude']].to_numpy()),metric='haversine')
    out=origins[['cluster_id']].copy()
    for name in ['station_distance_m','stations_500m','stations_1000m','lines_1000m','transfer_distance_m']:out[name]=np.nan
    out['coordinate_status']=np.where(valid,'available',np.where(xy.isna().any(axis=1),'missing','invalid'))
    if not valid.any():return out
    points=np.radians(xy.loc[valid].to_numpy());d,_=tree.query(points,k=1)
    out.loc[valid,'station_distance_m']=d[:,0]*EARTH_RADIUS_M
    nearby=tree.query_radius(points,r=1000/EARTH_RADIUS_M)
    for i,ids in zip(out.index[valid],nearby):
        station_ids=set(unique.iloc[ids].facility_id)
        lines=fac[fac.facility_id.isin(station_ids)].line.dropna().astype(str)
        if lines.str.strip().eq('').any():raise ValueError('노선 미상은 노선 수0으로 처리하지 않음')
        out.loc[i,'stations_1000m']=len(station_ids);out.loc[i,'lines_1000m']=lines.nunique()
    out.loc[valid,'stations_500m']=tree.query_radius(points,r=500/EARTH_RADIUS_M,count_only=True)
    line_counts=fac.groupby('facility_id').line.nunique()
    transfers=unique[unique.facility_id.isin(line_counts[line_counts>=2].index)]
    if len(transfers):
        transfer_tree=BallTree(np.radians(transfers[['latitude','longitude']].to_numpy()),metric='haversine')
        out.loc[valid,'transfer_distance_m']=transfer_tree.query(points,k=1)[0][:,0]*EARTH_RADIUS_M
    out.attrs.update({'distance':'haversine straight-line metres; not walking distance',
                      'historical_availability_proven':False,'earth_radius_m':EARTH_RADIUS_M})
    return out
