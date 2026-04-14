const api = require("./api");
var config = require("../config");

class ReportsLeadModel {
  constructor(clickId) {
    this.clickId = clickId;
    this.lead = null;
    this.isLoading = false;
    this.error = null;
  }

  getLead() {
    this.isLoading = true;
    this.error = null;

    return api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/reports/leads/${this.clickId}`,
    })
      .then(function (payload) {
        this.lead = payload;
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = "Failed to load lead details.";
        this.isLoading = false;
      }.bind(this));
  }
}

module.exports = ReportsLeadModel;
