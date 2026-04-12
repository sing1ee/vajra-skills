#!/usr/bin/env python3
"""
八字排盘计算
使用 lunar_python 库进行精确计算
"""
import sys
from datetime import datetime
from typing import Dict

try:
    from lunar_python import Solar
except ImportError:
    print("错误: 请先安装 lunar_python 库")
    print("运行: pip install lunar-python")
    sys.exit(1)


def calculate_bazi(birth_datetime: datetime) -> Dict:
    """
    计算完整的八字

    Args:
        birth_datetime: 出生日期时间

    Returns:
        包含年、月、日、时柱的字典
    """
    solar = Solar.fromYmdHms(
        birth_datetime.year,
        birth_datetime.month,
        birth_datetime.day,
        birth_datetime.hour,
        birth_datetime.minute,
        0
    )
    lunar = solar.getLunar()
    ba = lunar.getEightChar()

    year_gan = ba.getYearGan()
    year_zhi = ba.getYearZhi()
    month_gan = ba.getMonthGan()
    month_zhi = ba.getMonthZhi()
    day_gan = ba.getDayGan()
    day_zhi = ba.getDayZhi()
    hour_gan = ba.getTimeGan()
    hour_zhi = ba.getTimeZhi()

    return {
        "year": year_gan + year_zhi,
        "month": month_gan + month_zhi,
        "day": day_gan + day_zhi,
        "hour": hour_gan + hour_zhi,
        "year_gan": year_gan,
        "year_zhi": year_zhi,
        "month_gan": month_gan,
        "month_zhi": month_zhi,
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "hour_gan": hour_gan,
        "hour_zhi": hour_zhi
    }


def main():
    if len(sys.argv) < 5:
        print("用法: python bazi.py <年份> <月份> <日期> <小时>")
        print("示例: python bazi.py 1990 8 15 8")
        sys.exit(1)

    try:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4])
    except ValueError:
        print("错误: 请输入有效的数字")
        sys.exit(1)

    dt = datetime(year, month, day, hour)
    result = calculate_bazi(dt)

    print(f"\n{year}年{month}月{day}日{hour}时")
    print(f"年柱: {result['year']}")
    print(f"月柱: {result['month']}")
    print(f"日柱: {result['day']}")
    print(f"时柱: {result['hour']}")


if __name__ == "__main__":
    main()
