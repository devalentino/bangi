const m = require("mithril");
const api = require("./api");
var config = require("../config");

class DomainModel {
  constructor(domainId) {
    this.domainId = domainId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.campaigns = [];
    this.campaignError = null;
    this.domain = null;
    this.form = {
      hostname: "",
      purpose: "campaign",
      campaignId: "",
      isDisabled: false,
      isARecordSet: null,
    };
  }

  setFormValues(payload) {
    this.form.hostname = payload.hostname || "";
    this.form.purpose = payload.purpose || "campaign";
    this.form.campaignId = payload.campaignId === null || payload.campaignId === undefined ? "" : String(payload.campaignId);
    this.form.isDisabled = Boolean(payload.isDisabled);
    this.form.isARecordSet = payload.isARecordSet === undefined ? null : payload.isARecordSet;
  }

  resetForm() {
    if (this.lastLoaded) {
      this.setFormValues(this.lastLoaded);
    } else {
      this.setFormValues({});
    }
  }

  fetchCampaigns() {
    this.campaignError = null;

    api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/core/campaigns`,
      params: {
        page: 1,
        pageSize: 1000,
        sortBy: "id",
        sortOrder: "asc",
      },
    })
      .then(function (payload) {
        this.campaigns = payload.content;
      }.bind(this))
      .catch(function () {
        this.campaigns = [];
        this.campaignError = "Failed to load campaign options.";
      });
  }

  fetch() {
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.isLoading = true;

    api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/domains/${this.domainId}`,
    })
      .then(function (payload) {
        this.domain = payload;
        this.lastLoaded = payload;
        this.setFormValues(payload);
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = "Failed to load domain details.";
        this.isLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.hostname.trim()) {
      return "Hostname is required.";
    }

    if (this.domainId === "new" && !this.form.purpose) {
      return "Purpose is required.";
    }

    return null;
  }

  buildPayload() {
    let payload = {
      hostname: this.form.hostname.trim(),
      isDisabled: Boolean(this.form.isDisabled),
      purpose: this.form.purpose,
    };

    if (this.domainId === "new") {
      return payload;
    }

    if (this.form.campaignId === "") {
      payload.campaignId = null;
    } else {
      payload.campaignId = Number(this.form.campaignId);
    }

    return payload;
  }

  validationAlertText() {
    if (!this.domain || !this.domain.validationFailed) {
      return null;
    }

    return "The latest Nginx validation snapshot reports an inconsistency. Check Health for details.";
  }

  save() {
    this.error = null;
    this.successMessage = null;

    let validationError = this.validate();
    if (validationError) {
      this.error = validationError;
      return;
    }

    let isNew = this.domainId === "new";
    let method = isNew ? "POST" : "PATCH";
    let url = isNew
      ? `${config.backendApiBaseUrl}/domains`
      : `${config.backendApiBaseUrl}/domains/${this.domainId}`;

    api.request({
      method: method,
      url: url,
      body: this.buildPayload(),
    })
      .then(function () {
        this.successMessage = isNew
          ? "Domain created successfully."
          : "Domain updated successfully.";
        setTimeout(function () {
          m.route.set("/domains");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? "Failed to create domain."
          : "Failed to update domain.";
      }.bind(this));
  }
}

module.exports = DomainModel;
