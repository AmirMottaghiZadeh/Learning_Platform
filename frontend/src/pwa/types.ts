export type InstallState = {
  environment: "browser" | "standalone" | "native";
  canPrompt: boolean;
  manual: "ios" | "browser";
  busy: boolean;
};
export type InstallOutcome = "accepted" | "dismissed" | "manual" | "error";
