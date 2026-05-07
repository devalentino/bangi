var runtimeConfig = {};

if (typeof window !== "undefined" && window.APP_CONFIG) {
  runtimeConfig = window.APP_CONFIG;
}

var backendApiBaseUrl =
  runtimeConfig.BACKEND_API_BASE_URL || process.env.BACKEND_API_BASE_URL || "/api/v2";

module.exports = {
  backendApiBaseUrl: backendApiBaseUrl,
};
