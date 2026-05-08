var runtimeConfig = {};

if (typeof window !== "undefined" && window.APP_CONFIG) {
  runtimeConfig = window.APP_CONFIG;
}

var backendApiBaseUrl = runtimeConfig.BACKEND_API_BASE_URL || "/api/v2";
var debugPersistentAuth = runtimeConfig.DEBUG_PERSIST_AUTH === true
  || runtimeConfig.DEBUG_PERSIST_AUTH === "true";

module.exports = {
  backendApiBaseUrl: backendApiBaseUrl,
  debugPersistentAuth: debugPersistentAuth,
};
