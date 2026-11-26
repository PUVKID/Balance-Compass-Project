import copy
from dataclasses import asdict
import unittest
import numpy as np
from rentlab.research_metrics import AnalysisConfig,_blank,_finish
from run_dashboard import validate_summary
from test_dashboard_v3 import fixture


class ConfirmatoryEvidenceTests(unittest.TestCase):
    def summary(self):
        d=fixture();d['mode']='REAL'
        d['split_counts']={name:dict(counts) for name,counts in d['split_counts'].items()}
        for name,target in d['targets'].items():
            target['metrics']['n']=20;target['groups'][0]['n']=20
            target['split_counts']['test']=20
            d['split_counts'][name]['test']=20
        d['research']={'config':asdict(AnalysisConfig())}
        d['research_hypotheses']=[dict(id='H1',title='control',target='jeonse',status='measured',effect=1.,
                                     ci=[.5,1.5],decision='support',n=20,clusters=20,
                                     bootstrap_requested=9999,bootstrap_valid=9999)]
        return d

    def test_changed_scientific_settings_are_technical_only(self):
        for change in [dict(minimum_clusters=2),dict(confidence=.9),dict(seed=1),dict(alpha=.2)]:
            with self.subTest(change=change):
                config=AnalysisConfig(**change)
                row=_finish(_blank('H1','jeonse'),1.,np.ones(9999),config,20,20)
                self.assertEqual(row['status'],'partial')
                self.assertEqual(row['decision'],'inconclusive')

    def test_display_requires_bootstrap_proof_and_frozen_conditions(self):
        validate_summary(self.summary())
        changes=[lambda d:d['research_hypotheses'][0].pop('bootstrap_valid'),
                 lambda d:d['research_hypotheses'][0].update(bootstrap_requested=99,bootstrap_valid=99),
                 lambda d:d['research_hypotheses'][0].update(bootstrap_valid=1),
                 lambda d:d['research_hypotheses'][0].update(bootstrap_valid=10000),
                 lambda d:d['research_hypotheses'][0].update(clusters=2),
                 lambda d:d['research']['config'].update(confidence=.9)]
        for change in changes:
            with self.subTest(change=change):
                d=self.summary();change(d)
                with self.assertRaises(ValueError):validate_summary(d)

    def test_percentile_ci_can_still_exclude_estimate(self):
        d=self.summary();d['research_hypotheses'][0]['effect']=.1
        validate_summary(d)

    def test_h6_needs_both_price_subgroup_cluster_counts(self):
        d=self.summary();d['rows']=72
        d['targets']['jeonse']['metrics']['n']=40;d['targets']['jeonse']['groups'][0]['n']=40
        d['targets']['jeonse']['split_counts']['test']=40;d['split_counts']['jeonse']['test']=40
        row=d['research_hypotheses'][0];row.update(id='H6',n=40,subgroup_clusters={'low':20,'high':20})
        validate_summary(d)
        for subgroups in [None,{'low':1,'high':1},{'low':True,'high':20},{'low':21,'high':20}]:
            with self.subTest(subgroups=subgroups):
                changed=copy.deepcopy(d)
                if subgroups is None:changed['research_hypotheses'][0].pop('subgroup_clusters')
                else:changed['research_hypotheses'][0]['subgroup_clusters']=subgroups
                with self.assertRaises(ValueError):validate_summary(changed)


if __name__=='__main__':unittest.main()
