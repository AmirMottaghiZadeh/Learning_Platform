import React from "react";
import { ClinicalArticleReader } from "@/components/article/ClinicalArticleReader";

/** Diseases and guidelines use the same controls, highlights and document bridge. */
export function MedscapeArticleScreen() {
  return <ClinicalArticleReader source="medscape" />;
}
