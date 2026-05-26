const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class CoreFlowsModel {
  constructor(campaignId) {
    this.campaignId = campaignId;
    this.items = [];
    this.pagination = null;
    this.isLoading = false;
    this.error = null;
  }

  updateOrderBulk(campaignId, orderMapping) {
    if (campaignId === undefined || campaignId === null || campaignId === "") {
      this.error = i18n.t("messages.campaignIdRequired");
      return Promise.reject(new Error(i18n.t("messages.campaignIdRequired")));
    }

    return api.request({
      method: "PATCH",
      url: `${config.backendApiBaseUrl}/core/campaigns/${campaignId}/flows/order`,
      body: { order: orderMapping },
    });
  }

  fetch(params) {
    this.isLoading = true;
    this.error = null;

    let requestParams = {
      page: params.page || 1,
      pageSize: params.pageSize || 1000,
      sortBy: params.sortBy || "orderValue",
      sortOrder: params.sortOrder || "asc",
    };

    api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/core/campaigns/${this.campaignId}/flows`,
      params: requestParams,
    })
      .then(function (payload) {
        this.items = payload.content;
        this.pagination = payload.pagination;
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.flows") });
        this.isLoading = false;
      }.bind(this));
  }

  deleteFlow(flowId) {
    return api.request({
      method: "DELETE",
      url: `${config.backendApiBaseUrl}/core/campaigns/${this.campaignId}/flows/${flowId}`,
    });
  }
}

module.exports = CoreFlowsModel;
