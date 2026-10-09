# Pharmexa — custom icon prompts

Every section, entry point and lesson topic in the app, each with an image-generation prompt.
All icons share one visual style (the **style block** below) so the set looks like a single family.

## How to use

1. Paste the **style block** first, then add `Subject:` and that icon's line from the tables.
   Example: `<style block> Subject: an open textbook with two short text lines on each page and a small green leaf bookmark.`
2. Generate at 1024×1024, then export a **512×512 transparent PNG** (no background tile, because the app draws the tile itself).
3. File name = the `file` column, saved in `frontend/assets/icons/`.
4. Test each icon at **24px** (nav bar) and **48px** (tiles) on both the cream background `#F7F5EF` and the dark background `#171F1D`. If it can't be recognised at 24px, simplify it.

> Don't generate the **UpToDate** or **LexiComp** logos. Those are trademarks, so the app keeps using their real logos.

---

## Style block (paste before every subject)

```
Flat 2D vector icon, minimal and modern, for a pharmacy-education mobile app.
Centered single object on a fully transparent background, no tile, no frame, no text, no letters.
Simple geometric shapes with softly rounded corners, uniform 2px-equivalent rounded strokes only where needed for detail, no outlines around the whole object.
No gradients, no 3D, no shadows, no glow, no texture, no photorealism. Solid flat fills only.
Strict palette:
- primary deep teal #0F5C52
- secondary teal #14746A
- light mint #9DD4B8
- cream #F7F5EF (for highlights / paper surfaces)
- one small accent only when it helps meaning: coral #E07A5F, warm amber #E0B04F, or soft lavender #A48BD0
Dominant colour is teal; accents cover less than 15% of the icon.
Must stay recognisable at 24×24 px and read well on both a cream (#F7F5EF) and a near-black (#171F1D) background, so use mid-tone fills and avoid very dark or near-white shapes as the main silhouette.
Consistent visual weight, about 10% padding on all sides, 1:1 square canvas, friendly and clean, Material/iOS SF-symbol level of simplicity.
```

**Navigation variant** (for the 5 bottom-bar icons only): add this to the end of the style block:

```
Even simpler: maximum 3 shapes, bold silhouette, a single teal tone plus mint, designed to sit inside a 56px pill at 24px size.
```

---

## 1. Bottom navigation (5 tabs)

| Section | فارسی | file | Subject |
|---|---|---|---|
| Home | خانه | `nav-home.png` | a rounded house with a small medical cross on the door |
| Lessons | درسنامه | `nav-lessons.png` | an open book seen from the front, two pages, a mint bookmark ribbon |
| Flashcards | فلش‌کارت | `nav-flashcards.png` | two stacked cards slightly fanned, the front card showing a small capsule |
| Quiz | آزمون | `nav-quiz.png` | a clipboard with three check-box rows, the top one ticked |
| Profile | پروفایل | `nav-profile.png` | a simple person bust in a circle |

## 2. Dashboard: entry points (درِ ورودی مسیرها)

| Section | فارسی | file | Subject |
|---|---|---|---|
| Education | آموزش | `entry-education.png` | a graduation cap resting on a closed book |
| Clinical guidelines | راهنماهای بالینی | `entry-guidelines.png` | a document with a decision-flowchart (three connected boxes) and a small check-mark seal |
| Diseases & conditions | بیماری‌ها و شرایط | `entry-diseases.png` | a magnifying glass over a simple stethoscope |
| Clinical calculator | ماشین‌حساب بالینی | `entry-calculator.png` | a rounded calculator with a small semicircle gauge on its screen |
| Next chapter card | فصل بعدی | `entry-next-chapter.png` | an open book with a forward arrow coming out of its right page |
| Study plan card | برنامهٔ امروز | `entry-today-plan.png` | a calendar page with a small clock in the corner |

## 3. Education hub (inside آموزش)

