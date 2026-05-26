const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

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
    this.certificate = null;
    this.certificateError = null;
    this.isCertificateLoading = false;
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
        this.campaignError = i18n.t("messages.failedLoad", { entity: i18n.t("entities.campaignOptions") });
      });
  }

  fetch() {
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.certificate = null;
    this.certificateError = null;
    this.isCertificateLoading = false;
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
        if (payload.certificateStatus) {
          this.fetchCertificate();
        }
      }.bind(this))
      .catch(function () {
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.domainDetails") });
        this.isLoading = false;
      }.bind(this));
  }

  fetchCertificate() {
    this.certificate = null;
    this.certificateError = null;
    this.isCertificateLoading = true;

    api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/domains/${this.domainId}/certificate`,
    })
      .then(function (payload) {
        this.certificate = payload;
        this.isCertificateLoading = false;
      }.bind(this))
      .catch(function () {
        this.certificateError = i18n.t("messages.failedLoad", { entity: i18n.t("entities.certificateDetails") });
        this.isCertificateLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.hostname.trim()) {
      return i18n.t("validation.hostnameRequired");
    }

    if (this.domainId === "new" && !this.form.purpose) {
      return i18n.t("validation.purposeRequired");
    }

    return null;
  }

  buildPayload() {
    let payload = {
      hostname: this.form.hostname.trim(),
      isDisabled: Boolean(this.form.isDisabled),
      purpose: this.form.purpose,
    };

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

    return i18n.t("messages.domainValidationInconsistent");
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
          ? i18n.t("messages.created", { entity: i18n.t("entities.domain") })
          : i18n.t("messages.updated", { entity: i18n.t("entities.domain") });
        setTimeout(function () {
          m.route.set("/domains");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? i18n.t("messages.failedCreate", { entity: i18n.t("entities.domain") })
          : i18n.t("messages.failedUpdate", { entity: i18n.t("entities.domain") });
      }.bind(this));
  }
}

module.exports = DomainModel;
