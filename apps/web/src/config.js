var runtimeConfig = {};

if (typeof window !== "undefined" && window.APP_CONFIG) {
  runtimeConfig = window.APP_CONFIG;
}

var backendApiBaseUrl = "http://138.68.85.45/api/v2";
var debugPersistentAuth = runtimeConfig.DEBUG_PERSIST_AUTH === true
  || runtimeConfig.DEBUG_PERSIST_AUTH === "true";

module.exports = {
  backendApiBaseUrl: backendApiBaseUrl,
  debugPersistentAuth: debugPersistentAuth,
};
