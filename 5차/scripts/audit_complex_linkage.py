"""KAPT 현재 단지와 원문 신규 계약의 주소·이름 연결 감사. 학습 없음."""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rentlab.complex_linkage import build_index,match_complex,derive_features
from rentlab.runtime import now,atomic_json
from audit_national_sources import read_source,digest


def audit(project,output):
    project=Path(project).resolve();output=Path(output).resolve()
    if output.exists():raise ValueError('새 감사 파일 필요')
    source,receipt=read_source(project/'외부 자료/2차/KAPT_검증취득')
    index=build_index(source);source_bad=Counter();feature_missing=Counter();feature_valid=0
    for r in source:
        try:
            features=derive_features(r);feature_valid+=1
            feature_missing.update(k for k,v in features.items() if v is None)
        except ValueError as error:source_bad[str(error)]+=1
    folder=project/'실제 실험/확장 입력 1차'
    manifest=json.loads((folder/'자료_manifest.json').read_text(encoding='utf-8-sig'))
    by_year=defaultdict(Counter);by_province=defaultdict(Counter);cache={};cluster_codes=defaultdict(set)
    matched_codes=set();new_rows=0;examples={};files=[]
    for entry in manifest['files']:
        path=(folder/entry['path']).resolve(strict=True)
        if not path.is_relative_to(folder.resolve()) or digest(path)!=entry['sha256']:raise ValueError('입력 해시/경로 불일치')
        n=0
        with path.open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream):
                n+=1
                if row['계약구분'].strip() not in {'신규','신규계약'}:continue
                new_rows+=1
                key=tuple(row[k] for k in ['시군구','번지','단지명','도로명'])
                if key not in cache:cache[key]=match_complex(row,index)
                match=cache[key];status=match['status'];year=row['계약년월'][:4]
                by_year[year][status]+=1;by_province[row['시군구'].split()[0]][status]+=1
                if match['source']:
                    code=match['source']['단지코드'];matched_codes.add(code)
                    if row['cluster_id']:cluster_codes[row['cluster_id']].add(code)
                elif status not in examples:examples[status]=dict(zip(['region','parcel','complex','road'],key))
        if n!=entry['rows'] or digest(path)!=entry['sha256']:raise ValueError('입력 행 수/처리 중 변경')
        files.append(dict(path=entry['path'],rows=n,sha256=entry['sha256']))
        print(path.name,n,flush=True)
    result=dict(created_at=now(),status='linkage_audit_not_feature_approval',model_training_executed=False,
                source=receipt,input_files=files,kapt_complexes=len(source),matched_unique_kapt_codes=len(matched_codes),
                new_raw_contracts=new_rows,unique_contract_address_name_keys=len(cache),
                by_year={k:dict(v) for k,v in by_year.items()},by_province={k:dict(v) for k,v in by_province.items()},
                conflicting_cluster_codes=sum(len(v)>1 for v in cluster_codes.values()),
                source_features=dict(valid_household_denominator_rows=feature_valid,rejected=dict(source_bad),missing=dict(feature_missing)),
                unmatched_examples=examples,historical_availability_proven=False,feature_ready=False,
                limitations=['현재 KAPT 단지 식별의 보수적 후보 연결. 표본검토 없이 오연결 0을 보증하지 않음.',
                             '법정동주소의 단지명 접미사를 정확 제거 후 번지·단지명이 일치하고 도로명도 일치할 때만 연결.',
                             '별칭/명칭변경/행정구역 개편/번지 표기 자동 교정 없음. 연결률 최대화보다 오연결 억제 우선.',
                             '원문 신규 계약이며 분석 정제 전 표본. 미연결/모호를 0값 특징으로 바꾸지 않음.',
                             '현재 세대/주차/승강기 상태를 2022~2025 상태로 해석할 수 없음. 좌표는 아직 없음.'])
    atomic_json(output,result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=audit(args.project,args.output)
    print(json.dumps({k:result[k] for k in ['kapt_complexes','new_raw_contracts','matched_unique_kapt_codes','by_year','source_features']},ensure_ascii=False,indent=2))
