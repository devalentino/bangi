const m = require("mithril");
const api = require("./api");
var config = require("../config");

class FacebookPacsAdCabinetModel {
  constructor(adCabinetId) {
    this.adCabinetId = adCabinetId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.form = {
      name: "",
      isBanned: false,
    };
    this.businessPortfolio = null;
  }

  setFormValues(payload) {
    this.form.name = payload.name || "";
    this.form.isBanned = payload.isBanned || false;
    this.businessPortfolio = payload.businessPortfolio || null;
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
      url: `${config.backendApiBaseUrl}/facebook/pacs/ad-cabinets/${this.adCabinetId}`,
    })
      .then(function (payload) {
        this.lastLoaded = payload;
        this.setFormValues(payload);
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = "Failed to load ad cabinet details.";
        this.isLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.name.trim()) {
      return "Name is required.";
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
    let isNew = this.adCabinetId === "new";
    let method = isNew ? "POST" : "PATCH";
    let url = isNew
      ? `${config.backendApiBaseUrl}/facebook/pacs/ad-cabinets`
      : `${config.backendApiBaseUrl}/facebook/pacs/ad-cabinets/${this.adCabinetId}`;

    api.request({
      method: method,
      url: url,
      body: payload,
    })
      .then(function () {
        this.successMessage = isNew
          ? "Ad cabinet created successfully."
          : "Ad cabinet updated successfully.";
        setTimeout(function () {
          m.route.set("/facebook/pacs/ad-cabinets");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? "Failed to create ad cabinet."
          : "Failed to update ad cabinet.";
      }.bind(this));
  }

  searchBusinessPortfolios(query) {
    let trimmed = query.trim();

    if (!trimmed) {
      return Promise.resolve([]);
    }

    return api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-portfolios`,
      params: {
        page: 1,
        pageSize: 20,
        sortBy: "id",
        sortOrder: "asc",
        partialName: trimmed,
      },
    })
      .then(function (payload) {
        let currentId = this.businessPortfolio
          ? this.businessPortfolio.id
          : null;
        return (payload.content || []).filter(function (portfolio) {
          return !currentId || portfolio.id !== currentId;
        });
      }.bind(this));
  }

  bindBusinessPortfolio(businessPortfolioId) {
    return api.request({
      method: "POST",
      url: `${config.backendApiBaseUrl}/facebook/pacs/ad-cabinets/${this.adCabinetId}/business-portfolio/${businessPortfolioId}`,
    });
  }

  unbindBusinessPortfolio(businessPortfolioId) {
    return api.request({
      method: "DELETE",
      url: `${config.backendApiBaseUrl}/facebook/pacs/ad-cabinets/${this.adCabinetId}/business-portfolio/${businessPortfolioId}`,
    });
  }
}

module.exports = FacebookPacsAdCabinetModel;
