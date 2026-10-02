import { CalculatorListItem } from "@/api/types";

/** The source snapshot tags each calculator with a flat list of category
 * names, but each category entry there also carries `main_category` and
 * `subcategory_of` -- a real two-level clinical taxonomy that the import
 * command flattens away (a calculator only needs its own tags to be
 * searchable/filterable). These two tables are that taxonomy, extracted
 * once from the full snapshot (every `(name, main_category, subcategory_of)`
 * triple across all ~500 calculators' category trees) so browsing can group
 * the ~170 flat tags under the ~30 broader domains they actually belong to.
 *
 * A name can be both a main domain itself and a cross-listed subtopic of a
 * *different* domain (e.g. "Pediatrics" is its own domain, but a calculator
 * elsewhere nests it under "Mental Health") -- so these two tables are
 * checked independently, not as an if/else, to keep that genuine dual
 * membership rather than forcing one canonical home per name. A handful of
 * subtopics (e.g. "Sleep") were likewise seen under more than one parent
 * across different calculators; all of their real parents are kept rather
 * than picking one arbitrarily.
 */
const MAIN_CATEGORIES = [
  "Addiction Medicine", "Anesthesiology", "COVID-19", "Cardiac Surgery", "Cardiology",
  "Critical Care", "Emergency", "Endocrinology", "Gastroenterology", "General Calculators",
  "Geriatrics", "Hematology", "Infectious Disease", "Medical Administration", "Medical Imaging",
  "Mental Health", "Nephrology", "Neurology / Neurosurgery", "Obstetrics & Gynecology",
  "Oncology", "Orthopedics", "Otolaryngology (ENT)", "Pathology & Lab Medicine", "Pediatrics",
  "Physical Medicine and Rehabilitation", "Physiotherapy", "Preventive Medicine", "Respirology",
  "Rheumatology", "Surgery", "Transplant", "Urology", "Vascular Surgery",
];

