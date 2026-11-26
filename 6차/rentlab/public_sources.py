"""공공데이터포털 표준자료의 공개 다운로드. 인증·제한 우회 없음."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import io
import re
from pathlib import Path
import tempfile
import shutil
import requests
from .runtime import atomic_json, now

STANDARD_IDS={'15021148':'SCHOOL','15012890':'PARK','15013205':'RAIL'}
FILE_IDS={'15106861':'COMPLEX_ID','15073271':'KAPT_FILE'}
BASE='https://www.data.go.kr'


def validate_pages(header, pages):
    total=header.get('totalCount')
    if isinstance(total,bool) or not isinstance(total,int) or total<1:
        raise ValueError('표준자료 전체 행 수 없음')
    columns=[x['columCode'] for x in header['columList']]
    if not columns or len(set(columns))!=len(columns):raise ValueError('칼럼 중복/누락')
    rows=[];seen=set()
    for page in pages:
        if not isinstance(page,list) or not page:raise ValueError('빈 페이지 또는 오류 응답')
        signature=hashlib.sha256(json.dumps(page,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if signature in seen:raise ValueError('동일 페이지 반복 수신')
        seen.add(signature)
        for row in page:
            if not isinstance(row,dict) or not set(columns).issubset(row):raise ValueError('응답 칼럼 누락')
        rows.extend(page)
    if len(rows)!=total:raise ValueError(f'전체 행 수 불일치: {len(rows)} / {total}')
    return rows


def collect_standard(public_id, output):
    if public_id not in STANDARD_IDS:raise ValueError('검토한 표준자료 ID만 허용')
    output=Path(output).resolve()
    if output.exists():raise ValueError('새 출력 폴더가 필요합니다')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.source-',dir=output.parent))
    try:
        with requests.Session() as session:
            session.headers['User-Agent']='BalanceCompassResearch/4 (public data download)'
            records=[]
            def fetch(name,url,params):
                r=session.get(url,params=params,timeout=(10,60));r.raise_for_status()
                data=r.json()  # HTML 오류·로그인 화면은 데이터로 저장하지 않는다.
                (stage/name).write_bytes(r.content)
                records.append({'path':name,'sha256':hashlib.sha256(r.content).hexdigest(),
                                'bytes':len(r.content),'url':r.url,'acquired_at':now(),'status_code':r.status_code})
                return data
            header=fetch('header.json',BASE+'/download/columList.json',{'pk':public_id,'ext':'CSV'})
            table=header['tableVO'];pages=[]
            total=header.get('totalCount')
            if isinstance(total,bool) or not isinstance(total,int) or not 0<total<=2000000:
                raise ValueError('전체 행 수 비정상')
            for page in range(1,math.ceil(total/10000)+1):
                params={'publicDataPk':public_id,'colNmList':table['colNmList'],
                        'svcTableNm':table['svcTableNm'],'totalCount':total,'perPage':10000,'page':page}
                pages.append(fetch(f'page_{page:04}.json',BASE+'/download/standard.json',params))
            rows=validate_pages(header,pages)
            after=session.get(BASE+'/download/columList.json',params={'pk':public_id,'ext':'CSV'},timeout=30)
            after.raise_for_status()
            current=after.json()
            if current.get('totalCount')!=total or current.get('columList')!=header['columList']:
                raise ValueError('취득 도중 전체 행 수/칼럼 변경')
        cols=header['columList']
        with (stage/'data.csv').open('x',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow([x['columNm'] for x in cols])
            writer.writerows([[r[x['columCode']] for x in cols] for r in rows])
        digest=hashlib.sha256((stage/'data.csv').read_bytes()).hexdigest()
        result={'schema_version':1,'status':'acquired_current_snapshot','source_id':STANDARD_IDS[public_id],
                'source_url':f'{BASE}/data/{public_id}/standard.do','rows':len(rows),'expected_rows':total,
                'data_path':'data.csv','data_sha256':digest,'raw_responses':records,'acquired_at':now(),
                'historical_availability_proven':False,'limitations':[
                    '현재 통합자료. 과거 위치·운영 상태를 입증하지 않음.',
                    '페이지 경계 중 원천 수정이 있었다면 동일 행 수여도 내용 변화를 배제할 수 없음.',
                    '취득 완료는 과거 계약에 매칭·사용 자격 통과를 의미하지 않음.']}
        atomic_json(stage/'manifest.json',result)
        stage.rename(output)
        return result
    except BaseException:
        shutil.rmtree(stage)
        raise


def collect_file(public_id, output):
    """사이트 다운로드 버튼과 동일한 공개 메타 조회·제한 확인·파일 취득."""
    if public_id not in FILE_IDS:raise ValueError('검토한 파일 ID만 허용')
    output=Path(output).resolve()
    if output.exists():raise ValueError('새 출력 폴더가 필요합니다')
    with requests.Session() as session:
        page=session.get(f'{BASE}/data/{public_id}/fileData.do',timeout=30);page.raise_for_status()
        pattern=r"fn_fileDataDown\('"+public_id+r"',\s*'([^']+)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)"
        match=re.search(pattern,page.text)
        if not match:raise ValueError('공개 파일 다운로드 버튼 명세를 찾지 못함')
        dpk,atch,sn,hist=match.groups()
        meta=session.get(BASE+'/tcs/dss/selectFileDataDownload.do',params={
            'publicDataPk':public_id,'publicDataDetailPk':dpk,'atchFileId':atch,'fileDetailSn':sn,
            'publicDataTyCode':'PR0051'},timeout=30);meta.raise_for_status();info=meta.json()
        if info.get('status') is not True:raise ValueError('공개 파일 조회 실패')
        params={'atchFileId':info['atchFileId'],'fileDetailSn':info['fileDetailSn']}
        check=session.post(BASE+'/cmm/cmm/check-limit.json',data=params,timeout=30)
        check.raise_for_status();limit=check.json()
        if limit.get('needCaptcha') is not False:raise ValueError('추가 인증 또는 제한 확인 필요; 자동 취득 중단')
        metadata=info['fileDataRegistVO'];params['dataNm']=metadata['dataNm']
        download=session.get(BASE+'/cmm/cmm/fileDownload.do',params=params,timeout=(10,60))
        download.raise_for_status();body=download.content
        if 'html' in download.headers.get('Content-Type','').lower() or not body:raise ValueError('파일 대신 오류 응답')
    if metadata.get('atchFileExtsn','').lower()!='csv':raise ValueError('검토한 CSV 파일만 허용')
    text=None
    for encoding in ('utf-8-sig','cp949'):
        try:text=body.decode(encoding);break
        except UnicodeDecodeError:pass
    if text is None:raise ValueError('CSV 디코딩 실패')
    reader=csv.reader(io.StringIO(text),strict=True);columns=next(reader);count=0
    if len(columns)<2 or len(columns)!=len(set(columns)):raise ValueError('CSV 머리글 오류')
    for row in reader:
        if len(row)!=len(columns):raise ValueError('CSV 칼럼 수 오류')
        count+=1
    advertised=metadata.get('atchFileCo')
    count_matches=not advertised or int(advertised)==count
    output.parent.mkdir(parents=True,exist_ok=True)
    output.mkdir(exist_ok=False)
    (output/'data.csv').write_bytes(body)
    result={'schema_version':1,'status':'acquired_current_snapshot' if count_matches else 'quarantined_count_mismatch','source_id':FILE_IDS[public_id],
      'source_url':f'{BASE}/data/{public_id}/fileData.do','rows':count,'data_path':'data.csv',
      'data_sha256':hashlib.sha256(body).hexdigest(),'encoding':encoding,'columns':columns,
      'source_file_name':metadata.get('orginlFileNm'),'acquired_at':now(),'advertised_rows':advertised,
      'historical_availability_proven':False,'limitations':['현재 파일. 과거 속성·주소·운영 이력을 입증하지 않음.']}
    atomic_json(output/'manifest.json',result)
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id',required=True,choices=list(STANDARD_IDS)+list(FILE_IDS));p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(argv)
    try:
        result=(collect_standard if a.id in STANDARD_IDS else collect_file)(a.id,a.output)
        print(json.dumps(result,ensure_ascii=False))
        return 0 if result['status']=='acquired_current_snapshot' else 2
    except (ValueError,OSError,requests.RequestException,KeyError) as e:print(f'자료 취득 실패: {e}');return 2

if __name__=='__main__':raise SystemExit(main())
