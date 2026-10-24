import React, { useState } from "react";
import { Modal, Pressable, View } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";

import { OfflineDataset } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { SUPPORTS_BACKGROUND } from "@/offline/downloader";
import { useOffline } from "@/offline/store";
import { usePackageView } from "@/offline/view";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

import { OfflinePackageCard } from "./OfflinePackageCard";

/** The small round button in the UpToDate / Lexicomp header: shows whether
 * the package is on the device (or how far its download is), and opens a
 * sheet to download or manage it. */
export function OfflineDownloadButton({ dataset, size = 34 }: { dataset: OfflineDataset; size?: number }) {
  const { colors, shadows } = useTheme();
  const { t } = useLang();
  const view = usePackageView(dataset);
  const [open, setOpen] = useState(false);

  if (view.phase === "unpublished") return null;

  const icon = 16;
  const ring = size - 4;
  const r = (ring - 3) / 2;
  const circumference = 2 * Math.PI * r;
  const active = view.phase === "downloading" || view.phase === "verifying" || view.phase === "paused";
  const warn = view.phase === "locked" || view.phase === "expired" || view.phase === "error";
  const ready = view.phase === "ready";

  return (
    <>
      <Pressable
        onPress={() => setOpen(true)}
        accessibilityRole="button"
        accessibilityLabel={t("offlineButtonLabel")}
        hitSlop={6}
        style={[
          {
            width: size,
            height: size,
            borderRadius: size / 2,
            backgroundColor: ready ? colors.accent : colors.softBg,
            alignItems: "center",
            justifyContent: "center",
          },
          shadows.raisedSm,
        ]}
      >
        {active ? (
          <Svg width={ring} height={ring} style={{ position: "absolute", transform: [{ rotate: "-90deg" }] }}>
            <Circle cx={ring / 2} cy={ring / 2} r={r} stroke={colors.trackBg} strokeWidth={3} fill="none" />
            <Circle
              cx={ring / 2}
              cy={ring / 2}
              r={r}
              stroke={colors.accent}
              strokeWidth={3}
              fill="none"
              strokeLinecap="round"
              strokeDasharray={`${circumference} ${circumference}`}
              strokeDashoffset={circumference * (1 - Math.max(0.03, view.progress))}
            />
          </Svg>
        ) : null}
        <Svg width={icon} height={icon} viewBox="0 0 24 24" fill="none">
          {ready ? (
            <Path d="M5 12.5l4.5 4.5L19 7.5" stroke={colors.onAccent} strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" />
          ) : view.phase === "paused" ? (
            <Path d="M9 6v12M15 6v12" stroke={colors.accent} strokeWidth={2.6} strokeLinecap="round" />
          ) : warn ? (
            <Path d="M12 7v6M12 17.2v.3" stroke={colors.denyLabel} strokeWidth={2.6} strokeLinecap="round" />
          ) : (
            <Path
              d="M12 4v11M7 10.5l5 5 5-5M5 20h14"
              stroke={colors.accent}
              strokeWidth={2.4}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}
        </Svg>
        {view.updateAvailable ? (
          <View
            style={{
              position: "absolute",
              top: 0,
              right: 0,
              width: 10,
              height: 10,
              borderRadius: 5,
              backgroundColor: "#E8785D",
              borderWidth: 2,
              borderColor: colors.cardBg,
            }}
          />
        ) : null}
      </Pressable>
      {open ? <OfflineSheet dataset={dataset} onClose={() => setOpen(false)} /> : null}
    </>
  );
}

function OfflineSheet({ dataset, onClose }: { dataset: OfflineDataset; onClose: () => void }) {
  const { colors } = useTheme();
  const { t } = useLang();
  const navigate = useNav((s) => s.navigate);
  const wifiOnly = useOffline((s) => s.wifiOnly);
  useBackInterceptor(true, onClose);

  return (
    <Modal transparent animationType="slide" visible onRequestClose={onClose}>
      <Pressable onPress={onClose} style={{ flex: 1, backgroundColor: "rgba(4,10,9,0.35)", justifyContent: "flex-end" }}>
        <Pressable
          style={{
            backgroundColor: colors.cardBg,
            borderTopLeftRadius: 24,
            borderTopRightRadius: 24,
            padding: 22,
            paddingBottom: 34,
            gap: 16,
          }}
        >
          <View style={{ width: 40, height: 4, borderRadius: 2, backgroundColor: colors.trackBg, alignSelf: "center" }} />
          <OfflinePackageCard dataset={dataset} />
          <AppText muted weight="600" size={11} style={{ lineHeight: 18 }}>
            {t(SUPPORTS_BACKGROUND ? "offlineBackgroundNote" : "offlineWebNote")}
            {SUPPORTS_BACKGROUND && wifiOnly ? ` ${t("offlineWifiOnlySub")}` : ""}
          </AppText>
          <Pressable
            onPress={() => {
              onClose();
              navigate("downloads");
            }}
            style={{ alignSelf: "center", paddingVertical: 6, paddingHorizontal: 12 }}
          >
            <AppText weight="800" size={13} color={colors.accent}>
              {t("offlineManage")}
            </AppText>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}