const PARENTS_BY_SUBCATEGORY: Record<string, string[]> = {
  "AKI Clinical Trials": ["Nephrology"],
  "Acute Kidney Injury": ["Nephrology"],
  "Acute Lymphoblastic Leukemia": ["Hematology"],
  "Addictions": ["Mental Health"],
  "Airway": ["Emergency"],
  "Airway & Respiratory": ["Anesthesiology"],
  "Ankylosing Spondylitis": ["Rheumatology"],
  "Antibiotics": ["Infectious Disease"],
  "Anxiety": ["Mental Health"],
  "Aortic Disease": ["Cardiology"],
  "Aortic Stenosis/Outflow": ["Cardiology"],
  "Arrhythmia": ["Cardiology"],
  "Arteriovenous Malformation": ["Neurology / Neurosurgery"],
  "Asthma & COPD": ["Respirology"],
  "Atrial Fibrillation": ["Cardiology"],
  "BMI": ["Anesthesiology"],
  "Benign Hematology": ["Hematology"],
  "Bipolar": ["Mental Health"],
  "Bleeding Risk": ["Cardiology"],
  "Body Imaging": ["Medical Imaging"],
  "Body Surface Area": ["Hematology"],
  "Body Surface Area, BMI and Lean Body Weight": ["Oncology"],
  "Burns": ["Emergency"],
  "Cardiac": ["Transplant"],
  "Cardiac & Cerebrovascular": ["Geriatrics"],
  "Cardiac ICU": ["Critical Care"],
  "Cardiac Surgery": ["Anesthesiology"],
  "Chest Pain & Cardiac": ["Emergency"],
  "Chronic Kidney Disease": ["Nephrology"],
  "Clinical Status Assessment": ["Anesthesiology"],
  "Clostridium Difficile": ["Infectious Disease"],
  "Coma/Level of Consciousness": ["Neurology / Neurosurgery"],
  "Coronary Artery Disease": ["Cardiology"],
  "DVT/PE": ["Respirology"],
  "Dementia/Neurodegenerative": ["Neurology / Neurosurgery"],
  "Depression": ["Mental Health"],
  "Diabetes": ["Endocrinology"],
  "Diagnostic Criteria": ["Infectious Disease"],
  "Diagnostic criteria": ["Rheumatology"],
  "Diarrhea": ["Gastroenterology"],
  "ECG": ["Cardiology"],
  "Eating Disorder": ["Mental Health"],
  "Echocardiography": ["Cardiology"],
  "Electrolytes": ["Endocrinology"],
  "Familial Hypercholesterolemia": ["Cardiology"],
  "Febrile Neutropenia": ["Infectious Disease"],
  "Fever in Infants": ["Infectious Disease"],
  "Fluids & Electrolytes": ["Nephrology"],
  "Frailty": ["Geriatrics"],
  "Functional Outcome": ["Neurology / Neurosurgery"],
  "GI Bleed": ["Gastroenterology"],
  "Gastrointestinal cancer": ["Gastroenterology"],
  "General Medicine": ["Emergency", "Geriatrics"],
  "General Otolaryngology": ["Otolaryngology (ENT)"],
  "General Pediatrics": ["Pediatrics"],
  "General Respirology": ["Respirology"],
  "Genitourinary Cancers": ["Oncology", "Urology"],
  "Geriatric Psychiatry": ["Geriatrics"],
  "Glomerulonephritis": ["Nephrology"],
  "Growth": ["Pediatrics"],
  "Head & Neck Cancer Staging": ["Oncology", "Otolaryngology (ENT)"],
  "Head & Neck Trauma": ["Neurology / Neurosurgery"],
  "Headache": ["Neurology / Neurosurgery"],
  "Heart Failure": ["Cardiology"],
  "Hemodialysis": ["Nephrology"],
  "Hepatology": ["Gastroenterology"],
  "Hypertension": ["Cardiology"],
  "ICU AKI": ["Critical Care"],
  "Illness Severity": ["Critical Care"],
  "Infectious Disease": ["Pediatrics"],
  "Inflammatory Bowel Disease": ["Gastroenterology"],
  "Injuries & Trauma": ["Emergency"],
  "Intracerebral Hemorrhage": ["Neurology / Neurosurgery"],
  "Invasive Hemodynamics": ["Cardiology"],
  "Ischemic Stroke": ["Cardiology", "Neurology / Neurosurgery"],
  "Kidney Disease": ["Geriatrics"],
  "Lipids": ["Endocrinology"],
  "Liver": ["Infectious Disease", "Transplant"],
  "Lung Cancer": ["Respirology"],
  "Lupus": ["Rheumatology"],
  "Lupus Nephritis": ["Nephrology"],
  "Malignant Hematology": ["Hematology", "Oncology"],
  "Medical ICU": ["Critical Care"],
  "Mental Health": ["Pediatrics"],
  "Miscellaneous": ["Cardiology"],
  "Mitral Regurgitation": ["Cardiology"],
  "Mitral Stenosis": ["Cardiology"],
  "Movement Disorder": ["Neurology / Neurosurgery"],
  "Multiple Sclerosis & Demyelinating Disease": ["Neurology / Neurosurgery"],
  "Nephrolithiasis": ["Nephrology", "Urology"],
  "Neurocognitive Disorder": ["Geriatrics"],
  "Neuroimaging": ["Medical Imaging"],
  "Neurologic ICU": ["Critical Care"],
  "Neurophysiology": ["Neurology / Neurosurgery"],
  "Obsessive Compulsive Disorder": ["Mental Health"],
  "Obstetrical Anesthesia": ["Anesthesiology"],
  "Obstetrical imaging": ["Medical Imaging"],
  "Osteoporosis": ["Endocrinology"],
  "PCI and Cardiac Surgery": ["Cardiology"],
  "PD": ["Nephrology"],
  "Pancreatitis": ["Gastroenterology"],
  "Pathology": ["Nephrology"],
  "Pediatrics": ["Mental Health"],
  "Pediatrics ER": ["Emergency"],
  "Pneumonia": ["Respirology"],
  "Post Traumatic Stress": ["Mental Health"],
  "Pre-operative Assessment": ["Cardiology"],
  "Preoperative Assessment": ["Anesthesiology", "Surgery", "Urology", "Vascular Surgery"],
  "Psychiatry": ["Emergency"],
  "Psychosis": ["Mental Health"],
  "Psychosomatic": ["Mental Health"],
  "Renal": ["Transplant"],
  "Respiratory ICU": ["Critical Care"],
  "Respiratory Tract Infection": ["Infectious Disease"],
  "Rheumatoid Arthritis": ["Rheumatology"],
  "Risk Scores": ["Cardiology"],
  "Seizure": ["Neurology / Neurosurgery"],
  "Sepsis": ["Critical Care", "Emergency", "Infectious Disease"],
  "Sexual Function": ["Mental Health", "Urology"],
  "Sexual Health": ["Obstetrics & Gynecology"],
  "Shunts": ["Cardiology"],
  "Sleep": ["Mental Health", "Respirology"],
  "Solid Tumor": ["Oncology"],
  "Subarachnoid Hemorrhage": ["Neurology / Neurosurgery"],
  "Surgery": ["Emergency"],
  "Surgical Diagnosis & Management": ["Surgery"],
  "Surgical diagnosis & management": ["Vascular Surgery"],
  "Syncope": ["Cardiology"],
  "Thrombosis": ["Emergency", "Urology"],
  "Thrombosis imaging": ["Medical Imaging"],
  "Thyroid disease & cancer": ["Endocrinology"],
  "Tools Based on Vascular Quality Initiative (VQI) Data": ["Vascular Surgery"],
  "Transplant": ["Nephrology"],
  "Trauma": ["Critical Care", "Surgery"],
  "Trauma/Critical Care": ["Pediatrics"],
  "Trauma/MSK imaging": ["Medical Imaging"],
  "Treadmill Testing": ["Cardiology"],
  "Treatment Side Effects": ["Mental Health"],
  "Tuberculosis": ["Infectious Disease"],
  "Urologic disease": ["Urology"],
  "Vasculitis": ["Rheumatology"],
  "WHO Surgical Safety Checklist": ["Surgery", "Urology", "Vascular Surgery"],
  "eGFR": ["Nephrology"],
};

