"""Units of measurement in Persian text, written as their standard English
symbols: «۱۰ میلی‌گرم بر کیلوگرم در روز» -> «۱۰ mg/kg/day».

The Persian lesson summaries and calculator texts spelled units out in
Persian (میلی‌گرم، میلی‌لیتر در دقیقه، میلی‌گرم بر متر مربع ...), which a
clinician reads more slowly than the symbol and which no longer matched the
English text beside them. Only the unit changes: the number before it and the
sentence around it are left exactly as they were.

What counts as a unit:
- a unit word -- a base (گرم، لیتر، مول، متر، واحد ...) with an optional
  prefix (میلی، میکرو، نانو، کیلو ...), the parts joined by a ZWNJ, a space or
  nothing -- and the units chained to it with «بر»، «در» or «/»
  (mg/kg/day). A time (دقیقه، ساعت، روز ...) counts only inside such a chain,
  and not where it is a point in time rather than a rate («در روز اول»،
  «در ساعت ۸»); a duration on its own («۷ روز») stays Persian.
- a word that is also ordinary Persian -- گرم (warm), واحد (single), مول
  (a hydatidiform mole), کالری, متر, سی‌سی -- only right after a number
  («۲ گرم»; «دوز واحد» is left alone) or when written with a slash.

The number a unit measures is written in Latin digits too, with the numbers
of its range or list: «۲۵ تا ۵۰ میلی‌گرم» -> «25 تا 50 mg». Other numbers
(«۷ روز») keep their Persian digits.
"""

import re

_JOIN = "[\u200c ]?"
# A Persian letter (or a harakat) or ZWNJ -- not a digit («۱۰میلی‌گرم» still
# has a unit) and not punctuation («میلی‌گرم در روز،» ends at the comma).
_LETTER = "[\u0620-\u0652\u0670-\u06D3\u06D5\u06FA-\u06FF\u200c]"
_DIGIT = "[0-9\u06F0-\u06F9\u0660-\u0669]"
_NUMBER_BEFORE = re.compile(
    "(?:[0-9\u06F0-\u06F9\u0660-\u0669\u2070-\u2079\u00B2\u00B3\u00B9]|\\$result\\d+|\\$\\d+|میلیون|هزار|میلیارد)[\\s\u200c]*$"
)

# morphemes -> (symbol, needs a number before it). Longest spellings first.
_UNITS = [
    (("میلی", "متر", "جیوه"), "mmHg", False),
    (("سانتی", "متر", "آب"), "cmH2O", False),
    (("میلی", "واحد", "بین", "المللی"), "mIU", False),
    (("واحد", "بین", "المللی"), "IU", False),
    (("میلی", "اکی", "والان"), "mEq", False),
    (("اکی", "والان"), "Eq", False),
    (("میلی", "اسمول"), "mOsm", False),
    (("اسمول",), "Osm", False),
    (("کیلو", "کالری"), "kcal", False),
    (("سانتی", "متر", "مربع"), "cm²", False),
    (("میلی", "متر", "مربع"), "mm²", False),
    (("سانتی", "متر", "مکعب"), "cm³", False),
    (("میلی", "متر", "مکعب"), "mm³", False),
    (("متر", "مربع"), "m²", False),
    (("میلی", "گرم"), "mg", False),
    (("میکرو", "گرم"), "mcg", False),
    (("نانو", "گرم"), "ng", False),
    (("پیکو", "گرم"), "pg", False),
    (("کیلو", "گرم"), "kg", False),
    (("میلی", "لیتر"), "mL", False),
    (("میکرو", "لیتر"), "µL", False),
    (("دسی", "لیتر"), "dL", False),
    (("میلی", "مولار"), "mM", False),
    (("میکرو", "مولار"), "µM", False),
    (("نانو", "مولار"), "nM", False),
    (("پیکو", "مولار"), "pM", False),
    (("میلی", "مول"), "mmol", False),
    (("میکرو", "مول"), "µmol", False),
    (("نانو", "مول"), "nmol", False),
    (("پیکو", "مول"), "pmol", False),
    (("میلی", "واحد"), "mU", False),
    (("سانتی", "متر"), "cm", False),
    (("میلی", "متر"), "mm", False),
    (("میکرو", "متر"), "µm", False),
    (("نانو", "متر"), "nm", False),
    (("لیتر",), "L", False),
    (("گرم",), "g", True),
    (("مولار",), "M", True),
    (("مول",), "mol", True),
    (("واحد",), "units", True),
    (("کالری",), "cal", True),
    (("متر",), "m", True),
    (("سی", "سی"), "mL", True),
]
# «۱ واحد» is one unit, «۱۱ واحد» or «۰٫۱ واحد» are not.
_ONE_BEFORE = re.compile("(?<![0-9\u06F0-\u06F9٬,.٫])[1۱][\\s\u200c]*$")
_TIMES = {"ثانیه": "s", "دقیقه": "min", "ساعت": "h", "روز": "day", "هفته": "week", "ماه": "month", "سال": "year"}


