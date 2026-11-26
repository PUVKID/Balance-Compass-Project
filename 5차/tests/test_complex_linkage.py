import unittest
from rentlab.complex_linkage import build_index, match_complex, derive_features


def source(code='A1', households='200.0'):
    return {'단지코드':code,'단지명':'단지','법정동주소':'서울특별시 중구 신당동 1 단지',
            '도로명주소':'서울특별시 중구 도로 10','세대수':households,'동수':'2','총주차대수':'250',
            '승강기(승객용)':'4','최고층수':'20','최고층수(건축물대장상)':'21'}


class ComplexLinkageTests(unittest.TestCase):
    def test_two_addresses_agree_with_exact_name(self):
        index=build_index([source()])
        row={'시군구':'서울특별시 중구 신당동','번지':'1','단지명':'단지','도로명':'도로 10'}
        self.assertEqual(match_complex(row,index)['status'],'matched_dual_address_name')
        row['도로명']='도로 11'
        self.assertEqual(match_complex(row,index)['status'],'address_disagreement')
        row['단지명']='비슷한단지'
        self.assertEqual(match_complex(row,index)['status'],'unmatched')

    def test_ambiguous_source_and_missing_key_not_guessed(self):
        index=build_index([source(),source('A2')])
        row={'시군구':'서울특별시 중구 신당동','번지':'1','단지명':'단지','도로명':'도로 10'}
        self.assertEqual(match_complex(row,index)['status'],'ambiguous')
        row['번지']='-'
        self.assertEqual(match_complex(row,index)['status'],'incomplete_contract_key')

    def test_features_ratio_missing_and_invalid(self):
        result=derive_features(source())
        self.assertEqual(result['parking_per_household'],1.25)
        self.assertEqual(result['max_floor'],21)
        self.assertIsNone(result['elevators_per_household'])  # 다른 종류의 미입력을 0으로 가정하지 않는다.
        for v in ['0','-1','nan','Infinity']:
            with self.subTest(v=v), self.assertRaises(ValueError):derive_features(source(households=v))


if __name__=='__main__':unittest.main()
