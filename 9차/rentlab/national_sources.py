"""공식 전국 시계열 다운로드. 학습·과거 빈티지 승인 기능은 포함하지 않는다."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
from datetime import date
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
import requests
from .runtime import atomic_json, now

MOIS_PAGE = 'https://jumin.mois.go.kr/statMonth.do'
MOIS_DOWNLOAD = 'https://jumin.mois.go.kr/downloadCsv.do?searchYearMonth=month&xlsStats=2'
BOK_PAGE = 'https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSecd=00001&menuNo=200643'
METRICS = ['총인구수', '세대수', '세대당 인구', '남자 인구수', '여자 인구수', '남여 비율']


def number(text, integer=False):
    value = text.strip()
    if not value:
        return None
    if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?', value):
        raise ValueError('비정상 수치')
    try:
        result = Decimal(value.replace(',', ''))
    except InvalidOperation as exc:
        raise ValueError('비정상 수치') from exc
    if not result.is_finite() or result < 0 or (integer and result != result.to_integral_value()):
        raise ValueError('유한한 비음수 수치 필요')
    return int(result) if integer else float(result)


def parse_population(payload: bytes, year: int) -> list[dict]:
    if type(year) is not int or not 2008 <= year <= 2100:
        raise ValueError('지원 연도 아님')
    try:
        text = payload.decode('cp949')
    except UnicodeDecodeError as exc:
        raise ValueError('주민등록 CSV 인코딩 불일치') from exc
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    expected = ['행정구역'] + [f'{year}년{m:02}월_{v}' for m in range(1, 13) for v in METRICS]
    if next(reader, None) != expected:
        raise ValueError('요청 연도 12개월/통계 열이 응답과 다름')
    result = []; seen = set()
    for raw in reader:
        if len(raw) != len(expected):
            raise ValueError('CSV 열 수 불일치')
        match = re.fullmatch(r'\s*(.*?)\s*\((\d{10})\)\s*', raw[0])
        if not match or not match[1] or match[2] in seen:
            raise ValueError('지역 코드 누락/중복')
        seen.add(match[2])
        for month in range(1, 13):
            cells = raw[1 + (month-1)*6:1 + month*6]
            pop, households, persons, male, female, ratio = [number(v, i in (0, 1, 3, 4)) for i, v in enumerate(cells)]
            status = 'missing_source_cells' if any(v is None for v in [pop, households, persons, male, female, ratio]) else 'valid'
            if pop is not None and male is not None and female is not None and pop != male+female:
                raise ValueError('총인구와 남녀 합계 불일치')
            if pop is not None and households is not None:
                if households == 0 and pop != 0:
                    raise ValueError('인구가 있으나 세대 수 0')
                if pop == households == 0:
                    status = 'inactive_or_zero_source' if status == 'valid' else status
                elif persons is not None and abs(persons-pop/households) > .011:
                    raise ValueError('세대당 인구 불일치')
            result.append(dict(region_code=match[2], region_name=' '.join(match[1].split()),
                               month=f'{year}-{month:02}', population=pop, resident_households=households,
                               persons_per_household=persons, male_population=male, female_population=female,
                               source_sex_ratio=ratio, quality_status=status))
    if not result:
        raise ValueError('빈 주민등록 자료')
    return result


class _Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        elif tag in ('td', 'th') and self.row is not None: self.cell = []
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(''.join(self.cell).strip()); self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row); self.row = None


def parse_base_rates(html: str) -> list[dict]:
    parser = _Tables(); parser.feed(html)
    result = []; seen = set()
    for row in parser.rows:
        if not row or not re.fullmatch(r'\d{4}', row[0]): continue
        if len(row) != 3: raise ValueError('기준금리 결정행 열 수 변경')
        match = re.fullmatch(r'(\d{1,2})월\s*(\d{1,2})일', row[1])
        if not match: raise ValueError('기준금리 결정일 형식 변경')
        day = date(int(row[0]), int(match[1]), int(match[2])).isoformat()
        value = number(row[2])
        if value is None or value > 100 or day in seen:
            raise ValueError('기준금리 날짜 중복/값 비정상')
        seen.add(day); result.append(dict(decision_date=day, base_rate=value))
    if not result: raise ValueError('기준금리 변경표 없음')
    return sorted(result, key=lambda x: x['decision_date'])


def rate_before_day(records: list[dict], day: str):
    day = date.fromisoformat(day).isoformat()
    eligible = [row for row in records if row['decision_date'] < day]
    return max(eligible, key=lambda x: x['decision_date'])['base_rate'] if eligible else None


class AmbiguousPopulationError(ValueError):
    """동일 지명에 여러 행정 계층/코드가 있어 자동 선택할 수 없음."""


def population_before_month(records: list[dict], region: str, day: str, lag_months: int = 2):
    """명시적 월 지연의 정확한 이름 접두사 연결. 공표 시각 증명이 아니다.

    시군구가 없으면 시도 값이 반환될 수 있으므로 반환 지역의 공간 해상도를
    반드시 별도로 보고한다. 개편 이름/경계의 자동 변환과 과거값 보간은 없다.
    """
    if type(lag_months) is not int or lag_months < 1:
        raise ValueError('양의 지연 개월 필요')
    target = date.fromisoformat(day)
    month_index = target.year*12 + target.month-1-lag_months
    year, month = divmod(month_index, 12)
    wanted = f'{year:04}-{month+1:02}'
    region = ' '.join(region.split())
    eligible = [r for r in records if r['month'] == wanted and r['quality_status'] == 'valid'
                and (region == r['region_name'] or region.startswith(r['region_name']+' '))]
    if not eligible: return None
    longest = max(len(r['region_name']) for r in eligible)
    matches = [r for r in eligible if len(r['region_name']) == longest]
    if len(matches) != 1: raise AmbiguousPopulationError('지역·월 연결키 모호/중복')
    return dict(matches[0])


def _collect(output, source_id, fetch):
    output = Path(output).resolve()
    if output.exists(): raise ValueError('새 출력 폴더 필요')
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.national-', dir=output.parent))
    try:
        receipts = []
        with requests.Session() as session:
            session.headers['User-Agent'] = 'BalanceCompassResearch/5 (public data download)'
            def request(name, method, url, data=None):
                response = session.request(method, url, data=data, timeout=(10, 60)); response.raise_for_status()
                (stage/name).write_bytes(response.content)
                receipts.append(dict(path=name, sha256=hashlib.sha256(response.content).hexdigest(),
                                     bytes=len(response.content), method=method, url=url, form=data,
                                     acquired_at=now(), status_code=response.status_code))
                return response.content
            rows, page, extra = fetch(request)
        with (stage/'data.csv').open('x', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        manifest = dict(schema_version=1, status='acquired_current_snapshot', source_id=source_id,
                        source_url=page, rows=len(rows), data_path='data.csv',
                        data_sha256=hashlib.sha256((stage/'data.csv').read_bytes()).hexdigest(),
                        encoding='utf-8-sig', raw_responses=receipts, acquired_at=now(),
                        historical_availability_proven=False, feature_ready=False, **extra)
        atomic_json(stage/'manifest.json', manifest); stage.rename(output)
        return manifest
    except BaseException:
        shutil.rmtree(stage); raise


def collect_population(year: int, output):
    if type(year) is not int or not 2008 <= year <= date.today().year-1:
        raise ValueError('완료된 연간 자료만 지원')
    def fetch(request):
        request('source_page.html', 'GET', MOIS_PAGE)
        form = dict(sltOrgType='1', sltOrgLvl1='A', sltOrgLvl2='', gender='gender', genderPer='genderPer',
                    generation='generation', sltUndefType='', searchYearStart=str(year), searchMonthStart='01',
                    searchYearEnd=str(year), searchMonthEnd='12', sltOrderType='1', sltOrderValue='ASC', category='month', state='2')
        rows = parse_population(request('population_original.csv', 'POST', MOIS_DOWNLOAD, form), year)
        return rows, MOIS_PAGE, dict(year=year, months=12, geography='시군구 이상; 합계와 하위 지역 혼재',
                                    limitations=['외국인 제외 주민등록 인구. 취득일 현재의 과거 통계이며 과거 빈티지 증명 아님.',
                                                 '지역 개편의 0값/결측은 임의 보간 금지. 중첩 행을 모두 더해 전국 합계로 사용 금지.'])
    return _collect(output, 'MOIS_POPULATION', fetch)


def collect_base_rates(output):
    def fetch(request):
        rows = parse_base_rates(request('source_page.html', 'GET', BOK_PAGE).decode('utf-8'))
        return rows, BOK_PAGE, dict(unit='percent_per_year', limitations=[
            '기준금리이며 실제 주택대출 금리가 아님. 역사 변경표의 현재 스냅샷.',
            '일자 단위 연결은 결정일 당일 제외. 실제 발표 시각/당시 원본 확보를 의미하지 않음.'])
    return _collect(output, 'BOK_BASE_RATE', fetch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', choices=['population', 'base-rate']); parser.add_argument('--year', type=int)
    parser.add_argument('--output', required=True); args = parser.parse_args()
    if args.source == 'population' and args.year is None: parser.error('--year 필요')
    result = collect_population(args.year, args.output) if args.source == 'population' else collect_base_rates(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
