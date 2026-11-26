import io
import unittest
from zipfile import ZipFile
from rentlab.kapt_source import parse_kapt_xlsx


def fixture(code='A0001', duplicate=False, formula=False):
    rows = '<row r="1"><c r="A1" t="inlineStr"><is><t>주의: 현재 자료</t></is></c></row>'
    headers = ['단지코드', '단지명', '법정동주소', '도로명주소', '세대수']
    rows += '<row r="2">'+''.join(f'<c r="{chr(65+i)}2" t="inlineStr"><is><t>{v}</t></is></c>' for i,v in enumerate(headers))+'</row>'
    values = [code, '아파트', '서울특별시 중구 신당동 1 아파트', '서울특별시 중구 도로 1', '200.0']
    for n in range(3, 5 if duplicate else 4):
        rows += f'<row r="{n}">'+''.join(f'<c r="{chr(65+i)}{n}" t="inlineStr">'+ ('<f>1+1</f>' if formula and i==4 else '')+f'<is><t>{v}</t></is></c>' for i,v in enumerate(values))+'</row>'
    stream=io.BytesIO()
    with ZipFile(stream,'w') as z:
        z.writestr('xl/worksheets/sheet1.xml', '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+rows+'</sheetData></worksheet>')
    return stream.getvalue()


class KaptSourceTests(unittest.TestCase):
    def test_selected_data_preserves_codes_and_source_cells(self):
        rows = parse_kapt_xlsx(fixture())
        self.assertEqual(rows[0]['단지코드'], 'A0001')
        self.assertEqual(rows[0]['세대수'], '200.0')
        self.assertEqual(rows[0]['source_excel_row'], 3)
        self.assertNotIn('관리사무소 연락처', rows[0])

    def test_reject_html_duplicate_code_and_formulas(self):
        for value in [b'<html>error</html>', fixture(duplicate=True), fixture(formula=True), fixture(code='')]:
            with self.subTest(size=len(value)), self.assertRaises(ValueError):
                parse_kapt_xlsx(value)

    def test_negative_shared_string_reference_rejected(self):
        original=fixture();stream=io.BytesIO()
        with ZipFile(io.BytesIO(original)) as src, ZipFile(stream,'w') as dest:
            xml=src.read('xl/worksheets/sheet1.xml').decode().replace('<c r="A3" t="inlineStr"><is><t>A0001</t></is></c>', '<c r="A3" t="s"><v>-1</v></c>')
            dest.writestr('xl/worksheets/sheet1.xml',xml)
            dest.writestr('xl/sharedStrings.xml','<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>A0001</t></si></sst>')
        with self.assertRaises(ValueError):parse_kapt_xlsx(stream.getvalue())


if __name__ == '__main__': unittest.main()
