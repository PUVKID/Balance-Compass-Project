"""K-apt 공개 자료실의 현재 기본정보. 원본 XLSX 보존, 연구용 열만 분리."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import requests
from .runtime import now, atomic_json

BASE = 'https://www.k-apt.go.kr'
PAGE = BASE+'/web/board/goKaptBasicExcelDownload.do'
NS = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
SELECTED = ['시도','시군구','읍면','동리','단지코드','단지명','단지분류','법정동주소','도로명주소',
            '분양형태','사용승인일','가입일','동수','세대수','관리방식','난방방식','복도유형','건물구조',
            '승강기(승객용)','승강기(화물용)','승강기(승객+화물)','승강기(장애인)','승강기(비상용)','승강기(기타)',
            '총주차대수','지상주차대수','지하주차대수','최고층수','최고층수(건축물대장상)','지하층수']


def parse_kapt_xlsx(payload: bytes) -> list[dict]:
    try:
        archive = ZipFile(io.BytesIO(payload))
    except BadZipFile as exc: raise ValueError('XLSX ZIP 형식 아님') from exc
    with archive:
        if 'xl/worksheets/sheet1.xml' not in archive.namelist(): raise ValueError('첫 시트 없음')
        if sum(i.file_size for i in archive.infolist()) > 1_000_000_000: raise ValueError('XLSX 확장 크기 초과')
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            for _, elem in ET.iterparse(archive.open('xl/sharedStrings.xml'), events=('end',)):
                if elem.tag == '{'+NS['m']+'}si':
                    strings.append(''.join(t.text or '' for t in elem.findall('.//m:t', NS))); elem.clear()
        result = []; headers = None; codes = set()
        for _, row in ET.iterparse(archive.open('xl/worksheets/sheet1.xml'), events=('end',)):
            if row.tag != '{'+NS['m']+'}row': continue
            n = int(row.attrib.get('r', 0)); values = {}; formula_columns = set()
            for cell in row.findall('m:c', NS):
                address = re.fullmatch(r'([A-Z]+)(\d+)', cell.attrib.get('r',''))
                if not address or int(address[2]) != n: raise ValueError('셀 주소 오류')
                col = 0
                for letter in address[1]: col = col*26+ord(letter)-64
                if col in values: raise ValueError('셀 중복')
                if cell.find('m:f', NS) is not None: formula_columns.add(col)
                if cell.attrib.get('t') == 'inlineStr':
                    text = ''.join(t.text or '' for t in cell.findall('.//m:t', NS))
                else:
                    value = cell.find('m:v', NS); text = '' if value is None else value.text or ''
                    if cell.attrib.get('t') == 's':
                        if not re.fullmatch(r'[0-9]+',text): raise ValueError('문자열 참조는 비음수 정수여야 함')
                        try: text = strings[int(text)]
                        except (ValueError, IndexError) as exc: raise ValueError('문자열 참조 오류') from exc
                    elif cell.attrib.get('t') == 'e': raise ValueError('Excel 오류 셀')
                values[col] = text
            if n == 2:
                if not values or len(values.values()) != len(set(values.values())): raise ValueError('머리글 중복')
                headers = {v:k for k,v in values.items()}
                if not {'단지코드','단지명','법정동주소','도로명주소','세대수'}.issubset(headers): raise ValueError('KAPT 필수 열 없음')
            elif n > 2 and any(values.values()):
                if headers is None: raise ValueError('머리글 순서 오류')
                code = values.get(headers['단지코드'],'')
                if not code or code in codes: raise ValueError('단지코드 누락/중복')
                if formula_columns & {headers[k] for k in SELECTED if k in headers}: raise ValueError('연구 입력 열에 수식 있음')
                codes.add(code)
                result.append({**{k:values.get(headers[k],'') for k in SELECTED if k in headers}, 'source_excel_row':n})
            row.clear()
    if not result: raise ValueError('KAPT 단지 자료 없음')
    return result


def collect_kapt(output):
    output = Path(output).resolve()
    if output.exists(): raise ValueError('새 출력 폴더 필요')
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.kapt-', dir=output.parent)); receipts = []
    try:
        with requests.Session() as session:
            session.headers['User-Agent'] = 'BalanceCompassResearch/5 (public data download)'
            response = session.get(BASE+'/web/main/index.do', timeout=(10,60)); response.raise_for_status()
            response = session.get(PAGE, timeout=(10,60)); response.raise_for_status(); html=response.text
            # 일반 공개 페이지가 제공하는 CSRF 보호를 그대로 준수한다. 인증 우회 없음.
            csrf = re.search(r'name="_csrf" content="([^"]+)"', html)
            seq = re.search(r'name="seq" value="(\d+)"', html)
            if not csrf or not seq or '단지 기본정보' not in html: raise ValueError('공개 자료실 첨부 페이지 없음')
            (stage/'source_page.html').write_bytes(response.content)
            receipts.append(dict(path='source_page.html', sha256=hashlib.sha256(response.content).hexdigest(), url=PAGE, acquired_at=now()))
            form={'boardType':'03','pageNo':'1','stype':'','keyword':'','seq':seq[1],'scode':'01'}
            url=BASE+'/web/board/webReference/fileListData.do?seq=BOARD_FILE'
            response=session.post(url,json=form,headers={'X-CSRF-TOKEN':csrf[1],'Accept':'application/json, */*'},timeout=(10,60))
            response.raise_for_status(); listing=response.json()
            (stage/'attachment_list.json').write_bytes(response.content)
            receipts.append(dict(path='attachment_list.json',sha256=hashlib.sha256(response.content).hexdigest(),url=url,request_json=form,acquired_at=now()))
            files=listing.get('data',[])
            if listing.get('code')!='SCC' or not isinstance(files,list) or len(files)!=1: raise ValueError('첨부 목록 모호/오류')
            file=files[0]
            if not re.fullmatch(r'\d{8}_단지_기본정보\.xlsx',file.get('fileName','')): raise ValueError('첨부 이름 변경: 수동 확인 필요')
            if str(file.get('boardSeq'))!=seq[1]: raise ValueError('게시글 첨부 불일치')
            response=session.get(BASE+'/cmm/file/BOARD/fileDownload.do',params={'key':file['seq'],'fileName':file['fileName']},timeout=(10,60))
            response.raise_for_status(); payload=response.content
            (stage/'original.xlsx').write_bytes(payload)
            receipts.append(dict(path='original.xlsx',sha256=hashlib.sha256(payload).hexdigest(),url=response.url,bytes=len(payload),acquired_at=now()))
        rows=parse_kapt_xlsx(payload)
        with (stage/'data.csv').open('x',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        result=dict(schema_version=1,status='acquired_current_snapshot',source_id='KAPT_FILE',source_url=PAGE,
                    source_filename=file['fileName'],rows=len(rows),encoding='utf-8-sig',data_path='data.csv',
                    data_sha256=hashlib.sha256((stage/'data.csv').read_bytes()).hexdigest(),raw_responses=receipts,
                    acquired_at=now(),historical_availability_proven=False,feature_ready=False,
                    limitations=['관리비공개의무단지 중심의 현재 자료. 소규모/미등록 단지 모집단 대표성 주의.',
                                 '정규화 CSV는 연구용 30개 열과 원본 행 번호. 연락처/사업자번호는 분리하지 않음.',
                                 '사용승인일이 과거여도 세대수/주차/승강기 등의 과거 상태 증명 아님.',
                                 '원본 XLSX와 제공자 주의 문구 보존. 좌표 열은 없음.'])
        atomic_json(stage/'manifest.json',result); stage.rename(output); return result
    except BaseException:
        shutil.rmtree(stage); raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    print(json.dumps(collect_kapt(parser.parse_args().output),ensure_ascii=False,indent=2))
