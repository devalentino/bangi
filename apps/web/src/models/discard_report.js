const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class DiscardReportFilter {
  constructor() {
    this.campaignId = null;
    this.window = "1h";
    this.groupBy = "country";
  }

  isReady() {
    return this.campaignId !== null;
  }
}

class DiscardReportModel {
  constructor() {
    this.filter = new DiscardReportFilter();
    this.campaigns = [];
    this.campaignError = null;
    this.isLoading = false;
    this.error = null;
    this.content = null;
  }

  _buildContent(payload) {
    return {
      rows: payload.content || [],
      summary: payload.summary || {
        discardCount: 0,
        totalCount: 0,
        rate: 0,
        eligible: false,
      },
    };
  }

  loadCampaigns() {
    return api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/core/filters/campaigns`,
      })
      .then(
        function (payload) {
          this.campaigns = payload;
          this.campaignError = null;
        }.bind(this),
      )
      .catch(
        function () {
          this.campaigns = [];
          this.campaignError = i18n.t("messages.failedLoad", { entity: i18n.t("entities.campaigns") });
        }.bind(this),
      );
  }

  initialize() {
    return this.loadCampaigns().then(
      function () {
        if (this.filter.campaignId === null && this.campaigns.length > 0) {
          this.filter.campaignId = this.campaigns[0].id;
        }
        return this.loadReport();
      }.bind(this),
    );
  }

  loadReport() {
    if (!this.filter.isReady()) {
      return Promise.resolve();
    }

    this.isLoading = true;
    this.error = null;

    return api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/reports/discard`,
        params: {
          campaignId: this.filter.campaignId,
          window: this.filter.window,
          groupBy: this.filter.groupBy,
        },
      })
      .then(
        function (payload) {
          this.content = this._buildContent(payload);
          this.isLoading = false;
        }.bind(this),
      )
      .catch(
        function () {
          this.content = null;
          this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.discardReport") });
          this.isLoading = false;
        }.bind(this),
      );
  }
}

module.exports = DiscardReportModel;
