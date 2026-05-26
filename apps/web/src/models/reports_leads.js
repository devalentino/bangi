const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class ReportsLeadsModel {
  constructor() {
    this.campaigns = [];
    this.leads = [];
    this.pagination = null;
    this.isLoading = false;
    this.isLoadingCampaigns = false;
    this.error = null;
    this.campaignError = null;
  }

  loadCampaigns() {
    this.isLoadingCampaigns = true;
    this.campaignError = null;

    return api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/core/campaigns`,
    })
      .then(function (payload) {
        this.campaigns = payload.content || [];
        this.isLoadingCampaigns = false;
      }.bind(this))
      .catch(function () {
        this.campaigns = [];
        this.campaignError = i18n.t("messages.failedLoad", { entity: i18n.t("entities.campaigns") });
        this.isLoadingCampaigns = false;
      }.bind(this));
  }

  loadLeads() {
    let campaignId = Number(m.route.param("campaignId"));

    if (!campaignId) {
      this.leads = [];
      this.pagination = null;
      return Promise.resolve();
    }

    this.isLoading = true;
    this.error = null;

    let page = Number(m.route.param("page") || 1);
    let pageSize = Number(m.route.param("pageSize") || 20);
    let sortBy = m.route.param("sortBy") || "createdAt";
    let sortOrder = m.route.param("sortOrder") || "desc";

    return api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/reports/leads`,
      params: {
        campaignId: campaignId,
        page: page,
        pageSize: pageSize,
        sortBy: sortBy,
        sortOrder: sortOrder,
      },
    })
      .then(function (payload) {
        this.leads = payload.content;
        this.pagination = Object.assign({}, payload.pagination, {
          campaignId: campaignId,
          pageSize: pageSize,
          sortBy: sortBy,
          sortOrder: sortOrder,
        });
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.leads") });
        this.isLoading = false;
      }.bind(this));
  }
}

module.exports = ReportsLeadsModel;