| Section | فارسی | file | Subject |
|---|---|---|---|
| Lessons | درسنامه | `edu-lessons.png` | an open textbook with two short text lines on each page and a small green leaf bookmark |
| Quiz | آزمون | `edu-quiz.png` | a question-mark speech bubble next to a ticked check box |
| Flashcards | فلش‌کارت | `edu-flashcards.png` | a card flipping over, front teal, back cream, with a curved rotate arrow |
| Statistics | آمار | `edu-stats.png` | three rising bar columns with a small upward trend line |
| Mistakes | اشتباهات | `edu-mistakes.png` | a notebook page with a coral cross mark and a small circular "redo" arrow |
| Profile | پروفایل | `edu-profile.png` | a person bust with a small graduation cap |

## 4. Profile menu and stats

| Section | فارسی | file | Subject |
|---|---|---|---|
| Full statistics | تحلیل کامل آمار | `profile-full-stats.png` | a donut chart beside a small bar chart |
| Study planning | برنامه‌ریزی مطالعه | `profile-planning.png` | a calendar with a target/bullseye on one day |
| Notifications | اعلان‌ها | `profile-notifications.png` | a bell with a small amber dot |
| Mistakes | اشتباهات | `profile-mistakes.png` | same as `edu-mistakes.png` (reuse) |
| Log out | خروج از حساب | `profile-logout.png` | a door half open with an arrow pointing out |
| Streak | روزهای پیاپی | `stat-streak.png` | a flame with an amber core |
| XP | امتیاز | `stat-xp.png` | a star badge with a small ribbon |
| Accuracy | دقت | `stat-accuracy.png` | a target with an arrow in the centre |
| Quizzes taken | آزمون‌ها | `stat-quizzes.png` | a small stack of ticked papers |
| Mastery | تسلط | `stat-mastery.png` | a medal with a capsule shape on it |

## 5. Lesson categories (12 body systems)

| Section | فارسی | file | Subject |
|---|---|---|---|
| Cardiovascular & blood | قلب، عروق و خون | `cat-cardio-blood.png` | a stylised heart with a single heartbeat line and a coral blood drop |
| Endocrine & metabolism | غدد و متابولیسم | `cat-endocrine-metabolic.png` | a butterfly-shaped thyroid gland with a small hormone hexagon |
| Gastrointestinal | گوارش | `cat-gi.png` | a stylised stomach with a short intestine curve |
| Renal & genito-urinary | کلیه و ادراری-تناسلی | `cat-renal-gu.png` | a pair of kidneys with a small drop below |
| Infectious disease | عفونت‌ها | `cat-infection.png` | a round microbe with short spikes |
| Oncology & immune | سرطان و ایمنی | `cat-onco-immune.png` | a shield with a cell inside it |
| Musculoskeletal | اسکلتی-عضلانی | `cat-musculoskeletal.png` | a bone crossed with a small flexed-arm muscle |
| Neurology & psychiatry | اعصاب و روان | `cat-neuro-psych.png` | a brain in side profile |
| Respiratory | تنفسی | `cat-respiratory.png` | a pair of lungs with a bronchial tree |
| Dermatology | پوست | `cat-dermatology.png` | a rounded square skin cross-section with three layers and a hair |
| Sensory organs | اندام‌های حسی | `cat-sensory.png` | an eye and an ear side by side |
| Miscellaneous | متفرقه | `cat-misc.png` | a medicine box with a few mixed pills in front of it |

## 6. Lesson study topics (52)

Each topic icon = its organ/subject **plus one small drug element** (pill, capsule, vial, inhaler…), so they read as pharmacology lessons rather than anatomy.

