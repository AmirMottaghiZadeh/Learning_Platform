const PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
const ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩";

/** Latin digits for Persian and Arabic-Indic ones; everything else as is. */
export function latinDigits(text: string): string {
  return text.replace(/[۰-۹٠-٩]/g, (d) => {
    const persian = PERSIAN_DIGITS.indexOf(d);
    return String(persian >= 0 ? persian : ARABIC_DIGITS.indexOf(d));
  });
}

/** A number as a learner types it on any keyboard: Persian or Arabic digits
 * (a Persian phone keyboard gives «۲۵», which parseFloat reads as NaN), the
 * Persian decimal separator «٫», a slash or comma as the decimal point
 * («۲/۵», «2,5»), and thousands separators («٬», or a comma before exactly
 * three digits: «1,000»). NaN when the text is not a whole number. */
export function parseTypedNumber(text: string): number {
  const clean = latinDigits(text)
    .replace(/[\s‌‎‏٬]/g, "")
    .replace(/−/g, "-")
    .replace(/,(?=\d{3}(?!\d))/g, "")
    .replace(/[٫,/]/g, ".");
  return /^[-+]?(\d+\.?\d*|\.\d+)$/.test(clean) ? Number(clean) : NaN;
}
