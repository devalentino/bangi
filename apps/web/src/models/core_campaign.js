const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class CoreCampaignModel {
  constructor(campaignId) {
    this.campaignId = campaignId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.form = {
      name: "",
      costModel: "cpa",
      costValue: "",
      currency: "usd",
      statusMapperText: "",
      internalProcessUrl: "",
      defaultFlowId: "",
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
    this.form.defaultFlowId = payload.defaultFlowId == null
      ? ""
      : String(payload.defaultFlowId);
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
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.campaignDetails") });
        this.isLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.name.trim()) {
      return i18n.t("validation.nameRequired");
    }

    if (!this.form.costModel) {
      return i18n.t("validation.costModelRequired");
    }

    if (!this.form.currency) {
      return i18n.t("validation.currencyRequired");
    }

    if (this.form.costValue === "") {
      return i18n.t("validation.costValueRequired");
    }

    if (Number.isNaN(Number(this.form.costValue))) {
      return i18n.t("validation.costValueNumber");
    }

    if (this.form.statusMapperText.trim().length > 0) {
      try {
        let parsed = JSON.parse(this.form.statusMapperText);

        if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
          return i18n.t("validation.statusMapperObject");
        }

        if (typeof parsed.parameter !== "string" || !parsed.parameter.trim()) {
          return i18n.t("validation.statusMapperParameter");
        }

        if (
          parsed.mapping === null
          || typeof parsed.mapping !== "object"
          || Array.isArray(parsed.mapping)
        ) {
          return i18n.t("validation.statusMapperMappingObject");
        }

        let keys = Object.keys(parsed.mapping);
        for (let i = 0; i < keys.length; i += 1) {
          let key = keys[i];
          if (typeof key !== "string" || !key.trim()) {
            return i18n.t("validation.statusMapperMappingKey");
          }

          if (typeof parsed.mapping[key] !== "string") {
            return i18n.t("validation.statusMapperMappingValue");
          }
        }
      } catch (error) {
        return i18n.t("validation.statusMapperJson");
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

    let payload = {
      name: this.form.name.trim(),
      costModel: this.form.costModel,
      costValue: Number(this.form.costValue),
      currency: this.form.currency,
      statusMapper: statusMapper,
    };

    if (this.campaignId !== "new") {
      payload.defaultFlowId = this.form.defaultFlowId === ""
        ? null
        : Number(this.form.defaultFlowId);
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
          ? i18n.t("messages.created", { entity: i18n.t("entities.campaign") })
          : i18n.t("messages.updated", { entity: i18n.t("entities.campaign") });
        setTimeout(function () {
          m.route.set("/core/campaigns");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? i18n.t("messages.failedCreate", { entity: i18n.t("entities.campaign") })
          : i18n.t("messages.failedUpdate", { entity: i18n.t("entities.campaign") });
      }.bind(this));
  }
}

module.exports = CoreCampaignModel;
