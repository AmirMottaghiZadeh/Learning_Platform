import { apiClient } from "@/api/client";
import { PEDIATRIC_DOSE_SLUG } from "./catalog";
import { isCompatibleDataset } from "./version";
import { PediatricDataset } from "./types";

export class PediatricDatasetVersionError extends Error {}

export async function fetchPediatricDataset(): Promise<PediatricDataset> {
  const { data } = await apiClient.get<PediatricDataset>(`/calculators/${PEDIATRIC_DOSE_SLUG}/`);
  if (!isCompatibleDataset(data)) throw new PediatricDatasetVersionError("Incompatible pediatric dose engine and data");
  if (!Array.isArray(data.drugs) || !data.drugs.length) throw new Error("Empty pediatric dose dataset");
  return data;
}
