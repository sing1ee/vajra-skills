---
name: bazi
description: 八字排盘计算。根据出生年月日时计算八字四柱（年柱、月柱、日柱、时柱），基于精确的农历/节气算法。
---

# Bazi Skill

八字排盘计算工具，使用 lunar_python 库进行精确计算。

## 快速开始（推荐）

使用 uvx，无需安装任何依赖：

```bash
uvx --with lunar-python python scripts/bazi.py 1990 8 15 8
```

输出：
```
1990年8月15日8时
年柱: 庚午
月柱: 甲申
日柱: 壬子
时柱: 甲辰
```

## 安装 uv

如果还没有安装 uv，运行：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

或者通过包管理器安装：
```bash
# brew
brew install uv

# pip
pip install uv
```

如果不想每次输入 `--with lunar-python`，也可以提前安装：

```bash
pip install lunar-python
# 或
uv add lunar-python
```

## 使用方式

### 命令行

```bash
python scripts/bazi.py <年份> <月份> <日期> <小时>
```

示例：
```bash
python scripts/bazi.py 1990 8 15 8
```

### 作为模块导入

```python
from datetime import datetime
import sys
sys.path.insert(0, 'skill-bazi/scripts')
from bazi import calculate_bazi

dt = datetime(1990, 8, 15, 8)
result = calculate_bazi(dt)
print(result)
```

## 输出格式

返回字典包含：
- `year`: 年柱（如 "庚午"）
- `month`: 月柱（如 "甲申"）
- `day`: 日柱（如 "壬子"）
- `hour`: 时柱（如 "甲辰"）
- `year_gan`, `year_zhi`: 年干支分开的干和支
- `month_gan`, `month_zhi`: 月干支
- `day_gan`, `day_zhi`: 日干支
- `hour_gan`, `hour_zhi`: 时干支

## 算法说明

- 年柱：从立春开始切换
- 月柱：从节气（中气）开始切换
- 日柱：使用儒略日精确计算
- 时柱：23-1点为子时，以此类推

使用 lunar_python 库，基于专业天文算法，结果精确可靠。
