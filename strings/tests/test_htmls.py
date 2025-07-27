# -*- coding: utf-8 -*-
"""
HTML处理模块测试
"""
import unittest

from lebase.strings.htmls import filt_base64, filt_htmltag, filt_js, filt_tag, filt_weixintag, parse_links


class TestHtmls(unittest.TestCase):

    def test_filt_htmltag(self):
        """测试filt_htmltag函数"""
        html = "<p>这是一个<b>测试</b>文本</p>"
        result = filt_htmltag(html)
        self.assertEqual(result.strip(), "这是一个测试文本")

    def test_filt_tag(self):
        """测试filt_tag函数"""
        html = "<p>这是一个<b>测试</b>文本</p>"
        result = filt_tag(html)
        self.assertEqual(result.strip(), "这是一个测试文本")

    def test_filt_base64(self):
        """测试filt_base64函数"""
        html = '<p>文本<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" alt="测试"></p>'
        result = filt_base64(html)
        self.assertEqual(result, "<p>文本</p>")

    def test_filt_js(self):
        """测试filt_js函数"""
        html = '<p>文本</p><script>alert("测试");</script><p>更多文本</p>'
        result = filt_js(html)
        self.assertEqual(result, "<p>文本</p><p>更多文本</p>")

    def test_filt_weixintag(self):
        """测试filt_weixintag函数"""
        text = "图片/ Unsplash内容/图虫创意"
        result = filt_weixintag(text)
        self.assertEqual(result, "图片\n内容\n图\n")

    def test_parse_links(self):
        """测试parse_links函数"""
        html = '<p>链接1<a href="http://example.com">示例</a>和链接2<a href="http://test.com">测试</a></p>'
        result = parse_links(html)
        self.assertEqual(result, ["http://example.com", "http://test.com"])


if __name__ == "__main__":
    unittest.main()
