let m = require("mithril");
let DomainModel = require("../models/domain");
let { timestamp2LocalTime, timestamp2UtcTime } = require("../utils/date");
let i18n = require("../i18n");

class DomainView {
  constructor() {
    this.model = new DomainModel(m.route.param("domainId") || "new");
  }

  oninit() {
    let domainId = m.route.param("domainId") || "new";
    this.model.fetchCampaigns();

    if (domainId !== "new") {
      this.model.fetch();
    }
  }

  _campaignField() {
    if (this.model.form.purpose !== "campaign") {
      return null;
    }

    return [
      m("label.form-label", { for: "domainCampaign" }, i18n.t("nav.facebookPacs.campaigns")),
      m(
        "select.form-select",
        {
          id: "domainCampaign",
          value: this.model.form.campaignId,
          onchange: function (event) {
            this.model.form.campaignId = event.target.value;
          }.bind(this),
        },
        [m("option", { value: "" }, i18n.t("domains.noCampaign"))].concat(
          this.model.campaigns.map(function (campaign) {
            return m("option", { value: campaign.id }, campaign.name);
          }),
        ),
      ),
    ];
  }

  _purposeBadge() {
    return this.model.form.purpose === "dashboard" ? i18n.t("domains.dashboard") : i18n.t("nav.facebookPacs.campaigns");
  }

  _purposeSelect(disabled) {
    return m(
      "select.form-select",
      {
        id: "domainPurpose",
        value: this.model.form.purpose,
        disabled: disabled,
        onchange: function (event) {
          this.model.form.purpose = event.target.value;
        }.bind(this),
      },
      [
        m("option", { value: "campaign" }, i18n.t("nav.facebookPacs.campaigns")),
        m("option", { value: "dashboard" }, i18n.t("domains.dashboard")),
      ],
    );
  }

  _aRecordBadge() {
    if (this.model.form.isARecordSet === true) {
      return [
        m("i.fa.fa-check.text-success.me-2", { title: i18n.t("domains.set") }),
        i18n.t("domains.set"),
      ];
    }

    if (this.model.form.isARecordSet === false) {
      return [
        m("i.fa.fa-times.text-danger.me-2", { title: i18n.t("domains.missing") }),
        i18n.t("domains.missing"),
      ];
    }

    return [
      m("i.fa.fa-question.text-muted.me-2", { title: i18n.t("domains.unchecked") }),
      i18n.t("domains.unchecked"),
    ];
  }

  _certificateStatusText(status) {
    if (!status) {
      return i18n.t("domains.certificate.none");
    }

    return {
      pending: i18n.t("status.pending"),
      active: i18n.t("status.active"),
      failed: i18n.t("status.failed"),
      expired: i18n.t("status.expired"),
    }[status] || status;
  }

  _certificateRow(label, value) {
    return m(".d-flex.justify-content-between.border-bottom.py-2.small", [
      m("span.text-muted", label),
      m("span.text-end", value || "-"),
    ]);
  }

