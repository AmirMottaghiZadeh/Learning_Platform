import { useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { AppState } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { supportApi } from "@/api/support";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";

export function useSupportSummary() {
  const userId = useAuth(s => s.status === "signedIn" ? s.user?.id : null);
  return useQuery({ queryKey: ["support-summary", userId], queryFn: supportApi.summary, enabled: !!userId, refetchInterval: 30000, retry: false });
}

export function useSupportNotifications() {
  const userId = useAuth(s => s.status === "signedIn" ? s.user?.id : null);
  const { data } = useSupportSummary();
  const enabled = data?.push_enabled === true;
  useEffect(() => {
    if (!userId || !enabled) return;
    let disposed = false;
    let cleanup = () => undefined as void;
    const restore = async () => {
      if (await AsyncStorage.getItem(`pharmenta.notifications.${userId}`) === "on" && !disposed && useAuth.getState().user?.id === userId) {
        const registration = await import("./registration");
        if (!disposed) await registration.refreshSupportNotifications();
      }
    };
    void restore().catch(() => undefined);
    const state = AppState.addEventListener("change", next => { if (next === "active") void restore().catch(() => undefined); });
    void import("./registration").then(registration => {
      if (disposed) return;
      cleanup = registration.listenSupportNotifications(conversationId => {
        if (useAuth.getState().user?.id === userId) useNav.getState().navigate("support", { conversationId });
      });
    }).catch(() => undefined);
    return () => { disposed = true; cleanup(); state.remove(); };
  }, [userId, enabled]);
}
