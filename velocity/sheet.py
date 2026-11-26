"""练习纸与演示页生成模块。

题库按固定顺序循环生成，使用 random.Random(seed) 保证同一随机种子结果可复现。
所有 HTML 均由字符串拼接而成，动态文本统一经过 html.escape 转义。
"""

import html
import random
from collections.abc import Sequence as ABCSequence
from dataclasses import dataclass
from typing import List, Sequence

from .core import (
    MAX_RESULT,
    average_speed,
    convert_speed,
    distance_travelled,
    meeting_time,
    speed,
    time_seconds,
)

# 题目数量上限
MAX_QUESTIONS = 50

_SHEET_STYLE = """
@page { size: A4; margin: 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #f5f7fa;
  color: #1f2933;
  font-family: "Songti SC", "SimSun", "Noto Serif CJK SC", serif;
  font-size: 12pt;
  line-height: 1.6;
}
main.sheet {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  padding: 16mm;
  background: #ffffff;
}
header.head { border-bottom: 2px solid #2c7a7b; padding-bottom: 6mm; }
header.head h1 { margin: 0 0 2mm; font-size: 20pt; color: #234e52; letter-spacing: 2px; }
p.meta { margin: 0; font-size: 11pt; color: #52606d; }
section.questions { margin-top: 6mm; }
section.q { padding: 3mm 0 2mm; border-bottom: 1px dashed #cbd2d9; page-break-inside: avoid; }
div.q-head { display: flex; align-items: baseline; gap: 2mm; margin-bottom: 1mm; }
span.no { font-weight: bold; color: #2c7a7b; }
span.kind { font-size: 9pt; color: #7b8794; border: 1px solid #cbd2d9; border-radius: 3px; padding: 0 2mm; }
p.prompt { margin: 0; }
div.space { height: 18mm; }
section.answers { margin-top: 8mm; page-break-before: always; }
section.answers h2 { font-size: 16pt; color: #234e52; border-bottom: 1px solid #cbd2d9; padding-bottom: 2mm; }
section.answers div.ans { padding: 2mm 0; border-bottom: 1px dotted #e4e7eb; }
footer.foot { margin-top: 8mm; text-align: center; font-size: 9pt; color: #9aa5b1; }
"""

_DEMO_STYLE = """
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px;
  background: #f5f7fa;
  color: #1f2933;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.6;
}
main.wrap { max-width: 980px; margin: 0 auto; }
h1 { margin: 0 0 8px; font-size: 28px; color: #234e52; }
p.lead { margin: 0 0 24px; color: #52606d; }
div.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
section.card { background: #ffffff; border: 1px solid #e4e7eb; border-radius: 10px; padding: 18px; }
section.card h2 { margin: 0 0 6px; font-size: 18px; color: #2c7a7b; }
p.formula { margin: 0 0 10px; font-family: "Times New Roman", serif; font-size: 20px; color: #1f2933; }
p.note { margin: 0 0 8px; color: #52606d; font-size: 14px; }
p.example { margin: 0; padding: 8px; background: #f0fdfa; border-left: 3px solid #2c7a7b; font-size: 14px; }
footer.foot { margin-top: 28px; text-align: center; color: #9aa5b1; font-size: 12px; }
"""


@dataclass(frozen=True)
class Question:
    """一道练习题：编号、类型、题干与参考答案。"""

    number: int
    kind: str
    prompt: str
    answer: str


