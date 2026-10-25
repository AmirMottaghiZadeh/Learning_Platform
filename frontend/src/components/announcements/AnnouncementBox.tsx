import { useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Modal, Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { announcementsApi } from "@/api/endpoints";
import { AnnouncementEvent, AppAnnouncement } from "@/api/types";
import { useLang } from "@/i18n/LanguageProvider";
import { useNav } from "@/store/nav";
import { useTourContext } from "@/tour/TourContext";
import { APP_VERSION, versionCodeOf } from "@/utils/appVersion";

import { AnnouncementCard } from "./AnnouncementCard";
import { openButton } from "./links";

export const ANNOUNCEMENTS_KEY = ["announcements"];

/** The admin's announcements on the home, as a card at the top (design
 * form 1). One the learner hasn't seen yet first opens dimmed: the screen
 * behind it darkens so only the card is clear. «بعداً» lifts the shade and
 * leaves the card on the home; × or its button closes it for good. */
export function AnnouncementBox() {
  const queryClient = useQueryClient();
  const navigate = useNav((s) => s.navigate);
  const setTab = useNav((s) => s.setTab);
  const tour = useTourContext();
  const { data } = useQuery({
    queryKey: ANNOUNCEMENTS_KEY,
    queryFn: () => announcementsApi.list(versionCodeOf(APP_VERSION)),
    staleTime: 5 * 60 * 1000,
  });

  // closed here, before the server's list catches up
  const [closed, setClosed] = useState<number[]>([]);
  const items = useMemo(() => (data ?? []).filter((a) => !closed.includes(a.id)), [data, closed]);
  const [index, setIndex] = useState(0);
  const current = items[Math.min(index, Math.max(0, items.length - 1))];

  // The dimmed first showing: the ones not seen when the list came, once
  // the home tour (if it is playing or about to) is done.
  const [spotIds, setSpotIds] = useState<number[] | null>(null);
  const [spotIndex, setSpotIndex] = useState(0);
  const offered = useRef(false);
  const tourBusy = !!tour && (!tour.loaded || !!tour.active || !tour.isSeen("home"));
  useEffect(() => {
    if (offered.current || !data || tourBusy) return;
    const fresh = data.filter((a) => !a.seen).map((a) => a.id);
    offered.current = true;
    if (fresh.length) setSpotIds(fresh);
  }, [data, tourBusy]);
  const spotItems = useMemo(() => (spotIds ? items.filter((a) => spotIds.includes(a.id)) : []), [items, spotIds]);
  const spotCurrent = spotItems[Math.min(spotIndex, Math.max(0, spotItems.length - 1))];

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
    report(item, "dismiss");
    setClosed((ids) => [...ids, item.id]);
    if (spotIds && spotItems.length <= 1) lift();
  };
  const press = (item: AppAnnouncement) => {
    if (!item.button) return;
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