  _certificatePanel() {
    if (this.model.domainId === "new") {
      return null;
    }

    let certificateStatus = this.model.domain
      ? this.model.domain.certificateStatus
      : null;

    if (!certificateStatus) {
      return m(".mt-4", [
        m("h6.mb-3", i18n.t("domains.certificate")),
        this._certificateRow(i18n.t("domains.certificate.status"), this._certificateStatusText(null)),
      ]);
    }

    if (this.model.isCertificateLoading) {
      return m(".mt-4", [
        m("h6.mb-3", i18n.t("domains.certificate")),
        m("div", i18n.t("domains.certificate.loading")),
      ]);
    }

    if (this.model.certificateError) {
      return m(".mt-4", [
        m("h6.mb-3", i18n.t("domains.certificate")),
        m(".alert.alert-warning", this.model.certificateError),
        this._certificateRow(i18n.t("domains.certificate.status"), this._certificateStatusText(certificateStatus)),
      ]);
    }

    if (!this.model.certificate) {
      return m(".mt-4", [
        m("h6.mb-3", i18n.t("domains.certificate")),
        this._certificateRow(i18n.t("domains.certificate.status"), this._certificateStatusText(certificateStatus)),
      ]);
    }

    let certificate = this.model.certificate;
    return m(".mt-4", [
      m("h6.mb-3", i18n.t("domains.certificate")),
      this._certificateRow(i18n.t("domains.certificate.status"), this._certificateStatusText(certificate.status)),
      this._certificateRow(i18n.t("domains.certificate.ca"), certificate.ca),
      this._certificateRow(i18n.t("domains.certificate.validationMethod"), certificate.validationMethod),
      this._certificateRow(i18n.t("domains.certificate.expiresLocal"), timestamp2LocalTime(certificate.expiresAt)),
      this._certificateRow(i18n.t("domains.certificate.expiresUtc"), timestamp2UtcTime(certificate.expiresAt)),
      this._certificateRow(i18n.t("domains.certificate.lastAttemptedLocal"), timestamp2LocalTime(certificate.lastAttemptedAt)),
      this._certificateRow(i18n.t("domains.certificate.lastAttemptedUtc"), timestamp2UtcTime(certificate.lastAttemptedAt)),
      this._certificateRow(i18n.t("domains.certificate.lastIssuedLocal"), timestamp2LocalTime(certificate.lastIssuedAt)),
      this._certificateRow(i18n.t("domains.certificate.lastIssuedUtc"), timestamp2UtcTime(certificate.lastIssuedAt)),
      this._certificateRow(i18n.t("domains.certificate.lastRenewedLocal"), timestamp2LocalTime(certificate.lastRenewedAt)),
      this._certificateRow(i18n.t("domains.certificate.lastRenewedUtc"), timestamp2UtcTime(certificate.lastRenewedAt)),
      this._certificateRow(i18n.t("domains.certificate.nextRetryLocal"), timestamp2LocalTime(certificate.nextRetryAt)),
      this._certificateRow(i18n.t("domains.certificate.nextRetryUtc"), timestamp2UtcTime(certificate.nextRetryAt)),
      this._certificateRow(i18n.t("domains.certificate.failureReason"), certificate.failureReason),
    ]);
  }

  view() {
    let isNew = this.model.domainId === "new";
    let validationAlertText = this.model.validationAlertText();
    let isCampaignBound = this.model.form.campaignId !== "";

    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-7", [
          m(".bg-light.rounded.h-100.p-4", [
            m(
              "h6.mb-4",
              isNew ? i18n.t("domains.newManaged") : i18n.t("domains.modify"),
            ),
            this.model.isLoading
              ? m("div", i18n.t("domains.loadingOne"))
              : [
                  this.model.error
                    ? m(".alert.alert-danger", this.model.error)
                    : null,
                  this.model.successMessage
                    ? m(".alert.alert-success", this.model.successMessage)
                    : null,
                  validationAlertText
                    ? m(".alert.alert-danger", validationAlertText)
                    : null,
                  this.model.campaignError
                    ? m(".alert.alert-warning", this.model.campaignError)
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
                        m("label.form-label", { for: "domainHostname" }, i18n.t("domains.hostname")),
                        m("input.form-control", {
                          id: "domainHostname",
                          type: "text",
                          placeholder: "example.com",
                          value: this.model.form.hostname,
                          oninput: function (event) {
                            this.model.form.hostname = event.target.value;
                          }.bind(this),
                        }),
                      ]),
                      m(".row.g-3", [
                        m(".col-sm-12.col-md-6", [
                          m("label.form-label", { for: "domainPurpose" }, i18n.t("domains.purpose")),
                          this._purposeSelect(!isNew && isCampaignBound),
                        ]),
                        m(".col-sm-12.col-md-6", [
                          this._campaignField(),
                        ]),
                      ]),
                      m(".form-check.my-3", [
                        m("input.form-check-input", {
                          id: "domainDisabled",
                          type: "checkbox",
                          checked: this.model.form.isDisabled,
                          onchange: function (event) {
                            this.model.form.isDisabled = event.target.checked;
                          }.bind(this),
                        }),
                        m(
                          "label.form-check-label",
                          { for: "domainDisabled" },
                          i18n.t("common.disabled"),
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
        m(".col-12.col-xl-5", [
          m(".bg-light.rounded.h-100.p-4", [
            m("h6.mb-4", i18n.t("domains.domainStatus")),
            this._certificateRow(i18n.t("domains.aRecord"), this._aRecordBadge()),
            this._certificatePanel(),
          ]),
        ]),
      ]),
    );
  }
}

module.exports = DomainView;
