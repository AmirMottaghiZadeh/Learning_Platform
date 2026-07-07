const githubPagesBasePath = process.env.EXPO_BASE_URL || "";

module.exports = ({config}) => ({
  ...config,
  experiments: {
    ...config.experiments,
    typedRoutes: false,
    ...(githubPagesBasePath ? {baseUrl: githubPagesBasePath.replace(/\/+$/, "")} : {}),
  },
});
