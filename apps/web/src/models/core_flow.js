const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class CoreFlowModel {
  constructor(flowId, campaignId) {
    this.flowId = flowId;
    this.campaignId = campaignId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.form = {
      name: null,
      rule: null,
      actionType: "redirect",
      redirectUrl: null,
      landingArchive: null,
      hasLandingPage: false,
      orderValue: null,
      isEnabled: true,
      showOncePerVisitor: false,
    };
  }

  setFormValues(payload) {
    this.form.name = payload.name || "";
    this.form.rule = payload.rule || "";
    this.form.actionType = payload.actionType || "redirect";
    this.form.redirectUrl = payload.redirectUrl || "";
    this.form.landingArchive = null;
    this.form.hasLandingPage = payload.hasLandingPage || false;
    this.form.isEnabled = payload.isEnabled ?? true;
    this.form.showOncePerVisitor = payload.showOncePerVisitor || false;
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
      url: `${config.backendApiBaseUrl}/core/campaigns/${this.campaignId}/flows/${this.flowId}`,
    })
      .then(function (payload) {
        this.lastLoaded = payload;
        this.setFormValues(payload);
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.flowDetails") });
        this.isLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.name.trim()) {
      return i18n.t("validation.nameRequired");
    }

    if (!this.form.actionType) {
      return i18n.t("validation.actionTypeRequired");
    }

    if (this.form.actionType === "redirect") {
      let redirectUrl = (this.form.redirectUrl || "").trim();
      if (!redirectUrl) {
        return i18n.t("validation.redirectUrlRequired");
      }
      try {
        new URL(redirectUrl);
      } catch (error) {
        return i18n.t("validation.redirectUrlInvalid");
      }
    }

    if (
      this.form.actionType === "render" &&
      !this.form.hasLandingPage &&
      !this.form.landingArchive
    ) {
      return i18n.t("validation.landingArchiveRequired");
    }

    return null;
  }

  buildPayload() {
    let rule = this.form.rule ? this.form.rule.trim() : null;

    return {
      name: this.form.name.trim(),
      rule: rule,
      actionType: this.form.actionType,
      redirectUrl:
        this.form.actionType === "redirect"
          ? this.form.redirectUrl.trim() || null
          : null,
      isEnabled: this.form.isEnabled,
      showOncePerVisitor: this.form.showOncePerVisitor,
    };
  }

  buildFormData(payload) {
    let formData = new FormData();

    Object.keys(payload).forEach(function (key) {
      if (payload[key] !== undefined && payload[key] !== null) {
        formData.append(key, payload[key]);
      }
    });

    if (this.form.landingArchive) {
      formData.append("landingArchive", this.form.landingArchive);
    }

    return formData;
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
    let isNew = this.flowId === "new";
    let method = isNew ? "POST" : "PATCH";
    let url = isNew
      ? `${config.backendApiBaseUrl}/core/campaigns/${this.campaignId}/flows`
      : `${config.backendApiBaseUrl}/core/campaigns/${this.campaignId}/flows/${this.flowId}`;

    api.request(
      {
        method: method,
        url: url,
        body: this.buildFormData(payload),
        serialize: function (value) {
          return value;
        },
      },
    )
      .then(function () {
        this.successMessage = isNew
          ? i18n.t("messages.created", { entity: i18n.t("entities.flow") })
          : i18n.t("messages.updated", { entity: i18n.t("entities.flow") });
        setTimeout(function () {
          if (this.campaignId) {
            m.route.set(`/core/campaigns/${this.campaignId}`);
          } else {
            m.route.set("/core/campaigns");
          }
        }.bind(this), 2000);
      }.bind(this))
      .catch(function (error) {
        let formErrors =
          error &&
          error.response &&
          error.response.errors &&
          error.response.errors.form;

        if (formErrors && formErrors.rule && formErrors.rule.length > 0) {
          this.error = formErrors.rule[0];
          return;
        }

        if (
          formErrors &&
          formErrors.redirectUrl &&
          formErrors.redirectUrl.length > 0
        ) {
          this.error = formErrors.redirectUrl[0];
          return;
        }

        if (
          formErrors &&
          formErrors.landingArchive &&
          formErrors.landingArchive.length > 0
        ) {
          this.error = formErrors.landingArchive[0];
          return;
        }

        this.error = isNew
          ? i18n.t("messages.failedCreate", { entity: i18n.t("entities.flow") })
          : i18n.t("messages.failedUpdate", { entity: i18n.t("entities.flow") });
      }.bind(this));
  }
}

module.exports = CoreFlowModel;
