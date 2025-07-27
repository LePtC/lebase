import unittest

from lebase.lists import (
    compare,
    filt_null,
    flatten,
    lidic2table,
    lidic2table_cols,
    listset,
    safe_li0,
    table2html,
    table_append,
    transpose,
)


class TestLists(unittest.TestCase):

    def test_transpose(self):
        # 测试正常的二维列表转置
        input_lst = [[1, 2], [3, 4]]
        expected = [[1, 3], [2, 4]]
        self.assertEqual(transpose(input_lst), expected)

        # 测试不等长列表转置（会被裁短）
        input_lst = [[1, 2], [3, 4], [5]]
        expected = [[1, 3, 5]]
        self.assertEqual(transpose(input_lst), expected)

    def test_flatten(self):
        # 测试嵌套列表展平
        input_lst = [[1, 2], [3, [4, 5]], 6]
        expected = [1, 2, 3, 4, 5, 6]
        self.assertEqual(flatten(input_lst), expected)

        # 测试空列表
        self.assertEqual(flatten([]), [])

        # 测试单个元素
        self.assertEqual(flatten(1), [1])

    def test_filt_null(self):
        # 测试过滤空元素
        input_lst = ["a", "", "b", None, "c"]
        expected = ["a", "b", "c"]
        self.assertEqual(filt_null(input_lst), expected)

    def test_listset(self):
        # 测试一维列表去重
        input_lst = [1, 2, 2, 3, 1]
        expected = [1, 2, 3]
        self.assertEqual(listset(input_lst), expected)

        # 测试二维列表去重
        input_lst = [[1, "a"], [2, "b"], [1, "c"]]
        expected = [[1, "c"], [2, "b"]]
        self.assertEqual(listset(input_lst), expected)

        # 测试空列表
        self.assertEqual(listset([]), [])

    def test_safe_li0(self):
        # 测试正常列表
        input_lst = [1, 2, 3]
        self.assertEqual(safe_li0(input_lst), 1)

        # 测试空列表
        input_lst = []
        self.assertEqual(safe_li0(input_lst), "")

    def test_lidic2table(self):
        # 测试字典列表转二维表
        input_lst = [{"a": 1, "b": 2}, {"a": 3, "c": 4}]
        expected = [["a", "b", "c"], [1, 2, 0], [3, 0, 4]]
        self.assertEqual(lidic2table(input_lst), expected)

        # 测试指定列
        expected = [["a", "b"], [1, 2], [3, 0]]
        self.assertEqual(lidic2table(input_lst, cols=["a", "b"]), expected)

    def test_table_append(self):
        # 测试二维表右侧添加一列
        input_lst = [[1, 2], [3, 4]]
        expected = [[1, 2, 0], [3, 4, 0]]
        self.assertEqual(table_append(input_lst), expected)

    def test_lidic2table_cols(self):
        # 测试按指定列转换字典列表
        input_lst = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        expected = [["a", "b"], [1, 2], [3, 4]]
        self.assertEqual(lidic2table_cols(input_lst, ["a", "b"]), expected)

    def test_table2html(self):
        # 测试二维表转HTML
        input_lst = [["a", "b"], [1, 2]]
        expected = "<table><tbody><tr><td>a</td><td>b</td></tr><tr><td>1</td><td>2</td></tr></tbody></table>"
        self.assertEqual(table2html(input_lst), expected)

    def test_compare(self):
        # 测试列表比较功能
        standard_lst = [1, 2, 3, 4, 5]
        compare_lst = [2, 3, 4, 6, 7]
        expected = ([6, 7], [1, 5])
        self.assertEqual(compare(standard_lst, compare_lst), expected)


if __name__ == "__main__":
    unittest.main()
