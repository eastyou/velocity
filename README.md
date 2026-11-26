# velocity

[![CI](https://github.com/eastyou/velocity/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/velocity/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

## 简介

velocity 是一个面向初中物理教学的命令行工具，用于计算速度、路程、时间、全程平均速度、单位换算与相向而行的相遇时间，并可生成 A4 练习纸与公式卡片页。全部功能只依赖 Python 标准库，无需联网。

## 特性

- 覆盖 v = s / t、s = v * t、t = s / v 三个基本公式，结果同时给出常用单位。
- 平均速度按总路程除以总时间计算，可一次输入 1 到 20 段「路程:时间」。
- m/s 与 km/h 互转，支持 mps、kph 等别名，大小写与空格自动归一化。
- 相遇问题按 t = s / (v1 + v2) 计算，速度单位 km/h、距离单位 km。
- 练习纸按随机种子出题，同一 seed 结果完全可复现，可单独输出答案页。
- 所有输入都做数值与范围校验，非法输入返回退出码 2 并输出中文错误信息。
- 生成的 HTML 使用内联样式与 A4 打印规则，浏览器直接打开即可打印。

## 安装

需要 Python 3.9 及以上版本，不需要任何第三方依赖。

```bash
pip install .
```

也可以不安装，直接在项目根目录用模块方式运行：

```bash
python3 -m velocity --help
```

## 使用

```bash
velocity speed --distance 100 --time 8
速度：12.50 m/s
速度：45.00 km/h

velocity distance --speed 5 --time 12
路程：60.00 m
路程：0.06 km

velocity time --distance 3600 --speed 5
时间：720.00 秒
时间：12.00 分钟

velocity average --segments 100:10,300:20
总路程：400.00 m
总时间：30.00 s
平均速度：13.33 m/s
平均速度：48.00 km/h

velocity convert --value 36 --from km/h --to m/s
36.000 km/h = 10.000 m/s

velocity meeting --v1 60 --v2 40 --distance 200
相遇时间：2.00 小时

velocity sheet --count 8 --seed 1 -o sheet.html --answers
已生成练习纸：sheet.html（8 题）

velocity demo -o demo.html
已生成演示页：demo.html
```

非法输入示例：

```bash
velocity speed --distance 100 --time 0
错误：时间必须大于 0
```

### 参数

| 子命令 | 参数 | 说明 |
| --- | --- | --- |
| `speed` | `--distance` | 路程，单位 m，必须大于 0 |
| `speed` | `--time` | 时间，单位 s，必须大于 0 |
| `distance` | `--speed` | 速度，单位 m/s，必须大于 0 |
| `distance` | `--time` | 时间，单位 s，必须大于 0 |
| `time` | `--distance` | 路程，单位 m，必须大于 0 |
| `time` | `--speed` | 速度，单位 m/s，必须大于 0 |
| `average` | `--segments` | 形如 `100:10,300:20`，1 到 20 段，每段路程与时间都必须大于 0 |
| `convert` | `--value` | 待换算的速度，必须大于 0 |
| `convert` | `--from` | 原单位，仅支持 m/s 或 km/h（别名 mps、kph） |
| `convert` | `--to` | 目标单位，仅支持 m/s 或 km/h（别名 mps、kph） |
| `meeting` | `--v1` / `--v2` | 两人的速度，单位 km/h，必须大于 0 |
| `meeting` | `--distance` | 两地距离，单位 km，必须大于 0 |
| `sheet` | `--count` | 题目数量，1 到 50，默认 8 |
| `sheet` | `--seed` | 随机种子，整数，默认 1 |
| `sheet` | `-o` / `--output` | 输出 HTML 文件路径，必填 |
| `sheet` | `--answers` | 附加答案页 |
| `demo` | `-o` / `--output` | 输出 HTML 文件路径，必填 |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 计算或生成成功 |
| 2 | 参数缺失、输入非法或文件写入失败（标准错误含「错误：」） |

## 作为库使用

```python
from velocity import (
    average_speed,
    convert_speed,
    distance_travelled,
    make_questions,
    meeting_time,
    render_sheet,
    speed,
    time_seconds,
)

print(speed(100.0, 8.0))                       # 12.5
print(distance_travelled(5.0, 12.0))           # 60.0
print(time_seconds(5.0, 3600.0))               # 720.0
print(average_speed([(100.0, 10.0), (300.0, 20.0)]))  # 13.333...
print(convert_speed(36.0, "km/h", "m/s"))      # 10.0
print(meeting_time(60.0, 40.0, 200.0))         # 2.0

questions = make_questions(8, 1)
page = render_sheet(questions, True)
with open("sheet.html", "w", encoding="utf-8") as handle:
    handle.write(page)
```

所有计算函数在输入非法时抛出中文 `ValueError`，例如距离为 0、速度是布尔值、单位为 mph、结果超过 1e12 等。

## 开发与测试

测试仅使用标准库 unittest，共 129 个测试方法，覆盖各公式的正常值与边界、非法输入、随机种子可复现、HTML 可被 `html.parser` 解析以及每个子命令的退出码。

```bash
python3 -m unittest discover -s tests -v
python3 -m velocity --help
```

## License

[MIT](LICENSE) © 2026 eastyou
