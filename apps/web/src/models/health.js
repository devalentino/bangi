const api = require("./api");
var config = require("../config");

class HealthModel {
  constructor() {
    this.summary = null;
    this.history = [];
    this.error = null;
    this.isLoading = false;
  }

  load() {
    this.isLoading = true;

    return api
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
          this.isLoading = false;
        }.bind(this),
      )
      .catch(
        function () {
          this.summary = null;
          this.history = [];
          this.error = "Failed to load disk utilization.";
          this.isLoading = false;
        }.bind(this),
      );
  }

  isNeverReported() {
    return this.summary !== null && this.summary.lastReceivedAt === null && this.history.length === 0;
  }
}

module.exports = HealthModel;
