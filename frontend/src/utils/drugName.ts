/** Old cached chapter lists may not yet contain the Persian name. */
export function drugName(drug: { name: string; name_fa?: string | null } | null | undefined, isFa: boolean): string {
  return (isFa ? drug?.name_fa?.trim() : "") || drug?.name || "";
}
