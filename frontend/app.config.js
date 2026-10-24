// Merges app.json and, for a GitHub Pages build, applies the sub-path base URL
// from EXPO_BASE_URL (e.g. "/Learning_Platform") so exported asset paths resolve
// under https://<user>.github.io/<repo>/. Local dev and native builds leave it unset.
const basePath = (process.env.EXPO_BASE_URL || "").replace(/\/+$/, "");

module.exports = ({ config }) => ({
  ...config,
  experiments: {
    ...config.experiments,
    ...(basePath ? { baseUrl: basePath } : {}),
  },
});