const OTHER = "Other";

export interface CalculatorSubgroup {
  name: string;
  calculators: CalculatorListItem[];
}

export interface CalculatorMainGroup {
  name: string;
  subgroups: CalculatorSubgroup[];
  /** Calculators tagged with this domain's bare name, not any finer subtopic. */
  directCalculators: CalculatorListItem[];
}

export function groupByMainCategory(items: CalculatorListItem[]): CalculatorMainGroup[] {
  const mainSet = new Set(MAIN_CATEGORIES);
  const mains = new Map<string, { subgroups: Map<string, CalculatorListItem[]>; direct: CalculatorListItem[] }>();

  const ensureMain = (name: string) => {
    let m = mains.get(name);
    if (!m) {
      m = { subgroups: new Map(), direct: [] };
      mains.set(name, m);
    }
    return m;
  };

  for (const item of items) {
    const categories = item.categories.length ? item.categories : [OTHER];
    for (const name of categories) {
      const parents = PARENTS_BY_SUBCATEGORY[name] ?? [];
      for (const parent of parents) {
        const m = ensureMain(parent);
        const list = m.subgroups.get(name);
        if (list) list.push(item);
        else m.subgroups.set(name, [item]);
      }
      if (mainSet.has(name) || name === OTHER) {
        ensureMain(name).direct.push(item);
      } else if (!parents.length) {
        // Unexpected tag not seen in the source taxonomy walk -- surface it
        // rather than silently dropping the calculator from every list.
        ensureMain(OTHER).direct.push(item);
      }
    }
  }

  return [...mains.entries()]
    .map(([name, m]) => ({
      name,
      subgroups: [...m.subgroups.entries()]
        .map(([subName, calculators]) => ({ name: subName, calculators }))
        .sort((a, b) => a.name.localeCompare(b.name)),
      directCalculators: m.direct,
    }))
    .sort((a, b) => (a.name === OTHER ? 1 : b.name === OTHER ? -1 : a.name.localeCompare(b.name)));
}
