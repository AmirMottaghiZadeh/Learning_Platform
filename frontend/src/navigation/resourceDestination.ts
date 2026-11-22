import { ScreenKey } from "./types";

type Destination = { screen: ScreenKey; params?: Record<string, string> };

export function resourceDestination(search: string): Destination | undefined {
  const params = new URLSearchParams(search);
  const query = (params.get("q") ?? "").trim().slice(0, 120);
  const scope = params.get("scope");

  switch (params.get("open")) {
    case "search":
      return { screen: "resourceSearch", params: { query, scope: scope === "articles" || scope === "drugs" ? scope : "all" } };
    case "clinical":
      return { screen: "clinical" };
    case "uptodate":
      return { screen: "uptodate", params: { query } };
    case "lexicomp":
      return { screen: "lexicomp" };
    case "conditions":
      return { screen: "diseasesConditions" };
    case "drug": {
      const code = (params.get("code") ?? "").toUpperCase();
      const slug = params.get("slug") ?? "";
      if (/^[A-Z]\d{2}$/.test(code) && slug.length <= 200 && /^[\w-]+$/.test(slug)) {
        return { screen: "lessonDetail", params: { code, slug } };
      }
      return { screen: "lessons" };
    }
    default:
      return undefined;
  }
}