def _int_value(value: int, name: str, low: int, high: int) -> int:
    """校验整数范围。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s必须是整数" % name)
    if value < low or value > high:
        raise ValueError("%s必须在 %d 到 %d 之间" % (name, low, high))
    return value


def _speed_question(number: int, rng: random.Random) -> Question:
    distance_value = rng.randint(20, 600)
    time_value = rng.randint(2, 60)
    value = speed(float(distance_value), float(time_value))
    prompt = "某物体在 %d s 内通过 %d m 的路程，求它的速度（保留 2 位小数，单位 m/s）。" % (
        time_value,
        distance_value,
    )
    answer = "v = s / t = %d m / %d s = %.2f m/s" % (distance_value, time_value, value)
    return Question(number, "速度", prompt, answer)


def _distance_question(number: int, rng: random.Random) -> Question:
    speed_value = rng.randint(2, 30)
    time_value = rng.randint(3, 120)
    value = distance_travelled(float(speed_value), float(time_value))
    prompt = "一辆车以 %d m/s 的速度匀速行驶 %d s，求行驶的路程（单位 m）。" % (
        speed_value,
        time_value,
    )
    answer = "s = v * t = %d m/s * %d s = %.0f m" % (speed_value, time_value, value)
    return Question(number, "路程", prompt, answer)


def _time_question(number: int, rng: random.Random) -> Question:
    distance_value = rng.randint(60, 3000)
    speed_value = rng.randint(2, 25)
    value = time_seconds(float(speed_value), float(distance_value))
    prompt = "某人以 %d m/s 的速度走完 %d m 的路程，需要多少时间（保留 2 位小数，单位 s）？" % (
        speed_value,
        distance_value,
    )
    answer = "t = s / v = %d m / %d m/s = %.2f s" % (distance_value, speed_value, value)
    return Question(number, "时间", prompt, answer)


def _average_question(number: int, rng: random.Random) -> Question:
    first_distance = rng.randint(50, 400)
    first_time = rng.randint(5, 40)
    second_distance = rng.randint(50, 400)
    second_time = rng.randint(5, 40)
    value = average_speed(
        [
            (float(first_distance), float(first_time)),
            (float(second_distance), float(second_time)),
        ]
    )
    prompt = (
        "小明第一段路走 %d m 用了 %d s，第二段路走 %d m 用了 %d s，"
        "求全程平均速度（保留 2 位小数，单位 m/s）。"
        % (first_distance, first_time, second_distance, second_time)
    )
    answer = "v = (s1 + s2) / (t1 + t2) = (%d + %d) / (%d + %d) = %.2f m/s" % (
        first_distance,
        second_distance,
        first_time,
        second_time,
        value,
    )
    return Question(number, "平均速度", prompt, answer)


def _convert_question(number: int, rng: random.Random) -> Question:
    value = rng.randint(5, 200)
    from_unit = rng.choice(["m/s", "km/h"])
    to_unit = "km/h" if from_unit == "m/s" else "m/s"
    result = convert_speed(float(value), from_unit, to_unit)
    prompt = "把 %d %s 换算成 %s（保留 3 位小数）。" % (value, from_unit, to_unit)
    answer = "%d %s = %.3f %s" % (value, from_unit, result, to_unit)
    return Question(number, "单位换算", prompt, answer)


def _meeting_question(number: int, rng: random.Random) -> Question:
    first_speed = rng.randint(20, 90)
    second_speed = rng.randint(20, 90)
    distance_value = rng.randint(50, 800)
    value = meeting_time(float(first_speed), float(second_speed), float(distance_value))
    prompt = (
        "甲、乙两人分别以 %d km/h 和 %d km/h 的速度相向而行，"
        "两地相距 %d km，求相遇时间（保留 2 位小数，单位小时）。"
        % (first_speed, second_speed, distance_value)
    )
    answer = "t = s / (v1 + v2) = %d / (%d + %d) = %.2f 小时" % (
        distance_value,
        first_speed,
        second_speed,
        value,
    )
    return Question(number, "相遇问题", prompt, answer)


_BUILDERS = [
    _speed_question,
    _distance_question,
    _time_question,
    _average_question,
    _convert_question,
    _meeting_question,
]


def make_questions(count: int, seed: int) -> List[Question]:
    """生成指定数量的练习题，同一 seed 结果完全一致。"""
    total = _int_value(count, "题目数量", 1, MAX_QUESTIONS)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("随机种子必须是整数")
    if abs(seed) >= MAX_RESULT:
        raise ValueError("随机种子超出允许范围（绝对值需小于 1e12）")
    rng = random.Random(seed)
    questions = []  # type: List[Question]
    for index in range(total):
        builder = _BUILDERS[index % len(_BUILDERS)]
        questions.append(builder(index + 1, rng))
    return questions


def _question_items(questions: Sequence[Question]) -> List[Question]:
    """校验题目序列并返回列表副本。"""
    if isinstance(questions, (str, bytes, dict)) or not isinstance(questions, ABCSequence):
        raise ValueError("题目必须是 Question 组成的序列")
    items = list(questions)
    if not items:
        raise ValueError("题目不能为空")
    for index, item in enumerate(items, start=1):
        if not isinstance(item, Question):
            raise ValueError("第 %d 项不是 Question 对象" % index)
        if isinstance(item.number, bool) or not isinstance(item.number, int) or item.number < 1:
            raise ValueError("第 %d 题的编号必须是正整数" % index)
    return items


def render_sheet(questions: Sequence[Question], answers: bool) -> str:
    """把题目渲染成 A4 练习纸 HTML，answers 为真时附带答案页。"""
    items = _question_items(questions)
    if not isinstance(answers, bool):
        raise ValueError("答案开关必须是布尔值")
    blocks = []  # type: List[str]
    for question in items:
        blocks.append(
            '<section class="q">'
            '<div class="q-head"><span class="no">%d.</span>'
            '<span class="kind">%s</span></div>'
            '<p class="prompt">%s</p>'
            '<div class="space"></div>'
            "</section>"
            % (
                question.number,
                html.escape(question.kind, quote=True),
                html.escape(question.prompt, quote=True),
            )
        )
    parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>速度与平均速度练习纸</title>",
        "<style>%s</style>" % _SHEET_STYLE,
        "</head>",
        "<body>",
        '<main class="sheet">',
        '<header class="head">',
        "<h1>速度与平均速度练习</h1>",
        '<p class="meta">共 %d 题　姓名：__________　班级：__________　日期：__________</p>'
        % len(items),
        "</header>",
        '<section class="questions">',
    ]
    parts.extend(blocks)
    parts.append("</section>")
    if answers:
        answer_blocks = []  # type: List[str]
        for question in items:
            answer_blocks.append(
                '<div class="ans">%d.（%s）%s</div>'
                % (
                    question.number,
                    html.escape(question.kind, quote=True),
                    html.escape(question.answer, quote=True),
                )
            )
        parts.append('<section class="answers">')
        parts.append("<h2>参考答案</h2>")
        parts.extend(answer_blocks)
        parts.append("</section>")
    parts.append('<footer class="foot">velocity · 初中物理速度练习</footer>')
    parts.append("</main>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)


def render_demo() -> str:
    """生成公式与例题卡片页 HTML。"""
    cards = [
        (
            "速度公式",
            "v = s / t",
            "速度等于路程除以时间，单位由路程与时间共同决定。",
            "v = 100 m / 8 s = %.2f m/s" % speed(100.0, 8.0),
        ),
        (
            "路程公式",
            "s = v * t",
            "已知速度（m/s）与时间（s）时，可直接求路程。",
            "s = 5 m/s * 12 s = %.0f m" % distance_travelled(5.0, 12.0),
        ),
        (
            "时间公式",
            "t = s / v",
            "已知路程与速度时，求出运动时间。",
            "t = 3600 m / 5 m/s = %.0f s" % time_seconds(5.0, 3600.0),
        ),
        (
            "平均速度",
            "v = (s1 + s2 + ...) / (t1 + t2 + ...)",
            "平均速度用总路程除以总时间，不能直接把速度相加后取平均。",
            "v = (100 + 300) m / (10 + 20) s = %.2f m/s"
            % average_speed([(100.0, 10.0), (300.0, 20.0)]),
        ),
        (
            "单位换算",
            "1 m/s = 3.6 km/h",
            "m/s 换 km/h 乘 3.6，km/h 换 m/s 除以 3.6。",
            "36 km/h = %.3f m/s" % convert_speed(36.0, "km/h", "m/s"),
        ),
        (
            "相遇问题",
            "t = s / (v1 + v2)",
            "相向而行时，两人速度相加，总距离除以速度和。",
            "t = 200 km / (60 + 40) km/h = %.2f 小时" % meeting_time(60.0, 40.0, 200.0),
        ),
    ]
    blocks = []  # type: List[str]
    for title, formula, note, example in cards:
        blocks.append(
            '<section class="card">'
            "<h2>%s</h2>"
            '<p class="formula">%s</p>'
            '<p class="note">%s</p>'
            '<p class="example">%s</p>'
            "</section>"
            % (
                html.escape(title, quote=True),
                html.escape(formula, quote=True),
                html.escape(note, quote=True),
                html.escape(example, quote=True),
            )
        )
    parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>速度公式与例题</title>",
        "<style>%s</style>" % _DEMO_STYLE,
        "</head>",
        "<body>",
        '<main class="wrap">',
        "<h1>速度与平均速度</h1>",
        '<p class="lead">六个常用公式与对应例题，数值均按题目要求取近似值。</p>',
        '<div class="grid">',
    ]
    parts.extend(blocks)
    parts.append("</div>")
    parts.append('<footer class="foot">velocity · 初中物理公式卡片</footer>')
    parts.append("</main>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)


def write_html(path: str, content: str) -> None:
    """把 HTML 内容写入文件，写入失败时抛出中文 ValueError。"""
    if not isinstance(path, str):
        raise ValueError("输出路径必须是文本")
    target = path.strip()
    if not target:
        raise ValueError("输出路径不能为空")
    if not isinstance(content, str):
        raise ValueError("HTML 内容必须是文本")
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(content)
    except OSError as exc:
        raise ValueError("无法写入文件 %s：%s" % (target, exc))
