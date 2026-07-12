import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {createContext, useCallback, useContext, useEffect, useMemo, useState} from "react";

type OnboardingState = {
  completed: boolean;
  loading: boolean;
  completeOnboarding: () => Promise<void>;
  resetOnboarding: () => Promise<void>;
};

const ONBOARDING_KEY = "pharmexa_onboarding_complete";
const OnboardingContext = createContext<OnboardingState | undefined>(undefined);

export function OnboardingProvider({children}: {children: React.ReactNode}) {
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const value = await AsyncStorage.getItem(ONBOARDING_KEY);
        if (active) setCompleted(value === "true");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const completeOnboarding = useCallback(async () => {
    await AsyncStorage.setItem(ONBOARDING_KEY, "true");
    setCompleted(true);
  }, []);

  const resetOnboarding = useCallback(async () => {
    await AsyncStorage.removeItem(ONBOARDING_KEY);
    setCompleted(false);
  }, []);

  const value = useMemo(
    () => ({completed, loading, completeOnboarding, resetOnboarding}),
    [completed, loading, completeOnboarding, resetOnboarding],
  );

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) throw new Error("useOnboarding must be used within OnboardingProvider.");
  return context;
}
