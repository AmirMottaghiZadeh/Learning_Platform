import { IconName } from "@/components/primitives/IconImage";

/** English specialty name (as the API sends it, for both calculator domains
 * and Medscape specialties) -> its drawn icon. Names with no fitting icon are
 * left out on purpose; their tiles keep the monogram fallback. */
const SPECIALTY_ICONS: Record<string, IconName> = {
  // Calculator domains
  Cardiology: "spec-cardiology",
  "COVID-19": "spec-covid",
  "Critical Care": "spec-critical-care",
  Emergency: "spec-emergency",
  Endocrinology: "spec-endocrinology",
  Gastroenterology: "spec-gastro",
  "General Calculators": "spec-general",
  Geriatrics: "spec-geriatrics",
  Hematology: "spec-hematology",
  "Infectious Disease": "spec-infectious",
  "Medical Administration": "spec-admin",
  "Medical Imaging": "spec-imaging",
  "Mental Health": "spec-mental-health",
  Nephrology: "spec-nephrology",
  "Neurology / Neurosurgery": "spec-neurology",
  "Obstetrics & Gynecology": "spec-obgyn",
  Oncology: "spec-oncology",
  Orthopedics: "spec-orthopedics",
  "Otolaryngology (ENT)": "spec-ent",
  "Pathology & Lab Medicine": "spec-pathology",
  Pediatrics: "spec-pediatrics",
  "Physical Medicine and Rehabilitation": "spec-rehab",
  Physiotherapy: "spec-physio",
  "Preventive Medicine": "spec-preventive",
  Respirology: "spec-respirology",
  Rheumatology: "spec-rheumatology",
  Surgery: "spec-surgery",
  Transplant: "spec-transplant",
  Urology: "spec-urology",
  "Vascular Surgery": "spec-vascular",

  // Medscape specialties (names that differ from the calculator ones)
  "Allergy Immunology": "topic-resp-allergy",
  Anesthesiology: "topic-cns-anesthesia",
  "Cancer Guides": "spec-oncology",
  Dentistry: "topic-dental",
  Dermatology: "cat-dermatology",
  "Emergency Medicine": "spec-emergency",
  "Infectious Diseases": "spec-infectious",
  "Laboratory Medicine": "spec-pathology",
  Neurology: "spec-neurology",
  "Obstetrics Gynecology": "spec-obgyn",
  Pathology: "spec-pathology",
  Psychiatry: "spec-mental-health",
  Pulmonology: "spec-respirology",
  Radiology: "spec-imaging",
  Rehabilitation: "spec-rehab",
  "Sports Medicine": "spec-physio",
  "Pediatrics Cardiac": "spec-pediatrics",
  "Pediatrics Development": "spec-pediatrics",
  "Pediatrics General": "spec-pediatrics",
  "Pediatrics Genetics": "spec-pediatrics",
  "Pediatrics Surgery": "spec-pediatrics",
  "General Surgery": "spec-surgery",
  Neurosurgery: "spec-neurology",
  Ophthalmology: "topic-sense-eye",
  "Orthopedic Surgery": "spec-orthopedics",
  Otolaryngology: "spec-ent",
};

export function specialtyIcon(name: string): IconName | null {
  return SPECIALTY_ICONS[name.trim()] ?? null;
}
