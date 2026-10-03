import { useQuery } from "@tanstack/react-query";
import React from "react";
import { View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeSection } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";

export function MedscapeArticleScreen() {
  const { t } = useLang();
  const goBack = useNav((s) => s.goBack);
  const slug = String(useNav((s) => s.params.slug ?? ""));

  const { data, isLoading } = useQuery({
    queryKey: ["medscape-article", slug],
    queryFn: () => medscapeApi.detail(slug),
    enabled: !!slug,
  });

  if (isLoading || !data) return <LoadingState />;

  const screenTitleKey = data.kind === "guideline" ? "guidelinesLabel" : "diseasesConditionsLabel";
  const specialties = data.categories.map((c) => c.specialty).join(" · ");

  return (
    <Screen>
      <ScreenChrome title={t(screenTitleKey)} onBack={goBack} />

      <AppText
        weight="900"
        size={21}
        style={{ lineHeight: 29, marginBottom: 6, textAlign: "left", writingDirection: "ltr" }}
      >
        {data.title}
      </AppText>
      {specialties ? (
        <AppText muted weight="700" size={12} style={{ marginBottom: 4, textAlign: "left", writingDirection: "ltr" }}>
          {specialties}
        </AppText>
      ) : null}
      {data.meta ? (
        <AppText muted weight="600" size={11.5} style={{ marginBottom: 16, lineHeight: 18, textAlign: "left", writingDirection: "ltr" }}>
          {data.meta}
        </AppText>
      ) : null}

      <View style={{ gap: 16 }}>
        {data.sections.map((section, i) => (
          <SectionBlock key={i} section={section} depth={0} />
        ))}
      </View>
    </Screen>
  );
}

function SectionBlock({ section, depth }: { section: MedscapeSection; depth: number }) {
  if (!section.heading && !section.content && section.children.length === 0) return null;

  return (
    <View style={depth > 0 ? { marginTop: 10 } : undefined}>
      {section.heading ? (
        <AppText
          weight={depth === 0 ? "900" : "800"}
          size={depth === 0 ? 16 : 14}
          style={{ textAlign: "left", writingDirection: "ltr" }}
        >
          {section.heading}
        </AppText>
      ) : null}
      {section.content ? (
        <AppText
          weight="500"
          size={14}
          style={{ lineHeight: 24, marginTop: 6, textAlign: "left", writingDirection: "ltr" }}
        >
          {section.content}
        </AppText>
      ) : null}
      {section.children.length > 0 ? (
        <View style={{ gap: 4, marginTop: 8 }}>
          {section.children.map((child, i) => (
            <SectionBlock key={i} section={child} depth={depth + 1} />
          ))}
        </View>
      ) : null}
    </View>
  );
}
