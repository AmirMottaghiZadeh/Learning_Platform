// Credits follow the supplied list. The English text is translated for the app.
const QUOTES = [
  {
    authorFa: "وین دایر", authorEn: "Wayne Dyer",
    fa: "اگر معتقدید که نتیجه می گیرید، فرصت ها را خواهید دید. اگر باور ندارید که می توانید، موانع را خواهید دید.",
    en: "If you believe you can succeed, you will see opportunities. If you doubt that you can, you will see obstacles.",
  },
  {
    authorFa: "آلبرت اینشتین", authorEn: "Albert Einstein",
    fa: "سعی کنید مرد موفقی نشوید، بلکه مرد ارزشمندی شوید.",
    en: "Aim to become a person of value instead of chasing success.",
  },
  {
    authorFa: "آلی رایسمن", authorEn: "Aly Raisman",
    fa: "روزهای سخت شما را قوی تر می‌کند.",
    en: "Hard days build your strength.",
  },
  {
    authorFa: "تئودور روزولت", authorEn: "Theodore Roosevelt",
    fa: "افق دیدتان را به سمت ستاره‌ها نگه دارید اما روی زمین حرکت کنید.",
    en: "Set your sights on the stars while keeping your feet on the ground.",
  },
  {
    authorFa: "مهاتما گاندی", authorEn: "Mahatma Gandhi",
    fa: "با ملایمت، می‌توان جهان را تکان داد.",
    en: "Gentleness can shake the world.",
  },
  {
    authorFa: "کالین آر دیویس", authorEn: "Colin R. Davis",
    fa: "مسیر رسیدن به موفقیت هیچ تفاوتی با مسیر شکست نداره.",
    en: "Success and failure follow the same road.",
  },
  {
    authorFa: "جان دی. راکفلر", authorEn: "John D. Rockefeller",
    fa: "راز موفقیت در انجام دادن کارهای معمولی، به شکل غیر معمولیه.",
    en: "The secret to success is doing ordinary things in an extraordinary way.",
  },
  {
    authorFa: "ارسطو", authorEn: "Aristotle",
    fa: "امید رویای بیداری است.",
    en: "Hope is a dream we have while awake.",
  },
  {
    authorFa: "کریستیانو رونالدو", authorEn: "Cristiano Ronaldo",
    fa: "من به هیچ وجه نمی خوام در مورد رویاهام با شما حرف بزنم اما بدون شک اونا رو بهتون نشون خواهم داد.",
    en: "I have no wish to talk to you about my dreams, but I will certainly show them to you.",
  },
  {
    authorFa: "کیمیاگر (پائولو کوئلیو)", authorEn: "The Alchemist (Paulo Coelho)",
    fa: "این امکان رسیدن به یک رویا است که زندگی را جالب می کند.",
    en: "Life is interesting because a dream might come true.",
  },
  {
    authorFa: "دو برج (تالکین)", authorEn: "The Two Towers (Tolkien)",
    fa: "چیزهای خوبی در این دنیا وجود دارد و ارزش جنگیدن را دارد.",
    en: "There is still good in this world, and it is worth fighting for.",
  },
  {
    authorFa: "نامه‌ای به دخترم (مایا آنجلو)", authorEn: "Letter to My Daughter (Maya Angelou)",
    fa: "با اتفاقاتی که برای من می‌افتد می‌توانم تغییر کنم. اما من از کوچک شدن با آن جلوگیری می کنم.",
    en: "What happens to me can change me, but I can keep it from making me smaller.",
  },
  {
    authorFa: "کیمیاگر (پائولو کوئلیو)", authorEn: "The Alchemist (Paulo Coelho)",
    fa: "وقتی چیزی را می خواهید، همه جهان برای رسیدن به آن به شما کمک می کنند.",
    en: "When you want something, the whole world helps you reach it.",
  },
  {
    authorFa: "وصیتنامه امید: نوشته ها و گفتارهای ضروری (مارتین لوتر کینگ جونیور)",
    authorEn: "A Testament of Hope: The Essential Writings and Speeches (Martin Luther King Jr.)",
    fa: "تاریکی نمی تواند تاریکی را از بین ببرد: فقط نور می تواند این کار را انجام دهد. نفرت نمی تواند نفرت را از بین ببرد: فقط عشق می تواند این کار را انجام دهد.",
    en: "It takes light to dispel darkness and love to overcome hate. Darkness and hate cannot undo themselves.",
  },
  {
    authorFa: "نوری در قلب (روی تی بنت)", authorEn: "The Light in the Heart (Roy T. Bennett)",
    fa: "یاد بگیرید که در تاریک ترین لحظات زندگی کسی شمع روشن کنید. نوری باشید که به دیگران کمک می کند تا ببینند؛ این چیزی است که عمیق ترین اهمیت را به زندگی می بخشد.",
    en: "Learn to light a candle in someone’s darkest moments. Being a light that helps others see gives life its deepest meaning.",
  },
  {
    authorFa: "وودی آلن", authorEn: "Woody Allen",
    fa: "اگر تا به حال شکست نخورده اید، خوشحال نباشید چرا که نشانه این است که کارهای تان را خلاقانه انجام نمی‌دهید.",
    en: "If you have never failed, don’t celebrate yet. It may be a sign that you are not working creatively.",
  },
  {
    authorFa: "رابرت براونینگ", authorEn: "Robert Browning",
    fa: "موفقیت یک دقیقه‌ای حاصل سالها شکست است.",
    en: "One minute of success can come from years of failure.",
  },
  {
    authorFa: "اپرا وینفری", authorEn: "Oprah Winfrey",
    fa: "من شخصاً به شکست اعتقادی ندارم. اگر در زندگی تان از انجام کاری لذت بردین، مطمئن باشید که در آن کار شکست را تجربه نخواهید کرد.",
    en: "I personally don’t believe in failure. If you have enjoyed doing something in life, you can be sure it wasn’t a failure.",
  },
  {
    authorFa: "توماس ادیسون", authorEn: "Thomas Edison",
    fa: "اغلب شکست های زندگی برای کسانی اتفاق می افتد که هنگام تسلیم شدن نمی دانستند چقدر به موفقیت نزدیک شده اند.",
    en: "Many failures happen to people who give up without realizing how close they were to succeeding.",
  },
  {
    authorFa: "تونی رابینز", authorEn: "Tony Robbins",
    fa: "در زندگی تلاش کن وقتی چیزی را از دست می‌دهی، درسی را که از آن گرفته ای از دست ندهی.",
    en: "When you lose something in life, try to hold on to what it taught you.",
  },
  {
    authorFa: "زیگ زیگلار", authorEn: "Zig Ziglar",
    fa: "اگر سعی کنید که از شکست یاد بگیرید، به هیچ وجه شکست نخورده اید.",
    en: "If you try to learn from a failure, you haven’t really failed.",
  },
  {
    authorFa: "لو هولتز", authorEn: "Lou Holtz",
    fa: "این بار نیست که شما را خراب می کند، بلکه چگونگی حمل آن است.",
    en: "What wears you down is how you carry the load.",
  },
  {
    authorFa: "باراک اوباما", authorEn: "Barack Obama",
    fa: "شما نباید اجازه دهید شکست هایتان شما را تعریف کنند، بلکه باید بگذارید شکست هایتان به شما بیاموزند.",
    en: "Let your failures teach you and never let them define you.",
  },
  {
    authorFa: "کنفوسیوس", authorEn: "Confucius",
    fa: "تا وقتی که توقف نکنید اصلاً مهم نیست که چقدر آهسته پیش می روید.",
    en: "Your pace doesn’t matter as long as you keep going.",
  },
  {
    authorFa: "نرمن وان", authorEn: "Norman Vaughan",
    fa: "در خود رویای بزرگ و جرات شکست داشته باشید.",
    en: "Dream big and have the courage to fail.",
  },
  {
    authorFa: "بیورلی سیلز", authorEn: "Beverly Sills",
    fa: "احتمالاً در صورت شکست ناامید شوید، اما بدون شک اگر تلاش نکنید تا ابد محکوم به شکست هستید.",
    en: "Failure may disappoint you. If you never try, failure is certain.",
  },
  {
    authorFa: "جون وودن", authorEn: "John Wooden",
    fa: "شکست کشنده نیست، امّا تغییر نکردن احتمالاً کشنده باشد.",
    en: "Failure won’t necessarily end things, but refusing to change might.",
  },
  {
    authorFa: "هنری فورد", authorEn: "Henry Ford",
    fa: "شکست فرصتی است برای شروع دوباره؛ اما بدون شک این بار، هوشمندانه‌تر.",
    en: "Failure gives you a chance to begin again, wiser this time.",
  },
  {
    authorFa: "مولانا", authorEn: "Rumi",
    fa: "دیروز من باهوش بودم و می خواستم جهان را تغییر دهم. امروز من عاقل هستم، بنابراین خودم را تغییر می دهم.",
    en: "Yesterday I was clever and wanted to change the world. Today I am wise, so I am changing myself.",
  },
  {
    authorFa: "ناپلئون بناپارت", authorEn: "Napoleon Bonaparte",
    fa: "اگر نمی توانی برای مشکلت کاری انجام دهی، آن را رها کن. اسیر چیزهایی نباش که نمی توانی تغییر دهی.",
    en: "If there is nothing you can do about a problem, let it go. Don’t become a prisoner of things you cannot change.",
  },
  {
    authorFa: "لوئیس", authorEn: "Lewis",
    fa: "نمی توانی به عقب برگردی و آغاز چیزی را تغییر دهی، اما می‌توانی از جایی که هستی شروع کنی و پایان را تغییر دهی.",
    en: "You can’t go back and change the beginning, but you can start where you are and change the ending.",
  },
  {
    authorFa: "جیمین شاه", authorEn: "Jimin Shah",
    fa: "هیچ کس به جز خودتان مقصر وضعیت آینده شما نیست. اگر می خواهید موفق باشید، پس «موفق» شوید.",
    en: "You alone are responsible for where you end up. If you want to succeed, make it happen.",
  },
  {
    authorFa: "آلبرت اینشتین", authorEn: "Albert Einstein",
    fa: "یادمان باشد که جهانی که برای خود ساخته ایم، نتیجه تفکرات امروزمان است. بنابراین به هیچ عنوان نمیتوان دنیا را بدون تغییر طرز فکرمان تغییر دهیم.",
    en: "Remember that the world we have made reflects how we think. Changing the world requires changing the way we think.",
  },
  {
    authorFa: "جرج برنارد شاو", authorEn: "George Bernard Shaw",
    fa: "کسانی که نمی توانند نظر خود را تغییر دهند، نمی توانند چیزی را تغییر دهند.",
    en: "People who cannot change their minds cannot change anything.",
  },
  {
    authorFa: "بودا", authorEn: "Buddha",
    fa: "مشکل اینجاست که فکر میکنی زمان داری",
    en: "The trouble is that you think you have time.",
  },
] as const;

export function homeQuoteForDate(date: Date) {
  // Use the device's calendar day without introducing DST-dependent indexing.
  const day = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86_400_000;
  return QUOTES[((day % QUOTES.length) + QUOTES.length) % QUOTES.length];
}
