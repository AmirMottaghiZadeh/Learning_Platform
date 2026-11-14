"""Gregorian <-> Jalali (Solar Hijri) dates -- the calendar every learner
and operator in Iran reads dates in. A port of the jalaali-js algorithm
(Borkowski's breaks table), valid for Jalali years -61..3177.
"""

from datetime import date

_BREAKS = [
    -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060,
    2097, 2192, 2262, 2324, 2394, 2456, 3178,
]
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


def _div(a, b):
    # The algorithm is written for truncating division (JavaScript's ~~),
    # not Python's flooring // -- they differ for negative operands.
    return int(a / b)


def _mod(a, b):
    return a - _div(a, b) * b


def _jal_cal(jy):
    gy = jy + 621
    leap_j = -14
    jp = _BREAKS[0]
    jump = 0
    for jm in _BREAKS[1:]:
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm
    n = jy - jp
    leap_j += _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, gy, march


def to_gregorian(jy, jm, jd):
    _, gy, march = _jal_cal(jy)
    days = (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1
    return date.fromordinal(date(gy, 3, march).toordinal() + days)


def to_jalali(value):
    """(year, month, day) of a `date` (or the date part of a datetime)."""
    ordinal = value.toordinal()
    jy = value.year - 621
    leap, gy, march = _jal_cal(jy)
    k = ordinal - date(gy, 3, march).toordinal()
    if k >= 0:
        if k <= 185:
            return jy, 1 + _div(k, 31), _mod(k, 31) + 1
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    return jy, 7 + _div(k, 30), _mod(k, 30) + 1


def month_start(value):
    """The Gregorian date the Jalali month holding `value` starts on."""
    jy, jm, _ = to_jalali(value)
    return to_gregorian(jy, jm, 1)


def fa_digits(value):
    return str(value).translate(_FA_DIGITS)


def format_date(value, with_month_name=False):
    """"۱۴۰۵/۰۷/۲۲", or "۲۲ مهر ۱۴۰۵"."""
    if value is None:
        return ""
    jy, jm, jd = to_jalali(value)
    if with_month_name:
        return fa_digits(f"{jd} {MONTHS[jm - 1]} {jy}")
    return fa_digits(f"{jy}/{jm:02d}/{jd:02d}")
