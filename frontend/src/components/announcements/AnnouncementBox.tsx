import { useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Modal, Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { announcementsApi } from "@/api/endpoints";
import { AnnouncementEvent, AppAnnouncement } from "@/api/types";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useAuth } from "@/store/auth";
import { requestInstall } from "@/pwa/install";
import { usePwaInstall } from "@/pwa/usePwaInstall";
import type { InstallOutcome } from "@/pwa/types";
import { useTourContext } from "@/tour/TourContext";
import { APP_VERSION, versionCodeOf } from "@/utils/appVersion";

import { AnnouncementCard } from "./AnnouncementCard";
import { openButton } from "./links";
import { loadDismissals, rememberDismissal, syncDismissals } from "./dismissals";

export const ANNOUNCEMENTS_KEY = ["announcements"];

/** The admin's announcements on the home, as a card at the top (design
 * form 1). One the learner hasn't seen yet first opens dimmed: the screen
 * behind it darkens so only the card is clear. «بعداً» lifts the shade and
 * leaves the card on the home. An install button only invokes the browser;
 * its separate "Don't show again" action closes the notice for good. */
export function AnnouncementBox() {
  const queryClient = useQueryClient();
  const navigate = useNav((s) => s.navigate);
  const setTab = useNav((s) => s.setTab);
  const tour = useTourContext();
  const userId = useAuth((s) => s.user?.id);
  const install = usePwaInstall();
  const { data, dataUpdatedAt } = useQuery({
    queryKey: [...ANNOUNCEMENTS_KEY, userId, install.environment],
    queryFn: () => announcementsApi.list(versionCodeOf(APP_VERSION), install.environment),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  });

  // closed here, before the server's list catches up
  const [closed, setClosed] = useState<number[]>([]);
  const [saved, setSaved] = useState<{ userId: number; ids: number[] } | null>(null);
  const [installHelp, setInstallHelp] = useState<InstallOutcome | null>(null);
  useEffect(() => {
    if (!userId) return;
    setClosed([]);
    setSpotIds(null);
    offered.current = false;
    reported.current.clear();
    let active = true;
    loadDismissals(userId).then((ids) => { if (active) setSaved({ userId, ids }); });
    return () => { active = false; };
  }, [userId]);
  useEffect(() => { if (userId) void syncDismissals(userId); }, [userId, dataUpdatedAt]);
  const items = useMemo(() => saved?.userId !== userId ? [] : (data ?? []).filter((a) =>
    !closed.includes(a.id) && !saved?.ids.includes(a.id) && (a.button?.kind !== "pwa" || install.environment === "browser")
  ), [data, closed, saved, userId, install.environment]);
  const [index, setIndex] = useState(0);
  const current = items[Math.min(index, Math.max(0, items.length - 1))];

  // The dimmed first showing: the ones not seen when the list came, once
  // the home tour (if it is playing or about to) is done.
  const [spotIds, setSpotIds] = useState<number[] | null>(null);
  const [spotIndex, setSpotIndex] = useState(0);
  const offered = useRef(false);
  const tourBusy = !!tour && (!tour.loaded || !!tour.active || !tour.isSeen("home"));
  useEffect(() => {
    if (offered.current || !data || saved?.userId !== userId || tourBusy) return;
    const fresh = items.filter((a) => !a.seen).map((a) => a.id);
    offered.current = true;
    if (fresh.length) setSpotIds(fresh);
  }, [data, items, saved, userId, tourBusy]);
  const spotItems = useMemo(() => (spotIds ? items.filter((a) => spotIds.includes(a.id)) : []), [items, spotIds]);
  const spotCurrent = spotItems[Math.min(spotIndex, Math.max(0, spotItems.length - 1))];
  useEffect(() => { if (spotIds && !spotItems.length) setSpotIds(null); }, [spotIds, spotItems.length]);

  const reported = useRef(new Set<string>());
  const report = (item: AppAnnouncement, event: AnnouncementEvent) => {
    const key = `${item.id}:${event}`;
    if (reported.current.has(key)) return;
    reported.current.add(key);
    announcementsApi.event(item.id, event).catch(() => reported.current.delete(key));
  };
  // whatever is on screen counts as seen
  const shown = spotCurrent ?? (spotIds ? undefined : current);
  useEffect(() => {
    if (shown && !shown.seen) report(shown, "seen");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shown?.id]);

  const lift = () => {
    setSpotIds(null);
    queryClient.invalidateQueries({ queryKey: ANNOUNCEMENTS_KEY });
  };
  const close = (item: AppAnnouncement) => {
    setClosed((ids) => [...ids, item.id]);
    if (item.button?.kind === "pwa" && userId) {
      void rememberDismissal(userId, item.id).then(() => syncDismissals(userId));
    } else {
      report(item, "dismiss");
    }
    if (spotIds && spotItems.length <= 1) lift();
  };
  const press = (item: AppAnnouncement) => {
    if (!item.button) return;
    if (item.button.kind === "pwa") {
      // Invoke before any network request/await to retain the user gesture.
      const outcome = requestInstall();
      report(item, "click");
      void outcome.then(setInstallHelp);
      return;
    }
    report(item, "click");
    if (item.dismissible) close(item);
    else if (spotIds) lift();
    openButton(item.button, { navigate, setTab });
  };

  if (!items.length) return null;
  return (
    <>
      {current && !spotIds ? (
        <View style={{ marginBottom: 14 }}>
          <AnnouncementCard
            item={current}
            index={items.indexOf(current)}
            total={items.length}
            onPress={() => press(current)}
            installHelp={installHelp}
            installing={install.busy}
            onDismiss={() => close(current)}
            onPage={(step) => setIndex((i) => Math.max(0, Math.min(items.length - 1, i + step)))}
          />
        </View>
      ) : null}
      {spotCurrent ? (
        <Spotlight onLater={lift}>
          <AnnouncementCard
            item={spotCurrent}
            index={spotItems.indexOf(spotCurrent)}
            total={spotItems.length}
            onPress={() => press(spotCurrent)}
            installHelp={installHelp}
            installing={install.busy}
            onDismiss={() => close(spotCurrent)}
            onPage={(step) => setSpotIndex((i) => Math.max(0, Math.min(spotItems.length - 1, i + step)))}
            onLater={lift}
          />
        </Spotlight>
      ) : null}
    </>
  );
}

/** The shade over the whole app with the card clear on top of it. Back and
 * a tap on the shade are «بعداً». */
function Spotlight({ children, onLater }: { children: React.ReactNode; onLater: () => void }) {
  const insets = useSafeAreaInsets();
  const { isFa } = useLang();
  return (
    <Modal transparent visible animationType="fade" statusBarTranslucent onRequestClose={onLater}>
      <View style={{ flex: 1 }} accessibilityViewIsModal>
        <Pressable
          style={[StyleSheet.absoluteFill, { backgroundColor: "rgba(4,10,9,0.62)" }]}
          onPress={onLater}
          accessibilityRole="button"
          accessibilityLabel={isFa ? "بعداً" : "Later"}
        />
        <View
          pointerEvents="box-none"
          style={{ flex: 1, justifyContent: "center", paddingTop: insets.top + 16, paddingBottom: insets.bottom + 16, paddingHorizontal: 20 }}
        >
          <View style={{ width: "100%", maxWidth: 420, alignSelf: "center" }}>{children}</View>
        </View>
      </View>
    </Modal>
  );
}
