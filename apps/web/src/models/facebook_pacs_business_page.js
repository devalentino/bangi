const m = require("mithril");
const api = require("./api");
var config = require("../config");

class FacebookPacsBusinessPageModel {
  constructor(businessPageId) {
    this.businessPageId = businessPageId;
    this.isLoading = false;
    this.error = null;
    this.successMessage = null;
    this.lastLoaded = null;
    this.form = {
      name: "",
      isBanned: false,
    };
  }

  setFormValues(payload) {
    this.form.name = payload.name || "";
    this.form.isBanned = payload.isBanned || false;
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
      url: `${config.backendApiBaseUrl}/facebook/pacs/business-pages/${this.businessPageId}`,
    })
      .then(function (payload) {
        this.lastLoaded = payload;
        this.setFormValues(payload);
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = "Failed to load business page details.";
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
    let isNew = this.businessPageId === "new";
    let method = isNew ? "POST" : "PATCH";
    let url = isNew
      ? `${config.backendApiBaseUrl}/facebook/pacs/business-pages`
      : `${config.backendApiBaseUrl}/facebook/pacs/business-pages/${this.businessPageId}`;

    api.request({
      method: method,
      url: url,
      body: payload,
    })
      .then(function () {
        this.successMessage = isNew
          ? "Business page created successfully."
          : "Business page updated successfully.";
        setTimeout(function () {
          m.route.set("/facebook/pacs/business-pages");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? "Failed to create business page."
          : "Failed to update business page.";
      }.bind(this));
  }
}

module.exports = FacebookPacsBusinessPageModel;
