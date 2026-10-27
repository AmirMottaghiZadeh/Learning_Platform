import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { AppState, Linking, Modal, Platform, Pressable, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { releaseApi } from "@/api/endpoints";
import { AppReleaseInfo } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { IconImage } from "@/components/primitives/IconImage";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { useTheme } from "@/theme/ThemeProvider";
import { APP_VERSION, versionCodeOf } from "@/utils/appVersion";

// "Later" on an optional update quiets that version for a day.
const DISMISS_KEY = "pharmexa.updateDismissed";
const DISMISS_MS = 24 * 60 * 60 * 1000;
// Coming back to the app checks again, at most this often.
const RECHECK_MS = 30 * 60 * 1000;

type Offer = { release: AppReleaseInfo; required: boolean };

async function dismissedRecently(version: string): Promise<boolean> {
  try {
    const saved = JSON.parse((await AsyncStorage.getItem(DISMISS_KEY)) ?? "null");
    return saved?.version === version && Date.now() - saved.at < DISMISS_MS;
  } catch {
    return false;
  }
}

/** Mounted once at the app root on the phone: asks the server whether a
 * newer version is out -- a release entered in the site panel with «پیشنهاد
 * به‌روزرسانی در اپ» -- on opening and on coming back to the app. An
 * optional update is a sheet the learner can put off for a day; a required
 * one -- this version is below the minimum supported -- covers the app until
 * it is updated. The button opens the site's download page, which links
 * every store and the APK. */
export function UpdatePrompt() {
  const [offer, setOffer] = useState<Offer | null>(null);
  const lastCheck = useRef(0);

  const check = useCallback(async () => {
    if (Date.now() - lastCheck.current < RECHECK_MS) return;
    lastCheck.current = Date.now();
    try {
      const result = await releaseApi.check(Platform.OS === "ios" ? "ios" : "android", versionCodeOf(APP_VERSION));
      if (!result.latest || result.update === "none") return setOffer(null);
      const required = result.update === "required";
      if (!required && (await dismissedRecently(result.latest.version))) return;
      setOffer({ release: result.latest, required });
    } catch {
      // Offline or the server is down: ask again next time.
      lastCheck.current = 0;
    }
  }, []);

  useEffect(() => {
    void check();
    const sub = AppState.addEventListener("change", (state) => {
      if (state === "active") void check();
    });
    return () => sub.remove();
  }, [check]);

  const later = useCallback(() => {
    if (!offer) return;
    AsyncStorage.setItem(DISMISS_KEY, JSON.stringify({ version: offer.release.version, at: Date.now() })).catch(
      () => undefined,
    );
    setOffer(null);
  }, [offer]);

  if (!offer) return null;
  return offer.required ? <RequiredUpdate release={offer.release} /> : <OptionalUpdate release={offer.release} onLater={later} />;
}

function openRelease(release: AppReleaseInfo) {
  Linking.openURL(release.download_url).catch(() => undefined);
}

function Notes({ release }: { release: AppReleaseInfo }) {
  const { colors } = useTheme();
  const { row } = useLang();
  if (!release.notes.length) return null;
  return (
    <View style={{ gap: 8 }}>
      {release.notes.map((note, i) => (
        <View key={i} style={{ flexDirection: row, gap: 10, alignItems: "flex-start" }}>
          <View style={{ width: 6, height: 6, borderRadius: 3, marginTop: 7, backgroundColor: colors.accent }} />
          <AppText weight="600" size={13} muted style={{ flex: 1, lineHeight: 21 }}>
            {note}
          </AppText>
        </View>
      ))}
    </View>
  );
}

function OptionalUpdate({ release, onLater }: { release: AppReleaseInfo; onLater: () => void }) {
  const { colors } = useTheme();
  const { t } = useLang();
  const insets = useSafeAreaInsets();
  useBackInterceptor(true, onLater);

  return (
    <Modal transparent animationType="slide" visible onRequestClose={onLater}>
      <Pressable
        onPress={onLater}
        accessibilityLabel={t("dismiss")}
        style={{ flex: 1, backgroundColor: "rgba(4,10,9,0.35)", justifyContent: "flex-end" }}
      >
        <Pressable
          style={{
            backgroundColor: colors.cardBg,
            borderTopLeftRadius: 24,
            borderTopRightRadius: 24,
            padding: 22,
            paddingBottom: Math.max(22, insets.bottom + 12),
            gap: 16,
          }}
        >
          <View
            style={{ width: 40, height: 4, borderRadius: 2, backgroundColor: colors.trackBg, alignSelf: "center" }}
          />
          <View style={{ gap: 4 }}>
            <AppText weight="800" size={17}>
              {t("updateTitle")}
            </AppText>
            <AppText weight="600" size={13} muted>
              {t("updateOptional").replace("{v}", release.version)}
            </AppText>
          </View>
          <Notes release={release} />
          <View style={{ gap: 8 }}>
            <Button label={t("updateNow")} onPress={() => openRelease(release)} />
            <Button label={t("updateLater")} variant="ghost" onPress={onLater} />
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

function RequiredUpdate({ release }: { release: AppReleaseInfo }) {
  const { colors } = useTheme();
  const { t } = useLang();
  const insets = useSafeAreaInsets();
  return (
    // Back does nothing here: the app stays covered until it is updated.
    <Modal animationType="fade" visible onRequestClose={() => undefined}>
      <View
        style={{
          flex: 1,
          backgroundColor: colors.appBg,
          paddingTop: insets.top + 48,
          paddingBottom: Math.max(24, insets.bottom + 16),
          paddingHorizontal: 24,
          gap: 24,
        }}
      >
        <View style={{ flex: 1, justifyContent: "center", gap: 20 }}>
          <IconImage name="app-logo" size={80} style={{ alignSelf: "center" }} />
          <View style={{ gap: 8 }}>
            <AppText weight="800" size={20} center>
              {t("updateTitle")}
            </AppText>
            <AppText weight="600" size={14} muted center style={{ lineHeight: 23 }}>
              {t("updateRequired").replace("{v}", release.version)}
            </AppText>
          </View>
          <Notes release={release} />
        </View>
        <Button label={t("updateNow")} onPress={() => openRelease(release)} />
      </View>
    </Modal>
  );
}
