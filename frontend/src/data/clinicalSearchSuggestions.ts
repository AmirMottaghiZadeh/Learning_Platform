/** Editorial question bank: selecting a question only fills the composer. */
export type ClinicalSearchSuggestion = { id: string; category: string; fa: string; en: string };

const groups: Array<{ category: string; questions: Array<[string, string]> }> = [
  { category: "cardiology", questions: [
    ["درمان اولیهٔ فیبریلاسیون دهلیزی چگونه انتخاب می‌شود؟", "How is initial treatment for atrial fibrillation selected?"],
    ["دارودرمانی نارسایی قلبی با کسر جهشی کاهش‌یافته چیست؟", "What is the drug treatment for heart failure with reduced ejection fraction?"],
    ["در بیمار مبتلا به فشار خون و دیابت، داروی اولیه چگونه انتخاب می‌شود؟", "How is initial antihypertensive therapy selected in a patient with diabetes?"],
    ["ارزیابی درد قفسهٔ سینه در اورژانس چه مراحلی دارد؟", "What are the steps in evaluating chest pain in the emergency department?"],
    ["مصرف ضدانعقاد در فیبریلاسیون دهلیزی بر چه اساسی تعیین می‌شود؟", "How is the need for anticoagulation in atrial fibrillation determined?"],
  ] },
  { category: "pediatrics", questions: [
    ["در کودک مبتلا به تب بدون کانون، ارزیابی اولیه چیست؟", "What is the initial evaluation of fever without a source in a child?"],
    ["درمان اوتیت میانی حاد در کودکان چگونه انتخاب می‌شود؟", "How is treatment for acute otitis media in children selected?"],
    ["برخورد با اولین تشنج همراه تب در کودک چیست؟", "What is the approach to a first febrile seizure in a child?"],
    ["در کم‌آبی ناشی از گاستروانتریت کودکان چه درمانی پیشنهاد می‌شود؟", "How is dehydration from gastroenteritis in children treated?"],
    ["ارزیابی و درمان آسم در کودکان چه تفاوتی با بزرگسالان دارد؟", "How do asthma evaluation and treatment in children differ from adults?"],
  ] },
  { category: "endocrinology", questions: [
    ["دارودرمانی اولیهٔ دیابت نوع دو چگونه انتخاب می‌شود؟", "How is initial pharmacologic therapy for type 2 diabetes selected?"],
    ["در بیمار دیابتی با بیماری کلیوی، انتخاب دارو چگونه است؟", "How are diabetes medications selected in a patient with kidney disease?"],
    ["مراحل درمان کتواسیدوز دیابتی در بزرگسالان چیست؟", "What are the steps in treating diabetic ketoacidosis in adults?"],
    ["درمان کم‌کاری تیروئید چگونه آغاز و پایش می‌شود؟", "How is hypothyroidism treatment initiated and monitored?"],
    ["ارزیابی اولیهٔ هیپرکلسمی چگونه انجام می‌شود؟", "How is hypercalcemia initially evaluated?"],
  ] },
  { category: "infectious_diseases", questions: [
    ["درمان تجربی پنومونی اکتسابی از جامعه در بزرگسالان چیست؟", "What is empiric treatment for community-acquired pneumonia in adults?"],
    ["در عفونت ادراری بدون عارضه، آنتی‌بیوتیک چگونه انتخاب می‌شود؟", "How are antibiotics selected for uncomplicated urinary tract infection?"],
    ["اقدامات اولیه برای بیمار مشکوک به سپسیس چیست؟", "What are the initial measures for a patient with suspected sepsis?"],
    ["درمان هلیکوباکتر پیلوری با توجه به مقاومت دارویی چگونه انتخاب می‌شود؟", "How is Helicobacter pylori treatment selected considering antibiotic resistance?"],
    ["در شک به مننژیت باکتریایی، بررسی و درمان اولیه چیست؟", "What is the initial evaluation and treatment for suspected bacterial meningitis?"],
  ] },
  { category: "pulmonology", questions: [
    ["درمان مرحله‌ای آسم در بزرگسالان چگونه انجام می‌شود؟", "How is stepwise asthma treatment performed in adults?"],
    ["در تشدید حاد COPD چه داروهایی و با چه مدت مصرفی توصیه می‌شوند؟", "Which medications and treatment durations are recommended for an acute COPD exacerbation?"],
    ["ارزیابی بیمار مشکوک به آمبولی ریه چه مراحلی دارد؟", "What are the steps in evaluating suspected pulmonary embolism?"],
    ["علل شایع سرفهٔ مزمن و مسیر بررسی آن چیست؟", "What are the common causes and diagnostic approach to chronic cough?"],
    ["برای آپنهٔ انسدادی خواب چه روش‌های درمانی وجود دارد؟", "What treatment options are available for obstructive sleep apnea?"],
  ] },
  { category: "neurology", questions: [
    ["درمان حملهٔ حاد میگرن و پیشگیری از آن چگونه انتخاب می‌شود؟", "How are acute and preventive migraine treatments selected?"],
    ["در بیمار مشکوک به سکتهٔ مغزی ایسکمیک، اقدامات اولیه چیست؟", "What are the initial measures for suspected acute ischemic stroke?"],
    ["انتخاب داروی اولیه برای تشنج فوکال در بزرگسالان چگونه است؟", "How is initial medication for focal seizures in adults selected?"],
    ["ارزیابی سرگیجه برای افتراق علل مرکزی و محیطی چگونه است؟", "How is dizziness evaluated to distinguish central and peripheral causes?"],
    ["درمان درد نوروپاتیک دیابتی چگونه انتخاب می‌شود؟", "How is treatment for painful diabetic neuropathy selected?"],
  ] },
  { category: "nephrology", questions: [
    ["در آسیب حاد کلیه، ارزیابی اولیه و مدیریت داروها چگونه است؟", "What are the initial evaluation and medication management steps in acute kidney injury?"],
    ["در هیپرکالمی شدید چه اقداماتی و با چه ترتیبی انجام می‌شود؟", "What interventions are used for severe hyperkalemia and in what order?"],
    ["تنظیم دوز دارو در بیماری مزمن کلیه بر چه اساسی انجام می‌شود؟", "How is medication dosing adjusted in chronic kidney disease?"],
    ["درمان هیپوناترمی بر اساس علائم و وضعیت حجم چگونه است؟", "How is hyponatremia treated according to symptoms and volume status?"],
    ["پیشگیری دارویی از عود سنگ کلیه چگونه انتخاب می‌شود؟", "How is pharmacologic prevention of recurrent kidney stones selected?"],
  ] },
  { category: "gastroenterology", questions: [
    ["در رفلاکس معده به مری، درمان دارویی و مدت آن چگونه تعیین می‌شود؟", "How are drug treatment and duration determined for gastroesophageal reflux disease?"],
    ["برخورد اولیه با خونریزی گوارشی فوقانی چیست؟", "What is the initial approach to upper gastrointestinal bleeding?"],
    ["درمان یبوست مزمن در بزرگسالان چه مراحلی دارد؟", "What are the steps in treating chronic constipation in adults?"],
    ["در اسهال حاد بزرگسالان چه زمانی آنتی‌بیوتیک لازم است؟", "When are antibiotics indicated for acute diarrhea in adults?"],
    ["ارزیابی افزایش بدون علامت آنزیم‌های کبدی چگونه انجام می‌شود؟", "How are asymptomatic elevations of liver enzymes evaluated?"],
  ] },
  { category: "psychiatry", questions: [
    ["دارودرمانی اولیهٔ افسردگی اساسی چگونه انتخاب می‌شود؟", "How is initial pharmacotherapy for major depressive disorder selected?"],
    ["در اضطراب فراگیر، انتخاب درمان دارویی و پایش آن چگونه است؟", "How is medication for generalized anxiety disorder selected and monitored?"],
    ["عوارض مهم آریپیپرازول و نحوهٔ پایش آن‌ها چیست؟", "What are the important adverse effects of aripiprazole and how are they monitored?"],
    ["در اختلال دوقطبی، درمان مانیا چگونه انتخاب می‌شود؟", "How is treatment for mania in bipolar disorder selected?"],
    ["برخورد با علائم قطع ناگهانی داروهای ضدافسردگی چیست؟", "What is the approach to antidepressant discontinuation symptoms?"],
  ] },
  { category: "dermatology", questions: [
    ["درمان آکنه بر اساس شدت بیماری چگونه انتخاب می‌شود؟", "How is acne treatment selected according to severity?"],
    ["برای درماتیت آتوپیک چه درمان‌های موضعی وجود دارد؟", "What topical treatments are available for atopic dermatitis?"],
    ["در پسوریازیس با درگیری مفصلی، انتخاب درمان چگونه است؟", "How is treatment selected for psoriasis with joint involvement?"],
    ["درمان کهیر مزمن چه مراحلی دارد؟", "What are the treatment steps for chronic urticaria?"],
    ["درمان زونا و زمان مناسب آغاز داروی ضدویروس چیست؟", "How is herpes zoster treated and when should antivirals be started?"],
  ] },
  { category: "women_health", questions: [
    ["درمان فشار خون در بارداری چگونه انتخاب می‌شود؟", "How is antihypertensive treatment selected during pregnancy?"],
    ["در بارداری، عفونت ادراری با چه داروهایی درمان می‌شود؟", "Which medications are used for urinary tract infections in pregnancy?"],
    ["ارزیابی و درمان تهوع و استفراغ بارداری چه مراحلی دارد؟", "What are the evaluation and treatment steps for nausea and vomiting in pregnancy?"],
    ["در شیردهی، ایمنی مصرف دارو چگونه بررسی می‌شود؟", "How is medication safety assessed during breastfeeding?"],
    ["درمان دارویی خونریزی غیرطبیعی رحم چگونه انتخاب می‌شود؟", "How is medical treatment for abnormal uterine bleeding selected?"],
  ] },
  { category: "urology", questions: [
    ["دارودرمانی بزرگی خوش‌خیم پروستات با چه داروها و دوزهایی انجام می‌شود؟", "Which medications and doses are used for benign prostatic hyperplasia?"],
    ["در عفونت‌های ادراری عودکننده چه روش‌های پیشگیری وجود دارد؟", "What prevention strategies are available for recurrent urinary tract infections?"],
    ["درمان مثانهٔ بیش‌فعال چگونه انتخاب می‌شود؟", "How is treatment for overactive bladder selected?"],
    ["در کولیک کلیوی، انتخاب مسکن چگونه است؟", "How is analgesia selected for renal colic?"],
    ["در احتباس ادراری حاد، اقدامات اولیه چیست؟", "What are the initial measures for acute urinary retention?"],
  ] },
  { category: "drug_safety", questions: [
    ["در مصرف همزمان وارفارین و آنتی‌بیوتیک‌ها چه پایشی لازم است؟", "What monitoring is required when warfarin and antibiotics are used together?"],
    ["کدام داروها می‌توانند فاصلهٔ QT را طولانی کنند؟", "Which medications can prolong the QT interval?"],
    ["در مصرف داروهای سروتونرژیک، علائم هشدار سندرم سروتونین چیست؟", "What are the warning signs of serotonin syndrome with serotonergic medications?"],
    ["در بیمار با سابقهٔ زخم معده، خطر NSAIDها چگونه کاهش می‌یابد؟", "How is NSAID risk reduced in a patient with a history of peptic ulcer?"],
    ["برای پایش ایمنی متوترکسات چه بررسی‌هایی لازم است؟", "What tests are needed for methotrexate safety monitoring?"],
  ] },
  { category: "clinical_scenarios", questions: [
    ["بیمار سالمند با گیجی ناگهانی و داروهای متعدد چگونه ارزیابی می‌شود؟", "How is an older adult with acute confusion and multiple medications evaluated?"],
    ["بیمار مبتلا به آسم و فشار خون بالا، برای انتخاب دارو چه ملاحظاتی دارد؟", "What medication considerations apply to a patient with asthma and hypertension?"],
    ["در بیمار دیابتی با درد قفسهٔ سینه و تعریق، ارزیابی اولیه چیست؟", "What is the initial evaluation for chest pain and sweating in a patient with diabetes?"],
    ["بیمار با مصرف ضدانعقاد و خونریزی گوارشی چگونه مدیریت می‌شود؟", "How is gastrointestinal bleeding managed in a patient taking an anticoagulant?"],
    ["در بیمار بیهوش مشکوک به حملهٔ قلبی، اقدامات اولیه و محدودیت مصرف خوراکی دارو چیست؟", "What are the initial measures and limitations of oral medication in an unconscious patient with suspected myocardial infarction?"],
  ] },
  { category: "hematology_rheumatology", questions: [
    ["تشخیص و درمان کم‌خونی فقر آهن در بزرگسالان چگونه انجام می‌شود؟", "How is iron deficiency anemia diagnosed and treated in adults?"],
    ["برای حملهٔ حاد نقرس، دارو و دوز چگونه انتخاب می‌شود؟", "How are medication and dosing selected for an acute gout flare?"],
    ["درمان اولیهٔ آرتریت روماتوئید چگونه انتخاب و پایش می‌شود؟", "How is initial rheumatoid arthritis treatment selected and monitored?"],
    ["پیشگیری و درمان پوکی استخوان در مصرف طولانی کورتون چیست؟", "How is osteoporosis prevented and treated during long-term glucocorticoid use?"],
    ["در بیمار با ترومبوسیتوپنی اتفاقی، بررسی اولیه چیست؟", "What is the initial evaluation of incidentally detected thrombocytopenia?"],
  ] },
  { category: "reference_media", questions: [
    ["جدول مقایسهٔ داروهای ضدانعقاد خوراکی را نشان بده.", "Show the comparison table for oral anticoagulants."],
    ["الگوریتم ارزیابی کم‌خونی میکروسیتیک را پیدا کن.", "Find the algorithm for evaluating microcytic anemia."],
    ["جدول داروهای مؤثر بر فاصلهٔ QT را پیدا کن.", "Find the table of medications that affect the QT interval."],
    ["تصویر الگوهای ECG در هیپرکالمی را نشان بده.", "Show the figure of ECG patterns in hyperkalemia."],
    ["الگوریتم ارزیابی ندول تیروئید را نشان بده.", "Show the algorithm for evaluating a thyroid nodule."],
  ] },
];

export const CLINICAL_SEARCH_SUGGESTIONS: readonly ClinicalSearchSuggestion[] = groups.flatMap(({ category, questions }) =>
  questions.map(([fa, en], i) => ({ id: `${category}-${i + 1}`, category, fa, en })),
);

/** Pick distinct categories first, without mutating the bank. Stable until the screen remounts. */
export function pickClinicalSearchSuggestions(count = 4, random: () => number = Math.random): ClinicalSearchSuggestion[] {
  const remaining = [...groups];
  const selected: ClinicalSearchSuggestion[] = [];
  for (let i = 0; i < Math.min(Math.max(0, Math.floor(count)), groups.length); i++) {
    const index = Math.min(remaining.length - 1, Math.floor(random() * remaining.length));
    const [{ category, questions }] = remaining.splice(index, 1);
    const questionIndex = Math.min(questions.length - 1, Math.floor(random() * questions.length));
    const [fa, en] = questions[questionIndex];
    selected.push({ id: `${category}-${questionIndex + 1}`, category, fa, en });
  }
  return selected;
}
