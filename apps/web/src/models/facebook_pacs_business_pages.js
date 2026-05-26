const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class FacebookPacsBusinessPagesModel {
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
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-pages`,
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
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.businessPage") });
        this.isLoading = false;
      }.bind(this));
  }
}

module.exports = FacebookPacsBusinessPagesModel;
