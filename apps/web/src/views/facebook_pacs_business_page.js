let m = require("mithril");
let FacebookPacsBusinessPageModel = require("../models/facebook_pacs_business_page");

class FacebookPacsBusinessPageView {
  constructor() {
    this.model = new FacebookPacsBusinessPageModel(m.route.param("businessPageId"));
  }

  oninit() {
    let businessPageId = m.route.param("businessPageId");
    if (businessPageId !== "new") {
      this.model.fetch();
    }
  }

  view() {
    let isNew = this.model.businessPageId === "new";

    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-6", [
          m(".bg-light.rounded.h-100.p-4", [
            m(
              "h6.mb-4",
              isNew ? "New Business Page" : "Business Page Modification",
            ),
            this.model.isLoading
              ? m("div", "Loading business page...")
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
                        m("label.form-label", { for: "businessPageName" }, "Name"),
                        m("input.form-control", {
                          type: "text",
                          id: "businessPageName",
                          placeholder: "Business page name",
                          value: this.model.form.name,
                          oninput: function (event) {
                            this.model.form.name = event.target.value;
                          }.bind(this),
                        }),
                      ]),
                      m(".form-check.mb-3", [
                        m("input.form-check-input", {
                          type: "checkbox",
                          id: "businessPageIsBanned",
                          checked: this.model.form.isBanned,
                          onchange: function (event) {
                            this.model.form.isBanned = event.target.checked;
                          }.bind(this),
                        }),
                        m(
                          "label.form-check-label",
                          { for: "businessPageIsBanned" },
                          "Banned",
                        ),
                      ]),
                      m(
                        "button.btn.btn-primary",
                        { type: "submit" },
                        "Save changes",
                      ),
                      m(
                        "button.btn.btn-secondary.ms-2",
                        { type: "reset" },
                        "Reset",
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

module.exports = FacebookPacsBusinessPageView;
