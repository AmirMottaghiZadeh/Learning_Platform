import React, { useState } from "react";
import { Linking, Pressable, View } from "react-native";
import { SvgXml } from "react-native-svg";

import type { DrugChemistry } from "@/api/types";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { AppText } from "./primitives/AppText";

const SUBSCRIPTS = "₀₁₂₃₄₅₆₇₈₉";

/** Only element/group counts become subscripts; terminal ionic charge stays raised. */
function formulaLabel(formula: string): string {
  return formula.replace(/([A-Za-z)\]])(\d+)/g, (_, element: string, count: string) =>
    element + count.replace(/\d/g, (d) => SUBSCRIPTS[Number(d)]))
    .replace(/\+$/, "⁺").replace(/-$/, "⁻");
}

export function DrugChemistryCard({ chemistry, name }: { chemistry?: DrugChemistry | null; name: string }) {
  const { colors } = useTheme();
  const { lang } = useLang();
  const isFa = lang === "fa";
  const [linkFailed, setLinkFailed] = useState(false);
  if (!chemistry) return null;
  const openSource = () => {
    // Construct from the integer identifier; never open an arbitrary API-provided URL.
    if (!Number.isSafeInteger(chemistry.pubchem_cid) || chemistry.pubchem_cid <= 0) return;
    Linking.openURL(`https://pubchem.ncbi.nlm.nih.gov/compound/${chemistry.pubchem_cid}`)
      .then(() => setLinkFailed(false)).catch(() => setLinkFailed(true));
  };
  return (
    <View style={{ marginTop: 22, borderRadius: 14, padding: 16, backgroundColor: colors.softBg,
      borderWidth: 1, borderColor: colors.trackBg }}>
      <AppText weight="800" size={16}>{isFa ? "فرمول و ساختار شیمیایی" : "Chemical formula & structure"}</AppText>
      <AppText muted size={12} style={{ marginTop: 4 }}>{isFa ? "فرمول مولکولی مادهٔ مؤثره" : "Active ingredient molecular formula"}</AppText>
      <AppText selectable weight="800" size={25} style={{ writingDirection: "ltr", textAlign: "left", marginTop: 8 }}>
        {formulaLabel(chemistry.molecular_formula)}
      </AppText>
      <View accessible accessibilityRole="image" accessibilityLabel={isFa ? `ساختار دوبعدی ${name}` : `2D molecular structure of ${name}`}
        style={{ marginTop: 12, backgroundColor: "#FFFFFF", borderRadius: 10, overflow: "hidden", height: 200 }}>
        <SvgXml xml={chemistry.structure_svg} width="100%" height="100%" />
      </View>
      <Pressable accessibilityRole="link" onPress={openSource}
        style={{ minHeight: 44, justifyContent: "center", marginTop: 8 }}>
        <AppText color={colors.accent} weight="700" size={13}>
          {isFa ? "منبع و جزئیات در PubChem" : "Source & details on PubChem"}
        </AppText>
      </Pressable>
      {linkFailed ? <AppText size={12} muted>{isFa ? "باز کردن منبع ممکن نشد؛ اتصال را بررسی و دوباره تلاش کنید." : "Could not open the source. Check your connection and try again."}</AppText> : null}
    </View>
  );
}
