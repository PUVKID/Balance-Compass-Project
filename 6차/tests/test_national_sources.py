import csv
import io
import unittest
from rentlab.national_sources import parse_population, parse_base_rates, rate_before_day, population_before_month, AmbiguousPopulationError


def population_payload():
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    metrics = ['총인구수', '세대수', '세대당 인구', '남자 인구수', '여자 인구수', '남여 비율']
    writer.writerow(['행정구역'] + [f'2021년{m:02}월_{v}' for m in range(1, 13) for v in metrics])
    writer.writerow(['서울특별시  (1100000000)'] + ['1,000', '400', '2.50', '480', '520', '0.92'] * 12)
    return stream.getvalue().encode('cp949')


class NationalSourcesTests(unittest.TestCase):
    def test_population_preserves_grain_and_units(self):
        rows = parse_population(population_payload(), 2021)
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0]['region_code'], '1100000000')
        self.assertEqual(rows[0]['region_name'], '서울특별시')
        self.assertEqual(rows[0]['population'], 1000)
        self.assertEqual(rows[-1]['month'], '2021-12')

    def test_population_rejects_html_partial_period_bad_counts(self):
        for payload in [b'<html>error</html>', population_payload().replace(b'2021', b'2020', 1),
                        population_payload().replace(b'480', b'490', 1),
                        population_payload().replace(b'400', b'0', 1)]:
            with self.subTest(payload=payload[:30]), self.assertRaises(ValueError):
                parse_population(payload, 2021)

    def test_duplicate_code_or_ragged_rows_rejected(self):
        payload = population_payload()
        duplicate = payload + payload.splitlines(keepends=True)[1]
        with self.assertRaises(ValueError):
            parse_population(duplicate, 2021)
        with self.assertRaises(ValueError):
            parse_population(payload + b'"bad"\r\n', 2021)

    def test_missing_cells_preserved_and_only_complete_months_validated(self):
        payload = population_payload().replace(b'"1,000",400,2.50,480,520,0.92', b',,,,,', 1)
        row = parse_population(payload, 2021)[0]
        self.assertIsNone(row['population'])
        self.assertEqual(row['quality_status'], 'missing_source_cells')

    def test_rates_parse_and_no_same_day_information(self):
        html = '<table><tbody><tr><td>2022</td><td>01월 14일</td><td>1.25</td></tr><tr><td>2021</td><td>11월 25일</td><td>1.00</td></tr></tbody></table>'
        rows = parse_base_rates(html)
        self.assertEqual(rate_before_day(rows, '2022-01-14'), 1.0)
        self.assertEqual(rate_before_day(rows, '2022-01-15'), 1.25)
        self.assertIsNone(rate_before_day(rows, '2021-11-25'))

    def test_rates_reject_duplicate_dates_invalid_values_and_empty(self):
        row = '<tr><td>2022</td><td>01월 14일</td><td>1.25</td></tr>'
        for html in ['<html>error</html>', '<table>'+row+row+'</table>', '<table>'+row.replace('1.25', 'nan')+'</table>']:
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_base_rates(html)

    def test_partial_malformed_decision_is_not_silently_dropped(self):
        html='<table><tr><td>2022</td><td>01월 14일 (변경)</td><td>1.25</td></tr><tr><td>2021</td><td>11월 25일</td><td>1.00</td></tr></table>'
        with self.assertRaises(ValueError):parse_base_rates(html)

    def test_population_lag_exact_boundary_longest_prefix_and_no_alias(self):
        rows = [dict(region_name='서울특별시', region_code='1100000000', month='2021-11', population=1000, quality_status='valid'),
                dict(region_name='서울특별시 종로구', region_code='1111000000', month='2021-11', population=200, quality_status='valid'),
                dict(region_name='서울특별시 중구', region_code='1114000000', month='2021-11', population=300, quality_status='inactive_or_zero_source')]
        found = population_before_month(rows, '서울특별시 종로구 청운동', '2022-01-01')
        self.assertEqual(found['population'], 200)
        self.assertIsNone(population_before_month(rows, '전남광주통합특별시 동구', '2022-01-01'))
        self.assertEqual(population_before_month(rows, '서울특별시 종로구밖', '2022-01-01')['population'], 1000)
        self.assertIsNone(population_before_month(rows, '서울특별시 종로구', '2022-02-01'))
        with self.assertRaises(ValueError):
            population_before_month(rows, '서울특별시', '2022-01-01', lag_months=0)

    def test_same_named_hierarchy_is_explicitly_ambiguous(self):
        rows = [dict(region_name='세종특별자치시', region_code=code, month='2021-11', population=200, quality_status='valid')
                for code in ['3600000000', '3611000000']]
        with self.assertRaises(AmbiguousPopulationError):
            population_before_month(rows, '세종특별자치시 나성동', '2022-01-01')


if __name__ == '__main__':
    unittest.main()
