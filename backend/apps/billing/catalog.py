"""What the code knows how to sell: the built-in features (each one locked
somewhere in the API by apps.billing.enforcement), the kinds of content an
operator can fence off with a new "content" feature, and the custom feature
keys code has since been wired to check.
"""

from apps.lessons.data.study_topics import CATEGORIES

# key, Persian name, English name, countable, unit (what one use counts)
BUILTIN_FEATURES = [
    ("lessons", "درس‌نامه‌های دارویی", "Drug lessons", False, ""),
    ("uptodate", "مقالات UpToDate فارسی", "UpToDate articles", True, "مقاله"),
    ("lexicomp", "اطلاعات و تداخل‌های Lexicomp", "Lexicomp interactions", True, "بررسی تداخل"),
    ("medscape", "بیماری‌ها و گایدلاین‌های Medscape", "Medscape diseases and guidelines", True, "مقاله"),
    ("calculators", "ماشین‌حساب‌های بالینی", "Clinical calculators", True, "ماشین‌حساب"),
    ("flashcards", "فلش‌کارت", "Flashcards", True, "کارت"),
    ("quiz", "آزمون‌ها", "Quizzes", True, "سؤال"),
    ("stats", "آمار و برنامه‌ریزی مطالعه", "Statistics and study planning", False, ""),
]
BUILTIN_KEYS = {row[0] for row in BUILTIN_FEATURES}

# What a "content" feature can fence off. A content feature locks the
# matching content for everyone whose plans do not include it.
SCOPE_TOPIC_CATEGORY = "topic_category"
SCOPE_ATC_PREFIX = "atc_prefix"
SCOPE_TYPES = [
    (SCOPE_TOPIC_CATEGORY, "یک دسته‌ی مطالعه (فلش‌کارت و آزمون آن دسته)"),
    (SCOPE_ATC_PREFIX, "کد ATC (درس‌نامه و آزمون داروهای آن گروه)"),
]
TOPIC_CATEGORY_CHOICES = [(c["key"], c["name_fa"]) for c in CATEGORIES]

# Custom features a developer has since wired into the code (with
# enforcement.require_feature(request, "<key>")). Listing a key here is what
# turns its "waiting to be connected" badge off in the console.
WIRED_CUSTOM_KEYS: set[str] = set()
