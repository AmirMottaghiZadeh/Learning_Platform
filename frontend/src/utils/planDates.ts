import { GREGORIAN_MONTHS_EN, JALALI_MONTHS_FA, toGregorian, toJalali } from "@/utils/jalali";

/** A local calendar day as the API writes it: "2026-12-06". */
export function isoDay(date: Date): string {
  const pad = (v: number) => String(v).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** "2026-12-06" -> local noon of that day (noon, so a day count never slips
 * over a DST change). */
export function parseIsoDay(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d, 12);
}

/** Today plus `months` calendar months, as an API day. */
export function monthsFromToday(months: number): string {
  const d = new Date();
  d.setHours(12, 0, 0, 0);
  d.setMonth(d.getMonth() + months);
  return isoDay(d);
}

/** An API day from a Jalali date, or null when it is not a real date. */
export function isoFromJalali(jy: number, jm: number, jd: number): string | null {
  if (!jy || !jm || !jd || jm > 12 || jd > 31) return null;
  const { gy, gm, gd } = toGregorian(jy, jm, jd);
  const back = toJalali(gy, gm, gd);
  if (back.jy !== jy || back.jm !== jm || back.jd !== jd) return null;
  return isoDay(new Date(gy, gm - 1, gd, 12));
}

/** "۱۵ آذر ۱۴۰۵" in Persian, "6 December 2026" in English. `digits` writes
 * the numbers (the language's n()). */
export function formatDay(iso: string, isFa: boolean, digits: (v: number) => string): string {
  const d = parseIsoDay(iso);
  if (!isFa) return `${d.getDate()} ${GREGORIAN_MONTHS_EN[d.getMonth()]} ${d.getFullYear()}`;
  const { jy, jm, jd } = toJalali(d.getFullYear(), d.getMonth() + 1, d.getDate());
  return `${digits(jd)} ${JALALI_MONTHS_FA[jm - 1]} ${digits(jy)}`;
}

/** Whole days from today to an API day (negative when it has passed). */
export function daysUntil(iso: string): number {
  const today = new Date();
  today.setHours(12, 0, 0, 0);
  return Math.round((parseIsoDay(iso).getTime() - today.getTime()) / 86_400_000);
}

/** The Jalali year today, for the exact-date fields. */
export function currentJalaliYear(): number {
  const d = new Date();
  return toJalali(d.getFullYear(), d.getMonth() + 1, d.getDate()).jy;
}
