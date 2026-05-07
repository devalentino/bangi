const m = require("mithril");
const api = require("./api");
const session = require("./session");
var config = require("../config");

class FacebookPacsBusinessPortfolioAccessUrlModel {
  constructor(businessPortfolioId) {
    this.businessPortfolioId = businessPortfolioId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.form = {
      url: "",
      email: "",
      expiresAt: "",
    };
  }

  resetForm() {
    this.form.url = "";
    this.form.email = "";
    this.form.expiresAt = "";
  }

  validate() {
    if (!this.form.url.trim()) {
      return "URL is required.";
    }

    if (!this.form.expiresAt.trim()) {
      return "Expiration date is required.";
    }

    return null;
  }

  buildPayload() {
    var payload = {
      url: this.form.url.trim(),
      expiresAt: this.form.expiresAt.trim(),
    };

    if (this.form.email.trim()) {
      payload.email = this.form.email.trim();
    }

    return payload;
  }

  save() {
    this.error = null;
    this.successMessage = null;

    let validationError = this.validate();
    if (validationError) {
      this.error = validationError;
      return;
    }

    let payload = this.buildPayload();

    api.request({
      method: "POST",
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios/${this.businessPortfolioId}/access-urls`,
      body: payload,
    })
      .then(function () {
        session.alerts.fetch().catch(function () {});
        this.successMessage = "Access URL created successfully.";
        setTimeout(function () {
          m.route.set(`/facebook/pacs/business-portfolios/${this.businessPortfolioId}/access-urls`);
        }.bind(this), 2000);
      }.bind(this))
      .catch(function () {
        this.error = "Failed to create access URL.";
      }.bind(this));
  }
}

module.exports = FacebookPacsBusinessPortfolioAccessUrlModel;