def _spelling(parts):
    return _JOIN.join(re.escape(p) for p in parts)


_UNIT_RE = "|".join(f"(?:{_spelling(parts)})" for parts, _, _ in _UNITS)
_SYMBOLS = {"".join(parts): (symbol, needs_number) for parts, symbol, needs_number in _UNITS}
# A time is a rate's denominator only if no number, ordinal or suffix follows
# it: «در روز اول»، «در ساعت ۸»، «در ساعت‌های» are points in time.
_ORDINALS = (
    "اول|دوم|سوم|چهارم|پنجم|ششم|هفتم|هشتم|نهم|دهم|نخست|نخستین|اولیه|آخر|بعد|بعدی|قبل|قبلی"
    "|گذشته|جاری|پیش|متوالی|ها|های"
)
_POINT_IN_TIME = f"(?!\u200c|[ \\t]*(?:{_DIGIT}|(?:{_ORDINALS})(?!{_LETTER})))"
_TIME_RE = "|".join(re.escape(t) for t in _TIMES)
# «بر»، «در»، «/» and «(به ازای|در|بر) هر» (per each) between the units of one chain.
_SEP = "\\s*(?:(?:به[\u200c ]?ازای|در|بر)\\s+هر|بر|در|/)\\s*"
_BSA = "(?:۱[٫.]۷۳|1\\.73)\\s*" + _spelling(("متر", "مربع"))
_PART = f"(?:{_UNIT_RE}|(?:{_TIME_RE}){_POINT_IN_TIME}|{_BSA})"
_CHAIN = re.compile(f"(?<!{_LETTER})(?P<first>{_UNIT_RE})(?P<rest>(?:{_SEP}{_PART}(?!{_LETTER}))*)(?!{_LETTER})")
_PART_SPLIT = re.compile(f"({_SEP})")
# The adjective «۵۰۰ میلی‌گرمی» (a 500-mg ...) after a number: «۵۰۰ mg».
_ADJECTIVE = re.compile(f"(?<!{_LETTER})(?P<unit>{_UNIT_RE})ی(?!{_LETTER})")

_PHRASES = [
    (re.compile(f"(?<!{_LETTER})ضربان(?:{_JOIN}قلب)?\\s*در\\s*دقیقه(?!{_LETTER})"), "beats/min"),
    (re.compile(f"(?<!{_LETTER})تنفس\\s*در\\s*دقیقه(?!{_LETTER})"), "breaths/min"),
]
# «سلول در میکرولیتر»، «۷۵×۱۰⁹ در لیتر»: a count per volume reads «.../µL».
_COUNT_PER = re.compile(
    "(?P<count>سلول|×\\s*(?:۱۰|10)\\s*(?:\\^\\s*)?[0-9\u06F0-\u06F9\u2070-\u2079]+)\\s*(?:در|بر)\\s*"
    f"(?=(?:{_UNIT_RE})(?!{_LETTER}))"
)
# «۱۵۰۰ در میلی‌متر مکعب» (a cell count): «۱۵۰۰/mm³». Volumes only -- in
# «۵ میلی‌گرم در ۱۰ میلی‌لیتر» the number follows «در» and nothing changes.
_NUMBER_PER_VOLUME = re.compile(
    f"(?P<number>{_DIGIT}|میلیون|هزار)\\s*در\\s*(?=(?:{_spelling(('میلی', 'متر', 'مکعب'))}|{_spelling(('میکرو', 'لیتر'))}"
    f"|{_spelling(('میلی', 'لیتر'))}|{_spelling(('دسی', 'لیتر'))}|لیتر)(?!{_LETTER}))"
)
_LATIN = [
    (re.compile("(?<![A-Za-z])ml(?![A-Za-z])"), "mL"),
    (re.compile("(?<![A-Za-z])dl(?![A-Za-z])"), "dL"),
    (re.compile("(?<![A-Za-z])(?:Kg|KG)(?![A-Za-z])"), "kg"),
    (re.compile("(?<![A-Za-z])(?:ug|\u00b5g|\u03bcg)(?![A-Za-z])"), "mcg"),
    (re.compile("(?<=/)hr(?![A-Za-z])"), "h"),
    (re.compile("(?<=[/\\s0-9])m2(?![0-9A-Za-z])"), "m²"),
]


