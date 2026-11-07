import { useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { AppState } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { supportApi } from "@/api/support";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { listenSupportNotifications, refreshSupportNotifications } from "./registration";

export function useSupportSummary() {
  const userId = useAuth(s => s.status === "signedIn" ? s.user?.id : null);
  return useQuery({ queryKey: ["support-summary", userId], queryFn: supportApi.summary, enabled: !!userId, refetchInterval: 30000, retry: false });
}

export function useSupportNotifications() {
  const userId = useAuth(s => s.status === "signedIn" ? s.user?.id : null);
  useSupportSummary();
  useEffect(() => {
    if (!userId) return;
    const restore = async () => {
      if (await AsyncStorage.getItem(`pharmenta.notifications.${userId}`) === "on" && useAuth.getState().user?.id === userId) await refreshSupportNotifications();
    };
    void restore().catch(() => undefined);
    const state = AppState.addEventListener("change", next => { if (next === "active") void restore().catch(() => undefined); });
    const stop = listenSupportNotifications(conversationId => {
      if (useAuth.getState().user?.id === userId) useNav.getState().navigate("support", { conversationId });
    });
    return () => { stop(); state.remove(); };
  }, [userId]);
}
