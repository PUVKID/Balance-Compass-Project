"""기존 8가설·15개 평가의 고정 분석 조건. 입력 검사가 이 조건을 완화하지 않는다."""
from types import MappingProxyType

ANALYSIS_DEFAULTS=MappingProxyType(dict(alpha=.1,coverage_tolerance=.02,confidence=.95,family_size=15,
    bootstrap_replicates=9999,minimum_clusters=20,minimum_group_n=30,minimum_group_clusters=5,
    regional_calibration_min=100,seed=20261126))


def confirmatory_settings(settings):
    """축소 반복/변경된 과학 조건은 기술 확인으로만 남긴다."""
    if not isinstance(settings,dict):return False
    for name,expected in ANALYSIS_DEFAULTS.items():
        value=settings.get(name)
        if type(expected) is int:
            if type(value) is not int:return False
        elif type(value) not in (int,float):return False
        if name=='bootstrap_replicates':
            if value<expected:return False
        elif value!=expected:return False
    return True
