"""Curated clinical study topics for the lessons taxonomy.

ATC is a *mechanism/chemical* classification (built for WHO drug-utilisation
statistics), not a *clinical* one — so pharmacologically related drugs often
land in different ATC L2 codes. The textbook example: beta blockers (C07),
thiazide diuretics (C03), ACE inhibitors/ARBs (C09) and calcium-channel
blockers (C08) are all first-line antihypertensives, but ATC's own
"Antihypertensives" code (C02) is actually a residual bucket for centrally-
acting agents and direct vasodilators — none of the mechanism-specific classes
live there. A learner browsing "Cardiovascular" sees eight unrelated-looking
L2 codes and has to already know which ones treat high blood pressure.

This module is a presentation-only overlay: it groups existing, unmodified
ATC L2 codes into topics that match how pharmacology is actually taught and
examined (by indication / organ system). It does not touch `apps.drugs` or
the ATC data at all — a "chapter" is still exactly one ATC L2 code with its
real ATC name and its own progress record; only the *grouping above it*
changes. An L2 code may legitimately appear under more than one topic (e.g.
beta blockers are first-line for hypertension, angina, arrhythmia AND heart
failure) — each appearance is the same chapter, just reachable from more than
one topic section.

Every populated L2 code in the bundled reference (`apps.drugs.data
.atc_reference.ATC_L2`) must appear at least once below —
`apps.lessons.tests.StudyTopicsCoverageTests` fails otherwise, so adding a new
ATC class to the reference without deciding where it belongs here is caught
immediately rather than silently dropping the class from the topic view.
(`apps.lessons.selectors.lesson_groups` also has a runtime fallback — grouping
by ATC L1 — for the same case, so production never hides a chapter either.)

Ordering matters: `lesson_groups()` treats the first topic listing a code as
that chapter's "primary" topic (used for `Chapter.group_code`/`group_name_*`).
List each topic's most iconic/common use first.

Fifty-two topics is still a lot to scan in one flat list, so each one also
carries a `category` — one of the 12 broad body-system/domain groups in
`CATEGORIES` below — purely for presentation (an accordion-of-accordions:
category -> topic -> chapter). `StudyTopicsCoverageTests` checks every
topic's `category` is a real key in `CATEGORIES`.
"""

# Broad presentation-only groups that cluster the topics above so a learner
# picks a body system first, then a topic, then a chapter, instead of
# scanning all 52 topics in one flat list.
CATEGORIES = [
    {"key": "cardio-blood", "name_fa": "قلب، عروق و خون", "name_en": "Cardiovascular & blood"},
    {"key": "endocrine-metabolic", "name_fa": "غدد و متابولیسم", "name_en": "Endocrine & metabolism"},
    {"key": "gi", "name_fa": "گوارش", "name_en": "Gastrointestinal"},
    {"key": "renal-gu", "name_fa": "کلیه و ادراری-تناسلی", "name_en": "Renal & genito-urinary"},
    {"key": "infection", "name_fa": "عفونت‌ها", "name_en": "Infectious disease"},
    {"key": "onco-immune", "name_fa": "سرطان و ایمنی", "name_en": "Oncology & immune"},
    {"key": "musculoskeletal", "name_fa": "اسکلتی-عضلانی", "name_en": "Musculoskeletal"},
    {"key": "neuro-psych", "name_fa": "اعصاب و روان", "name_en": "Neurology & psychiatry"},
    {"key": "respiratory", "name_fa": "تنفسی", "name_en": "Respiratory"},
    {"key": "dermatology", "name_fa": "پوست", "name_en": "Dermatology"},
    {"key": "sensory", "name_fa": "اندام‌های حسی", "name_en": "Sensory organs"},
    {"key": "misc", "name_fa": "متفرقه", "name_en": "Miscellaneous"},
]

