let m = require("mithril");
let FacebookPacsExecutorModel = require("../models/facebook_pacs_executor");

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
            m("h6.mb-4", isNew ? "New Executor" : "Executor Modification"),
            this.model.isLoading
              ? m("div", "Loading executor...")
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
                        m("label.form-label", { for: "executorName" }, "Name"),
                        m("input.form-control", {
                          type: "text",
                          id: "executorName",
                          placeholder: "Executor name",
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

module.exports = FacebookPacsExecutorView;