### Cardiovascular & blood
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Hypertension | فشار خون بالا | `topic-cv-htn.png` | a blood-pressure cuff gauge with the needle in the high zone |
| Heart failure | نارسایی قلبی | `topic-cv-hf.png` | a heart with a low battery indicator |
| Angina & ischaemic heart disease | آنژین و ایسکمی قلبی | `topic-cv-angina.png` | a heart with a narrowed artery on top and a small coral spot |
| Cardiac arrhythmia | آریتمی قلبی | `topic-cv-arrhythmia.png` | an irregular zig-zag ECG line across a heart outline |
| Dyslipidaemia | چربی خون | `topic-cv-lipid.png` | a blood vessel cross-section with an amber fat deposit on its wall |
| Peripheral & venous circulation | گردش خون محیطی و وریدی | `topic-cv-peripheral.png` | a leg silhouette with a branching vein line |
| Coagulation & antithrombotics | انعقاد خون و ضدانعقادها | `topic-heme-clot.png` | a blood drop with a small clot cluster and a pill beside it |
| Anaemia & blood products | کم‌خونی و فرآورده‌های خونی | `topic-heme-other.png` | a blood bag with round red cells |

### Endocrine & metabolism
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Diabetes | دیابت | `topic-endo-diabetes.png` | a glucose meter with a blood drop and an insulin pen |
| Thyroid | تیروئید | `topic-endo-thyroid.png` | a butterfly-shaped thyroid gland with a small pill |
| Systemic corticosteroids | کورتیکواستروئیدهای سیستمیک | `topic-endo-cortico.png` | an adrenal gland cap on a kidney with a small tablet |
| Pituitary, hypothalamus & parathyroid | هیپوفیز، هیپوتالاموس و پاراتیروئید | `topic-endo-pituitary.png` | a brain outline with a small highlighted gland at its base |
| Sex hormones & fertility | هورمون‌های جنسی و باروری | `topic-endo-sex.png` | a circular pill-pack dial with male and female symbols |
| Obesity & other metabolic | چاقی و سایر متابولیک | `topic-endo-obesity.png` | a bathroom scale with a measuring tape |
| Vitamins & supplements | ویتامین‌ها و مکمل‌ها | `topic-vitamins.png` | a supplement bottle with a citrus slice and a soft-gel capsule |

### Gastrointestinal
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Acid-peptic & upper GI disease | بیماری‌های اسید-پپتیک و گوارش فوقانی | `topic-gi-upper.png` | a stomach with small flame-like acid bubbles and an antacid tablet |
| Nausea & vomiting | تهوع و استفراغ | `topic-gi-nausea.png` | a queasy face with a swirl above it |
| Liver & biliary | کبد و صفرا | `topic-gi-liver.png` | a liver with a small gallbladder |
| Constipation & diarrhoea | یبوست و اسهال | `topic-gi-bowel.png` | an intestine loop with up and down arrows |
| Dental | دندان‌پزشکی | `topic-dental.png` | a tooth with a small sparkle |

### Renal & genito-urinary
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Urinary tract (prostate & incontinence) | دستگاه ادراری (پروستات و بی‌اختیاری) | `topic-gu-tract.png` | a bladder with a drop and a small capsule |
| Gynaecological infections | عفونت‌های زنانه | `topic-gu-infection.png` | a female symbol with a small microbe |

### Infectious disease
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Antibacterials | آنتی‌بیوتیک‌های باکتریایی | `topic-infect-bacteria.png` | a rod-shaped bacterium next to a two-tone capsule |
| Systemic antifungals | ضدقارچ سیستمیک | `topic-infect-fungus.png` | a mushroom-shaped fungal spore with a tablet |
| Antimycobacterials (TB) | ضدسل | `topic-infect-tb.png` | lungs with small dots and a capsule |
| Antivirals | ضدویروس | `topic-infect-virus.png` | a spiky round virus with a shield |
| Immunoglobulins & sera | ایمونوگلوبولین‌ها و سرم‌ها | `topic-infect-immuno.png` | a Y-shaped antibody beside a small vial |
| Antiparasitics & pediculicides | ضدانگل، ضدکرم و ضدشپش | `topic-parasite.png` | a simple worm shape beside a small tablet |

### Oncology & immune
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Cancer chemotherapy | شیمی‌درمانی سرطان | `topic-onco-chemo.png` | an IV drip bag with a cell symbol on it |
| Immunomodulation | تعدیل سیستم ایمنی | `topic-immune-mod.png` | a shield with a slider control |

