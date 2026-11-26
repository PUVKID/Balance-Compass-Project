"""현재 KAPT 단지 식별을 위한 보수적 연결. 과거 건물 상태를 인증하지 않음."""
from collections import defaultdict
from .national_sources import number

ELEVATORS=['승강기(승객용)','승강기(화물용)','승강기(승객+화물)','승강기(장애인)','승강기(비상용)','승강기(기타)']


def clean(value):
    return ' '.join(str(value or '').split())


def build_index(sources):
    legal=defaultdict(list); road=defaultdict(list); codes=set()
    for row in sources:
        code=clean(row.get('단지코드'));name=clean(row.get('단지명'))
        if not code or code in codes:raise ValueError('단지코드 누락/중복')
        codes.add(code)
        address=clean(row.get('법정동주소'));street=clean(row.get('도로명주소'))
        if not name:continue
        # 공식 법정동주소 끝에 단지명이 정확하게 있을 때만 제거한다.
        if address.endswith(' '+name):legal[(address[:-len(name)-1],name)].append(row)
        if street:road[(street,name)].append(row)
    return dict(legal=legal,road=road)


def match_complex(contract,index):
    region=clean(contract.get('시군구'));parcel=clean(contract.get('번지'));name=clean(contract.get('단지명'))
    street=clean(contract.get('도로명'))
    if any(v in {'','-'} for v in [region,parcel,name,street]):return dict(status='incomplete_contract_key',source=None)
    left=index['legal'].get((region+' '+parcel,name),[])
    if not left:return dict(status='unmatched',source=None)
    # 원문 도로명은 시도/시군구가 없으므로 후보의 전체 주소와 토큰 경계를 확인한다.
    candidates=[r for r in left if clean(r.get('도로명주소')).endswith(' '+street)
                and clean(r.get('도로명주소')).startswith(region.split()[0]+' ')]
    if len(candidates)>1:return dict(status='ambiguous',source=None)
    if not candidates:return dict(status='address_disagreement',source=None)
    return dict(status='matched_dual_address_name',source=dict(candidates[0]))


def derive_features(row):
    def get(key):return number(clean(row.get(key)),integer=True)
    households=get('세대수')
    if households is None or households<=0:raise ValueError('유효한 세대 수 없음')
    buildings=get('동수');parking=get('총주차대수');elevators=[get(k) for k in ELEVATORS]
    maximum=get('최고층수(건축물대장상)')
    if maximum in (None,0):maximum=get('최고층수')
    return dict(households=households,buildings=buildings if buildings and buildings>0 else None,
                max_floor=maximum if maximum and maximum>0 else None,
                parking_per_household=None if parking is None else parking/households,
                elevators_per_household=None if any(v is None for v in elevators) else sum(elevators)/households)
