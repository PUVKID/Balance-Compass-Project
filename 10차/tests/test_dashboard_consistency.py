import copy
import unittest
from rentlab.research_protocol import ANALYSIS_DEFAULTS
from run_dashboard import validate_summary
from test_dashboard_v3 import fixture


class DashboardConsistencyTests(unittest.TestCase):
    def rejected(self, change):
        value = fixture(); change(value)
        with self.assertRaises(ValueError):
            validate_summary(value)

    def hypothesis_fixture(self):
        value=fixture();value['rows']=52
        for name,target in value['targets'].items():
            target['metrics']['n']=20;target['groups'][0]['n']=20
            target['split_counts']['test']=20;value['split_counts'][name]['test']=20
        value['research']={'config':dict(ANALYSIS_DEFAULTS)}
        return value

    def rejected_hypothesis(self, rows, mode='REAL'):
        value=self.hypothesis_fixture();value.update(mode=mode,research_hypotheses=rows)
        with self.assertRaises(ValueError):validate_summary(value)

    def test_regional_counts_and_unique_nonblank_regions(self):
        self.rejected(lambda d: d['targets']['jeonse']['groups'][0].update(n=200))
        self.rejected(lambda d: d['targets']['jeonse'].update(groups=[]))
        self.rejected(lambda d: d['targets']['jeonse']['groups'][0].update(region=' '))
        self.rejected(lambda d: d['targets']['jeonse']['groups'].append(copy.deepcopy(d['targets']['jeonse']['groups'][0])))

    def test_rmse_and_weighted_regional_mae_coverage(self):
        self.rejected(lambda d: d['targets']['jeonse']['metrics'].update(mae=100., rmse=1.))
        self.rejected(lambda d: d['targets']['jeonse']['groups'][0].update(mae=2.))
        self.rejected(lambda d: d['targets']['jeonse']['groups'][0].update(coverage=.1))

    def test_float_roundoff_and_unequal_regional_weights_accepted(self):
        value = fixture()
        for target in value['targets'].values():
            target['groups'] = [dict(region='A', n=1, mae=.5, coverage=.8), dict(region='B', n=1, mae=1.5, coverage=1.)]
            target['metrics']['mae'] = 1.+1e-12
            target['metrics']['rmse'] = 1.25
        validate_summary(value)

    def test_interval_missingness_must_be_consistent(self):
        self.rejected(lambda d: d['targets']['jeonse']['metrics'].update(width=None))
        self.rejected(lambda d: d['targets']['jeonse']['groups'][0].update(coverage=None))
        value = fixture()
        for target in value['targets'].values():
            target['metrics'].update(coverage=None, width=None, interval_score=None)
            target['groups'][0]['coverage'] = None
        validate_summary(value)

    @staticmethod
    def row(**overrides):
        row = dict(id='H1', title='control', target='jeonse', status='measured',
                   effect=2., ci=[1., 3.], decision='support', n=20, clusters=20,
                   bootstrap_requested=9999,bootstrap_valid=9999)
        row.update(overrides)
        return row

    def test_invalid_hypothesis_pairs_ci_and_decisions_rejected(self):
        changes = [dict(ci=[10., -10.]), dict(id='H9'), dict(id='H2', target='jeonse'),
                   dict(decision='made_up'), dict(status='unmeasured'), dict(ci=None),
                   dict(status='partial'), dict(n=-1), dict(clusters=21)]
        for change in changes:
            with self.subTest(change=change):
                self.rejected_hypothesis([self.row(**change)])

    def test_synthetic_support_and_duplicate_pairs_rejected(self):
        self.rejected_hypothesis([self.row()],mode='SYNTHETIC')
        self.rejected_hypothesis([self.row(), self.row()])

    def test_percentile_interval_need_not_contain_effect(self):
        value = self.hypothesis_fixture()
        value.update(mode='REAL', research_hypotheses=[self.row(effect=.9, ci=[1., 3.])])
        validate_summary(value)

    def test_decision_direction_and_hypothesis_denominators(self):
        for change in [dict(ci=[-3., -1.]), dict(ci=[-1., 1.]),
                       dict(id='H3', effect=.5, ci=[.4, .6]),
                       dict(n=21, clusters=20), dict(n=1, clusters=1)]:
            with self.subTest(change=change):
                self.rejected_hypothesis([self.row(**change)])
        for change in [dict(ci=[-3., -1.], decision='not_support'),
                       dict(ci=[-1., 1.], decision='inconclusive'),
                       dict(id='H3', effect=0., ci=[-.01, .01]),
                       dict(id='H3', effect=.5, ci=[.4, .6], decision='not_support'),
                       dict(id='H5', n=1, clusters=1,status='partial',ci=None,decision='inconclusive')]:
            value=self.hypothesis_fixture();value.update(mode='REAL', research_hypotheses=[self.row(**change)])
            validate_summary(value)


if __name__ == '__main__':
    unittest.main()
