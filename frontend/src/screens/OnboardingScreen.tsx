import React, { useState } from "react";
import { View } from "react-native";

import { authApi } from "@/api/endpoints";
import { AppShell } from "@/components/AppShell";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Chip } from "@/components/primitives/Chip";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useAuth } from "@/store/auth";
import { spacing } from "@/theme/tokens";

const FIELDS = [
  { v: "pharmacy", fa: "داروسازی", en: "Pharmacy" },
  { v: "medicine", fa: "پزشکی", en: "Medicine" },
  { v: "nursing", fa: "پرستاری", en: "Nursing" },
];
const GOALS = [
  { v: "residency", fa: "آزمون دستیاری", en: "Residency exam" },
  { v: "final", fa: "امتحانات ترم", en: "Term finals" },
  { v: "clinical", fa: "مرور بالینی روزانه", en: "Daily clinical review" },
];
const LEVELS = [
  { v: "beginner", fa: "مبتدی", en: "Beginner" },
  { v: "intermediate", fa: "متوسط", en: "Intermediate" },
  { v: "advanced", fa: "پیشرفته", en: "Advanced" },
];

export function OnboardingScreen() {
  const { t, isFa, lang } = useLang();
  const setUser = useAuth((s) => s.setUser);

  const [field, setField] = useState<string>("");
  const [goal, setGoal] = useState<string>("");
  const [level, setLevel] = useState<string>("");
  const [busy, setBusy] = useState(false);

  const ready = field && goal && level;

  const finish = async () => {
    setBusy(true);
    try {
      const user = await authApi.onboarding({
        study_field: field,
        study_goal: goal,
        study_level: level,
        language: lang,
      });
      setUser(user);
    } catch {
      setBusy(false);
    }
  };

  const Group = ({
    label,
    options,
    value,
    onChange,
  }: {
    label: string;
    options: typeof FIELDS;
    value: string;
    onChange: (v: string) => void;
  }) => (
    <View style={{ gap: 10, marginBottom: spacing.xl }}>
      <AppText weight="700" size={14}>
        {label}
      </AppText>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
        {options.map((o) => (
          <Chip
            key={o.v}
            label={isFa ? o.fa : o.en}
            selected={value === o.v}
            onPress={() => onChange(o.v)}
          />
        ))}
      </View>
    </View>
  );

  return (
    <AppShell>
      <Screen>
        <AppText weight="800" size={22}>
          {t("obFormTitle")}
        </AppText>
        <AppText muted weight="600" size={13} style={{ marginBottom: spacing.xl }}>
          {t("obFormSub")}
        </AppText>

        <Group label={t("obFieldLabel")} options={FIELDS} value={field} onChange={setField} />
        <Group label={t("obGoalLabel")} options={GOALS} value={goal} onChange={setGoal} />
        <Group label={t("obLevelLabel")} options={LEVELS} value={level} onChange={setLevel} />

        <Button label={t("obStart")} onPress={finish} disabled={!ready} loading={busy} />
      </Screen>
    </AppShell>
  );
}
