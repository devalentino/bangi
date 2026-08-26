let m = require("mithril");
let PatTokensModel = require("../models/pat_tokens");
let ConfirmModal = require("../components/confirm_modal");
let { timestamp2LocalTime } = require("../utils/date");
let i18n = require("../i18n");

class PatTokensView {
  constructor() {
    this.model = new PatTokensModel();
    this.form = { name: "" };
    this.isGenerating = false;
    this.generateError = null;
    this.generatedToken = null;
    this.revokeTarget = null;
    this.isRevoking = false;
    this.revokeError = null;
  }

  oninit() {
    this.model.fetch();
  }

  handleGenerate(event) {
    event.preventDefault();

    let name = this.form.name.trim();
    if (name === "") {
      return;
    }

    this.isGenerating = true;
    this.generateError = null;

    this.model
      .generate(name)
      .then(function (payload) {
        this.generatedToken = payload;
        this.form.name = "";
        return this.model.fetch();
      }.bind(this))
      .catch(function () {
        this.generateError = i18n.t("patTokens.generateFailed");
      }.bind(this))
      .finally(function () {
        this.isGenerating = false;
      }.bind(this));
  }

  handleRevoke() {
    if (!this.revokeTarget) {
      return;
    }

    this.isRevoking = true;
    this.revokeError = null;

    this.model
      .revoke(this.revokeTarget.id)
      .then(function () {
        this.revokeTarget = null;
        return this.model.fetch();
      }.bind(this))
      .catch(function () {
        this.revokeError = i18n.t("patTokens.revokeFailed");
      }.bind(this))
      .finally(function () {
        this.isRevoking = false;
      }.bind(this));
  }

  _statusBadge(token) {
    if (token.revokedAt === null) {
      return m("span.badge.bg-success", i18n.t("status.active"));
    }

    return m(
      "span.badge.bg-secondary",
      i18n.t("patTokens.revokedOn", { date: timestamp2LocalTime(token.revokedAt) }),
    );
  }

  view() {
    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12", [
          m(".bg-light.rounded.h-100.p-4", [
            m("h6.mb-4", i18n.t("patTokens.title")),

            this.generatedToken
              ? m(".alert.alert-success.d-flex.align-items-start.justify-content-between.gap-2.mb-4", [
                  m("div", [
                    m("div.fw-bold.mb-1", i18n.t("patTokens.newTokenTitle")),
                    m("div.small.mb-2", i18n.t("patTokens.newTokenWarning")),
                    m("code", this.generatedToken.token),
                  ]),
                  m(".d-flex.align-items-start.gap-2", [
                    m(
                      "button.btn.btn-link.btn-sm.p-0",
                      {
                        type: "button",
                        title: i18n.t("patTokens.copyToken"),
                        "aria-label": i18n.t("patTokens.copyToken"),
                        onclick: function () {
                          navigator.clipboard.writeText(this.generatedToken.token);
                        }.bind(this),
                      },
                      m("i", { class: "fa fa-copy" }),
                    ),
                    m("button.btn-close", {
                      type: "button",
                      "aria-label": i18n.t("patTokens.dismiss"),
                      onclick: function () {
                        this.generatedToken = null;
                      }.bind(this),
                    }),
                  ]),
                ])
              : null,

            this.generateError ? m(".alert.alert-danger", this.generateError) : null,
            this.revokeError ? m(".alert.alert-danger", this.revokeError) : null,

            m(
              "form.row.g-2.align-items-center.mb-4",
              {
                onsubmit: this.handleGenerate.bind(this),
              },
              [
                m(".col-auto", [
                  m(
                    "label.visually-hidden",
                    { for: "patTokenName" },
                    i18n.t("common.name"),
                  ),
                  m("input.form-control", {
                    type: "text",
                    id: "patTokenName",
                    placeholder: i18n.t("patTokens.namePlaceholder"),
                    value: this.form.name,
                    oninput: function (event) {
                      this.form.name = event.target.value;
                    }.bind(this),
                  }),
                ]),
                m(".col-auto", [
                  m(
                    "button.btn.btn-primary",
                    {
                      type: "submit",
                      disabled: this.form.name.trim() === "" || this.isGenerating,
                    },
                    this.isGenerating
                      ? i18n.t("patTokens.generating")
                      : i18n.t("patTokens.generate"),
                  ),
                ]),
              ],
            ),

            this.model.isLoading
              ? m("div", i18n.t("patTokens.loading"))
              : [
                  this.model.error
                    ? m(".alert.alert-danger", this.model.error)
                    : null,
                  m(
                    "div.table-responsive",
                    m("table.table", [
                      m(
                        "thead",
                        m("tr", [
                          m("th", { scope: "col" }, i18n.t("common.name")),
                          m("th", { scope: "col" }, i18n.t("patTokens.token")),
                          m("th", { scope: "col" }, i18n.t("patTokens.createdAt")),
                          m("th", { scope: "col" }, i18n.t("common.status")),
                          m("th", { scope: "col" }, ""),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 5 },
                                i18n.t("patTokens.notFound"),
                              ),
                            ])
                          : this.model.items.map(
                              function (token) {
                                return m("tr", [
                                  m("td", token.name),
                                  m(
                                    "td",
                                    m("code", `${token.tokenPrefix}...${token.tokenSuffix}`),
                                  ),
                                  m("td", timestamp2LocalTime(token.createdAt)),
                                  m("td", this._statusBadge(token)),
                                  m(
                                    "td",
                                    token.revokedAt === null
                                      ? m(
                                          "button.btn.btn-link.btn-sm.p-0.text-danger",
                                          {
                                            type: "button",
                                            onclick: function () {
                                              this.revokeTarget = token;
                                              this.revokeError = null;
                                            }.bind(this),
                                            title: i18n.t("patTokens.revoke"),
                                            "aria-label": i18n.t("patTokens.revoke"),
                                          },
                                          m("i", { class: "fa fa-ban" }),
                                        )
                                      : null,
                                  ),
                                ]);
                              }.bind(this),
                            ),
                      ),
                    ]),
                  ),
                ],

            m(ConfirmModal, {
              isOpen: Boolean(this.revokeTarget),
              isBusy: this.isRevoking,
              title: i18n.t("patTokens.revokeConfirmTitle"),
              body: this.revokeTarget
                ? m(
                    "p.mb-0",
                    i18n.t("patTokens.revokeConfirmMessage", { name: this.revokeTarget.name }),
                  )
                : null,
              confirmText: this.isRevoking
                ? i18n.t("patTokens.revoking")
                : i18n.t("patTokens.revoke"),
              cancelText: i18n.t("common.cancel"),
              onCancel: function () {
                if (this.isRevoking) {
                  return;
                }
                this.revokeTarget = null;
              }.bind(this),
              onConfirm: this.handleRevoke.bind(this),
            }),
          ]),
        ]),
      ]),
    );
  }
}

module.exports = PatTokensView;
