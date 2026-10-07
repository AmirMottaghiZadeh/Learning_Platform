import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Image, View } from "react-native";

import { medscapeApi } from "@/api/endpoints";
import { MedscapeBlock, MedscapeSection } from "@/api/types";
import { ScreenChrome } from "@/components/ScreenChrome";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

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
  const { colors } = useTheme();
  if (!section.heading && section.blocks.length === 0 && section.children.length === 0) return null;

  const isTitle = depth === 0;
  const isSubtitle = depth === 1;

  let headingStyle;
  if (isTitle) {
    headingStyle = {
      textAlign: "left" as const,
      writingDirection: "ltr" as const,
      paddingBottom: 8,
      marginBottom: 16,
      borderBottomWidth: 2,
      borderBottomColor: colors.accent,
    };
  } else if (isSubtitle) {
    headingStyle = {
      textAlign: "left" as const,
      writingDirection: "ltr" as const,
      lineHeight: 19,
      paddingLeft: 10,
      marginBottom: 8,
      borderLeftWidth: 3,
      borderLeftColor: colors.accent,
    };
  } else {
    // Sub-subtitle (depth >= 2): its own separator, distinct from the
    // title's full-width bottom border and the subtitle's accent-colored
    // left bar -- a soft, pill-shaped background chip that hugs just the
    // heading text.
    headingStyle = {
      textAlign: "left" as const,
      writingDirection: "ltr" as const,
      lineHeight: 18,
      marginBottom: 7,
      alignSelf: "flex-start" as const,
      backgroundColor: colors.accent + "1A",
      paddingHorizontal: 8,
      paddingVertical: 3,
      borderRadius: 6,
    };
  }

  return (
    <View>
      {section.heading ? (
        <AppText
          weight={isTitle ? "900" : isSubtitle ? "800" : "700"}
          size={isTitle ? 16 : isSubtitle ? 14.5 : 13.5}
          color={isSubtitle ? colors.accent : undefined}
          style={headingStyle}
        >
          {section.heading}
        </AppText>
      ) : null}
      {section.blocks.length > 0 ? (
        <View style={{ gap: 10, paddingLeft: isTitle ? 0 : isSubtitle ? 13 : 12 }}>
          {section.blocks.map((block, i) => (
            <BlockView key={i} block={block} />
          ))}
        </View>
      ) : null}
      {section.children.length > 0 ? (
        <View
          style={{
            gap: isTitle ? 20 : 14,
            marginTop: section.blocks.length > 0 ? (isTitle ? 20 : 14) : 0,
            paddingLeft: isTitle ? 0 : isSubtitle ? 13 : 12,
          }}
        >
          {section.children.map((child, i) => (
            <SectionBlock key={i} section={child} depth={depth + 1} />
          ))}
        </View>
      ) : null}
    </View>
  );
}

function BlockView({ block }: { block: MedscapeBlock }) {
  const { colors } = useTheme();

  if (block.type === "paragraph") {
    return (
      <AppText weight="500" size={14} style={{ lineHeight: 24, textAlign: "left", writingDirection: "ltr" }}>
        {block.text}
      </AppText>
    );
  }

  if (block.type === "list") {
    return (
      <View style={{ gap: 6 }}>
        {block.items.map((item, i) => (
          <View key={i} style={{ flexDirection: "row", gap: 8 }}>
            <AppText weight="700" size={14} color={colors.accent}>
              {block.ordered ? `${i + 1}.` : "•"}
            </AppText>
            <AppText
              weight="500"
              size={14}
              style={{ flex: 1, lineHeight: 22, textAlign: "left", writingDirection: "ltr" }}
            >
              {item}
            </AppText>
          </View>
        ))}
      </View>
    );
  }

  if (block.type === "table") {
    return (
      <View
        style={{
          borderWidth: 1,
          borderColor: colors.trackBg,
          borderRadius: 10,
          overflow: "hidden",
        }}
      >
        {block.headers ? <TableRow cells={block.headers} header /> : null}
        {block.rows.map((row, i) => (
          <TableRow key={i} cells={row} striped={i % 2 === 1} />
        ))}
      </View>
    );
  }

  if (block.type === "image") {
    return <ImageBlockView id={block.id} alt={block.alt} caption={block.caption} />;
  }

  return null;
}

function TableRow({ cells, header, striped }: { cells: string[]; header?: boolean; striped?: boolean }) {
  const { colors } = useTheme();
  return (
    <View
      style={{
        flexDirection: "row",
        backgroundColor: header ? colors.softBg : striped ? colors.appBg : colors.cardBg,
        borderTopWidth: header ? 0 : 1,
        borderTopColor: colors.trackBg,
      }}
    >
      {cells.map((cell, i) => (
        <View
          key={i}
          style={{
            flex: 1,
            paddingVertical: 8,
            paddingHorizontal: 10,
            borderLeftWidth: i > 0 ? 1 : 0,
            borderLeftColor: colors.trackBg,
          }}
        >
          <AppText
            weight={header ? "800" : "500"}
            size={12.5}
            style={{ lineHeight: 18, textAlign: "left", writingDirection: "ltr" }}
          >
            {cell}
          </AppText>
        </View>
      ))}
    </View>
  );
}

function ImageBlockView({ id, alt, caption }: { id: number; alt: string; caption: string }) {
  const { colors } = useTheme();
  const { data } = useQuery({
    queryKey: ["medscape-image", id],
    queryFn: () => medscapeApi.image(id),
  });

  return (
    <View style={{ gap: 6 }}>
      <View
        style={{
          height: 220,
          borderRadius: 12,
          backgroundColor: colors.softBg,
          borderWidth: 1,
          borderColor: colors.trackBg,
          overflow: "hidden",
        }}
      >
        {data ? (
          <Image
            source={{ uri: `data:${data.content_type};base64,${data.data_base64}` }}
            accessibilityLabel={alt}
            style={{ width: "100%", height: "100%" }}
            resizeMode="contain"
          />
        ) : null}
      </View>
      {caption ? (
        <AppText muted weight="600" size={11.5} style={{ textAlign: "left", writingDirection: "ltr" }}>
          {caption}
        </AppText>
      ) : null}
    </View>
  );
}
