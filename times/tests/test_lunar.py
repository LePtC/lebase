from lebase.times.lunar import str2lunar


def test_str2lunar():
    # 20230101 -> ['日', ...]
    lunar = str2lunar("20230101")
    assert isinstance(lunar, list)
    assert len(lunar) == 2
    assert isinstance(lunar[0], str)