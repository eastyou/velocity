"""velocity：初中物理速度与平均速度计算工具。"""

from .core import (
    MAX_SEGMENTS,
    average_speed,
    convert_speed,
    distance_travelled,
    meeting_time,
    normalize_unit,
    speed,
    time_seconds,
)
from .sheet import Question, make_questions, render_demo, render_sheet, write_html

__version__ = "0.1.0"

__all__ = [
    "MAX_SEGMENTS",
    "Question",
    "average_speed",
    "convert_speed",
    "distance_travelled",
    "make_questions",
    "meeting_time",
    "normalize_unit",
    "render_demo",
    "render_sheet",
    "speed",
    "time_seconds",
    "write_html",
    "__version__",
]