### Musculoskeletal
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Anti-inflammatories & analgesics | ضدالتهاب و مسکن اسکلتی-عضلانی | `topic-msk-nsaid.png` | a knee joint with small coral pain lines and a round tablet |
| Muscle relaxants | شل‌کننده‌های عضلانی | `topic-msk-relaxant.png` | a muscle shape with a gentle wave line |
| Gout | نقرس | `topic-msk-gout.png` | a big-toe joint with amber crystals |
| Osteoporosis & bone metabolism | پوکی استخوان و متابولیسم استخوان | `topic-msk-bone.png` | a bone with a porous dotted inner texture |

### Neurology & psychiatry
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Anaesthesia | بیهوشی | `topic-cns-anesthesia.png` | an anaesthesia mask with a small "z" |
| Analgesics (opioid & non-opioid) | مسکن‌ها (اوپیوئیدی و غیراوپیوئیدی) | `topic-cns-pain.png` | a lightning-bolt pain symbol crossed out by a capsule |
| Epilepsy | صرع | `topic-cns-epilepsy.png` | a brain with a small lightning bolt inside |
| Parkinson's disease | پارکینسون | `topic-cns-parkinson.png` | an open hand with small tremor lines |
| Psychosis, anxiety & insomnia | روان‌پریشی، اضطراب و بی‌خوابی | `topic-cns-psychosis.png` | a head profile with a crescent moon inside |
| Depression & other psychiatric | افسردگی و سایر روان‌پزشکی | `topic-cns-depression.png` | a head profile with a small rain cloud turning into a sun |
| Other neurological (dependence, vertigo…) | سایر اختلالات عصبی | `topic-cns-other.png` | a head with a spiral (vertigo) above it |

### Respiratory
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Asthma & COPD | آسم و COPD | `topic-resp-obstructive.png` | a metered-dose inhaler beside lungs |
| Antihistamines & allergy | آنتی‌هیستامین‌ها و آلرژی | `topic-resp-allergy.png` | a pollen flower with a tablet |
| Cold, cough & sore throat | سرماخوردگی، سرفه و گلودرد | `topic-resp-coldcough.png` | a cough-syrup bottle with a measuring spoon |

### Dermatology
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Antifungals & antiseptics | ضدقارچ و ضدعفونی‌کننده‌های پوستی | `topic-derm-infection.png` | a dropper bottle above a skin patch |
| Emollients & wound care | امولیان‌ها و ترمیم زخم | `topic-derm-wound.png` | an adhesive bandage beside a cream tube |
| Topical corticosteroids & antipruritics | کورتیکواستروئید موضعی و ضدخارش | `topic-derm-cortico.png` | an ointment tube with small soothing wave lines |
| Acne & psoriasis | آکنه و پسوریازیس | `topic-derm-acne.png` | a face outline with a few dots and a small cream jar |
| Other dermatological (hair & pigmentation) | سایر پوستی (مو و رنگدانه) | `topic-derm-other.png` | a hair strand and a pigment colour swatch |

### Sensory organs
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Eye | چشم | `topic-sense-eye.png` | an eye with an eye-drop bottle above it |
| Ear | گوش | `topic-sense-ear.png` | an ear with a dropper |

### Miscellaneous
| Topic | فارسی | file | Subject |
|---|---|---|---|
| Antidotes, diagnostics & other | پادزهر، تشخیصی و سایر | `topic-misc-other.png` | a first-aid kit with a small test tube |

## 7. Calculator specialties (30)

You can reuse these for the specialty grid in **Diseases & Conditions** as well.

