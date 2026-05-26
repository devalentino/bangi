const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class FacebookPacsBusinessPortfolioModel {
  constructor(businessPortfolioId) {
    this.businessPortfolioId = businessPortfolioId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.form = {
      name: "",
      isBanned: false,
    };
    this.executors = [];
    this.adCabinets = [];
  }

  setFormValues(payload) {
    this.form.name = payload.name || "";
    this.form.isBanned = payload.isBanned || false;
    this.executors = payload.executors || [];
    this.adCabinets = payload.adCabinets || [];
  }

  resetForm() {
    if (this.lastLoaded) {
      this.setFormValues(this.lastLoaded);
    } else {
      this.setFormValues({});
    }
  }

  fetch() {
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.isLoading = true;

    api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios/${this.businessPortfolioId}`,
    })
      .then(function (payload) {
        this.lastLoaded = payload;
        this.setFormValues(payload);
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.businessPortfolio") });
        this.isLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.name.trim()) {
      return i18n.t("validation.nameRequired");
    }

    return null;
  }

  buildPayload() {
    return {
      name: this.form.name.trim(),
      isBanned: this.form.isBanned,
    };
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
    let isNew = this.businessPortfolioId === "new";
    let method = isNew ? "POST" : "PATCH";
    let url = isNew
      ? `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios`
      : `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios/${this.businessPortfolioId}`;

    api.request({
      method: method,
      url: url,
      body: payload,
    })
      .then(function () {
        this.successMessage = isNew
          ? i18n.t("messages.created", { entity: i18n.t("entities.businessPortfolio") })
          : i18n.t("messages.updated", { entity: i18n.t("entities.businessPortfolio") });
        setTimeout(function () {
          m.route.set("/facebook/pacs/business-portfolios");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? i18n.t("messages.failedCreate", { entity: i18n.t("entities.businessPortfolio") })
          : i18n.t("messages.failedUpdate", { entity: i18n.t("entities.businessPortfolio") });
      }.bind(this));
  }

  addExecutor(executorId) {
    return api.request({
      method: "POST",
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios/${this.businessPortfolioId}/executors/${executorId}`,
    });
  }

  removeExecutor(executorId) {
    return api.request({
      method: "DELETE",
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios/${this.businessPortfolioId}/executors/${executorId}`,
    });
  }

  searchExecutors(query) {
    let model = this;
    let trimmed = query.trim();

    if (!trimmed) {
      return Promise.resolve([]);
    }

    return api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/facebook/pacs/executors`,
      params: {
        page: 1,
        pageSize: 20,
        sortBy: "id",
        sortOrder: "asc",
        partialName: trimmed,
      },
    })
      .then(function (payload) {
        let excludedIds = new Set(
          (model.executors || []).map(function (executor) {
            return executor.id;
          }),
        );
        return (payload.content || []).filter(function (executor) {
          return !excludedIds.has(executor.id);
        });
      });
  }

}

module.exports = FacebookPacsBusinessPortfolioModel;
