import React, { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, View } from "react-native";

import { OfflineDataset } from "@/api/types";
import { AppText } from "@/components/primitives/AppText";
import { IconImage } from "@/components/primitives/IconImage";
import { useLang } from "@/i18n/LanguageProvider";
import { StringKey } from "@/i18n/strings";
import { OfflineError, OfflineErrorCode, cancel, download, pause, remove, renewLicense, resume } from "@/offline/store";
import { PackagePhase, formatBytes, formatDay, sourceVersion, usePackageView } from "@/offline/view";
import { useTheme } from "@/theme/ThemeProvider";

const NAME: Record<OfflineDataset, StringKey> = { uptodate: "offlineNameUptodate", lexicomp: "offlineNameLexicomp" };
const LOGO = { uptodate: "uptodate-logo", lexicomp: "lexicomp-logo" } as const;

const PHASE_TEXT: Record<PackagePhase, StringKey> = {
  none: "offlineStatusNone",
  unpublished: "offlineStatusUnpublished",
  downloading: "offlineStatusDownloading",
  paused: "offlineStatusPaused",
  verifying: "offlineStatusVerifying",
  error: "offlineStatusError",
  ready: "offlineStatusReady",
  locked: "offlineStatusLocked",
  expired: "offlineStatusExpired",
};

const ERROR_TEXT: Record<OfflineErrorCode, StringKey> = {
  not_entitled: "offlineErrNotEntitled",
  not_published: "offlineErrNotPublished",
  no_space: "offlineErrNoSpace",
  network: "offlineErrNetwork",
  damaged: "offlineErrDamaged",
  failed: "offlineErrFailed",
};

/** One offline package: what is on the device, the download in progress,
 * and the actions that apply. Used in the download sheet of the UpToDate /
 * Lexicomp screens and on the downloads screen. */
