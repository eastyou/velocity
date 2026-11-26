"""velocity 命令行入口：速度、路程、时间、平均速度、单位换算与相遇问题。"""

import argparse
import math
import sys
from typing import List, Optional, Sequence, Tuple

from .core import (
    average_speed,
    convert_speed,
    distance_travelled,
    meeting_time,
    normalize_unit,
    speed,
    time_seconds,
)
from .sheet import make_questions, render_demo, render_sheet, write_html


def _ensure_utf8_console() -> None:
    """尽量把标准输出与标准错误切换为 UTF-8，失败时忽略。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            continue


def _to_float(text: str, name: str) -> float:
    """把命令行文本转成有限浮点数。"""
    if not isinstance(text, str):
        raise ValueError("%s必须是数字" % name)
    raw = text.strip()
    if not raw:
        raise ValueError("%s不能为空" % name)
    try:
        value = float(raw)
    except ValueError:
        raise ValueError("%s必须是数字，收到「%s」" % (name, text))
    if math.isnan(value) or math.isinf(value):
        raise ValueError("%s必须是有限数字" % name)
    return value


def _to_int(text: str, name: str) -> int:
    """把命令行文本转成整数。"""
    if not isinstance(text, str):
        raise ValueError("%s必须是整数" % name)
    raw = text.strip()
    if not raw:
        raise ValueError("%s不能为空" % name)
    try:
        return int(raw)
    except ValueError:
        raise ValueError("%s必须是整数，收到「%s」" % (name, text))


def _parse_segments(text: str) -> List[Tuple[float, float]]:
    """解析「路程:时间,路程:时间」格式的分段数据。"""
    if not isinstance(text, str):
        raise ValueError("分段必须是文本")
    raw = text.strip()
    if not raw:
        raise ValueError("分段不能为空，格式为「路程:时间,路程:时间」")
    parts = [part.strip() for part in raw.split(",")]
    segments = []  # type: List[Tuple[float, float]]
    for index, part in enumerate(parts, start=1):
        if not part:
            raise ValueError("第 %d 段为空，格式应为「路程:时间」" % index)
        if part.count(":") != 1:
            raise ValueError("第 %d 段格式错误，应为「路程:时间」" % index)
        left, right = part.split(":")
        distance_value = _to_float(left, "第 %d 段路程" % index)
        time_value = _to_float(right, "第 %d 段时间" % index)
        segments.append((distance_value, time_value))
    return segments


def _cmd_speed(args: argparse.Namespace) -> int:
    distance_value = _to_float(args.distance, "路程")
    time_value = _to_float(args.time, "时间")
    result = speed(distance_value, time_value)
    print("速度：%.2f m/s" % result)
    print("速度：%.2f km/h" % (result * 3.6))
    return 0


def _cmd_distance(args: argparse.Namespace) -> int:
    speed_value = _to_float(args.speed, "速度")
    time_value = _to_float(args.time, "时间")
    result = distance_travelled(speed_value, time_value)
    print("路程：%.2f m" % result)
    print("路程：%.2f km" % (result / 1000.0))
    return 0


def _cmd_time(args: argparse.Namespace) -> int:
    distance_value = _to_float(args.distance, "路程")
    speed_value = _to_float(args.speed, "速度")
    result = time_seconds(speed_value, distance_value)
    print("时间：%.2f 秒" % result)
    print("时间：%.2f 分钟" % (result / 60.0))
    return 0


def _cmd_average(args: argparse.Namespace) -> int:
    segments = _parse_segments(args.segments)
    result = average_speed(segments)
    total_distance = 0.0
    total_time = 0.0
    for distance_value, time_value in segments:
        total_distance += distance_value
        total_time += time_value
    print("总路程：%.2f m" % total_distance)
    print("总时间：%.2f s" % total_time)
    print("平均速度：%.2f m/s" % result)
    print("平均速度：%.2f km/h" % (result * 3.6))
    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    value = _to_float(args.value, "速度")
    from_unit = normalize_unit(args.from_unit)
    to_unit = normalize_unit(args.to_unit)
    result = convert_speed(value, from_unit, to_unit)
    print("%.3f %s = %.3f %s" % (value, from_unit, result, to_unit))
    return 0


def _cmd_meeting(args: argparse.Namespace) -> int:
    first_speed = _to_float(args.v1, "速度 v1")
    second_speed = _to_float(args.v2, "速度 v2")
    distance_value = _to_float(args.distance, "距离")
    result = meeting_time(first_speed, second_speed, distance_value)
    print("相遇时间：%.2f 小时" % result)
    return 0


def _cmd_sheet(args: argparse.Namespace) -> int:
    count = _to_int(args.count, "题目数量")
    seed = _to_int(args.seed, "随机种子")
    questions = make_questions(count, seed)
    page = render_sheet(questions, args.answers)
    write_html(args.output, page)
    print("已生成练习纸：%s（%d 题）" % (args.output, len(questions)))
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    page = render_demo()
    write_html(args.output, page)
    print("已生成演示页：%s" % args.output)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="velocity",
        description="初中物理：速度与平均速度计算工具",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="子命令")

    speed_parser = subparsers.add_parser("speed", help="由路程与时间求速度")
    speed_parser.add_argument("--distance", required=True, metavar="M", help="路程（m）")
    speed_parser.add_argument("--time", required=True, metavar="S", help="时间（s）")
    speed_parser.set_defaults(handler=_cmd_speed)

    distance_parser = subparsers.add_parser("distance", help="由速度与时间求路程")
    distance_parser.add_argument("--speed", required=True, metavar="V", help="速度（m/s）")
    distance_parser.add_argument("--time", required=True, metavar="S", help="时间（s）")
    distance_parser.set_defaults(handler=_cmd_distance)

    time_parser = subparsers.add_parser("time", help="由路程与速度求时间")
    time_parser.add_argument("--distance", required=True, metavar="M", help="路程（m）")
    time_parser.add_argument("--speed", required=True, metavar="V", help="速度（m/s）")
    time_parser.set_defaults(handler=_cmd_time)

    average_parser = subparsers.add_parser("average", help="求多段路程的平均速度")
    average_parser.add_argument(
        "--segments",
        required=True,
        metavar="路程:时间,...",
        help="每段「路程:时间」，逗号分隔，例如 100:10,300:20",
    )
    average_parser.set_defaults(handler=_cmd_average)

    convert_parser = subparsers.add_parser("convert", help="m/s 与 km/h 互转")
    convert_parser.add_argument("--value", required=True, metavar="V", help="待换算的速度")
    convert_parser.add_argument("--from", dest="from_unit", required=True, metavar="单位", help="原单位（m/s 或 km/h）")
    convert_parser.add_argument("--to", dest="to_unit", required=True, metavar="单位", help="目标单位（m/s 或 km/h）")
    convert_parser.set_defaults(handler=_cmd_convert)

    meeting_parser = subparsers.add_parser("meeting", help="相向而行的相遇时间")
    meeting_parser.add_argument("--v1", required=True, metavar="KM/H", help="甲的速度（km/h）")
    meeting_parser.add_argument("--v2", required=True, metavar="KM/H", help="乙的速度（km/h）")
    meeting_parser.add_argument("--distance", required=True, metavar="KM", help="两地距离（km）")
    meeting_parser.set_defaults(handler=_cmd_meeting)

    sheet_parser = subparsers.add_parser("sheet", help="生成 A4 练习纸")
    sheet_parser.add_argument("--count", default="8", metavar="N", help="题目数量（1-50，默认 8）")
    sheet_parser.add_argument("--seed", default="1", metavar="SEED", help="随机种子（整数，默认 1）")
    sheet_parser.add_argument("-o", "--output", required=True, metavar="FILE", help="输出 HTML 文件")
    sheet_parser.add_argument("--answers", action="store_true", help="附带答案页")
    sheet_parser.set_defaults(handler=_cmd_sheet)

    demo_parser = subparsers.add_parser("demo", help="生成公式与例题卡片页")
    demo_parser.add_argument("-o", "--output", required=True, metavar="FILE", help="输出 HTML 文件")
    demo_parser.set_defaults(handler=_cmd_demo)

    return parser


def _run(args: argparse.Namespace) -> int:
    handler = getattr(args, "handler", None)
    if handler is None:
        raise ValueError("未知子命令")
    return int(handler(args))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主入口，成功返回 0，输入非法或写文件失败返回 2。"""
    _ensure_utf8_console()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.error("请指定子命令（speed、distance、time、average、convert、meeting、sheet、demo）")
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
