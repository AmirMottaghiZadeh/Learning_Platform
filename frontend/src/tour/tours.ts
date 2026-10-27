import type { PreviewSpec } from "./previews";

/**
 * The guided tours, one per section. A step rings the element registered as
 * its `target` (a TourTarget; none: the card stands alone, for something
 * not on screen yet) and shows a looping preview of what it does, a title
 * and one short line -- brief, but together covering everything the
 * section is for.
 */
export type TourKey =
  | "home"
  | "lessons"
  | "lessonList"
  | "flashcards"
  | "leitner"
  | "quiz"
  | "calculator"
  | "guidelines"
  | "diseases"
  | "uptodate"
  | "lexicomp";

export type TourStep = {
  target?: string;
  fa: [title: string, body: string];
  en: [title: string, body: string];
  preview: PreviewSpec;
};

const FA_EN = (fa: string, en: string) => ({ fa, en });

export const TOURS: Record<TourKey, TourStep[]> = {
  home: [
    {
      target: "home.uptodate",
      fa: ["مرجع بالینی", "نام دارو یا بیماری را بنویس؛ مقاله‌های UpToDate همان‌جا می‌آیند."],
      en: ["Clinical reference", "Type a drug or a disease; UpToDate's articles come right up."],
      preview: { kind: "search", term: "warfarin", rows: ["Warfarin: Drug information", "Warfarin: Patient education", "Anticoagulation in AF"] },
    },
    {
      target: "home.lexicomp",
      fa: ["تداخل دارویی", "چند دارو را کنار هم بگذار تا تداخل‌ها با شدتشان بیایند."],
      en: ["Drug interactions", "Put a few drugs together to see their interactions and how serious they are."],
      preview: { kind: "interaction", a: "warfarin", b: "amiodarone", severity: FA_EN("شدید", "Major") },
    },
    {
      target: "home.paths",
      fa: ["درهای ورود", "آموزش، گایدلاین، بیماری‌ها و ماشین‌حساب، هر کدام یک لمس."],
      en: ["Ways in", "Education, guidelines, diseases and calculators, one tap each."],
      preview: {
        kind: "tap",
        tiles: [FA_EN("آموزش", "Education"), FA_EN("گایدلاین", "Guidelines"), FA_EN("بیماری‌ها", "Diseases"), FA_EN("ماشین‌حساب", "Calculators")],
        result: FA_EN("آموزش", "Education"),
      },
    },
    {
      target: "home.plan",
      fa: ["برنامهٔ مطالعه", "کارهای امروز و این هفته. دایره را بزن تا کار انجام‌شده شود؛ «ویرایش برنامه» همه را عوض می‌کند."],
      en: ["Study plan", "Today's tasks and this week. Tap a circle to tick a task off; “Edit plan” changes it all."],
      preview: { kind: "check", title: FA_EN("درسنامه: ضدفشارخون‌ها", "Lesson: Antihypertensives"), sub: FA_EN("۱۰ دقیقه", "10 min") },
    },
    {
      target: "nav",
      fa: ["بخش‌های اصلی", "درسنامه، فلش‌کارت، آزمون و پروفایل همیشه این پایین است."],
      en: ["The main sections", "Lessons, flashcards, quizzes and your profile are always down here."],
      preview: { kind: "nav" },
    },
  ],

  lessons: [
    {
      target: "lessons.search",
      fa: ["جست‌وجوی دارو", "نام فارسی یا انگلیسی دارو را بنویس تا درسش باز شود."],
      en: ["Find a drug", "Type a drug's name, in Persian or English, to open its lesson."],
      preview: { kind: "search", term: "metformin", rows: ["metformin", "metformin + sitagliptin", "metformin + glipizide"] },
    },
    {
      target: "lessons.category",
      fa: ["دسته، موضوع، زیرگروه", "دسته را باز کن، موضوع را انتخاب کن تا زیرگروه‌ها و داروهایش بیایند."],
      en: ["Category, topic, chapter", "Open a category, pick a topic, and its chapters and drugs follow."],
      preview: {
        kind: "list",
        rows: [FA_EN("قلب، عروق و خون", "Cardiovascular & blood"), FA_EN("فشار خون بالا", "Hypertension"), FA_EN("ضدفشارخون‌ها", "Antihypertensives")],
        highlight: 2,
      },
    },
    {
      target: "lessons.category",
      fa: ["پیشرفت", "عدد هر دسته یعنی چند دارو از کل را خوانده‌ای."],
      en: ["Progress", "Each category's count is how many of its drugs you have read."],
      preview: { kind: "check", title: FA_EN("قلب، عروق و خون", "Cardiovascular & blood"), sub: FA_EN("۱۰ از ۴۲۱ دارو", "10 of 421 drugs") },
    },
  ],

  lessonList: [
    {
      target: "lessonList.band",
      fa: ["گروه دارویی", "هر نوار سبز یک گروه است، با کد ATC و تعداد داروهایش."],
      en: ["Drug class", "Each green band is one class, with its ATC code and how many drugs it has."],
      preview: { kind: "bands", band: FA_EN("C02AC · آگونیست‌های ایمیدازولین", "C02AC · Imidazoline agonists"), rows: ["clonidine", "guanfacine"] },
    },
    {
      target: "lessonList.drug",
      fa: ["درس هر دارو", "روی دارو بزن تا درسش باز شود؛ دارویی که خواندی تیک می‌خورد."],
      en: ["A drug's lesson", "Tap a drug to open its lesson; the ones you have read get a tick."],
      preview: { kind: "check", title: "clonidine", sub: "Central alpha-2 agonist" },
    },
  ],

  flashcards: [
    {
      target: "flash.stats",
      fa: ["پیشرفت تو", "زیردسته‌های تمام‌شده و کارت‌هایی که مرور کرده‌ای."],
      en: ["Your progress", "Topics you have finished and cards you have reviewed."],
      preview: { kind: "check", title: FA_EN("فشار خون بالا", "Hypertension"), sub: FA_EN("۴۲ از ۱۵۴ کارت", "42 of 154 cards") },
    },
    {
      target: "flash.categories",
      fa: ["دسته‌ها", "دسته را باز کن، زیردسته را بزن و کارت‌ها را یکی‌یکی ببین."],
      en: ["Categories", "Open a category, pick a topic and go through its cards one by one."],
      preview: {
        kind: "tap",
        tiles: [FA_EN("قلب و عروق", "Cardio"), FA_EN("غدد", "Endocrine"), FA_EN("گوارش", "GI"), FA_EN("عفونت‌ها", "Infection")],
        result: FA_EN("فشار خون بالا", "Hypertension"),
      },
    },
    {
      fa: ["هر کارت", "روی کارت بزن تا جواب را ببینی. «یادم نبود» کارت را به جعبهٔ لایتنر می‌برد."],
      en: ["Each card", "Tap the card to see the answer. “I didn't know” sends it to the Leitner box."],
      preview: {
        kind: "flip",
        front: "amlodipine",
        chip: FA_EN("عوارض شایع", "Common side effects"),
        back: [FA_EN("ادم", "Edema"), FA_EN("برافروختگی", "Flushing"), FA_EN("سردرد، سرگیجه", "Headache, dizziness")],
      },
    },
    {
      target: "flash.leitner",
      fa: ["جعبهٔ لایتنر", "کارت‌هایی که بلد نبودی اینجا جمع می‌شوند تا مرورشان کنی."],
      en: ["Leitner box", "The cards you didn't know gather here for review."],
      preview: { kind: "drawers" },
    },
  ],

  leitner: [
    {
      target: "leitner.drawers",
      fa: ["پنج کشو", "شمارهٔ کشو یعنی چند بار اشتباه شده. هر کشو را بزن تا کارت‌هایش را مرور کنی."],
      en: ["Five drawers", "A drawer's number is how often its cards were missed. Tap one to review it."],
      preview: { kind: "drawers" },
    },
    {
      target: "leitner.today",
      fa: ["مرور امروز", "کارت‌های امروز، از کشوی بالاتر، به اندازهٔ وقت روزانه‌ات."],
      en: ["Today's review", "Today's cards, highest drawer first, as many as your daily time allows."],
      preview: { kind: "list", rows: [FA_EN("آملودیپین، عوارض شایع", "amlodipine, side effects"), FA_EN("وارفارین، تداخلات", "warfarin, interactions"), FA_EN("آتورواستاتین، مکانیسم", "atorvastatin, mechanism")] },
    },
    {
      fa: ["دو جواب", "«یادم نبود» کارت را یک کشو بالا می‌برد؛ «یادم بود» یک کشو پایین و از کشوی ۱ بیرون."],
      en: ["Two answers", "“I didn't know” moves a card up a drawer; “I knew it” moves it down, and out from drawer 1."],
      preview: { kind: "drawers" },
    },
  ],

  quiz: [
    {
      target: "quiz.stats",
      fa: ["کارنامه", "میانگین نمره، تعداد آزمون‌ها و موضوع‌هایی که ضعیف‌تری."],
      en: ["Your record", "Average score, quizzes taken and the topics you are weakest in."],
      preview: { kind: "check", title: FA_EN("میانگین نمره", "Average score"), sub: FA_EN("۷۸٪", "78%") },
    },
    {
      target: "quiz.search",
      fa: ["پیدا کردن موضوع", "موضوع آزمون را جست‌وجو کن."],
      en: ["Find a topic", "Search for the topic to be quizzed on."],
      preview: { kind: "search", term: FA_EN("فشار خون", "hypertension"), rows: [FA_EN("فشار خون بالا", "Hypertension"), FA_EN("نارسایی قلبی", "Heart failure")] },
    },
    {
      target: "quiz.topics",
      fa: ["انتخاب و شروع", "موضوع را بزن، فصل و تعداد سؤال را انتخاب کن و شروع کن. درصد، تسلط توست."],
      en: ["Pick and start", "Tap a topic, choose a chapter and how many questions, and start. The percentage is your mastery."],
      preview: { kind: "list", rows: [FA_EN("فشار خون بالا · ۶۲٪", "Hypertension · 62%"), FA_EN("همهٔ فصل‌ها", "All chapters"), FA_EN("۱۰ سؤال", "10 questions")], highlight: 0 },
    },
    {
      fa: ["جواب دادن", "جواب درست سبز و غلط قرمز می‌شود؛ فلش‌کارت نکتهٔ غلط به جعبهٔ لایتنر می‌رود."],
      en: ["Answering", "Right turns green, wrong turns red; a wrong answer's flashcard goes to the Leitner box."],
      preview: { kind: "choice", options: [FA_EN("ریفامپین", "Rifampin"), FA_EN("آمیودارون", "Amiodarone"), FA_EN("ویتامین K", "Vitamin K")], wrong: 0, correct: 1 },
    },
  ],

  calculator: [
    {
      target: "calc.search",
      fa: ["جست‌وجو", "نام امتیاز یا فرمول را بنویس؛ مثلاً CHA2DS2-VASc."],
      en: ["Search", "Type a score's or formula's name, such as CHA2DS2-VASc."],
      preview: { kind: "search", term: "CHA2DS2", rows: ["CHA2DS2-VASc Score", "HAS-BLED Score", "Wells Score for PE"] },
    },
    {
      target: "calc.domains",
      fa: ["حوزه‌ها", "ماشین‌حساب‌ها بر اساس تخصص دسته‌بندی شده‌اند."],
      en: ["Specialties", "The calculators are grouped by specialty."],
      preview: {
        kind: "tap",
        tiles: [FA_EN("قلب", "Cardiology"), FA_EN("کلیه", "Nephrology"), FA_EN("اورژانس", "Emergency"), FA_EN("ریه", "Pulmonary")],
        result: FA_EN("قلب", "Cardiology"),
      },
    },
    {
      fa: ["محاسبه", "به سؤال‌ها جواب بده؛ امتیاز همراهت به‌روز می‌شود و تفسیرش زیرش می‌آید."],
      en: ["Calculating", "Answer the questions; the score updates as you go, with what it means below."],
      preview: { kind: "score", options: [FA_EN("سن ≥ ۷۵ سال", "Age ≥ 75"), FA_EN("فشار خون بالا", "Hypertension"), FA_EN("دیابت", "Diabetes")] },
    },
  ],

  guidelines: [
    {
      target: "guide.specialties",
      fa: ["تخصص", "بین تخصص‌ها جابه‌جا شو؛ گایدلاین‌های هر کدام جداست."],
      en: ["Specialty", "Switch between specialties; each has its own guidelines."],
      preview: { kind: "nav", items: ["Guidelines", "Expert Insights", "Primary Care Hacks"] },
    },
    {
      target: "guide.search",
      fa: ["جست‌وجو", "در گایدلاین‌های همین تخصص جست‌وجو کن."],
      en: ["Search", "Search this specialty's guidelines."],
      preview: { kind: "search", term: "sepsis", rows: ["Sepsis Guidelines", "Septic Shock Management"] },
    },
    {
      target: "guide.list",
      fa: ["همهٔ گایدلاین‌ها", "فهرست الفبایی؛ روی هر گایدلاین بزن تا باز شود."],
      en: ["Every guideline", "An A–Z list; tap one to open it."],
      preview: { kind: "list", rows: ["A — Asthma", "D — Diabetes", "H — Hypertension"], highlight: 2 },
    },
    {
      fa: ["عکس و جدول", "در مقاله، روی عکس یا جدول بزن تا بزرگ و واضح شود."],
      en: ["Images and tables", "In an article, tap an image or table to see it full size."],
      preview: { kind: "zoom" },
    },
  ],

  diseases: [
    {
      target: "dis.search",
      fa: ["جست‌وجوی بیماری", "نام بیماری را بنویس."],
      en: ["Find a disease", "Type a disease's name."],
      preview: { kind: "search", term: "pneumonia", rows: ["Community-Acquired Pneumonia", "Aspiration Pneumonia"] },
    },
    {
      target: "dis.specialties",
      fa: ["تخصص‌ها", "بیماری‌ها بر اساس تخصص؛ یکی را باز کن."],
      en: ["Specialties", "Diseases by specialty; open one."],
      preview: {
        kind: "tap",
        tiles: [FA_EN("قلب", "Cardiology"), FA_EN("عفونی", "Infectious"), FA_EN("گوارش", "GI"), FA_EN("اعصاب", "Neurology")],
        result: FA_EN("عفونی", "Infectious"),
      },
    },
    {
      fa: ["خواندن مقاله", "فهرست مطالب برای پرش بین بخش‌ها؛ عکس و جدول با لمس بزرگ می‌شوند."],
      en: ["Reading", "The outline jumps between sections; images and tables open full size on a tap."],
      preview: { kind: "zoom" },
    },
  ],

  uptodate: [
    {
      target: "utd.search",
      fa: ["جست‌وجو در UpToDate", "عنوان مقاله را بنویس؛ اگر کلمه را اشتباه بنویسی، نزدیک‌ترینش جست‌وجو می‌شود."],
      en: ["Search UpToDate", "Type an article's title; a misspelt word is searched as the closest one."],
      preview: { kind: "search", term: "pnemonia", rows: ["Pneumonia in adults", "Pneumonia: Treatment", "Aspiration pneumonia"] },
    },
    {
      target: "utd.offline",
      fa: ["آفلاین", "بستهٔ UpToDate را دانلود کن تا بدون اینترنت هم بخوانی."],
      en: ["Offline", "Download the UpToDate package to read without internet."],
      preview: { kind: "offline" },
    },
    {
      fa: ["خواندن مقاله", "اول فهرست مطالب، بعد هر بخش؛ عکس‌ها با لمس بزرگ می‌شوند."],
      en: ["Reading", "First the outline, then any section; images open full size on a tap."],
      preview: { kind: "zoom" },
    },
  ],

  lexicomp: [
    {
      target: "lexi.search",
      fa: ["افزودن دارو", "نام دارو را بنویس و از نتیجه‌ها اضافه‌اش کن."],
      en: ["Add drugs", "Type a drug's name and add it from the results."],
      preview: { kind: "search", term: "warfarin", rows: ["warfarin", "Coumadin (warfarin)"] },
    },
    {
      fa: ["بررسی تداخل", "با دو دارو یا بیشتر «بررسی تداخل» را بزن؛ تداخل‌ها با شدت و راه مدیریتشان می‌آیند."],
      en: ["Check interactions", "With two drugs or more, tap “Check”; each interaction comes with its severity and management."],
      preview: { kind: "interaction", a: "warfarin", b: "amiodarone", severity: FA_EN("شدید", "Major") },
    },
    {
      target: "lexi.offline",
      fa: ["آفلاین", "بستهٔ LexiComp را دانلود کن تا بدون اینترنت هم بررسی کنی."],
      en: ["Offline", "Download the LexiComp package to check without internet."],
      preview: { kind: "offline" },
    },
  ],
};
