// Persian verses keep their original wording. Translations in either language
// are written for the app. Each source points to the work or an archival copy.
const QUOTES = [
  {
    authorFa: "فردوسی", authorEn: "Ferdowsi",
    fa: "توانا بود هر که دانا بود / ز دانش دل پیر برنا بود",
    en: "The wise are strong. Knowledge makes even an old heart young.",
    source: "https://ganjoor.net/ferdousi/shahname/aghaz/sh1/",
  },
  {
    authorFa: "لائوتسه", authorEn: "Laozi",
    fa: "سفری طولانی با نخستین گام آغاز می‌شود.",
    en: "A journey of a thousand li begins with the step beneath your feet.",
    source: "https://laozi-taoteching.org/en/chapters/64/",
  },
  {
    authorFa: "پروین اعتصامی", authorEn: "Parvin Etesami",
    fa: "گهر وقت، بدین خیرگی از دست مده",
    en: "Do not squander the jewel of time.",
    source: "https://fa.wikisource.org/wiki/پروین_اعتصامی_(مثنویات_و_تمثیلات_و_مقطعات)/هر_که_با_پاکدلان،_صبح_و_مسائی_دارد",
  },
  {
    authorFa: "فردریک داگلاس", authorEn: "Frederick Douglass",
    fa: "بی‌تلاش و مبارزه، پیشرفتی در کار نیست.",
    en: "If there is no struggle, there is no progress.",
    source: "https://home.nps.gov/frdo/learn/historyculture/thoughts-for-all-time.htm",
  },
  {
    authorFa: "حافظ", authorEn: "Hafez",
    fa: "درخت دوستی بنشان که کام دل به بار آرد / نهال دشمنی برکن که رنج بی‌شمار آرد",
    en: "Plant the tree of friendship. Uproot the sapling of hostility, for it bears endless grief.",
    source: "https://ganjoor.net/hafez/ghazal/sh115",
  },
  {
    authorFa: "جورج الیوت", authorEn: "George Eliot",
    fa: "برای چه زندگی می‌کنیم، اگر زندگی را برای یکدیگر آسان‌تر نکنیم؟",
    en: "What do we live for, if it is not to make life less difficult to each other?",
    source: "https://www.fiction.us/eliot/march/c72.html",
  },
  {
    authorFa: "سعدی", authorEn: "Saadi",
    fa: "مشک آن است که ببوید، نه آن که عطار بگوید.",
    en: "True musk is known by its scent, whatever the perfumer may say.",
    source: "https://ganjoor.net/saadi/golestan/gbab8/sh54/",
  },
  {
    authorFa: "رالف والدو امرسون", authorEn: "Ralph Waldo Emerson",
    fa: "هیچ کار بزرگی بی‌شور و اشتیاق به انجام نرسیده است.",
    en: "Nothing great was ever achieved without enthusiasm.",
    source: "https://emersoncentral.com/texts/essays-first-series/circles/",
  },
  {
    authorFa: "ناصرخسرو", authorEn: "Nasir Khusraw",
    fa: "درخت تو گر بار دانش بگیرد / به زیر آوری چرخ نیلوفری را",
    en: "If your tree bears the fruit of knowledge, even the blue heavens are within your reach.",
    source: "https://ganjoor.net/naserkhosro/divann/ghaside-naser/sh6/",
  },
  {
    authorFa: "هلن کلر", authorEn: "Helen Keller",
    fa: "زندگی یا ماجرایی جسورانه است یا هیچ.",
    en: "Life is either a daring adventure or nothing.",
    source: "https://afb.org/fun-facts-and-quotes",
  },
  {
    authorFa: "نظامی گنجوی", authorEn: "Nizami Ganjavi",
    fa: "کم گوی و گزیده گوی چون دُر / تا ز اندک تو جهان شود پر",
    en: "Speak sparingly and choose words like pearls. A few can fill the world.",
    source: "https://ganjoor.net/nezami/5ganj/leyli-majnoon/sh9/",
  },
  {
    authorFa: "هنری دیوید ثورو", authorEn: "Henry David Thoreau",
    fa: "زندگی‌مان در ریزه‌کاری‌ها هدر می‌رود. ساده کن، ساده کن.",
    en: "Our life is frittered away by detail. Simplify, simplify.",
    source: "https://en.wikisource.org/wiki/Walden_(1854)_Thoreau/Where_I_Lived,_and_What_I_Lived_for",
  },
  {
    authorFa: "سعدی", authorEn: "Saadi",
    fa: "عالم بی‌عمل به چه ماند؟ گفت به زنبور بی‌عسل.",
    en: "What is a scholar who never acts? A bee without honey.",
    source: "https://ganjoor.net/saadi/golestan/gbab8/sh74/",
  },
  {
    authorFa: "ویلیام شکسپیر", authorEn: "William Shakespeare",
    fa: "با خودت صادق باش.",
    en: "To thine own self be true.",
    source: "https://www.folger.edu/explore/shakespeares-works/hamlet/read/1/3/",
  },
  {
    authorFa: "پروین اعتصامی", authorEn: "Parvin Etesami",
    fa: "هر که با پاکدلان صبح و مسایی دارد / دلش از پرتو اسرار صفایی دارد",
    en: "Spend your days with the kindhearted, and their company will brighten your own heart.",
    source: "https://fa.wikisource.org/wiki/پروین_اعتصامی_(مثنویات_و_تمثیلات_و_مقطعات)/هر_که_با_پاکدلان،_صبح_و_مسائی_دارد",
  },
  {
    authorFa: "اپیکتتوس", authorEn: "Epictetus",
    fa: "برداشت ما از رویدادهاست که ناآراممان می‌کند.",
    en: "Men are disturbed, not by things, but by the principles and notions which they form concerning things.",
    source: "https://classics.mit.edu/Epictetus/epicench.html",
  },
  {
    authorFa: "حافظ", authorEn: "Hafez",
    fa: "هرگز نمیرد آن که دلش زنده شد به عشق",
    en: "Whoever has a heart awakened by love never dies.",
    source: "https://ganjoor.net/hafez/ghazal/sh11",
  },
  {
    authorFa: "ارسطو", authorEn: "Aristotle",
    fa: "یک پرستو تابستان نمی‌سازد، همان‌طور که یک روز هم نمی‌سازد.",
    en: "One swallow does not make a summer, nor does one day.",
    source: "https://classics.mit.edu/Aristotle/nicomachaen.1.i.html",
  },
  {
    authorFa: "مولانا", authorEn: "Rumi",
    fa: "از محبت تلخ‌ها شیرین شود / از محبت مس‌ها زرین شود",
    en: "Love turns bitterness sweet. Love turns copper into gold.",
    source: "https://ganjoor.net/moulavi/masnavi/daftar2/sh31",
  },
  {
    authorFa: "جین آستن", authorEn: "Jane Austen",
    fa: "به گذشته فقط تا جایی فکر کن که یادش مایهٔ شادی‌ات باشد.",
    en: "Think only of the past as its remembrance gives you pleasure.",
    source: "https://austen.unl.edu/visualizations/pride_and_prejudice/all",
  },
  {
    authorFa: "سعدی", authorEn: "Saadi",
    fa: "بنی‌آدم اعضای یکدیگرند / که در آفرینش ز یک گوهرند",
    en: "Human beings are limbs of one another, made of the same essence.",
    source: "https://ganjoor.net/saadi/golestan/gbab1/sh10",
  },
  {
    authorFa: "بنجامین فرانکلین", authorEn: "Benjamin Franklin",
    fa: "زمان ازدست‌رفته هرگز بازنمی‌گردد.",
    en: "Lost time is never found again.",
    source: "https://emend.press/way-to-wealth-original.html",
  },
  {
    authorFa: "نظامی گنجوی", authorEn: "Nizami Ganjavi",
    fa: "دانش طلب و بزرگی آموز",
    en: "Seek knowledge and learn how to grow into greatness.",
    source: "https://ganjoor.net/nezami/5ganj/leyli-majnoon/sh9/",
  },
  {
    authorFa: "فردریک داگلاس", authorEn: "Frederick Douglass",
    fa: "قدرت تا چیزی از آن مطالبه نشود، امتیازی نمی‌دهد.",
    en: "Power concedes nothing without a demand.",
    source: "https://home.nps.gov/frdo/learn/historyculture/thoughts-for-all-time.htm",
  },
  {
    authorFa: "سعدی", authorEn: "Saadi",
    fa: "تا مرد سخن نگفته باشد / عیب و هنرش نهفته باشد",
    en: "Until a person speaks, their flaws and gifts remain hidden.",
    source: "https://ganjoor.net/saadi/golestan/gbab1/sh3",
  },
  {
    authorFa: "ایمانوئل کانت", authorEn: "Immanuel Kant",
    fa: "دل آن را داشته باش که فهم خودت را به کار بگیری.",
    en: "Have courage to use your own understanding!",
    source: "https://warwick.ac.uk/fac/arts/english/currentstudents/undergraduates/modules/fulllist/second/en229/kant_what_is_enlightenment.pdf",
  },
  {
    authorFa: "حافظ", authorEn: "Hafez",
    fa: "آسایش دو گیتی تفسیر این دو حرف است / با دوستان مروت، با دشمنان مدارا",
    en: "Peace in both worlds comes from kindness to friends and forbearance with enemies.",
    source: "https://ganjoor.net/hafez/ghazal/sh5",
  },
  {
    authorFa: "ویلیام شکسپیر", authorEn: "William Shakespeare",
    fa: "تردیدهایمان به ما خیانت می‌کنند.",
    en: "Our doubts are traitors.",
    source: "https://www.folger.edu/explore/shakespeares-works/measure-for-measure/read/1/4/",
  },
  {
    authorFa: "مولانا", authorEn: "Rumi",
    fa: "آب کم جو، تشنگی آور به دست / تا بجوشد آب از بالا و پست",
    en: "Seek water less and cultivate thirst, so that water may spring up from high and low.",
    source: "https://ganjoor.net/moulavi/masnavi/daftar3/sh151/",
  },
  {
    authorFa: "امیلی دیکینسون", authorEn: "Emily Dickinson",
    fa: "امید، آن پرنده‌ای‌ست که در جان آشیان دارد.",
    en: "‘Hope’ is the thing with feathers that perches in the soul.",
    source: "https://rpo.library.utoronto.ca/content/hope-thing-feathers-254",
  },
  {
    authorFa: "حافظ", authorEn: "Hafez",
    fa: "سال‌ها دل طلب جام جم از ما می‌کرد / وآنچه خود داشت ز بیگانه تمنا می‌کرد",
    en: "For years my heart sought Jamshid’s cup, asking strangers for what it already held.",
    source: "https://ganjoor.net/hafez/ghazal/sh143/",
  },
  {
    authorFa: "سعدی، به نقل از لقمان", authorEn: "Luqman, as told by Saadi",
    fa: "ادب از که آموختی؟ گفت از بی‌ادبان.",
    en: "From whom did you learn good manners? From those who had none.",
    source: "https://ganjoor.net/saadi/golestan/gbab2/sh21",
  },
] as const;

export function homeQuoteForDate(date: Date) {
  // Use the device's calendar day without introducing DST-dependent indexing.
  const day = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86_400_000;
  return QUOTES[((day % QUOTES.length) + QUOTES.length) % QUOTES.length];
}
