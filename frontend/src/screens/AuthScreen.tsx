import React, {useState} from "react";
import {Pressable, StyleSheet, Text, TextInput, View} from "react-native";
import {LogIn, UserPlus} from "lucide-react-native";

import {API_BASE_URL} from "../api/client";
import {LearningCard, PrimaryButton} from "../components/ui";
import {colors, radius, spacing, typography} from "../design/tokens";
import {useAuth} from "../store/auth";

export function AuthScreen() {
  const {signIn, register, loading, error} = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function submit() {
    setLocalError(null);
    if (!username.trim() || !password.trim()) {
      setLocalError("Username and password are required.");
      return;
    }
    try {
      if (mode === "login") {
        await signIn(username.trim(), password);
      } else {
        await register(username.trim(), email.trim(), password);
      }
    } catch {
      // AuthProvider exposes the message.
    }
  }

  return (
    <View style={styles.root}>
      <View style={styles.brand}>
        <Text style={styles.brandMark}>K</Text>
        <View>
          <Text style={styles.brandTitle}>K_Game</Text>
          <Text style={styles.brandSubtitle}>Learning Platform</Text>
        </View>
      </View>

      <LearningCard tone="primary">
        <View style={styles.segment}>
          <Pressable
            accessibilityRole="button"
            onPress={() => setMode("login")}
            style={[styles.segmentItem, mode === "login" && styles.segmentActive]}
          >
            <Text style={[styles.segmentText, mode === "login" && styles.segmentTextActive]}>Login</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => setMode("register")}
            style={[styles.segmentItem, mode === "register" && styles.segmentActive]}
          >
            <Text style={[styles.segmentText, mode === "register" && styles.segmentTextActive]}>Register</Text>
          </Pressable>
        </View>

        <TextInput
          autoCapitalize="none"
          value={username}
          onChangeText={setUsername}
          placeholder="Username"
          placeholderTextColor={colors.softText}
          style={styles.input}
        />
        {mode === "register" ? (
          <TextInput
            autoCapitalize="none"
            keyboardType="email-address"
            value={email}
            onChangeText={setEmail}
            placeholder="Email"
            placeholderTextColor={colors.softText}
            style={styles.input}
          />
        ) : null}
        <TextInput
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          placeholder="Password"
          placeholderTextColor={colors.softText}
          style={styles.input}
        />

        {localError || error ? <Text style={styles.error}>{localError ?? error}</Text> : null}

        <PrimaryButton
          label={mode === "login" ? "Login" : "Create account"}
          Icon={mode === "login" ? LogIn : UserPlus}
          onPress={submit}
          disabled={loading}
        />
      </LearningCard>

      <Text style={styles.apiText}>{API_BASE_URL}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
    justifyContent: "center",
  },
  brand: {
    width: "100%",
    maxWidth: 520,
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.xl,
  },
  brandMark: {
    width: 58,
    height: 58,
    borderRadius: radius.md,
    backgroundColor: colors.primary,
    color: "#FFFFFF",
    fontSize: 34,
    fontWeight: "900",
    textAlign: "center",
    lineHeight: 58,
    marginRight: spacing.md,
  },
  brandTitle: {
    color: colors.ink,
    fontSize: typography.title,
    fontWeight: "900",
  },
  brandSubtitle: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: "700",
  },
  segment: {
    minHeight: 46,
    flexDirection: "row",
    backgroundColor: colors.surface,
    borderRadius: radius.pill,
    padding: spacing.xs,
    marginBottom: spacing.lg,
  },
  segmentItem: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.pill,
  },
  segmentActive: {
    backgroundColor: colors.primary,
  },
  segmentText: {
    color: colors.muted,
    fontWeight: "900",
  },
  segmentTextActive: {
    color: "#FFFFFF",
  },
  input: {
    minHeight: 50,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "700",
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.md,
  },
  error: {
    color: colors.danger,
    fontWeight: "800",
    marginBottom: spacing.md,
  },
  apiText: {
    color: colors.softText,
    fontSize: typography.small,
    textAlign: "center",
    marginTop: spacing.md,
  },
});
