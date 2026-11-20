"""Iranian mobile numbers, in the one form the system stores and sends to:
"09xxxxxxxxx"."""

import re

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_MOBILE = re.compile(r"^09\d{9}$")


class InvalidPhone(ValueError):
    pass


def normalize_phone(raw: str) -> str:
    """Accepts the usual ways a number is written -- Persian or Arabic
    digits, spaces and dashes, +98 / 0098 / 98 / no leading zero -- and
    returns "09xxxxxxxxx", or raises InvalidPhone."""
    digits = re.sub(r"[\s\-()]", "", (raw or "").translate(_DIGITS))
    if digits.startswith("+98"):
        digits = "0" + digits[3:]
    elif digits.startswith("0098"):
        digits = "0" + digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "0" + digits
    if not _MOBILE.match(digits):
        raise InvalidPhone("شمارهٔ موبایل معتبر نیست؛ مثل ۰۹۱۲۱۲۳۴۵۶۷ وارد کن.")
    return digits


def looks_like_phone(raw: str) -> bool:
    try:
        normalize_phone(raw)
    except InvalidPhone:
        return False
    return True