STUDY_TOPICS = [
    # -- Cardiovascular & blood -----------------------------------------------
    {
        "key": "cv-htn",
        "category": "cardio-blood",
        "name_fa": "فشار خون بالا",
        "name_en": "Hypertension",
        "l2": ["C02", "C03", "C07", "C08", "C09"],
    },
    {
        "key": "cv-hf",
        "category": "cardio-blood",
        "name_fa": "نارسایی قلبی",
        "name_en": "Heart failure",
        "l2": ["C01", "C03", "C07", "C09"],
    },
    {
        "key": "cv-angina",
        "category": "cardio-blood",
        "name_fa": "آنژین و ایسکمی قلبی",
        "name_en": "Angina & ischaemic heart disease",
        "l2": ["C01", "C07", "C08"],
    },
    {
        "key": "cv-arrhythmia",
        "category": "cardio-blood",
        "name_fa": "آریتمی قلبی",
        "name_en": "Cardiac arrhythmia",
        "l2": ["C01", "C07"],
    },
    {
        "key": "cv-lipid",
        "category": "cardio-blood",
        "name_fa": "چربی خون",
        "name_en": "Dyslipidaemia",
        "l2": ["C10"],
    },
    {
        "key": "cv-peripheral",
        "category": "cardio-blood",
        "name_fa": "گردش خون محیطی و وریدی",
        "name_en": "Peripheral & venous circulation",
        "l2": ["C04", "C05"],
    },
    {
        "key": "heme-clot",
        "category": "cardio-blood",
        "name_fa": "انعقاد خون و ضدانعقادها",
        "name_en": "Coagulation & antithrombotics",
        "l2": ["B01", "B02"],
    },
    {
        "key": "heme-other",
        "category": "cardio-blood",
        "name_fa": "کم‌خونی و فرآورده‌های خونی",
        "name_en": "Anaemia & blood products",
        "l2": ["B03", "B05", "B06"],
    },
    # -- Endocrine & metabolism ------------------------------------------------
    {
        "key": "endo-diabetes",
        "category": "endocrine-metabolic",
        "name_fa": "دیابت",
        "name_en": "Diabetes",
        "l2": ["A10"],
    },
    {
        "key": "endo-thyroid",
        "category": "endocrine-metabolic",
        "name_fa": "تیروئید",
        "name_en": "Thyroid",
        "l2": ["H03"],
    },
    {
        "key": "endo-cortico",
        "category": "endocrine-metabolic",
        "name_fa": "کورتیکواستروئیدهای سیستمیک",
        "name_en": "Systemic corticosteroids",
        "l2": ["H02"],
    },
    {
        "key": "endo-pituitary",
        "category": "endocrine-metabolic",
        "name_fa": "هیپوفیز، هیپوتالاموس و پاراتیروئید",
        "name_en": "Pituitary, hypothalamus & parathyroid",
        "l2": ["H01", "H04", "H05"],
    },
    {
        "key": "endo-sex",
        "category": "endocrine-metabolic",
        "name_fa": "هورمون‌های جنسی و باروری",
        "name_en": "Sex hormones & fertility",
        "l2": ["G02", "G03"],
    },
    {
        "key": "endo-obesity",
        "category": "endocrine-metabolic",
        "name_fa": "چاقی و سایر متابولیک",
        "name_en": "Obesity & other metabolic",
        "l2": ["A08", "A09", "A16"],
    },
    {
        "key": "vitamins",
        "category": "endocrine-metabolic",
        "name_fa": "ویتامین‌ها و مکمل‌ها",
        "name_en": "Vitamins & supplements",
        "l2": ["A11", "A14"],
    },
    # -- Gastrointestinal --------------------------------------------------------
    {
        "key": "gi-upper",
        "category": "gi",
        "name_fa": "بیماری‌های اسید-پپتیک و گوارش فوقانی",
        "name_en": "Acid-peptic & upper GI disease",
        "l2": ["A02", "A03"],
    },
    {
        "key": "gi-nausea",
        "category": "gi",
        "name_fa": "تهوع و استفراغ",
        "name_en": "Nausea & vomiting",
        "l2": ["A04"],
    },
    {
        "key": "gi-liver",
        "category": "gi",
        "name_fa": "کبد و صفرا",
        "name_en": "Liver & biliary",
        "l2": ["A05"],
    },
    {
        "key": "gi-bowel",
        "category": "gi",
        "name_fa": "یبوست و اسهال",
        "name_en": "Constipation & diarrhoea",
        "l2": ["A06", "A07"],
    },
    {
        "key": "dental",
        "category": "gi",
        "name_fa": "دندان‌پزشکی",
        "name_en": "Dental",
        "l2": ["A01"],
    },
    # -- Renal / genito-urinary -----------------------------------------------
    {
        "key": "gu-tract",
        "category": "renal-gu",
        "name_fa": "دستگاه ادراری (پروستات و بی‌اختیاری)",
        "name_en": "Urinary tract (prostate & incontinence)",
        "l2": ["G04"],
    },
    {
        "key": "gu-infection",
        "category": "renal-gu",
        "name_fa": "عفونت‌های زنانه",
        "name_en": "Gynaecological infections",
        "l2": ["G01"],
    },
    # -- Infection --------------------------------------------------------------
    {
        "key": "infect-bacteria",
        "category": "infection",
        "name_fa": "آنتی‌بیوتیک‌های باکتریایی",
        "name_en": "Antibacterials",
        "l2": ["J01"],
    },
    {
        "key": "infect-fungus",
        "category": "infection",
        "name_fa": "ضدقارچ سیستمیک",
        "name_en": "Systemic antifungals",
        "l2": ["J02"],
    },
    {
        "key": "infect-tb",
        "category": "infection",
        "name_fa": "ضدسل",
        "name_en": "Antimycobacterials (TB)",
        "l2": ["J04"],
    },
    {
        "key": "infect-virus",
        "category": "infection",
        "name_fa": "ضدویروس",
        "name_en": "Antivirals",
        "l2": ["J05"],
    },
    {
        "key": "infect-immuno",
        "category": "infection",
        "name_fa": "ایمونوگلوبولین‌ها و سرم‌ها",
        "name_en": "Immunoglobulins & sera",
        "l2": ["J06"],
    },
    {
        "key": "parasite",
        "category": "infection",
        "name_fa": "ضدانگل، ضدکرم و ضدشپش",
        "name_en": "Antiparasitics & pediculicides",
        "l2": ["P01", "P02", "P03"],
    },
    # -- Oncology / immune --------------------------------------------------------
    {
        "key": "onco-chemo",
        "category": "onco-immune",
        "name_fa": "شیمی‌درمانی سرطان",
        "name_en": "Cancer chemotherapy",
        "l2": ["L01", "L02"],
    },
    {
        "key": "immune-mod",
        "category": "onco-immune",
        "name_fa": "تعدیل سیستم ایمنی",
        "name_en": "Immunomodulation",
        "l2": ["L03", "L04"],
    },
    # -- Musculoskeletal & pain -----------------------------------------------
    {
        "key": "msk-nsaid",
        "category": "musculoskeletal",
        "name_fa": "ضدالتهاب و مسکن اسکلتی-عضلانی",
        "name_en": "Musculoskeletal anti-inflammatories & analgesics",
        "l2": ["M01", "M02", "M09"],
    },
    {
        "key": "msk-relaxant",
        "category": "musculoskeletal",
        "name_fa": "شل‌کننده‌های عضلانی",
        "name_en": "Muscle relaxants",
        "l2": ["M03"],
    },
    {
        "key": "msk-gout",
        "category": "musculoskeletal",
        "name_fa": "نقرس",
        "name_en": "Gout",
        "l2": ["M04"],
    },
    {
        "key": "msk-bone",
        "category": "musculoskeletal",
        "name_fa": "پوکی استخوان و متابولیسم استخوان",
        "name_en": "Osteoporosis & bone metabolism",
        "l2": ["M05"],
    },
    # -- Nervous system / psychiatry --------------------------------------------
    {
        "key": "cns-anesthesia",
        "category": "neuro-psych",
        "name_fa": "بیهوشی",
        "name_en": "Anaesthesia",
        "l2": ["N01"],
    },
    {
        "key": "cns-pain",
        "category": "neuro-psych",
        "name_fa": "مسکن‌ها (اوپیوئیدی و غیراوپیوئیدی)",
        "name_en": "Analgesics (opioid & non-opioid)",
        "l2": ["N02"],
    },
    {
        "key": "cns-epilepsy",
        "category": "neuro-psych",
        "name_fa": "صرع",
        "name_en": "Epilepsy",
        "l2": ["N03"],
    },
    {
        "key": "cns-parkinson",
        "category": "neuro-psych",
        "name_fa": "پارکینسون",
        "name_en": "Parkinson's disease",
        "l2": ["N04"],
    },
    {
        "key": "cns-psychosis",
        "category": "neuro-psych",
        "name_fa": "روان‌پریشی، اضطراب و بی‌خوابی",
        "name_en": "Psychosis, anxiety & insomnia",
        "l2": ["N05"],
    },
    {
        "key": "cns-depression",
        "category": "neuro-psych",
        "name_fa": "افسردگی و سایر روان‌پزشکی",
        "name_en": "Depression & other psychiatric",
        "l2": ["N06"],
    },
    {
        "key": "cns-other",
        "category": "neuro-psych",
        "name_fa": "سایر اختلالات عصبی (وابستگی، سرگیجه، ...)",
        "name_en": "Other neurological (dependence, vertigo, …)",
        "l2": ["N07"],
    },
    # -- Respiratory -------------------------------------------------------------
    {
        "key": "resp-obstructive",
        "category": "respiratory",
        "name_fa": "آسم و COPD",
        "name_en": "Asthma & COPD",
        "l2": ["R03"],
    },
    {
        "key": "resp-allergy",
        "category": "respiratory",
        "name_fa": "آنتی‌هیستامین‌ها و آلرژی",
        "name_en": "Antihistamines & allergy",
        "l2": ["R06"],
    },
    {
        "key": "resp-coldcough",
        "category": "respiratory",
        "name_fa": "سرماخوردگی، سرفه و گلودرد",
        "name_en": "Cold, cough & sore throat",
        "l2": ["R01", "R02", "R05", "R07"],
    },
    # -- Dermatology -------------------------------------------------------------
    {
        "key": "derm-infection",
        "category": "dermatology",
        "name_fa": "ضدقارچ و ضدعفونی‌کننده‌های پوستی",
        "name_en": "Dermatological antifungals & antiseptics",
        "l2": ["D01", "D08", "D09"],
    },
    {
        "key": "derm-wound",
        "category": "dermatology",
        "name_fa": "امولیان‌ها و ترمیم زخم",
        "name_en": "Emollients & wound care",
        "l2": ["D02", "D03"],
    },
    {
        "key": "derm-cortico",
        "category": "dermatology",
        "name_fa": "کورتیکواستروئید موضعی و ضدخارش",
        "name_en": "Topical corticosteroids & antipruritics",
        "l2": ["D04", "D07"],
    },
    {
        "key": "derm-acne",
        "category": "dermatology",
        "name_fa": "آکنه و پسوریازیس",
        "name_en": "Acne & psoriasis",
        "l2": ["D05", "D10"],
    },
    {
        "key": "derm-other",
        "category": "dermatology",
        "name_fa": "سایر پوستی (مو و رنگدانه)",
        "name_en": "Other dermatological (hair & pigmentation)",
        "l2": ["D06", "D11"],
    },
    # -- Sensory organs ----------------------------------------------------------
    {
        "key": "sense-eye",
        "category": "sensory",
        "name_fa": "چشم",
        "name_en": "Eye",
        "l2": ["S01", "S03"],
    },
    {
        "key": "sense-ear",
        "category": "sensory",
        "name_fa": "گوش",
        "name_en": "Ear",
        "l2": ["S02"],
    },
    # -- Miscellaneous -----------------------------------------------------------
    {
        "key": "misc-other",
        "category": "misc",
        "name_fa": "پادزهر، تشخیصی و سایر",
        "name_en": "Antidotes, diagnostics & other",
        "l2": ["V03", "V04", "V06"],
    },
]
