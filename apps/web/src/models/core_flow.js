const m = require("mithril");
const api = require("./api");
var config = require("../config");

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
      landingPath: null,
      orderValue: null,
      isEnabled: true,
    };
  }

  setFormValues(payload) {
    this.form.name = payload.name || "";
    this.form.rule = payload.rule || "";
    this.form.actionType = payload.actionType || "redirect";
    this.form.redirectUrl = payload.redirectUrl || "";
    this.form.landingArchive = null;
    this.form.landingPath = payload.landingPath || "";
    this.form.isEnabled = payload.isEnabled || true;
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
        this.error = "Failed to load flow details.";
        this.isLoading = false;
      }.bind(this));
  }

  validate() {
    if (!this.form.name.trim()) {
      return "Name is required.";
    }

    if (!this.form.actionType) {
      return "Action type is required.";
    }

    if (this.form.actionType === "redirect") {
      let redirectUrl = (this.form.redirectUrl || "").trim();
      if (redirectUrl) {
        try {
          new URL(redirectUrl);
        } catch (error) {
          return "Redirect URL must be a valid URL.";
        }
      }
    }

    if (this.form.actionType === "render" && !this.form.landingArchive) {
      return "Landing archive is required.";
    }

    return null;
  }

  buildPayload() {
    return {
      name: this.form.name.trim(),
      rule: this.form.rule ? this.form.rule.trim() : "",
      actionType: this.form.actionType,
      redirectUrl:
        this.form.actionType === "redirect"
          ? this.form.redirectUrl.trim() || null
          : null,
      isEnabled: this.form.isEnabled,
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
          ? "Flow created successfully."
          : "Flow updated successfully.";
        setTimeout(function () {
          if (this.campaignId) {
            m.route.set(`/core/campaigns/${this.campaignId}`);
          } else {
            m.route.set("/core/campaigns");
          }
        }.bind(this), 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? "Failed to create flow."
          : "Failed to update flow.";
      }.bind(this));
  }
}

module.exports = CoreFlowModel;
