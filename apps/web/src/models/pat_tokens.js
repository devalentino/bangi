const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class PatTokensModel {
  constructor() {
    this.items = [];
    this.isLoading = false;
    this.error = null;
  }

  fetch() {
    this.isLoading = true;
    this.error = null;

    return api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/auth/tokens`,
    })
      .then(function (payload) {
        this.items = payload.content;
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.patTokens") });
        this.isLoading = false;
      }.bind(this));
  }

  generate(name) {
    return api.request({
      method: "POST",
      url: `${config.backendApiBaseUrl}/auth/tokens`,
      body: { name: name },
    });
  }

  revoke(tokenId) {
    return api.request({
      method: "DELETE",
      url: `${config.backendApiBaseUrl}/auth/tokens/${tokenId}`,
    });
  }
}

module.exports = PatTokensModel;
