import { useSyncExternalStore } from "react";
import { getInstallState, subscribeInstall } from "./install";

export function usePwaInstall() {
  return useSyncExternalStore(subscribeInstall, getInstallState, getInstallState);
}
