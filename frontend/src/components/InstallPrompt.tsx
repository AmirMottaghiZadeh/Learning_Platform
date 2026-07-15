import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {useEffect, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {Download, Share2, Smartphone, X} from "lucide-react-native";

import {colors, radius, spacing, typography} from "../design/tokens";
import {PrimaryButton, SecondaryButton} from "./ui";

const INSTALL_GUIDE_HIDDEN_KEY = "pharmexa_install_guide_hidden";

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
  const [hideForever, setHideForever] = useState(false);
  const [loadedPreference, setLoadedPreference] = useState(false);
  const [showDismissChoice, setShowDismissChoice] = useState(false);
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

  useEffect(() => {
    let active = true;
    async function loadPreference() {
      try {
        const stored = await AsyncStorage.getItem(INSTALL_GUIDE_HIDDEN_KEY);
        if (active) setHideForever(stored === "true");
      } finally {
        if (active) setLoadedPreference(true);
      }
    }
    loadPreference();
    return () => {
      active = false;
    };
  }, []);

  if (!loadedPreference || dismissed || standalone || hideForever) return null;

  async function install() {
    if (deferredPrompt) {
      await deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      setDeferredPrompt(null);
    }
    setShowDismissChoice(true);
  }

  async function share() {
    if (typeof navigator !== "undefined" && "share" in navigator) {
      try {
        await navigator.share({
          title: "Pharmexa",
          text: "Pharmexa را برای یادگیری داروشناسی باز کن.",
          url: typeof window !== "undefined" ? window.location.href : undefined,
        });
      } catch {
        // کاربر ممکن است اشتراک‌گذاری را لغو کند.
      }
    }
    setShowDismissChoice(true);
  }

  async function dismissForever() {
    await AsyncStorage.setItem(INSTALL_GUIDE_HIDDEN_KEY, "true");
    setHideForever(true);
    setDismissed(true);
  }

  return (
    <View style={styles.card}>
      <View style={styles.top}>
        <View style={styles.iconWrap}>
          <Smartphone size={20} color={colors.primary} />
        </View>
        <View style={styles.copy}>
          <Text style={styles.title}>Pharmexa را مثل اپ نصب کن</Text>
          <Text style={styles.text}>
            در آیفون: اشتراک‌گذاری ← افزودن به صفحه اصلی. در دسکتاپ یا اندروید از دکمه نصب استفاده کن.
          </Text>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel="بستن راهنمای نصب" onPress={() => setShowDismissChoice(true)}>
          <X size={18} color="#64748B" />
        </Pressable>
      </View>
      <View style={styles.steps}>
        <Pressable accessibilityRole="button" onPress={share} style={styles.step}>
          <Share2 size={16} color="#0F172A" />
          <Text style={styles.stepText}>اشتراک‌گذاری</Text>
        </Pressable>
        <View style={styles.step}>
          <Smartphone size={16} color="#0F172A" />
          <Text style={styles.stepText}>نصب</Text>
        </View>
        <View style={styles.step}>
          <Download size={16} color="#0F172A" />
          <Text style={styles.stepText}>اجرای مستقل</Text>
        </View>
      </View>
      <PrimaryButton label="نصب" Icon={Download} onPress={install} />
      <View style={styles.secondaryAction}>
        <SecondaryButton label="بعداً نصب می‌کنم" onPress={() => setShowDismissChoice(true)} />
      </View>
      {showDismissChoice ? (
        <View style={styles.dismissChoice}>
          <Text style={styles.dismissTitle}>راهنمای نصب دوباره نمایش داده شود؟</Text>
          <View style={styles.dismissActions}>
            <SecondaryButton label="دیگر نشان نده" onPress={dismissForever} />
            <PrimaryButton label="بستن" onPress={() => setDismissed(true)} />
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.xl,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#D9E5E7",
    padding: spacing.lg,
    marginBottom: spacing.md,
    shadowColor: "#17343A",
    shadowOpacity: 0.12,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 10 },
    elevation: 3,
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
    backgroundColor: "#E7F8F5",
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  copy: {
    flex: 1,
    paddingRight: spacing.sm,
  },
  title: {
    color: "#0F172A",
    fontSize: typography.body,
    fontWeight: "900",
  },
  text: {
    color: "#475569",
    fontWeight: "600",
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
    backgroundColor: "#EAF8F7",
    borderWidth: 1,
    borderColor: "#D6ECE8",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.sm,
  },
  stepText: {
    color: "#0F172A",
    fontSize: typography.small,
    fontWeight: "800",
    marginTop: spacing.xs,
    textAlign: "center",
  },
  secondaryAction: {
    marginTop: spacing.sm,
  },
  dismissChoice: {
    marginTop: spacing.md,
    borderRadius: radius.lg,
    backgroundColor: "#F8FAFC",
    borderWidth: 1,
    borderColor: "#D9E5E7",
    padding: spacing.md,
  },
  dismissTitle: {
    color: "#0F172A",
    fontWeight: "900",
    textAlign: "center",
    marginBottom: spacing.sm,
  },
  dismissActions: {
    gap: spacing.sm,
  },
});
