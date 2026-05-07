const m = require("mithril");
var config = require("../config");

var POLL_INTERVAL_MS = 1 * 60 * 1000;

class AlertsModel {
  constructor(auth) {
    this.auth = auth;
    this.items = [];
    this.error = null;
    this.isLoading = false;
    this.pollTimerId = null;
  }

  fetch() {
    this.isLoading = true;

    return m.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/alerts`,
      headers: {
        Authorization: `Basic ${this.auth.token}`,
      },
    })
      .then(function (payload) {
        this.items = payload.content;
        this.error = null;
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.items = [];
        this.error = "Failed to load alerts.";
        this.isLoading = false;
      }.bind(this));
  }

  startPolling() {
    this.stopPolling();
    this.fetch();

    this.pollTimerId = setInterval(function () {
      this.fetch();
    }.bind(this), POLL_INTERVAL_MS);
  }

  stopPolling() {
    if (this.pollTimerId !== null) {
      clearInterval(this.pollTimerId);
      this.pollTimerId = null;
    }

    this.items = [];
    this.error = null;
    this.isLoading = false;
  }

  hasAlerts() {
    return this.items.length > 0;
  }

  highestSeverity() {
    var severities = this.items.map(function (item) {
      return item.severity;
    });

    if (severities.indexOf("error") !== -1) {
      return "error";
    }

    if (severities.indexOf("warning") !== -1) {
      return "warning";
    }

    if (severities.indexOf("info") !== -1) {
      return "info";
    }

    return null;
  }
}

module.exports = AlertsModel;
