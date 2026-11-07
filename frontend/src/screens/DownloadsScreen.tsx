import React, { useEffect, useState } from "react";
import { Switch, View } from "react-native";

import { ScreenChrome } from "@/components/ScreenChrome";
import { OfflinePackageCard } from "@/components/offline/OfflinePackageCard";
import { AppText } from "@/components/primitives/AppText";
import { Card } from "@/components/primitives/Card";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { SUPPORTS_BACKGROUND } from "@/offline/downloader";
import { freeBytes } from "@/offline/files";
import { DATASETS, pendingBytes, refreshRemote, setWifiOnly, useOffline } from "@/offline/store";
import { formatBytes } from "@/offline/view";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";
import { spacing } from "@/theme/tokens";

/** Profile -> downloads: every offline package on the device, its download,
 * license and the space it takes, plus the Wi-Fi-only setting. */
export function DownloadsScreen() {
  const { t, n, row, isFa } = useLang();
  const { colors } = useTheme();
  const goBack = useNav((s) => s.goBack);
  const datasets = useOffline((s) => s.datasets);
  const wifiOnly = useOffline((s) => s.wifiOnly);
  const [free, setFree] = useState<number | null>(null);

  useEffect(() => {
    refreshRemote().catch(() => undefined);
  }, []);

  const used = DATASETS.reduce((sum, d) => {
    const { installed, pending } = datasets[d];
    const pendingOnDisk = pending && pending.manifest.build !== installed?.manifest.build ? pendingBytes(pending) : 0;
    return sum + (installed?.manifest.total_size ?? 0) + pendingOnDisk;
  }, 0);

  useEffect(() => {
    freeBytes()
      .then(setFree)
      .catch(() => setFree(null));
  }, [used]);

  return (
    <Screen>
      <ScreenChrome title={t("offlineTitle")} onBack={goBack} />
      <AppText muted weight="600" size={12} style={{ marginBottom: spacing.md, lineHeight: 20 }}>
        {t("offlineSub")}
      </AppText>

      <View style={{ gap: spacing.md }}>
        {DATASETS.map((dataset) => (
          <Card key={dataset}>
            <OfflinePackageCard dataset={dataset} />
          </Card>
        ))}

        <Card style={{ gap: 10 }}>
          <View style={{ flexDirection: row, justifyContent: "space-between" }}>
            <AppText muted weight="600" size={12}>
              {t("offlineUsed")}
            </AppText>
            <AppText weight="800" size={12}>
              {formatBytes(used, n, isFa)}
            </AppText>
          </View>
          {free !== null ? (
            <View style={{ flexDirection: row, justifyContent: "space-between" }}>
              <AppText muted weight="600" size={12}>
                {t("offlineFree")}
              </AppText>
              <AppText weight="800" size={12}>
                {formatBytes(free, n, isFa)}
              </AppText>
            </View>
          ) : null}
          {SUPPORTS_BACKGROUND ? (
            <View
              style={{
                flexDirection: row,
                alignItems: "center",
                gap: 12,
                borderTopWidth: 1,
                borderTopColor: colors.trackBg,
                paddingTop: 12,
                marginTop: 2,
              }}
            >
              <View style={{ flex: 1, gap: 2 }}>
                <AppText weight="800" size={13}>
                  {t("offlineWifiOnly")}
                </AppText>
                <AppText muted weight="600" size={11}>
                  {t("offlineWifiOnlySub")}
                </AppText>
              </View>
              <Switch
                value={wifiOnly}
                onValueChange={setWifiOnly}
                trackColor={{ true: colors.accent, false: colors.trackBg }}
                thumbColor="#FFFFFF"
              />
            </View>
          ) : null}
        </Card>

        <AppText muted weight="600" size={11} style={{ lineHeight: 18 }}>
          {t(SUPPORTS_BACKGROUND ? "offlineBackgroundNote" : "offlineWebNote")}
        </AppText>
      </View>
    </Screen>
  );
}
