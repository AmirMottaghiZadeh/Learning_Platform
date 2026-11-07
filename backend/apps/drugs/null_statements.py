"""Lines of a summary that say nothing: that a section has no content
(«ندارد»، «None.»), that something is not mentioned or not reported («هیچ
منع مصرفی شناسایی نشده است»، «Rare: none separately reported»), that it was
not studied («مطالعهٔ رسمی تداخل دارویی انجام نشده است») or, in the abuse
section, that the drug is not controlled and not abused («زونیساماید مادهٔ
کنترل‌شده نیست»). A learner reads them for nothing, and an empty Persian
section used to fall back to an English «None.».

A line counts only when it states an absence and every word in it is a
generic one -- the section's own vocabulary, a qualifier («شایع:»، «فرم
قرص:»), or the drug's own name. One word that says something specific keeps
the whole line: «در کودکان بررسی نشده است» names a population, «با نلفیناویر
تداخل ندارد» a drug, «مادهٔ کنترل‌شدهٔ جدول IV است» states a fact, «خطر»،
«ممکن است» and «دارد» are not in the vocabulary. Lines are kept or dropped
whole, never rewritten.
"""

import re

_ZWNJ = "‌"

GENERIC_FA = set(
    """
    هیچ موردی مورد مواردی منع مصرف مطلق نسبی شناخته شده شناخته‌شده نشده است وجود ندارد ندارند نیست نیستند
    ذکر گزارش شناسایی مشاهده ارائه بیان ثبت دیده نشد نداد ندادند نشان نبوده نبوده‌اند انتظار نمی‌رود نمی‌شود
    هشدار هشدارها احتیاط احتیاط‌ها احتیاطی خاص ویژه جعبه‌ای ستون ورودی حاوی
    تداخل تداخلات دارویی دارو داروی داروها دارو-دارو این آن فرآورده فرآورده‌ها محصول
    عارضه عوارض جانبی جدی مهم/جدی مهم شایع نادر کلیات
    سوءمصرف سوء سوءاستفاده وابستگی تحمل فیزیکی روانی جسمی پتانسیل احتمال اعتیاد اعتیادآور
    ماده مادهٔ کنترل‌شده کنترل تحت قانونی زمان‌بندی‌شده
    اطلاعات داده داده‌ها کافی محدود موجود قطعی
    مطالعه مطالعهٔ مطالعات مطالعه‌ها رسمی انجام بررسی ارزیابی نظام‌مند به‌طور طور اختصاصی جداگانه دیگر سایر
    بالینی کارآزمایی کارآزمایی‌ها کارآزمایی‌های کنترل‌شده تجربه مشاهدات حیوانات حیوانی حیوان انسان انسانی انسان‌ها
    شواهد شواهدی مبنی گرایش رفتار جویای جستجوی جست‌وجوی داروجویانه
    متن خام برچسب منبع
    فرم فرم‌ها فرم‌های قرص کپسول تزریقی خوراکی موضعی ماهیت اجزای اجزا هم‌زمان همزمان شناسایی‌شده گزارش‌شده
    در برای با از و یا که به بر اساس درباره دربارهٔ نیز هم
    """.split()
)
GENERIC_EN = set(
    """
    none no not known is are was were be been being has have had stated listed identified reported separately
    specifically named mentioned provided documented described observed seen shown expected applicable unknown n/a na
    in the a an of for or and to with on by from any other its it this that these there
    source labeling label labels absolute relative contraindication contraindications warning warnings precaution
    precautions boxed drug drugs drug-drug interaction interactions formal studies study clinical clinically
    significant important serious common rare overall general specific trials trial performed conducted
    evaluated studied systematically controlled substance product products abuse misuse dependence
    potential physical psychological tolerance addiction data information available limited insufficient based
    humans human animals animal adverse reactions reaction effects form forms tablet tablets capsule
    injection oral topical nature components ingredients important/serious
    """.split()
)

_STATES_ABSENCE_FA = re.compile(
    r"(ندارد|ندارند|نیست|نیستند|نشده|نشد(?![؀-ۿ])|نبوده|نداد|ندادند|نمی‌رود|نمی‌شود)"
)
_STATES_ABSENCE_EN = re.compile(r"\b(none|no|not|unknown|n/?a)\b", re.I)
_WORD = re.compile(r"[؀-ۿ‌]+|[A-Za-z0-9][A-Za-z0-9/+\-]*")
_SUFFIXES = ("‌ای", "ای", "ی", "‌ها", "‌های", "ها", "های", "ٔ")


def _generic_fa(word, names):
    word = word.strip(_ZWNJ)
    if word in GENERIC_FA or word in names:
        return True
    return any(word.endswith(s) and (word[: -len(s)] in GENERIC_FA or word[: -len(s)] in names) for s in _SUFFIXES)


def name_words(*names):
    """The words of the drug's own names, which a null line may carry («لینزولید
    مادهٔ کنترل‌شده نیست»)."""
    words = set()
    for name in names:
        words.update(w.lower() for w in _WORD.findall(name or ""))
    return words


def is_null_statement(line, lang, names=frozenset()):
    """True when `line` (a summary line, its bullet already stripped) says
    nothing -- see the module docstring. `names` comes from name_words()."""
    body = line.strip().rstrip(".،؛;: ")
    if not body:
        return False
    words = _WORD.findall(body)
    if lang == "fa":
        if not _STATES_ABSENCE_FA.search(body):
            return False
        return all(_generic_fa(w, names) or w.lower() in names for w in words)
    if not _STATES_ABSENCE_EN.search(body):
        return False
    return all(w.lower() in GENERIC_EN or w.lower() in names for w in words)
