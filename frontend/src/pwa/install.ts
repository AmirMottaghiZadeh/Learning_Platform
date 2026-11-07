import type { InstallOutcome, InstallState } from "./types";

const state: InstallState = { environment: "native", canPrompt: false, manual: "browser", busy: false };
export const getInstallState = () => state;
export const subscribeInstall = (_listener: () => void) => () => {};
export function initializeInstall() {}
export async function requestInstall(): Promise<InstallOutcome> { return "manual"; }
