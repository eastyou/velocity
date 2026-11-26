"""速度与平均速度的核心计算函数。

本模块只依赖标准库，所有对外函数都会校验输入并返回有限数值，
非法输入统一抛出中文 ValueError。
"""

import math
from collections.abc import Sequence as ABCSequence
from typing import Dict, List, Sequence, Tuple

# 结果上限：超过该值视为输入不合理
MAX_RESULT = 1e12
# 平均速度最多允许的分段数
MAX_SEGMENTS = 20
# 每段数据的元素个数
SEGMENT_FIELDS = 2
# 1 m/s 对应的 km/h 数值
KPH_PER_MPS = 3.6
# 1 km 对应的 m 数值
METERS_PER_KM = 1000.0

# 单位别名表，键为归一化后的写法
UNIT_ALIASES = {
    "m/s": "m/s",
    "mps": "m/s",
    "km/h": "km/h",
    "kph": "km/h",
}  # type: Dict[str, str]


def _number(value: float, name: str) -> float:
    """把输入转成有限浮点数，拒绝布尔值与非数值类型。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s必须是数字" % name)
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        raise ValueError("%s必须是有限数字" % name)
    return number


def _positive(value: float, name: str) -> float:
    """校验数值大于 0。"""
    number = _number(value, name)
    if number <= 0:
        raise ValueError("%s必须大于 0" % name)
    return number


def _check_result(value: float, name: str) -> float:
    """校验结果有限且不超过上限。"""
    if math.isnan(value) or math.isinf(value):
        raise ValueError("%s结果不是有限数值" % name)
    if abs(value) >= MAX_RESULT:
        raise ValueError("%s结果超出允许范围（绝对值需小于 1e12）" % name)
    return value


def normalize_unit(text: str) -> str:
    """把单位写法归一化为 m/s 或 km/h。"""
    if not isinstance(text, str):
        raise ValueError("单位必须是文本")
    key = "".join(text.split()).lower()
    if not key:
        raise ValueError("单位不能为空")
    if key not in UNIT_ALIASES:
        raise ValueError("单位仅支持 m/s 与 km/h，收到「%s」" % text)
    return UNIT_ALIASES[key]


def _segment_list(segments: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """把分段输入整理成 (路程, 时间) 列表并校验结构。"""
    if isinstance(segments, (str, bytes, dict)) or not isinstance(segments, ABCSequence):
        raise ValueError("分段必须是「路程, 时间」组成的序列")
    items = list(segments)
    if not items:
        raise ValueError("至少需要 1 段路程")
    if len(items) > MAX_SEGMENTS:
        raise ValueError("分段数量不能超过 %d 段" % MAX_SEGMENTS)
    parsed = []  # type: List[Tuple[float, float]]
    for index, item in enumerate(items, start=1):
        if isinstance(item, (str, bytes, dict)):
            raise ValueError("第 %d 段必须是「路程, 时间」两个数值" % index)
        if not isinstance(item, ABCSequence):
            raise ValueError("第 %d 段必须是「路程, 时间」两个数值" % index)
        values = list(item)
        if len(values) != SEGMENT_FIELDS:
            raise ValueError("第 %d 段必须包含路程与时间两个数值" % index)
        parsed.append((values[0], values[1]))
    return parsed


def speed(distance: float, time: float) -> float:
    """由路程（m）与时间（s）求速度，返回 m/s。"""
    distance_value = _positive(distance, "路程")
    time_value = _positive(time, "时间")
    return _check_result(distance_value / time_value, "速度")


def distance_travelled(speed_value: float, time: float) -> float:
    """由速度（m/s）与时间（s）求路程，返回 m。"""
    speed_number = _positive(speed_value, "速度")
    time_value = _positive(time, "时间")
    return _check_result(speed_number * time_value, "路程")


def time_seconds(speed_value: float, distance: float) -> float:
    """由速度（m/s）与路程（m）求时间，返回 s。"""
    speed_number = _positive(speed_value, "速度")
    distance_value = _positive(distance, "路程")
    return _check_result(distance_value / speed_number, "时间")


def average_speed(segments: Sequence[Tuple[float, float]]) -> float:
    """由若干段「路程, 时间」求全程平均速度，返回 m/s。"""
    items = _segment_list(segments)
    total_distance = 0.0
    total_time = 0.0
    for distance_value, time_value in items:
        total_distance += _positive(distance_value, "每段路程")
        total_time += _positive(time_value, "每段时间")
    if total_time <= 0:
        raise ValueError("总时间必须大于 0")
    return _check_result(total_distance / total_time, "平均速度")


def convert_speed(value: float, from_unit: str, to_unit: str) -> float:
    """在 m/s 与 km/h 之间换算速度。"""
    number = _positive(value, "速度")
    source = normalize_unit(from_unit)
    target = normalize_unit(to_unit)
    if source == target:
        result = number
    elif source == "m/s":
        result = number * KPH_PER_MPS
    else:
        result = number / KPH_PER_MPS
    return _check_result(result, "换算结果")


def meeting_time(v1: float, v2: float, distance: float) -> float:
    """相向而行的相遇时间，速度单位 km/h，距离单位 km，返回小时。"""
    first_speed = _positive(v1, "速度 v1")
    second_speed = _positive(v2, "速度 v2")
    distance_value = _positive(distance, "距离")
    total_speed = first_speed + second_speed
    if total_speed <= 0:
        raise ValueError("两速度和必须大于 0")
    return _check_result(distance_value / total_speed, "相遇时间")
