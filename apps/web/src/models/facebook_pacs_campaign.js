const m = require("mithril");
const api = require("./api");
var config = require("../config");

class FacebookPacsCampaignModel {
  constructor(campaignId) {
    this.campaignId = campaignId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.form = {
      name: "",
      costModel: "cpc",
      costValue: "",
      currency: "usd",
      statusMapperText: "",
      executorId: "",
      adCabinetId: "",
      businessPageId: "",
    };
  }

  setFormValues(payload) {
    this.form.name = payload.name || "";
    this.form.costModel = payload.costModel || "cpa";
    this.form.costValue = payload.costValue || "";
    this.form.currency = payload.currency || "usd";
    this.form.statusMapperText = payload.statusMapper
      ? JSON.stringify(payload.statusMapper, null, 2)
      : "";
    this.form.executorId = payload.executor ? String(payload.executor.id) : "";
    this.form.adCabinetId = payload.adCabinet ? String(payload.adCabinet.id) : "";
    this.form.businessPageId = payload.businessPage ? String(payload.businessPage.id) : "";
  }

  resetForm() {
    if (this.lastLoaded) {
      this.setFormValues(this.lastLoaded);
    } else {
      this.setFormValues({});
    }
  }

  loadCampaign() {
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.isLoading = true;

    api.request({
      method: "GET",
      url: `${config.backendApiBaseUrl}/facebook/pacs/campaigns/${this.campaignId}`,
    })
      .then(function (payload) {
        this.lastLoaded = payload;
        this.setFormValues(payload);
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = "Failed to load campaign details.";
        this.isLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.name.trim()) {
      return "Name is required.";
    }

    if (!this.form.costModel) {
      return "Cost model is required.";
    }

    if (!this.form.currency) {
      return "Currency is required.";
    }

    if (this.form.costValue === "") {
      return "Cost value is required.";
    }

    if (Number.isNaN(Number(this.form.costValue))) {
      return "Cost value must be a number.";
    }

    if (!this.form.statusMapperText.trim()) {
      return "Status mapper is required.";
    }

    try {
      let parsed = JSON.parse(this.form.statusMapperText);

      if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
        return "Status mapper must be a JSON object.";
      }
    } catch (error) {
      return "Status mapper must be valid JSON.";
    }

    if (!this.form.executorId) {
      return "Executor is required.";
    }

    if (!this.form.adCabinetId) {
      return "Ad cabinet is required.";
    }

    if (!this.form.businessPageId) {
      return "Business page is required.";
    }

    return null;
  }

  buildPayload() {
    let statusMapper = JSON.parse(this.form.statusMapperText);

    return {
      name: this.form.name.trim(),
      costModel: this.form.costModel,
      costValue: Number(this.form.costValue),
      currency: this.form.currency,
      statusMapper: statusMapper,
      executorId: Number(this.form.executorId),
      adCabinetId: Number(this.form.adCabinetId),
      businessPageId: Number(this.form.businessPageId),
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
    let isNew = this.campaignId === "new";
    let method = isNew ? "POST" : "PATCH";
    let url = isNew
      ? `${config.backendApiBaseUrl}/facebook/pacs/campaigns`
      : `${config.backendApiBaseUrl}/facebook/pacs/campaigns/${this.campaignId}`;

    api.request({
      method: method,
      url: url,
      body: payload,
    })
      .then(function () {
        this.successMessage = isNew
          ? "Campaign created successfully."
          : "Campaign updated successfully.";
        setTimeout(function () {
          m.route.set("/facebook/pacs/campaigns");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? "Failed to create campaign."
          : "Failed to update campaign.";
      }.bind(this));
  }
}

module.exports = FacebookPacsCampaignModel;
