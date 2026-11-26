"""velocity 的单元测试：核心计算、题目生成、HTML 渲染与命令行接口。"""

import contextlib
import io
import os
import tempfile
import unittest
from html.parser import HTMLParser
from typing import List, Optional, Tuple

from velocity import (
    Question,
    average_speed,
    convert_speed,
    distance_travelled,
    make_questions,
    meeting_time,
    normalize_unit,
    render_demo,
    render_sheet,
    speed,
    time_seconds,
    write_html,
)
from velocity.cli import main
from velocity.core import MAX_RESULT


class _TagCollector(HTMLParser):
    """收集 HTML 起始标签，用于验证页面可被标准库解析。"""

    def __init__(self) -> None:
        super().__init__()
        self.tags = []  # type: List[str]

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.tags.append(tag)


def parse_html(text: str) -> _TagCollector:
    """解析 HTML 文本，解析失败会直接抛出异常。"""
    collector = _TagCollector()
    collector.feed(text)
    collector.close()
    return collector


def run_cli(args: List[str]) -> Tuple[int, str, str]:
    """运行命令行并返回 (退出码, 标准输出, 标准错误)。"""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(args)
    return code, out.getvalue(), err.getvalue()


def make_sample_questions(count: int) -> List[Question]:
    """构造用于渲染测试的题目列表。"""
    return make_questions(count, 7)


