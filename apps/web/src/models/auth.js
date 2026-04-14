var m = require("mithril");
var config = require("../config");

var STORAGE_KEY = "bangi.auth";
var PERSISTENT_AUTH = process.env.DEBUG_PERSIST_AUTH === "true";

function loadStoredCredentials() {
  if (!PERSISTENT_AUTH) {
    return null;
  }

  if (typeof localStorage === "undefined") {
    return null;
  }

  try {
    var raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }

    var data = JSON.parse(raw);
    if (!data || !data.username || !data.password) {
      return null;
    }

    return data;
  } catch (error) {
    return null;
  }
}

function persistCredentials(username, password) {
  if (!PERSISTENT_AUTH) {
    return;
  }

  if (typeof localStorage === "undefined") {
    return;
  }

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ username: username, password: password }),
  );
}

function clearCredentials() {
  if (!PERSISTENT_AUTH) {
    return;
  }

  if (typeof localStorage === "undefined") {
    return;
  }

  localStorage.removeItem(STORAGE_KEY);
}

class AuthModel {
  constructor() {
    this.username = null;
    this.password = null;
    this.isAuthenticated = false;
    this.token = null;
    this.onAuthenticated = null;
    this.onSignedOut = null;

    var storedCredentials = loadStoredCredentials();
    if (storedCredentials) {
      this.username = storedCredentials.username;
      this.password = storedCredentials.password;
      this.token = btoa(
        this.username + ":" + this.password,
      );
      this.isAuthenticated = true;
    }

    if (!PERSISTENT_AUTH && typeof localStorage !== "undefined") {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  signIn(username, password) {
    this.username = username;
    this.password = password;

    this.token = btoa(
      this.username + ":" + this.password,
    );

    m.request({
      method: "POST",
      url: config.backendApiBaseUrl + "/auth/authenticate",
      headers: { Authorization: "Basic " + this.token },
    })
      .then(function () {
        this.isAuthenticated = true;
        persistCredentials(username, password);
        if (typeof this.onAuthenticated === "function") {
          this.onAuthenticated();
        }
        m.route.set("");
      }.bind(this))
      .catch(function () {
        alert("Failed to authenticate");
        this.isAuthenticated = false;
        this.token = null;
        clearCredentials();
        m.route.set("");
      }.bind(this));
  }

  signOut() {
    this.username = null;
    this.password = null;
    this.isAuthenticated = false;
    this.token = null;
    clearCredentials();
    if (typeof this.onSignedOut === "function") {
      this.onSignedOut();
    }
    m.route.set("");
    alert("Signed out");
  }
}

module.exports = AuthModel;
