const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class HealthModel {
  constructor() {
    this.summary = null;
    this.history = [];
    this.nginxSnapshot = null;
    this.nginxError = null;
    this.certificateDiagnostics = [];
    this.certificateError = null;
    this.error = null;
    this.isLoading = false;
  }

  load() {
    this.isLoading = true;
    this.summary = null;
    this.history = [];
    this.error = null;
    this.nginxSnapshot = null;
    this.nginxError = null;
    this.certificateDiagnostics = [];
    this.certificateError = null;

    let diskPromise = api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/health/disk-utilization/history`,
        params: { days: 30 },
      })
      .then(
        function (payload) {
          this.summary = payload.summary;
          this.history = payload.content || [];
          this.error = null;
        }.bind(this),
      )
      .catch(
        function () {
          this.summary = null;
          this.history = [];
          this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.diskUtilization") });
        }.bind(this),
      );

    let nginxPromise = api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/health/nginx`,
      })
      .then(
        function (payload) {
          this.nginxSnapshot = payload.content;
          this.nginxError = null;
        }.bind(this),
      )
      .catch(
        function () {
          this.nginxSnapshot = null;
          this.nginxError = i18n.t("messages.failedLoad", { entity: i18n.t("entities.nginxValidationSnapshot") });
        }.bind(this),
      );

    let certificatePromise = api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/health/certificates`,
      })
      .then(
        function (payload) {
          this.certificateDiagnostics = payload.content || [];
          this.certificateError = null;
        }.bind(this),
      )
      .catch(
        function () {
          this.certificateDiagnostics = [];
          this.certificateError = i18n.t("messages.failedLoad", { entity: i18n.t("entities.certificateDiagnostics") });
        }.bind(this),
      );

    return Promise.all([diskPromise, nginxPromise, certificatePromise]).finally(
      function () {
        this.isLoading = false;
      }.bind(this),
    );
  }

  isNeverReported() {
    return this.summary !== null && this.summary.lastReceivedAt === null && this.history.length === 0;
  }
}

module.exports = HealthModel;
