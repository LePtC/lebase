from lebase.times.datecalc import time_str_list, convert_days_ago, lastday_of_month

import time


def test_convert_days_ago():
    result = convert_days_ago("3天前")
    assert isinstance(result, time.struct_time)


def test_lastday_of_month():
    result = lastday_of_month("202407")
    assert isinstance(result, str)


def test_time_str_list():
    lst = time_str_list('2020040611', '2020040723')
    assert isinstance(lst, list)
    assert lst[0].startswith('20200406')


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
