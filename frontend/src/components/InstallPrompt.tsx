import React, {useEffect, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {Download, Share2, Smartphone, X} from "lucide-react-native";

import {colors, radius, spacing, typography} from "../design/tokens";
import {PrimaryButton, SecondaryButton} from "./ui";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{outcome: "accepted" | "dismissed"; platform: string}>;
};

function isStandaloneDisplay() {
  if (typeof window === "undefined") return false;
  const navigatorStandalone = (window.navigator as typeof window.navigator & {standalone?: boolean}).standalone;
  return window.matchMedia?.("(display-mode: standalone)").matches || Boolean(navigatorStandalone);
}

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [standalone, setStandalone] = useState(isStandaloneDisplay);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    function handleBeforeInstallPrompt(event: Event) {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
    }

    function handleInstalled() {
      setStandalone(true);
      setDeferredPrompt(null);
    }

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, []);

  if (dismissed || standalone) return null;

  async function install() {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
  }

  return (
    <View style={styles.card}>
      <View style={styles.top}>
        <View style={styles.iconWrap}>
          <Smartphone size={20} color={colors.primary} />
        </View>
        <View style={styles.copy}>
          <Text style={styles.title}>Install Pharmexa like an app</Text>
          <Text style={styles.text}>
            For iPhone: Share → Add to Home Screen. On desktop or Android, use the install button when it appears.
          </Text>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel="Dismiss install guide" onPress={() => setDismissed(true)}>
          <X size={18} color={colors.muted} />
        </Pressable>
      </View>
      <View style={styles.steps}>
        <View style={styles.step}>
          <Share2 size={16} color={colors.ink} />
          <Text style={styles.stepText}>Share</Text>
        </View>
        <View style={styles.step}>
          <Smartphone size={16} color={colors.ink} />
          <Text style={styles.stepText}>Add to Home</Text>
        </View>
        <View style={styles.step}>
          <Download size={16} color={colors.ink} />
          <Text style={styles.stepText}>Open standalone</Text>
        </View>
      </View>
      {deferredPrompt ? (
        <PrimaryButton label="Install" Icon={Download} onPress={install} />
      ) : (
        <SecondaryButton label="I’ll install later" onPress={() => setDismissed(true)} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.xl,
    backgroundColor: "rgba(255,255,255,0.94)",
    borderWidth: 1,
    borderColor: colors.primaryMuted,
    padding: spacing.lg,
    marginBottom: spacing.md,
    shadowColor: "#17343A",
    shadowOpacity: 0.08,
    shadowRadius: 24,
    shadowOffset: {width: 0, height: 10},
    elevation: 2,
  },
  top: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: spacing.md,
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  copy: {
    flex: 1,
    paddingRight: spacing.sm,
  },
  title: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "900",
  },
  text: {
    color: colors.muted,
    fontWeight: "700",
    lineHeight: 20,
    marginTop: spacing.xs,
  },
  steps: {
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  step: {
    flex: 1,
    minHeight: 54,
    borderRadius: radius.lg,
    backgroundColor: colors.primarySoft,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.sm,
  },
  stepText: {
    color: colors.ink,
    fontSize: typography.small,
    fontWeight: "900",
    marginTop: spacing.xs,
    textAlign: "center",
  },
});
