/** iOS browsers zoom focused text fields when their text is too small. */
type BrowserDevice = { userAgent: string; platform: string; maxTouchPoints: number };

export function hasIosInputZoom(device: BrowserDevice | undefined): boolean {
  if (!device) return false;
  return /iPhone|iPad|iPod/.test(device.userAgent)
    || (device.platform === "MacIntel" && device.maxTouchPoints > 1);
}

export function readableInputFontSize(size: number | undefined): number {
  return Math.max(16, size ?? 16);
}