class SpeedTests(unittest.TestCase):
    def test_speed_basic(self) -> None:
        self.assertEqual(speed(100.0, 8.0), 12.5)

    def test_speed_fraction(self) -> None:
        self.assertAlmostEqual(speed(150.0, 12.0), 12.5)

    def test_speed_zero_distance(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            speed(0.0, 8.0)
        self.assertIn("路程", str(ctx.exception))

    def test_speed_zero_time(self) -> None:
        with self.assertRaises(ValueError):
            speed(100.0, 0.0)

    def test_speed_negative_distance(self) -> None:
        with self.assertRaises(ValueError):
            speed(-10.0, 2.0)

    def test_speed_negative_time(self) -> None:
        with self.assertRaises(ValueError):
            speed(10.0, -2.0)

    def test_speed_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            speed(True, 8.0)

    def test_speed_string_rejected(self) -> None:
        with self.assertRaises(ValueError):
            speed("100", 8.0)

    def test_speed_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            speed(float("nan"), 8.0)

    def test_speed_inf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            speed(float("inf"), 8.0)

    def test_speed_result_limit(self) -> None:
        with self.assertRaises(ValueError):
            speed(MAX_RESULT, 0.5)

    def test_speed_tiny_time_limit(self) -> None:
        with self.assertRaises(ValueError):
            speed(1.0, 1e-13)


class DistanceTests(unittest.TestCase):
    def test_distance_basic(self) -> None:
        self.assertEqual(distance_travelled(5.0, 12.0), 60.0)

    def test_distance_fraction(self) -> None:
        self.assertAlmostEqual(distance_travelled(1.5, 2.0), 3.0)

    def test_distance_zero_speed(self) -> None:
        with self.assertRaises(ValueError):
            distance_travelled(0.0, 12.0)

    def test_distance_zero_time(self) -> None:
        with self.assertRaises(ValueError):
            distance_travelled(5.0, 0.0)

    def test_distance_negative(self) -> None:
        with self.assertRaises(ValueError):
            distance_travelled(-5.0, 12.0)

    def test_distance_bool(self) -> None:
        with self.assertRaises(ValueError):
            distance_travelled(False, 12.0)

    def test_distance_limit(self) -> None:
        with self.assertRaises(ValueError):
            distance_travelled(1e11, 10.0)


class TimeTests(unittest.TestCase):
    def test_time_basic(self) -> None:
        self.assertEqual(time_seconds(5.0, 3600.0), 720.0)

    def test_time_fraction(self) -> None:
        self.assertAlmostEqual(time_seconds(3.0, 10.0), 10.0 / 3.0)

    def test_time_zero_speed(self) -> None:
        with self.assertRaises(ValueError):
            time_seconds(0.0, 100.0)

    def test_time_zero_distance(self) -> None:
        with self.assertRaises(ValueError):
            time_seconds(5.0, 0.0)

    def test_time_negative_distance(self) -> None:
        with self.assertRaises(ValueError):
            time_seconds(5.0, -100.0)

    def test_time_string_speed(self) -> None:
        with self.assertRaises(ValueError):
            time_seconds("5", 100.0)

    def test_time_limit(self) -> None:
        with self.assertRaises(ValueError):
            time_seconds(0.001, 1e9)


class AverageSpeedTests(unittest.TestCase):
    def test_average_basic(self) -> None:
        value = average_speed([(100.0, 10.0), (300.0, 20.0)])
        self.assertAlmostEqual(value, 400.0 / 30.0)

    def test_average_single_segment(self) -> None:
        self.assertEqual(average_speed([(50.0, 10.0)]), 5.0)

    def test_average_empty(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([])

    def test_average_too_many(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([(10.0, 2.0)] * 21)

    def test_average_twenty_segments(self) -> None:
        self.assertEqual(average_speed([(10.0, 2.0)] * 20), 5.0)

    def test_average_string_rejected(self) -> None:
        with self.assertRaises(ValueError):
            average_speed("100:10")

    def test_average_dict_rejected(self) -> None:
        with self.assertRaises(ValueError):
            average_speed({"a": 1})  # type: ignore[arg-type]

    def test_average_item_not_pair(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([5.0])  # type: ignore[list-item]

    def test_average_triple_item(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([(1.0, 2.0, 3.0)])  # type: ignore[list-item]

    def test_average_zero_distance(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([(0.0, 10.0)])

    def test_average_zero_time(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([(100.0, 0.0)])

    def test_average_negative(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([(100.0, -10.0)])

    def test_average_nan_segment(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([(float("nan"), 10.0)])

    def test_average_generator_rejected(self) -> None:
        with self.assertRaises(ValueError):
            average_speed((item for item in [(10.0, 2.0)]))

    def test_average_bool_value(self) -> None:
        with self.assertRaises(ValueError):
            average_speed([(True, 10.0)])


class ConvertTests(unittest.TestCase):
    def test_convert_kph_to_mps(self) -> None:
        self.assertAlmostEqual(convert_speed(36.0, "km/h", "m/s"), 10.0)

    def test_convert_mps_to_kph(self) -> None:
        self.assertAlmostEqual(convert_speed(10.0, "m/s", "km/h"), 36.0)

    def test_convert_same_unit(self) -> None:
        self.assertEqual(convert_speed(12.0, "m/s", "m/s"), 12.0)

    def test_convert_alias_mps(self) -> None:
        self.assertAlmostEqual(convert_speed(10.0, "mps", "km/h"), 36.0)

    def test_convert_alias_kph_with_space(self) -> None:
        self.assertAlmostEqual(convert_speed(36.0, " KM/H ", "MPS"), 10.0)

    def test_convert_invalid_unit(self) -> None:
        with self.assertRaises(ValueError):
            convert_speed(36.0, "mph", "m/s")

    def test_convert_empty_unit(self) -> None:
        with self.assertRaises(ValueError):
            convert_speed(36.0, "", "m/s")

    def test_convert_non_string_unit(self) -> None:
        with self.assertRaises(ValueError):
            convert_speed(36.0, 3, "m/s")  # type: ignore[arg-type]

    def test_convert_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            convert_speed(0.0, "m/s", "km/h")

    def test_convert_negative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            convert_speed(-1.0, "m/s", "km/h")

    def test_convert_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            convert_speed(float("nan"), "m/s", "km/h")

    def test_convert_result_limit(self) -> None:
        with self.assertRaises(ValueError):
            convert_speed(4e11, "m/s", "km/h")


class MeetingTests(unittest.TestCase):
    def test_meeting_basic(self) -> None:
        self.assertAlmostEqual(meeting_time(60.0, 40.0, 200.0), 2.0)

    def test_meeting_equal_speeds(self) -> None:
        self.assertAlmostEqual(meeting_time(50.0, 50.0, 200.0), 2.0)

    def test_meeting_zero_v1(self) -> None:
        with self.assertRaises(ValueError):
            meeting_time(0.0, 40.0, 200.0)

    def test_meeting_zero_v2(self) -> None:
        with self.assertRaises(ValueError):
            meeting_time(60.0, 0.0, 200.0)

    def test_meeting_zero_distance(self) -> None:
        with self.assertRaises(ValueError):
            meeting_time(60.0, 40.0, 0.0)

    def test_meeting_negative(self) -> None:
        with self.assertRaises(ValueError):
            meeting_time(-60.0, 40.0, 200.0)

    def test_meeting_string(self) -> None:
        with self.assertRaises(ValueError):
            meeting_time("60", 40.0, 200.0)

    def test_meeting_limit(self) -> None:
        with self.assertRaises(ValueError):
            meeting_time(1e-10, 1e-10, 1e12)


class NormalizeUnitTests(unittest.TestCase):
    def test_normalize_mps(self) -> None:
        self.assertEqual(normalize_unit("mps"), "m/s")

    def test_normalize_kph(self) -> None:
        self.assertEqual(normalize_unit("KPH"), "km/h")

    def test_normalize_valid_direct(self) -> None:
        self.assertEqual(normalize_unit("km/h"), "km/h")

    def test_normalize_invalid(self) -> None:
        with self.assertRaises(ValueError):
            normalize_unit("mph")

    def test_normalize_non_string(self) -> None:
        with self.assertRaises(ValueError):
            normalize_unit(3)  # type: ignore[arg-type]


class MakeQuestionsTests(unittest.TestCase):
    def test_make_questions_count(self) -> None:
        self.assertEqual(len(make_questions(10, 1)), 10)

    def test_make_questions_single(self) -> None:
        questions = make_questions(1, 1)
        self.assertEqual(len(questions), 1)

    def test_make_questions_kinds(self) -> None:
        kinds = set(question.kind for question in make_questions(6, 1))
        self.assertEqual(len(kinds), 6)
        self.assertIn("平均速度", kinds)
        self.assertIn("单位换算", kinds)
        self.assertIn("相遇问题", kinds)

    def test_make_questions_numbering(self) -> None:
        numbers = [question.number for question in make_questions(9, 3)]
        self.assertEqual(numbers, list(range(1, 10)))

    def test_make_questions_reproducible(self) -> None:
        self.assertEqual(make_questions(8, 42), make_questions(8, 42))

    def test_make_questions_different_seed(self) -> None:
        first = [question.prompt for question in make_questions(8, 1)]
        second = [question.prompt for question in make_questions(8, 2)]
        self.assertNotEqual(first, second)

    def test_make_questions_negative_seed(self) -> None:
        self.assertEqual(make_questions(3, -5), make_questions(3, -5))

    def test_make_questions_answers_nonempty(self) -> None:
        for question in make_questions(12, 5):
            self.assertTrue(question.answer)
            self.assertIn("=", question.answer)

    def test_make_questions_zero(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(0, 1)

    def test_make_questions_too_many(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(51, 1)

    def test_make_questions_bool_count(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(True, 1)

    def test_make_questions_float_count(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(3.0, 1)  # type: ignore[arg-type]

    def test_make_questions_string_count(self) -> None:
        with self.assertRaises(ValueError):
            make_questions("8", 1)  # type: ignore[arg-type]

    def test_make_questions_bool_seed(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(3, True)

    def test_make_questions_string_seed(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(3, "1")  # type: ignore[arg-type]

    def test_make_questions_prompts_end_with_period(self) -> None:
        for question in make_questions(6, 9):
            self.assertTrue(question.prompt.endswith(("。", "？")))


class RenderSheetTests(unittest.TestCase):
    def test_render_sheet_title(self) -> None:
        page = render_sheet(make_sample_questions(4), False)
        self.assertIn("速度与平均速度练习", page)

    def test_render_sheet_question_blocks(self) -> None:
        page = render_sheet(make_sample_questions(5), False)
        self.assertEqual(page.count('<section class="q">'), 5)

    def test_render_sheet_answers_hidden(self) -> None:
        page = render_sheet(make_sample_questions(4), False)
        self.assertNotIn("参考答案", page)

    def test_render_sheet_answers_shown(self) -> None:
        questions = make_sample_questions(4)
        page = render_sheet(questions, True)
        self.assertIn("参考答案", page)
        self.assertIn(questions[0].answer, page)

    def test_render_sheet_parseable(self) -> None:
        page = render_sheet(make_sample_questions(8), True)
        collector = parse_html(page)
        self.assertIn("html", collector.tags)
        self.assertIn("main", collector.tags)

    def test_render_sheet_escapes(self) -> None:
        question = Question(1, "速度", "a < b & c > d", "x < y")
        page = render_sheet([question], True)
        self.assertIn("a &lt; b &amp; c &gt; d", page)
        self.assertIn("x &lt; y", page)
        self.assertNotIn("a < b", page)

    def test_render_sheet_empty(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet([], False)

    def test_render_sheet_bad_item(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(["question"], False)  # type: ignore[list-item]

    def test_render_sheet_string_questions(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet("abc", False)  # type: ignore[arg-type]

    def test_render_sheet_answers_not_bool(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(make_sample_questions(2), 1)  # type: ignore[arg-type]

    def test_render_demo_contains_formula(self) -> None:
        page = render_demo()
        self.assertIn("v = s / t", page)
        self.assertIn("公式", page)

    def test_render_demo_parseable(self) -> None:
        collector = parse_html(render_demo())
        self.assertIn("html", collector.tags)
        self.assertIn("section", collector.tags)

    def test_render_demo_has_no_answers(self) -> None:
        self.assertNotIn("参考答案", render_demo())


class WriteHtmlTests(unittest.TestCase):
    def test_write_html_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "out.html")
            write_html(path, "<html></html>")
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "<html></html>")

    def test_write_html_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "out.html")
            write_html(path, "first")
            write_html(path, "second")
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "second")

    def test_write_html_empty_path(self) -> None:
        with self.assertRaises(ValueError):
            write_html("   ", "<html></html>")

    def test_write_html_non_string_path(self) -> None:
        with self.assertRaises(ValueError):
            write_html(3, "<html></html>")  # type: ignore[arg-type]

    def test_write_html_bad_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "missing", "out.html")
            with self.assertRaises(ValueError):
                write_html(path, "<html></html>")

    def test_write_html_non_string_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "out.html")
            with self.assertRaises(ValueError):
                write_html(path, 3)  # type: ignore[arg-type]

    def test_write_html_utf8_chinese(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "cn.html")
            write_html(path, "<p>速度</p>")
            with open(path, encoding="utf-8") as handle:
                self.assertIn("速度", handle.read())


class CliTests(unittest.TestCase):
    def test_cli_speed(self) -> None:
        code, out, err = run_cli(["speed", "--distance", "100", "--time", "8"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("12.50 m/s", out)
        self.assertIn("45.00 km/h", out)

    def test_cli_distance(self) -> None:
        code, out, _ = run_cli(["distance", "--speed", "5", "--time", "12"])
        self.assertEqual(code, 0)
        self.assertIn("60.00 m", out)
        self.assertIn("0.06 km", out)

    def test_cli_time(self) -> None:
        code, out, _ = run_cli(["time", "--distance", "3600", "--speed", "5"])
        self.assertEqual(code, 0)
        self.assertIn("720.00 秒", out)
        self.assertIn("12.00 分钟", out)

    def test_cli_average(self) -> None:
        code, out, _ = run_cli(["average", "--segments", "100:10,300:20"])
        self.assertEqual(code, 0)
        self.assertIn("总路程：400.00 m", out)
        self.assertIn("总时间：30.00 s", out)
        self.assertIn("13.33 m/s", out)
        self.assertIn("48.00 km/h", out)

    def test_cli_convert(self) -> None:
        code, out, _ = run_cli(["convert", "--value", "36", "--from", "km/h", "--to", "m/s"])
        self.assertEqual(code, 0)
        self.assertIn("36.000 km/h = 10.000 m/s", out)

    def test_cli_convert_alias(self) -> None:
        code, out, _ = run_cli(["convert", "--value", "10", "--from", "mps", "--to", "kph"])
        self.assertEqual(code, 0)
        self.assertIn("10.000 m/s = 36.000 km/h", out)

    def test_cli_meeting(self) -> None:
        code, out, _ = run_cli(["meeting", "--v1", "60", "--v2", "40", "--distance", "200"])
        self.assertEqual(code, 0)
        self.assertIn("2.00 小时", out)

    def test_cli_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "sheet.html")
            code, out, _ = run_cli(["sheet", "--count", "8", "--seed", "1", "-o", path])
            self.assertEqual(code, 0)
            self.assertIn("8 题", out)
            with open(path, encoding="utf-8") as handle:
                page = handle.read()
            parse_html(page)
            self.assertNotIn("参考答案", page)

    def test_cli_sheet_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "sheet.html")
            code, _, _ = run_cli(
                ["sheet", "--count", "6", "--seed", "2", "-o", path, "--answers"]
            )
            self.assertEqual(code, 0)
            with open(path, encoding="utf-8") as handle:
                self.assertIn("参考答案", handle.read())

    def test_cli_sheet_seed_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = os.path.join(temp_dir, "a.html")
            second = os.path.join(temp_dir, "b.html")
            run_cli(["sheet", "--count", "5", "--seed", "3", "-o", first])
            run_cli(["sheet", "--count", "5", "--seed", "3", "-o", second])
            with open(first, encoding="utf-8") as handle:
                content_one = handle.read()
            with open(second, encoding="utf-8") as handle:
                content_two = handle.read()
            self.assertEqual(content_one, content_two)

    def test_cli_demo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "demo.html")
            code, out, _ = run_cli(["demo", "-o", path])
            self.assertEqual(code, 0)
            self.assertIn("演示页", out)
            with open(path, encoding="utf-8") as handle:
                parse_html(handle.read())

    def test_cli_bad_number(self) -> None:
        code, _, err = run_cli(["speed", "--distance", "abc", "--time", "8"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_zero_time(self) -> None:
        code, _, err = run_cli(["speed", "--distance", "100", "--time", "0"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_negative_speed(self) -> None:
        code, _, err = run_cli(["distance", "--speed", "-5", "--time", "2"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_nan_distance(self) -> None:
        code, _, err = run_cli(["speed", "--distance", "nan", "--time", "8"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_inf_time(self) -> None:
        code, _, err = run_cli(["speed", "--distance", "100", "--time", "inf"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_bad_segments(self) -> None:
        code, _, err = run_cli(["average", "--segments", "100:10,abc:20"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_empty_segments(self) -> None:
        code, _, err = run_cli(["average", "--segments", "  "])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_segment_missing_colon(self) -> None:
        code, _, err = run_cli(["average", "--segments", "100,10"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_invalid_unit(self) -> None:
        code, _, err = run_cli(["convert", "--value", "36", "--from", "mph", "--to", "m/s"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_cli_count_too_many(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "sheet.html")
            code, _, err = run_cli(["sheet", "--count", "51", "--seed", "1", "-o", path])
            self.assertEqual(code, 2)
            self.assertIn("错误：", err)

    def test_cli_count_not_int(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "sheet.html")
            code, _, err = run_cli(["sheet", "--count", "abc", "-o", path])
            self.assertEqual(code, 2)
            self.assertIn("错误：", err)

    def test_cli_sheet_bad_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "missing", "sheet.html")
            code, _, err = run_cli(["sheet", "--count", "2", "--seed", "1", "-o", path])
            self.assertEqual(code, 2)
            self.assertIn("错误：", err)

    def test_cli_missing_argument(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["speed"])
        self.assertEqual(ctx.exception.code, 2)

    def test_cli_help(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_cli_no_command(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main([])
        self.assertEqual(ctx.exception.code, 2)

    def test_cli_unknown_command(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["jump"])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
