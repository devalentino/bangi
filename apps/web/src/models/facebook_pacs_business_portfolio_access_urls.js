const m = require("mithril");
const api = require("./api");
var config = require("../config");

class FacebookPacsBusinessPortfolioAccessUrlsModel {
  constructor(businessPortfolioId) {
    this.businessPortfolioId = businessPortfolioId;
    this.items = [];
    this.pagination = null;
    this.isLoading = false;
    this.error = null;
  }

  fetch() {
    this.isLoading = true;
    this.error = null;

    api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios/${this.businessPortfolioId}/access-urls`,
      params: {
        page: m.route.param("page") || 1,
        pageSize: m.route.param("pageSize") || 10,
        sortBy: m.route.param("sortBy") || "id",
        sortOrder: m.route.param("sortOrder") || "asc",
      },
    })
      .then(function (payload) {
        this.items = payload.content;
        this.pagination = payload.pagination;
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = "Failed to load access URLs.";
        this.isLoading = false;
      }.bind(this));
  }

  deleteAccessUrl(accessUrlId) {
    return api.request({
      method: "DELETE",
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios/${this.businessPortfolioId}/access-urls/${accessUrlId}`,
    });
  }
}

module.exports = FacebookPacsBusinessPortfolioAccessUrlsModel;
