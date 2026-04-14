const m = require("mithril");
const api = require("./api");
var config = require("../config");

class CoreCampaignModel {
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
      internalProcessUrl: "",
    };
  }

  setFormValues(payload) {
    this.form.name = payload.name || "";
    this.form.costModel = payload.costModel || "cpc";
    this.form.costValue = payload.costValue || "";
    this.form.currency = payload.currency || "usd";
    this.form.statusMapperText = payload.statusMapper
      ? JSON.stringify(payload.statusMapper, null, 2)
      : "";
    this.form.internalProcessUrl = payload.internalProcessUrl || "";
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
      url: `${config.backendApiBaseUrl}/core/campaigns/${this.campaignId}`,
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

    if (this.form.statusMapperText.trim().length > 0) {
      try {
        let parsed = JSON.parse(this.form.statusMapperText);

        if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
          return "Status mapper must be an object with parameter and mapping.";
        }

        if (typeof parsed.parameter !== "string" || !parsed.parameter.trim()) {
          return "Status mapper parameter must be a non-empty string.";
        }

        if (
          parsed.mapping === null
          || typeof parsed.mapping !== "object"
          || Array.isArray(parsed.mapping)
        ) {
          return "Status mapper mapping must be an object.";
        }

        let keys = Object.keys(parsed.mapping);
        for (let i = 0; i < keys.length; i += 1) {
          let key = keys[i];
          if (typeof key !== "string" || !key.trim()) {
            return "Status mapper mapping keys must be non-empty strings.";
          }

          if (typeof parsed.mapping[key] !== "string") {
            return "Status mapper mapping values must be strings.";
          }
        }
      } catch (error) {
        return "Status mapper must be valid JSON.";
      }
    }

    return null;
  }

  buildPayload() {
    let statusMapper = null;
    let statusMapperText = this.form.statusMapperText.trim();

    if (statusMapperText.length > 0) {
      statusMapper = JSON.parse(statusMapperText);
    }

    return {
      name: this.form.name.trim(),
      costModel: this.form.costModel,
      costValue: Number(this.form.costValue),
      currency: this.form.currency,
      statusMapper: statusMapper,
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
      ? `${config.backendApiBaseUrl}/core/campaigns`
      : `${config.backendApiBaseUrl}/core/campaigns/${this.campaignId}`;

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
          m.route.set("/core/campaigns");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? "Failed to create campaign."
          : "Failed to update campaign.";
      }.bind(this));
  }
}

module.exports = CoreCampaignModel;
