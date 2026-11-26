"""기존 취득 기록을 검증하며 원문 전 항목을 새 연구 입력에 보존한다."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from .acquire import sha256, SOURCE
from .runtime import atomic_json, now


def enrich_raw(root, output):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output.exists():raise ValueError('새 입력 폴더가 필요합니다')
    receipt_path=root/'원본취득목록.json'
    original_receipt=receipt_path.read_bytes();receipt=json.loads(original_receipt.decode('utf-8-sig'))
    entries=receipt['files']
    expected={f'{y}{m:02}' for y in range(2022,2026) for m in range(1,13)}
    if set(entries)!=expected:raise ValueError('고정 48개월 원본 필요')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.input-',dir=output.parent));files=[];total=0;master_header=None
    try:
        for month,entry in sorted(entries.items()):
            path=(root/entry['raw_path']).resolve(strict=True)
            if not path.is_relative_to(root):raise ValueError('원본 경로 범위 이탈')
            if sha256(path)!=entry['raw_sha256']:raise ValueError(f'원본 해시 불일치 {month}')
            name=f'연구입력_{month}.csv';count=0
            with path.open(encoding=entry['raw_encoding'],newline='') as stream, (stage/name).open('x',encoding='utf-8-sig',newline='') as dest:
                reader=csv.reader(stream,strict=True);header=None
                for i,row in enumerate(reader):
                    if row and row[0]=='NO':header=row;break
                    if i>=99:raise ValueError('머리글을 찾지 못함')
                if header!=entry['columns'] or len(header)!=len(set(header)):raise ValueError('원본 칼럼 불일치')
                if master_header is None:master_header=header
                if header!=master_header:raise ValueError('월별 원문 스키마 변화: 별도 검토 필요')
                positions=[header.index(c) for c in ('시군구','번지','단지명')]
                month_index=header.index('계약년월')
                writer=csv.writer(dest);writer.writerow(header+['source_row_id','cluster_id'])
                for row in reader:
                    if not row:continue
                    if len(row)!=len(header) or row[month_index]!=month:raise ValueError('원본 행 형식/월 불일치')
                    count+=1
                    key=[row[i].strip() for i in positions]
                    cluster=hashlib.sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest() if all(v and v!='-' for v in key) else ''
                    writer.writerow(row+[f"{entry['raw_sha256']}:{count}",cluster])
            if count!=entry['rows'] or sha256(path)!=entry['raw_sha256']:raise ValueError('원본 행수/처리 도중 해시 변경')
            files.append({'path':name,'sha256':sha256(stage/name),'rows':count,'source_url':entry['source_url'],
              'acquired_at':entry['acquired_at'],'snapshot_id':receipt['snapshot_id'],
              'original_sha256':entry['raw_sha256'],'original_path':str(path)})
            total+=count
            print(f'{month}: {count}',flush=True)
        if receipt_path.read_bytes()!=original_receipt:raise ValueError('취득 기록 변경')
        atomic_json(stage/'자료_manifest.json',{'schema_version':2,'files':files,'rows':total,
          'created_at':now(),'evaluation_mode':'retrospective_snapshot','historical_labels_verified':False,
          'receipt_sha256':hashlib.sha256(original_receipt).hexdigest(),'original_columns':master_header,
          'note':'계약기간·갱신권·종전가격 등 보존 칼럼은 예측 입력 허용 목록이 아님'})
        stage.rename(output)
        return output/'자료_manifest.json'
    except BaseException:
        shutil.rmtree(stage);raise


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv)
    try:print(enrich_raw(a.root,a.output));return 0
    except (ValueError,OSError,KeyError) as e:print(f'연구 입력 실패: {e}');return 2

if __name__=='__main__':raise SystemExit(main())
