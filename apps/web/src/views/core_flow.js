let m = require("mithril");
let CoreFlowModel = require("../models/core_flow");
let i18n = require("../i18n");

class CoreFlowView {
  constructor(vnode) {
    this.model = new CoreFlowModel(m.route.param("flowId"), m.route.param("campaignId"));
  }
  oninit() {
    let flowId = m.route.param("flowId");
    if (flowId !== "new") {
      this.model.fetch();
    }
  }

  view() {
    let isNew = this.model.flowId === "new";

    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-6", [
          m(".bg-light.rounded.h-100.p-4", [
            m("h6.mb-4", isNew ? i18n.t("flows.new") : i18n.t("flows.modify")),
            this.model.isLoading
              ? m("div", i18n.t("flows.loading"))
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
                      m("input.form-control", {
                        type: "hidden",
                        id: "orderValue",
                        value: this.model.form.orderValue || "0",
                        oninput: function () {},
                      }),
                      m(".row.g-3", [
                        m(".col-sm-12", [
                          m("label.form-label", { for: "flowName" }, i18n.t("common.name")),
                          m("input.form-control", {
                            type: "text",
                            id: "flowName",
                            placeholder: i18n.t("flows.namePlaceholder"),
                            value: this.model.form.name,
                            oninput: function (event) {
                              this.model.form.name = event.target.value;
                            }.bind(this),
                          }),
                        ]),
                        m(".col-sm-12", [
                          m("ul.nav.nav-tabs", [
                            m("li.nav-item", [
                              m(
                                "button.nav-link",
                                {
                                  type: "button",
                                  class:
                                    this.model.form.actionType === "redirect"
                                      ? "active"
                                      : "",
                                  onclick: function () {
                                    this.model.form.actionType = "redirect";
                                    this.model.form.landingArchive = null;
                                  }.bind(this),
                                },
                                i18n.t("flows.redirect"),
                              ),
                            ]),
                            m("li.nav-item", [
                              m(
                                "button.nav-link",
                                {
                                  type: "button",
                                  class:
                                    this.model.form.actionType === "render"
                                      ? "active"
                                      : "",
                                  onclick: function () {
                                    this.model.form.actionType = "render";
                                    this.model.form.redirectUrl = null;
                                  }.bind(this),
                                },
                                i18n.t("flows.render"),
                              ),
                            ]),
                          ]),
                        ]),
                      ]),
                      m(".row.g-3.mt-1", [
                        m(".col-sm-12.col-md-12", [
                          this.model.form.actionType === "redirect"
                            ? [
                                m(
                                  "label.form-label",
                                  { for: "redirectUrl" },
                                  i18n.t("flows.redirectUrl"),
                                ),
                                m("input.form-control", {
                                  type: "url",
                                  id: "redirectUrl",
                                  placeholder: "https://example.com",
                                  value: this.model.form.redirectUrl,
                                  oninput: function (event) {
                                    this.model.form.redirectUrl =
                                      event.target.value;
                                  }.bind(this),
                                }),
                              ]
                            : [
                                this.model.form.hasLandingPage
                                  ? m(".alert.alert-info.mb-3", [
                                      m(
                                        ".fw-semibold",
                                        i18n.t("flows.landingUploaded"),
                                      ),
                                      m(
                                        ".small.mt-1",
                                        i18n.t("flows.replaceArchiveHelp"),
                                      ),
                                    ])
                                  : null,
                                m(
                                  "label.form-label",
                                  { for: "renderFile" },
                                  i18n.t("flows.renderFile"),
                                ),
                                m("input.form-control", {
                                  type: "file",
                                  id: "renderFile",
                                  onchange: function (event) {
                                    this.model.form.landingArchive =
                                      event.target.files[0] || null;
                                  }.bind(this),
                                }),
                              ],
                        ]),
                      ]),
                      m(".mb-3.mt-3", [
                        m("label.form-label", { for: "flowRule" }, i18n.t("flows.rule")),
                        m("textarea.form-control", {
                          id: "flowRule",
                          rows: "4",
                          placeholder:
                            i18n.t("flows.rulePlaceholder"),
                          value: this.model.form.rule,
                          oninput: function (event) {
                            this.model.form.rule = event.target.value;
                          }.bind(this),
                        }),
                        m(".form-text", i18n.t("flows.ruleHelp")),
                      ]),
                      m(".form-check.mt-3", [
                        m("input.form-check-input", {
                          type: "checkbox",
                          id: "isEnabled",
                          checked: this.model.form.isEnabled,
                          onchange: function (event) {
                            this.model.form.isEnabled = event.target.checked;
                          }.bind(this),
                        }),
                        m(
                          "label.form-check-label",
                          { for: "isEnabled" },
                          i18n.t("common.enabled"),
                        ),
                      ]),
                      m(".form-check.mt-3", [
                        m("input.form-check-input", {
                          type: "checkbox",
                          id: "showOncePerVisitor",
                          checked: this.model.form.showOncePerVisitor,
                          onchange: function (event) {
                            this.model.form.showOncePerVisitor =
                              event.target.checked;
                          }.bind(this),
                        }),
                        m(
                          "label.form-check-label",
                          { for: "showOncePerVisitor" },
                          i18n.t("flows.showOncePerVisitor"),
                        ),
                        m(
                          ".form-text",
                          i18n.t("flows.showOncePerVisitorHelp"),
                        ),
                      ]),
                      m(
                        "button.btn.btn-primary.mt-3",
                        { type: "submit" },
                        i18n.t("common.saveChanges"),
                      ),
                      m(
                        "button.btn.btn-secondary.mt-3.ms-2",
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

module.exports = CoreFlowView;
