let m = require("mithril");
let FacebookPacsBusinessPortfolioAccessUrlModel = require("../models/facebook_pacs_business_portfolio_access_url");
let i18n = require("../i18n");

class FacebookPacsBusinessPortfolioAccessUrlView {
  constructor() {
    this.businessPortfolioId = m.route.param("businessPortfolioId");
    this.model = new FacebookPacsBusinessPortfolioAccessUrlModel(
      this.businessPortfolioId,
    );
  }

  view() {
    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-6", [
          m(".bg-light.rounded.h-100.p-4", [
            m("h6.mb-4", i18n.t("facebook.accessUrls.new")),
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
                  m("label.form-label", { for: "accessUrl" }, i18n.t("common.url")),
                  m("input.form-control", {
                    type: "text",
                    id: "accessUrl",
                    placeholder: "https://example.com",
                    value: this.model.form.url,
                    oninput: function (event) {
                      this.model.form.url = event.target.value;
                    }.bind(this),
                  }),
                ]),
                m(".mb-3", [
                  m("label.form-label", { for: "accessUrlEmail" }, i18n.t("common.email")),
                  m("input.form-control", {
                    type: "email",
                    id: "accessUrlEmail",
                    placeholder: "name@example.com",
                    value: this.model.form.email,
                    oninput: function (event) {
                      this.model.form.email = event.target.value;
                    }.bind(this),
                  }),
                ]),
                m(".mb-3", [
                  m(
                    "label.form-label",
                    { for: "expiresAt" },
                    i18n.t("facebook.accessUrls.expiresAt"),
                  ),
                  m("input.form-control", {
                    type: "date",
                    id: "expiresAt",
                    value: this.model.form.expiresAt,
                    oninput: function (event) {
                      this.model.form.expiresAt = event.target.value;
                    }.bind(this),
                  }),
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
          ]),
        ]),
      ]),
    );
  }
}

module.exports = FacebookPacsBusinessPortfolioAccessUrlView;
