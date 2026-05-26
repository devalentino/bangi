let m = require("mithril");
let FacebookPacsExecutorModel = require("../models/facebook_pacs_executor");
let i18n = require("../i18n");

class FacebookPacsExecutorView {
  constructor() {
    this.model = new FacebookPacsExecutorModel(m.route.param("executorId"));
  }

  oninit() {
    let executorId = m.route.param("executorId");
    if (executorId !== "new") {
      this.model.fetch();
    }
  }

  view() {
    let isNew = this.model.executorId === "new";

    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-6", [
          m(".bg-light.rounded.h-100.p-4", [
            m("h6.mb-4", isNew ? i18n.t("facebook.executors.new") : i18n.t("facebook.executors.modify")),
            this.model.isLoading
              ? m("div", i18n.t("facebook.executors.loadingOne"))
              : [
                  this.model.error
                    ? m(".alert.alert-danger", this.model.error)
                    : null,
                  this.model.successMessage
                    ? m(".alert.alert-success", this.model.successMessage)
                    : null,
                  m(
                    "form",
                    {
                      onsubmit: function (event) {
                        event.preventDefault();
                        this.model.save();
                      }.bind(this),
                      onreset: function (event) {
                        event.preventDefault();
                        this.model.resetForm();
                      }.bind(this),
                    },
                    [
                      m(".mb-3", [
                        m("label.form-label", { for: "executorName" }, i18n.t("common.name")),
                        m("input.form-control", {
                          type: "text",
                          id: "executorName",
                          placeholder: i18n.t("facebook.executors.namePlaceholder"),
                          value: this.model.form.name,
                          oninput: function (event) {
                            this.model.form.name = event.target.value;
                          }.bind(this),
                        }),
                      ]),
                      m(".form-check.mb-3", [
                        m("input.form-check-input", {
                          type: "checkbox",
                          id: "executorIsBanned",
                          checked: this.model.form.isBanned,
                          onchange: function (event) {
                            this.model.form.isBanned = event.target.checked;
                          }.bind(this),
                        }),
                        m(
                          "label.form-check-label",
                          { for: "executorIsBanned" },
                          i18n.t("common.banned"),
                        ),
                      ]),
                      m(
                        "button.btn.btn-primary",
                        { type: "submit" },
                        i18n.t("common.saveChanges"),
                      ),
                      m(
                        "button.btn.btn-secondary.ms-2",
                        { type: "reset" },
                        i18n.t("common.reset"),
                      ),
                    ],
                  ),
                ],
          ]),
        ]),
      ]),
    );
  }
}

module.exports = FacebookPacsExecutorView;
