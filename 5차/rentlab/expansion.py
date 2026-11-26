"""확장 정보의 동일 계약 탐색적 비교와 대규모 실행 전 준비 상태."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import shutil
import numpy as np
import pandas as pd
from . import engine
from .feature_store import FEATURES, ALLOWED, MODES, join_features, validate_feature_manifest
from .runtime import atomic_json, now


def readiness(sources, mode='retrospective_snapshot', labels_verified=False):
    if mode not in MODES:raise ValueError('평가 모드 오류')
    blockers=[]
    eligible=[s for s in sources if s.get('status')=='verified_feature_snapshot' and s.get('features')]
    if not eligible:blockers.append('external_features_missing')
    if mode=='strict_asof' and not labels_verified:blockers.append('label_availability_unproven')
    if mode=='strict_asof' and any(not s.get('historical_availability_proven') for s in eligible):
        blockers.append('feature_history_unproven')
    return {'ready':not blockers,'blockers':blockers,'mode':mode,'training_started':False,
            'eligible_feature_sources':len(eligible),'source_count':len(sources),'checked_at':now()}


def paired_cluster_ci(frame, comparator, replicates=9999, seed=20261126):
    """동일 계약 절대오차 차이의 단지 군집 percentile 근사구간. 모델은 재적합하지 않음."""
    if replicates<99:raise ValueError('재표집 횟수 부족')
    numbers=frame[['actual_won','prediction_full_won',comparator]].to_numpy(dtype=float)
    if not len(numbers) or not np.isfinite(numbers).all():raise ValueError('오차 차이 입력 오류')
    y,full,base=numbers.T
    delta=abs(y-base)-abs(y-full)
    result={'effect_won':float(delta.mean()),'ci_won':None,'n':len(frame),'clusters':None,
            'confidence':.95,'replicates':replicates,'seed':seed,
            'family_adjustment':'none; exploratory pointwise interval',
            'limitations':'단지 내 의존성의 근사 처리. 시간/지역 공통 충격·학습 불확실성 모두를 반영하지 않음.'}
    if 'cluster_id' not in frame or frame.cluster_id.isna().any() or frame.cluster_id.astype(str).str.strip().eq('').any():
        result['status']='cluster_id_missing';return result
    aggregate=pd.DataFrame({'cluster':frame.cluster_id.to_numpy(),'delta':delta,'n':1}).groupby('cluster',sort=True)[['delta','n']].sum().to_numpy()
    k=len(aggregate);result['clusters']=k
    if k<20:result['status']='insufficient_clusters';return result
    rng=np.random.default_rng(seed);samples=np.empty(replicates)
    for i in range(replicates):
        total=aggregate[rng.integers(0,k,size=k)].sum(axis=0);samples[i]=total[0]/total[1]
    result['ci_won']=np.quantile(samples,[.025,.975]).tolist();result['status']='measured_approximate'
    return result


def prediction_metrics(frame, column):
    result=engine.metrics(frame.actual_won,frame[column])
    suffix=column.removeprefix('prediction_')
    lower,upper='lower_'+suffix,'upper_'+suffix
    if lower in frame and upper in frame:
        bounds=frame[[lower,upper]].to_numpy(dtype=float)
        if np.isfinite(bounds).all():
            from .research_metrics import interval_score
            y=frame.actual_won.to_numpy(dtype=float);lo,hi=bounds.T
            result.update(coverage=float(np.mean((lo<=y)&(y<=hi))),width=float(np.mean(hi-lo)),
                          interval_score=float(np.mean(interval_score(y,lo,hi))))
    return result


def run_comparison(data, target, groups, holdout=None):
    if not groups or any(not v for v in groups.values()):raise ValueError('비어 있지 않은 특징군 필요')
    extras=[x for values in groups.values() for x in values]
    if holdout and set(extras)&set(FEATURES['lagged_prices']):
        raise ValueError('홀드아웃 가격 집계의 학습 집합 추적 미구현: 해당 특징 사용 금지')
    if len(set(extras))!=len(extras) or not set(extras).issubset(ALLOWED):raise ValueError('특징 중복/미등록')
    if not data.source_row_id.is_unique:raise ValueError('계약 ID 중복')
    for name in extras:
        if name not in data:raise ValueError('특징 칼럼 누락')
    frames=engine.split_data(data,holdout);train,val,cal,test=[frames[k] for k in ('train','validation','calibration','test')]
    for name in extras:
        if pd.to_numeric(train[name],errors='raise').notna().sum()==0:raise ValueError(f'학습에 관측 없는 특징: {name}')
    response='rent' if target=='monthly' else 'deposit' if target=='jeonse' else None
    if response is None:raise ValueError('목표 오류')
    def numeric(names):
        values=engine.NUMERIC+names+([x+'__missing' for x in names if x+'__missing' in data])+(['deposit'] if target=='monthly' else [])
        return values
    full_numeric=numeric(extras);full_features=full_numeric+engine.CATEGORICAL
    candidates=engine.ai_candidates(full_numeric);validation={};fitted={}
    for name,model in candidates.items():
        model.fit(train[full_features],train[response]);fitted[name]=model
        validation[name]=engine.metrics(val[response],model.predict(val[full_features]))['mae']
    selected=min(validation,key=lambda name:(validation[name],name));full=fitted[selected]
    p=full.predict(test[full_features]);radius=engine.conformal_radius(abs(cal[response].to_numpy()-full.predict(cal[full_features])))
    predictions=test[['source_row_id','cluster_id','date','region']].copy()
    predictions['actual_won']=test[response];predictions['prediction_full_won']=p
    predictions['lower_full_won']=p-radius if radius is not None else np.nan
    predictions['upper_full_won']=p+radius if radius is not None else np.nan
    result={'inference_role':'exploratory','full_model':selected,'n':len(test),'validation_mae':validation,
            'full_metrics':engine.metrics(test[response],p,radius),'features':groups,'comparisons':{},
            'formula':'MAE(comparator)-MAE(full); positive = lower full-model error',
            'ci_interpretation':'탐색적 점별 95% 단지 군집 근사구간; 동시 포함 보장 없음'}
    for name,names in {'basic':[],**{'without_'+group:[x for x in extras if x not in omitted] for group,omitted in groups.items()}}.items():
        nums=numeric(names);features=nums+engine.CATEGORICAL
        model=engine.ai_candidates(nums)[selected];model.fit(train[features],train[response])
        pp=model.predict(test[features]);r=engine.conformal_radius(abs(cal[response].to_numpy()-model.predict(cal[features])))
        m=engine.metrics(test[response],pp,r)
        delta=m['mae']-result['full_metrics']['mae']
        result['comparisons'][name]={'model':selected,'metrics':m,'mae_difference_won':delta,
          'relative_improvement_pct':100*delta/m['mae'] if m['mae'] else None,'numeric':nums}
        predictions['prediction_'+name+'_won']=pp
        predictions['lower_'+name+'_won']=pp-r if r is not None else np.nan
        predictions['upper_'+name+'_won']=pp+r if r is not None else np.nan
        result['comparisons'][name]['uncertainty']=paired_cluster_ci(predictions,'prediction_'+name+'_won')
    predictions['external_matched']=data.loc[test.index,extras].notna().all(axis=1).to_numpy()
    return result,predictions


def evaluate(manifest, feature_manifest, output, mode='retrospective_snapshot', holdout=None):
    """실측 입력 검증 후 실행. CLI에는 --execute 명시가 필요하다."""
    output=Path(output).resolve()
    if output.exists():raise ValueError('새 출력 폴더가 필요합니다')
    feature_manifest=Path(feature_manifest).resolve()
    descriptor=json.loads(feature_manifest.read_text(encoding='utf-8-sig'))
    # 원문 시설자료를 받은 것만으로 특징 입력 준비가 끝났다고 처리하지 않는다.
    gate=readiness([descriptor],mode,labels_verified=False)
    if not gate['ready']:raise ValueError('실행 전 조건 미충족: '+','.join(gate['blockers']))
    observations=validate_feature_manifest(descriptor,feature_manifest.parent)
    raw,provenance=engine.read_manifest(Path(manifest));prepared,audit=engine.prepare(raw)
    data=prepared[prepared.exclusion_reason.eq('')].copy()
    if set(observations.feature)!=set(descriptor['features']):raise ValueError('특징 목록과 본문 불일치')
    data,join_audit=join_features(data,observations,mode,key_column=descriptor.get('key_column','cluster_id'))
    groups={family:[x for x in names if x in descriptor['features']] for family,names in FEATURES.items()}
    groups={k:v for k,v in groups.items() if v}
    output.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.expansion-',dir=output.parent))
    try:
        summary={'mode':'REAL','evaluation_mode':mode,'inference_role':'exploratory','created_at':now(),
                 'provenance':provenance,'feature_sha256':descriptor['sha256'],'audit':audit,'join_audit':join_audit,'targets':{},
                 'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}}
        for target,mask in [('jeonse',data.rent.eq(0)),('monthly',data.rent.gt(0))]:
            result,pred=run_comparison(data[mask],target,groups,holdout)
            summary['targets'][target]=result
            pred.to_csv(stage/f'{target}_expansion_predictions.csv',index=False,encoding='utf-8-sig')
            records=[]
            for grouping,values in [('month',pd.to_datetime(pred.date).dt.strftime('%Y-%m')),('region',pred.region),('matched',pred.external_matched)]:
                for key,frame in pred.groupby(values,dropna=False):
                    for col in [x for x in pred if x.startswith('prediction_')]:
                        records.append({'grouping':grouping,'group':str(key),'predictor':col,'clusters':int(frame.cluster_id.nunique()),
                                        **prediction_metrics(frame,col)})
            pd.DataFrame(records).to_csv(stage/f'{target}_group_metrics.csv',index=False,encoding='utf-8-sig')
        atomic_json(stage/'summary.json',summary);stage.rename(output);return summary
    except BaseException:shutil.rmtree(stage);raise


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--features',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--mode',choices=sorted(MODES),default='retrospective_snapshot');p.add_argument('--execute',action='store_true')
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps({'status':'planned','training_started':False,'mode':a.mode,'output':str(a.output)},ensure_ascii=False));return 0
    try:evaluate(a.manifest,a.features,a.output,a.mode);return 0
    except (ValueError,OSError,KeyError) as e:print(f'확장 실험 실패: {e}');return 2

if __name__=='__main__':raise SystemExit(main())
