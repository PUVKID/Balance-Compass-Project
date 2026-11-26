"""KAPT 지도 원좌표 검증. 공식 JS의 PROJ 정의 사용; 충돌 대표점 추정 금지."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import tempfile
from collections import Counter,defaultdict
from pathlib import Path
from pyproj import CRS,Transformer,__version__ as pyproj_version
from pyproj.exceptions import ProjError
from .runtime import now,atomic_json

# 공식 knew_map.js knew_fn_coordinate(flag=1)의 정의를 그대로 사용한다.
# 원문 주석의 EPSG 번호와 별도로 실제 매개변수 전체를 보존한다.
SOURCE_PROJ='+proj=tmerc +lat_0=38 +lon_0=127.0028902777778 +k=1 +x_0=200000 +y_0=500000 +ellps=bessel +units=m +no_defs +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43'


def validate_coordinates(records):
    if not records:raise ValueError('빈 지도 좌표 자료')
    grouped=defaultdict(list)
    for r in records:
        if not isinstance(r,dict) or not isinstance(r.get('kaptCode'),str) or not r['kaptCode'].strip():raise ValueError('단지코드 누락')
        grouped[r['kaptCode']].append(r)
    transformer=Transformer.from_crs(CRS.from_proj4(SOURCE_PROJ),CRS.from_epsg(4326),always_xy=True)
    result=[]
    for code,rows in sorted(grouped.items()):
        points=set();invalid=False;missing=False
        for r in rows:
            x,y=r.get('xCoord'),r.get('yCoord')
            if x is None or y is None:missing=True;continue
            try:
                if isinstance(x,bool) or isinstance(y,bool):raise ValueError('boolean coordinate')
                x,y=float(x),float(y)
                if not math.isfinite(x) or not math.isfinite(y) or (x==0 and y==0):raise ValueError('invalid coordinate')
                points.add((x,y))
            except (TypeError,ValueError):invalid=True
        lon=lat=None
        if invalid:status='invalid_coordinates'
        elif missing:status='missing_coordinates'
        elif len(points)!=1:status='conflicting_coordinates'
        else:
            x,y=next(iter(points))
            try:lon,lat=transformer.transform(x,y,errcheck=True)
            except (ProjError,ValueError,OverflowError):status='projection_error';lon=lat=None
            else:
                status='valid_current_map_point' if math.isfinite(lon) and math.isfinite(lat) and 124<=lon<=132 and 32<=lat<=39.5 else 'outside_korea_bounds'
                if status!='valid_current_map_point':lon=lat=None
        result.append(dict(kapt_code=code,longitude=lon,latitude=lat,coordinate_status=status,
                           source_rows=len(rows),distinct_source_points=len(points)))
    return result


def prepare_snapshot(raw_root,output):
    raw_root=Path(raw_root).resolve(strict=True);output=Path(output).resolve()
    if output.exists():raise ValueError('새 출력 폴더 필요')
    manifest_path=raw_root/'manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    rows=[];receipts=manifest.get('receipts',[])
    if not receipts:raise ValueError('원응답 영수증 없음')
    page_payload=(raw_root/'source_page.html').read_bytes();method=raw_root/'coordinate_method.js';method_payload=method.read_bytes()
    if hashlib.sha256(page_payload).hexdigest()!=manifest.get('source_page_sha256') or hashlib.sha256(method_payload).hexdigest()!=manifest.get('coordinate_method_sha256'):
        raise ValueError('지도 원페이지/변환 코드 해시 오류')
    page_codes=re.findall(r'<map[^>]*id="map_(\d{2})"',page_payload.decode('utf-8-sig'))
    if not page_codes or len(set(page_codes))!=len(page_codes):raise ValueError('지도 지역 목록 누락/중복')
    codes=set();months=set()
    for receipt in receipts:
        p=(raw_root/receipt['path']).resolve(strict=True)
        if not p.is_relative_to(raw_root):raise ValueError('원응답 경로 오류')
        payload=p.read_bytes()
        if hashlib.sha256(payload).hexdigest()!=receipt['sha256']:raise ValueError('원응답 해시 오류')
        if receipt['province_code'] in codes:raise ValueError('지역 중복')
        codes.add(receipt['province_code'])
        query=receipt.get('request',{});month=query.get('searchDate','')
        if query.get('bjdCode')!=receipt['province_code'] or not isinstance(month,str) or not re.fullmatch(r'\d{4}(?:0[1-9]|1[0-2])',month):raise ValueError('영수증 검색 지역/월 불일치')
        months.add(month)
        page=json.loads(payload.decode('utf-8-sig'))['resultList']
        if not isinstance(page,list) or len(page)!=receipt['rows']:raise ValueError('응답 행 수 오류')
        rows.extend(page)
    if len(rows)!=manifest['rows'] or codes!=set(page_codes) or len(months)!=1:raise ValueError('전체 행 수/지역/검색월 범위 오류')
    search_month=next(iter(months));method_text=method_payload.decode('utf-8-sig')
    if SOURCE_PROJ not in method_text:raise ValueError('공식 좌표 변환 정의 변경')
    normalized=validate_coordinates(rows)
    output.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.coords-',dir=output.parent))
    try:
        with (stage/'data.csv').open('x',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(normalized[0]));writer.writeheader();writer.writerows(normalized)
        result=dict(status='validated_current_coordinates_not_feature_approval',source_id='KAPT_PUBLIC_MAP',
                    source_url='https://www.k-apt.go.kr/cmmn/knewMapView.do',raw_root=str(raw_root),raw_rows=len(rows),
                    rows=len(normalized),coordinate_status=dict(Counter(r['coordinate_status'] for r in normalized)),
                    data_path='data.csv',data_sha256=hashlib.sha256((stage/'data.csv').read_bytes()).hexdigest(),
                    method_sha256=hashlib.sha256(method_payload).hexdigest(),source_proj=SOURCE_PROJ,search_month=search_month,
                    pyproj_version=pyproj_version,always_xy=True,acquired_at=now(),historical_availability_proven=False,
                    raw_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),feature_ready=False,
                    limitations=[f'공개 지도 검색월 {search_month}의 현재 응답이며 역사 좌표/운영 이력 증명 아님.',
                                 '원시 다중 좌표 단지는 대표점/평균/첫 좌표를 선택하지 않고 격리.',
                                 '지도의 단지점이며 중심점/출입구/측량점/보행거리로 해석할 수 없음.',
                                 '단지 전체·계약 모집단 포괄성은 별도 연결 감사 필요.'])
        atomic_json(stage/'manifest.json',result);stage.rename(output);return result
    except BaseException:shutil.rmtree(stage);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--raw-root',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(prepare_snapshot(args.raw_root,args.output),ensure_ascii=False,indent=2))
