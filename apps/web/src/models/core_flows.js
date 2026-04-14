const m = require("mithril");
const api = require("./api");
var config = require("../config");

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
      this.error = "Campaign ID is required.";
      return Promise.reject(new Error("Campaign ID is required."));
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
        this.error = "Failed to load flows.";
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
