const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class DomainsModel {
  constructor() {
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
      url: `${config.backendApiBaseUrl}/domains`,
      params: {
        page: m.route.param("page") || 1,
        pageSize: m.route.param("pageSize") || 20,
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
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.domains") });
        this.isLoading = false;
      })
  }
}

module.exports = DomainsModel;
