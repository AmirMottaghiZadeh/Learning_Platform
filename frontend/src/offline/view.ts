import { useEffect, useState } from "react";

import { OfflineDataset, OfflinePackageInfo } from "@/api/types";
import { useAuth } from "@/store/auth";
import { toJalali, JALALI_MONTHS_FA, GREGORIAN_MONTHS_EN } from "@/utils/jalali";

import {
  InstalledPackage,
  OfflineErrorCode,
  PendingPackage,
  isUsable,
  licenseExpiresAt,
  pendingBytes,
  useOffline,
} from "./store";

/** What the download button, its sheet and the downloads screen show for
 * one dataset, derived from the offline store. */
export type PackagePhase =
  | "none"
  | "unpublished"
  | "downloading"
  | "paused"
  | "verifying"
  | "error"
  | "ready"
  | "locked"
  | "expired";

export type PackageView = {
  dataset: OfflineDataset;
  phase: PackagePhase;
  installed: InstalledPackage | null;
  pending: PendingPackage | null;
  remote: OfflinePackageInfo | undefined;
  /** 0..1 of the build being downloaded */
  progress: number;
  received: number;
  total: number;
  updateAvailable: boolean;
  validUntil: number | null;
  error: OfflineErrorCode | null;
};

export function usePackageView(dataset: OfflineDataset): PackageView {
  const state = useOffline((s) => s.datasets[dataset]);
  const remote = useOffline((s) => s.remote[dataset]);
  useAuth((s) => s.user?.id); // re-derive when the account changes
  // Re-check expiry now and then while a screen shows it.
  const [, tick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => tick((n) => n + 1), 60_000);
    return () => clearInterval(timer);
  }, []);

  const { installed, pending } = state;
  let phase: PackagePhase;
  if (pending) phase = pending.status;
  else if (installed) phase = installed.locked ? "locked" : isUsable(dataset) ? "ready" : "expired";
  else phase = remote && !remote.package ? "unpublished" : "none";

  const total = pending?.manifest.total_size ?? installed?.manifest.total_size ?? remote?.package?.total_size ?? 0;
  const received = pending ? pendingBytes(pending) : 0;
  return {
    dataset,
    phase,
    installed,
    pending,
    remote,
    progress: pending && total ? received / total : 0,
    received,
    total,
    updateAvailable: !!(installed && !pending && remote?.package && remote.package.build !== installed.manifest.build),
    validUntil: installed ? licenseExpiresAt(dataset) : null,
    error: pending?.error ?? null,
  };
}

export function formatBytes(bytes: number, n: (v: string | number) => string, isFa: boolean): string {
  const mb = bytes / (1024 * 1024);
  if (mb >= 1000) return `${n((mb / 1024).toFixed(2))} ${isFa ? "گیگابایت" : "GB"}`;
  return `${n(mb >= 10 ? Math.round(mb) : Math.max(mb, 0).toFixed(1))} ${isFa ? "مگابایت" : "MB"}`;
}

export function formatDay(ms: number, n: (v: string | number) => string, isFa: boolean): string {
  const d = new Date(ms);
  if (isFa) {
    const { jy, jm, jd } = toJalali(d.getFullYear(), d.getMonth() + 1, d.getDate());
    return `${n(jd)} ${JALALI_MONTHS_FA[jm - 1]} ${n(jy)}`;
  }
  return `${GREGORIAN_MONTHS_EN[d.getMonth()].slice(0, 3)} ${d.getDate()}, ${d.getFullYear()}`;
}

/** The snapshot a build was packed from, when it carries a stamp like
 * 202606 (a bare counter says nothing). */
export function sourceVersion(manifest: { source_version: string }): string {
  return /^\d{6}$/.test(manifest.source_version) ? manifest.source_version : "";
}
