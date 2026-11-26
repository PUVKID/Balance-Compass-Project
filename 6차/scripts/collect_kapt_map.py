"""공개 지도에 실제 존재하는 시도 경계만 순차 조회. 현재 응답 원문 보존."""
import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
import requests
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rentlab.runtime import now,atomic_json


def collect(output,search_month):
    if not re.fullmatch(r'\d{4}(?:0[1-9]|1[0-2])',search_month):raise ValueError('검색월 형식 오류')
    output=Path(output).resolve()
    if output.exists():raise ValueError('새 출력 폴더 필요')
    output.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.map-',dir=output.parent))
    base='https://www.k-apt.go.kr'
    try:
        with requests.Session() as s:
            response=s.get(base+'/web/main/index.do',timeout=(10,60));response.raise_for_status()
            token=re.search(r'name="_csrf" content="([^"]+)"',response.text)
            if not token:raise ValueError('공개 페이지 CSRF 토큰 없음')
            response=s.post(base+'/cmmn/knewMapView.do',data={'go_url':'/kaptinfo/openkaptinfo.do','_csrf':token[1]},timeout=(10,60));response.raise_for_status()
            html=response.text;(stage/'source_page.html').write_bytes(response.content)
            token=re.search(r'name="_csrf" content="([^"]+)"',html)
            regions=re.findall(r'<map[^>]*id="map_(\d{2})"[^>]*title="([^"]+)"',html)
            if not token or not regions or len({c for c,n in regions})!=len(regions):raise ValueError('공개 지역 목록 누락/중복')
            response=s.get(base+'/knew/js/knew_map.js?v=2',timeout=(10,60));response.raise_for_status()
            (stage/'coordinate_method.js').write_bytes(response.content)
            receipts=[];total=0
            for code,name in regions:
                url=base+'/kaptinfo/getKaptInfo_poi.do'
                form={'bjdCode':code,'searchDate':search_month}
                response=s.post(url,data={**form,'_csrf':token[1]},headers={'Accept':'application/json'},timeout=(10,60));response.raise_for_status()
                rows=response.json().get('resultList')
                if not isinstance(rows,list):raise ValueError('지도 응답 구조 오류')
                filename=f'poi_{code}.json';(stage/filename).write_bytes(response.content);total+=len(rows)
                receipts.append(dict(path=filename,sha256=hashlib.sha256(response.content).hexdigest(),rows=len(rows),province_code=code,province_name=name,url=url,request=form,acquired_at=now()))
                print(code,name,len(rows),flush=True)
        result=dict(status='acquired_current_map_rows_pending_coordinate_validation',rows=total,receipts=receipts,
                    historical_availability_proven=False,feature_ready=False,created_at=now(),
                    source_page_sha256=hashlib.sha256((stage/'source_page.html').read_bytes()).hexdigest(),
                    coordinate_method_sha256=hashlib.sha256((stage/'coordinate_method.js').read_bytes()).hexdigest())
        atomic_json(stage/'manifest.json',result);stage.rename(output);return result
    except BaseException:shutil.rmtree(stage);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--search-month',required=True)
    args=parser.parse_args();print(json.dumps(collect(args.output,args.search_month),ensure_ascii=False,indent=2))
