const m = require("mithril");
const api = require("./api");
var config = require("../config");
const i18n = require("../i18n");

class FacebookPacsExecutorModel {
  constructor(executorId) {
    this.executorId = executorId;
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
      url: `${config.backendApiBaseUrl}/facebook/pacs/executors/${this.executorId}`,
    })
      .then(function (payload) {
        this.lastLoaded = payload;
        this.setFormValues(payload);
        this.isLoading = false;
      }.bind(this))
      .catch(function () {
        this.error = i18n.t("messages.failedLoad", { entity: i18n.t("entities.executor") });
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
    let isNew = this.executorId === "new";
    let method = isNew ? "POST" : "PATCH";
    let url = isNew
      ? `${config.backendApiBaseUrl}/facebook/pacs/executors`
      : `${config.backendApiBaseUrl}/facebook/pacs/executors/${this.executorId}`;

    api.request({
      method: method,
      url: url,
      body: payload,
    })
      .then(function () {
        this.successMessage = isNew
          ? i18n.t("messages.created", { entity: i18n.t("entities.executor") })
          : i18n.t("messages.updated", { entity: i18n.t("entities.executor") });
        setTimeout(function () {
          m.route.set("/facebook/pacs/executors");
        }, 2000);
      }.bind(this))
      .catch(function () {
        this.error = isNew
          ? i18n.t("messages.failedCreate", { entity: i18n.t("entities.executor") })
          : i18n.t("messages.failedUpdate", { entity: i18n.t("entities.executor") });
      }.bind(this));
  }
}

module.exports = FacebookPacsExecutorModel;