# The unit symbols a quantity can be followed by (all of _UNITS, and the
# rates and counts written as a phrase), longest first.
_SYMBOL_RE = "|".join(
    re.escape(s)
    for s in sorted({symbol for _, symbol, _ in _UNITS} | {"unit", "beats/min", "breaths/min"}, key=len, reverse=True)
)
_NUM = "[0-9\u06F0-\u06F9\u0660-\u0669](?:[0-9\u06F0-\u06F9\u0660-\u0669٫٬.,]*[0-9\u06F0-\u06F9\u0660-\u0669])?[\u2070-\u2079\u00B2\u00B3\u00B9]*"
# «۲۵ تا ۵۰»، «۰٫۱، ۰٫۲ و ۰٫۳»، «۲۰۰/۵۰»، «۷۵×۱۰⁹» -- the numbers of one quantity.
_NUM_SEP = "\\s*(?:تا|و|یا|-|–|—|~|،|,|/|×)\\s*"
_QUANTITY = re.compile(
    f"(?<![0-9\u06F0-\u06F9\u0660-\u0669٫٬.])(?:{_NUM})(?:{_NUM_SEP}(?:{_NUM}))*(?=\\s*/?(?:{_SYMBOL_RE})(?![A-Za-z0-9]))"
)
_LATIN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫٬", "01234567890123456789.,")
# «روز ۱ و ۸۰ mg»: a number right after one of these counts days or steps,
# not the unit, even when «و» ties it to the dose that follows.
_COUNTED_BEFORE = re.compile(
    f"(?<!{_LETTER})(?:روز|روزهای|هفته|هفته‌های|ماه|سال|ساعت|مرحله|مرحلهٔ|سیکل|دوره|بار|نوبت)\\s*$"
)
_FIRST_NUM_SEP = re.compile(_NUM_SEP)


def _latin_quantity(match):
    quantity = match.group(0)
    if _COUNTED_BEFORE.search(match.string[: match.start()]):
        sep = _FIRST_NUM_SEP.search(quantity)
        if not sep:
            return quantity
        return quantity[: sep.end()] + quantity[sep.end():].translate(_LATIN_DIGITS)
    return quantity.translate(_LATIN_DIGITS)


def _key(text):
    return re.sub("[\u200c ]", "", text)


def _symbol_of(part):
    if re.fullmatch(_BSA, part):
        return "1.73 m²"
    if part in _TIMES:
        return _TIMES[part]
    return _SYMBOLS[_key(part)][0]


def _chain(match):
    text = match.string
    first, rest = match.group("first"), match.group("rest")
    symbol, needs_number = _SYMBOLS[_key(first)]
    before = text[: match.start()]
    if needs_number and not _NUMBER_BEFORE.search(before) and not rest.lstrip().startswith("/"):
        # Not a unit here («دوز واحد»، «کمپرس گرم»). What follows it may
        # still hold units of its own, so only this word is skipped.
        return first + _CHAIN.sub(_chain, rest)
    pieces = _PART_SPLIT.split(rest)[1:]  # separator, part, separator, part ...
    symbols, has_time, consumed = [symbol], False, 0
    for i in range(0, len(pieces), 2):
        part = pieces[i + 1].strip()
        if part in _TIMES:
            if has_time:  # a rate has one time: «در روز در روز» keeps the second
                break
            has_time = True
        symbols.append(_symbol_of(part))
        consumed += len(pieces[i]) + len(pieces[i + 1])
    if symbol == "units" and _ONE_BEFORE.search(before):
        symbols[0] = "unit"
    out = "/".join(symbols)
    if re.search(f"{_DIGIT}$", before):
        out = " " + out  # «۱۰میلی‌گرم» -> «۱۰ mg»
    return out + _CHAIN.sub(_chain, rest[consumed:])


def _adjective(match):
    before = match.string[: match.start()]
    if not _NUMBER_BEFORE.search(before):
        return match.group(0)  # «وسیلهٔ اندازه‌گیری میلی‌لیتری» stays as written
    symbol = _SYMBOLS[_key(match.group("unit"))][0]
    if symbol == "units" and _ONE_BEFORE.search(before):
        symbol = "unit"
    return (" " if re.search(f"{_DIGIT}$", before) else "") + symbol


def standardize_units(text):
    """`text` with its Persian units written as standard symbols (see the
    module docstring). Anything that is not a non-empty string is returned
    as it is."""
    if not isinstance(text, str) or not text:
        return text
    for pattern, symbol in _PHRASES:
        text = pattern.sub(symbol, text)
    text = _COUNT_PER.sub(lambda m: m.group("count") + "/", text)
    text = _NUMBER_PER_VOLUME.sub(lambda m: m.group("number") + "/", text)
    text = _ADJECTIVE.sub(_adjective, text)
    text = _CHAIN.sub(_chain, text)
    for pattern, symbol in _LATIN:
        text = pattern.sub(symbol, text)
    return _QUANTITY.sub(_latin_quantity, text)


def standardize_in(value):
    """`standardize_units` over every string in a JSON-like value (dicts and
    lists), returning a new value."""
    if isinstance(value, str):
        return standardize_units(value)
    if isinstance(value, list):
        return [standardize_in(v) for v in value]
    if isinstance(value, dict):
        return {k: standardize_in(v) for k, v in value.items()}
    return value