| Specialty | فارسی | file | Subject |
|---|---|---|---|
| Cardiology | قلب و عروق | `spec-cardiology.png` | a heart with a heartbeat line |
| COVID-19 | COVID-19 | `spec-covid.png` | a spiky coronavirus particle |
| Critical Care | مراقبت‌های ویژه | `spec-critical-care.png` | a bedside monitor showing a pulse line |
| Emergency | اورژانس | `spec-emergency.png` | a siren light with a medical cross |
| Endocrinology | غدد درون‌ریز | `spec-endocrinology.png` | a thyroid gland |
| Gastroenterology | گوارش | `spec-gastro.png` | a stomach and intestine |
| General Calculators | محاسبه‌گرهای عمومی | `spec-general.png` | a calculator with a plus sign |
| Geriatrics | سالمندی | `spec-geriatrics.png` | a walking cane beside a heart |
| Hematology | خون‌شناسی | `spec-hematology.png` | a blood drop with round cells |
| Infectious Disease | بیماری‌های عفونی | `spec-infectious.png` | a round microbe |
| Medical Administration | مدیریت پزشکی | `spec-admin.png` | a clipboard with a medical cross |
| Medical Imaging | تصویربرداری پزشکی | `spec-imaging.png` | an X-ray film showing ribs |
| Mental Health | سلامت روان | `spec-mental-health.png` | a head profile with a small heart |
| Nephrology | نفرولوژی | `spec-nephrology.png` | a kidney |
| Neurology / Neurosurgery | مغز و اعصاب / جراحی مغز و اعصاب | `spec-neurology.png` | a brain |
| Obstetrics & Gynecology | زنان و زایمان | `spec-obgyn.png` | a pregnant-belly silhouette |
| Oncology | انکولوژی | `spec-oncology.png` | an awareness ribbon |
| Orthopedics | ارتوپدی | `spec-orthopedics.png` | a bone with a joint |
| Otolaryngology (ENT) | گوش و حلق و بینی | `spec-ent.png` | an ear, nose and throat profile |
| Pathology & Lab Medicine | آسیب‌شناسی و پزشکی آزمایشگاهی | `spec-pathology.png` | a microscope |
| Pediatrics | کودکان | `spec-pediatrics.png` | a baby bottle and a small teddy bear head |
| Physical Medicine & Rehabilitation | طب فیزیکی و توان‌بخشی | `spec-rehab.png` | a wheelchair symbol |
| Physiotherapy | فیزیوتراپی | `spec-physio.png` | a figure stretching with a resistance band |
| Preventive Medicine | طب پیشگیری | `spec-preventive.png` | a shield with a check mark |
| Respirology | بیماری‌های تنفسی | `spec-respirology.png` | lungs |
| Rheumatology | روماتولوژی | `spec-rheumatology.png` | a hand with highlighted finger joints |
| Surgery | جراحی | `spec-surgery.png` | a scalpel crossed with forceps |
| Transplant | پیوند | `spec-transplant.png` | an organ (kidney) inside a cooler box |
| Urology | اورولوژی | `spec-urology.png` | a bladder |
| Vascular Surgery | جراحی عروق | `spec-vascular.png` | a branching artery with a small stent |

## 8. Diseases & Conditions: top-level groups

| Group | فارسی | file | Subject |
|---|---|---|---|
| Medicine | داخلی | `med-medicine.png` | a stethoscope |
| Surgery | جراحی | `med-surgery.png` | same as `spec-surgery.png` (reuse) |
| Pediatrics | کودکان | `med-pediatrics.png` | same as `spec-pediatrics.png` (reuse) |

## 9. App identity (optional)

| Item | file | Subject |
|---|---|---|
| App icon | `app-icon.png` | a mortar and pestle merged with an open book, on a solid deep-teal #0F5C52 rounded-square background (the **only** icon with a background) |
| Empty state | `empty-state.png` | an empty open box with a small capsule floating above it |
| Loading / offline | `offline.png` | a cloud with a small slash |

---

### Tips for consistency
- Generate in **batches of 6–8 icons per prompt** ("a set of 6 icons in a 3×2 grid, same style: 1) … 2) …"), then crop. Icons in one batch match each other much better than icons made one at a time.
- Keep the first good batch as a **style reference image** and attach it to every later prompt ("match the style of the attached reference exactly").
- After generating, vectorise (e.g. with Illustrator Image Trace or vectorizer.ai) and recolour to the exact hex values above. Image models drift on colours.
