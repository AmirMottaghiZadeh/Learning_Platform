import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Modal, Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { siteApi } from "@/api/endpoints";
import { AppText } from "@/components/primitives/AppText";
import { LoadingState } from "@/components/primitives/LoadingState";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";
import { parseAboutHtml } from "@/utils/html";

export type LegalSlug = "terms" | "privacy";

/** The page's <h2> headings as bold paragraphs: parseAboutHtml splits on
 * paragraphs, and reads a paragraph that is only bold text as a heading. */
function headingsAsBold(html: string) {
  return html.replace(/<h[1-6][^>]*>([\s\S]*?)<\/h[1-6]>/gi, "<p><strong>$1</strong></p>");
}

/** The terms or the privacy page, full screen over the sign-up form. The
 * text is the site's page (edited in the panel), read from the API. */
export function LegalSheet({ slug, onClose }: { slug: LegalSlug | null; onClose: () => void }) {
  const { colors } = useTheme();
  const { t, isFa, row } = useLang();
  const insets = useSafeAreaInsets();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["legal-page", slug],
    queryFn: () => siteApi.legal(slug as LegalSlug),
    enabled: slug !== null,
  });
  const dir = { writingDirection: isFa ? ("rtl" as const) : ("ltr" as const), textAlign: isFa ? ("right" as const) : ("left" as const) };

  return (
    <Modal visible={slug !== null} animationType="slide" onRequestClose={onClose}>
      <View style={{ flex: 1, backgroundColor: colors.appBg, paddingTop: insets.top }}>
        <View
          style={{
            flexDirection: row,
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            paddingHorizontal: 20,
            paddingVertical: 14,
            borderBottomWidth: 1,
            borderBottomColor: colors.border,
          }}
        >
          <AppText weight="900" size={17} style={{ flex: 1, ...dir }}>
            {data?.title ?? ""}
          </AppText>
          <Pressable
            onPress={onClose}
            hitSlop={8}
            style={{ paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.softBg }}
          >
            <AppText weight="800" size={13} color={colors.accent}>
              {t("legalClose")}
            </AppText>
          </Pressable>
        </View>
        {isLoading ? (
          <LoadingState />
        ) : isError || !data ? (
          <AppText weight="700" size={13} muted center style={{ marginTop: 40 }}>
            {t("loadFailed")}
          </AppText>
        ) : (
          <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: insets.bottom + 32, gap: 10 }}>
            {parseAboutHtml(headingsAsBold(data.body_html)).map((block, i) =>
              block.kind === "heading" ? (
                <AppText key={i} weight="800" size={15} style={{ marginTop: 6, ...dir }}>
                  {block.text}
                </AppText>
              ) : (
                <View key={i} style={{ flexDirection: row, gap: 8 }}>
                  {block.kind === "listItem" ? (
                    <AppText weight="700" size={14} color={colors.accent}>
                      •
                    </AppText>
                  ) : null}
                  <AppText weight="500" size={14} style={{ flex: 1, lineHeight: 24, ...dir }}>
                    {block.label ? <AppText weight="800" size={14}>{`${block.label}: `}</AppText> : null}
                    {block.text}
                  </AppText>
                </View>
              ),
            )}
          </ScrollView>
        )}
      </View>
    </Modal>
  );
}