export function OfflinePackageCard({ dataset }: { dataset: OfflineDataset }) {
  const { t, n, row, isFa } = useLang();
  const { colors } = useTheme();
  const view = usePackageView(dataset);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<OfflineErrorCode | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!confirmDelete) return;
    const timer = setTimeout(() => setConfirmDelete(false), 4000);
    return () => clearTimeout(timer);
  }, [confirmDelete]);

  const run = (action: () => Promise<void>) => async () => {
    setBusy(true);
    setFailure(null);
    try {
      await action();
    } catch (error) {
      setFailure(error instanceof OfflineError ? error.code : "failed");
    } finally {
      setBusy(false);
    }
  };

  const { phase, installed, pending, remote } = view;
  const tone =
    phase === "ready"
      ? colors.accent
      : phase === "locked" || phase === "expired" || phase === "error"
        ? colors.denyLabel
        : phase === "downloading" || phase === "verifying"
          ? colors.accent2
          : colors.muted;
  const shownError = failure ?? view.error;
  const manifest = pending?.manifest ?? installed?.manifest ?? remote?.package ?? null;
  const notEntitled = remote && !remote.entitled && !installed;

  const actions: { label: StringKey; onPress: () => void; primary?: boolean; danger?: boolean }[] = [];
  if (phase === "downloading") {
    actions.push({ label: "offlinePause", onPress: run(() => pause(dataset)) });
    actions.push({ label: "offlineCancel", onPress: run(() => cancel(dataset)) });
  } else if (phase === "paused" || phase === "error") {
    actions.push({ label: "offlineResume", onPress: run(() => resume(dataset)), primary: true });
    actions.push({ label: "offlineCancel", onPress: run(() => cancel(dataset)) });
  } else if (phase === "none") {
    if (!notEntitled) actions.push({ label: "offlineDownload", onPress: run(() => download(dataset)), primary: true });
  } else if (phase === "ready" || phase === "locked" || phase === "expired") {
    if (view.updateAvailable && phase === "ready") {
      actions.push({ label: "offlineUpdate", onPress: run(() => download(dataset)), primary: true });
    }
    if (phase !== "ready") {
      actions.push({ label: "offlineRecheck", onPress: run(() => renewLicense(dataset, { force: true })), primary: true });
    }
    actions.push({
      label: confirmDelete ? "offlineDeleteConfirm" : "offlineDelete",
      danger: true,
      onPress: confirmDelete ? run(() => remove(dataset)) : () => setConfirmDelete(true),
    });
  }

  const facts: [StringKey, string][] = [];
  if (manifest) facts.push(["offlineSize", formatBytes(manifest.total_size, n, isFa)]);
  // Separate rows: a number and a date on one RTL line come out jumbled.
  if (manifest) facts.push(["offlineVersion", formatDay(Date.parse(manifest.created_at), n, isFa)]);
  if (manifest && sourceVersion(manifest)) facts.push(["offlineSourceVersion", n(sourceVersion(manifest))]);
  if (view.validUntil && phase !== "locked") facts.push(["offlineValidUntil", formatDay(view.validUntil, n, isFa)]);

  return (
    <View style={{ gap: 12 }}>
      <View style={{ flexDirection: row, alignItems: "center", gap: 12 }}>
        <IconImage name={LOGO[dataset]} size={36} />
        <View style={{ flex: 1, gap: 2 }}>
          <AppText weight="800" size={15}>
            {t(NAME[dataset])}
          </AppText>
          <AppText weight="700" size={12} color={tone}>
            {t(PHASE_TEXT[phase])}
            {phase === "downloading" || phase === "paused"
              ? ` · ${n(Math.floor(view.progress * 100))}${isFa ? "٪" : "%"}`
              : ""}
          </AppText>
        </View>
        {busy || phase === "verifying" ? <ActivityIndicator color={colors.accent} /> : null}
      </View>

      {pending ? (
        <View style={{ gap: 6 }}>
          <View style={{ height: 8, borderRadius: 4, backgroundColor: colors.trackBg, overflow: "hidden" }}>
            <View
              style={{
                width: `${Math.min(100, Math.max(2, view.progress * 100))}%`,
                height: "100%",
                borderRadius: 4,
                backgroundColor: phase === "error" ? colors.denyLabel : colors.accent,
              }}
            />
          </View>
          <AppText muted weight="600" size={11}>
            {formatBytes(view.received, n, isFa)} / {formatBytes(view.total, n, isFa)}
          </AppText>
        </View>
      ) : null}

      {view.updateAvailable ? (
        <AppText weight="700" size={12} color={colors.accent2}>
          {t("offlineUpdateAvailable")}
        </AppText>
      ) : null}

      {facts.length ? (
        <View style={{ gap: 4 }}>
          {facts.map(([label, value]) => (
            <View key={label} style={{ flexDirection: row, justifyContent: "space-between", gap: 10 }}>
              <AppText muted weight="600" size={12}>
                {t(label)}
              </AppText>
              <AppText weight="700" size={12}>
                {value}
              </AppText>
            </View>
          ))}
        </View>
      ) : null}

      {notEntitled ? (
        <AppText weight="600" size={12} color={colors.cautInk}>
          {t("offlinePaidOnly")}
        </AppText>
      ) : null}
      {shownError ? (
        <AppText weight="700" size={12} color={colors.denyLabel}>
          {t(ERROR_TEXT[shownError])}
        </AppText>
      ) : null}

      {actions.length ? (
        <View style={{ flexDirection: row, gap: 8, flexWrap: "wrap" }}>
          {actions.map((a) => (
            <Pressable
              key={a.label}
              onPress={busy ? undefined : a.onPress}
              style={({ pressed }) => ({
                flexGrow: 1,
                minWidth: 110,
                height: 42,
                borderRadius: 12,
                alignItems: "center",
                justifyContent: "center",
                paddingHorizontal: 14,
                backgroundColor: a.primary ? colors.accent : a.danger ? colors.denyBg : colors.softBg,
                borderWidth: a.primary ? 0 : 1,
                borderColor: a.danger ? colors.denyBorder : colors.trackBg,
                opacity: busy ? 0.6 : 1,
                transform: [{ scale: pressed ? 0.98 : 1 }],
              })}
            >
              <AppText weight="800" size={13} color={a.primary ? colors.onAccent : a.danger ? colors.denyLabel : colors.ink}>
                {t(a.label)}
              </AppText>
            </Pressable>
          ))}
        </View>
      ) : null}
    </View>
  );
}
