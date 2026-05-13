let m = require("mithril");
let DomainModel = require("../models/domain");
let { timestamp2LocalTime, timestamp2UtcTime } = require("../utils/date");

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
      m("label.form-label", { for: "domainCampaign" }, "Campaign"),
      m(
        "select.form-select",
        {
          id: "domainCampaign",
          value: this.model.form.campaignId,
          onchange: function (event) {
            this.model.form.campaignId = event.target.value;
          }.bind(this),
        },
        [m("option", { value: "" }, "No campaign")].concat(
          this.model.campaigns.map(function (campaign) {
            return m("option", { value: campaign.id }, campaign.name);
          }),
        ),
      ),
    ];
  }

  _purposeBadge() {
    return this.model.form.purpose === "dashboard" ? "Dashboard" : "Campaign";
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
        m("option", { value: "campaign" }, "Campaign"),
        m("option", { value: "dashboard" }, "Dashboard"),
      ],
    );
  }

  _aRecordBadge() {
    if (this.model.form.isARecordSet === true) {
      return [
        m("i.fa.fa-check.text-success.me-2", { title: "Set" }),
        "Set",
      ];
    }

    if (this.model.form.isARecordSet === false) {
      return [
        m("i.fa.fa-times.text-danger.me-2", { title: "Missing" }),
        "Missing",
      ];
    }

    return [
      m("i.fa.fa-question.text-muted.me-2", { title: "Unchecked" }),
      "Unchecked",
    ];
  }

  _certificateStatusText(status) {
    if (!status) {
      return "None";
    }

    return {
      pending: "Pending",
      active: "Active",
      failed: "Failed",
      expired: "Expired",
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
        m("h6.mb-3", "Certificate"),
        this._certificateRow("Status", this._certificateStatusText(null)),
      ]);
    }

    if (this.model.isCertificateLoading) {
      return m(".mt-4", [
        m("h6.mb-3", "Certificate"),
        m("div", "Loading certificate..."),
      ]);
    }

    if (this.model.certificateError) {
      return m(".mt-4", [
        m("h6.mb-3", "Certificate"),
        m(".alert.alert-warning", this.model.certificateError),
        this._certificateRow("Status", this._certificateStatusText(certificateStatus)),
      ]);
    }

    if (!this.model.certificate) {
      return m(".mt-4", [
        m("h6.mb-3", "Certificate"),
        this._certificateRow("Status", this._certificateStatusText(certificateStatus)),
      ]);
    }

    let certificate = this.model.certificate;
    return m(".mt-4", [
      m("h6.mb-3", "Certificate"),
      this._certificateRow("Status", this._certificateStatusText(certificate.status)),
      this._certificateRow("CA", certificate.ca),
      this._certificateRow("Validation method", certificate.validationMethod),
      this._certificateRow("Expires (local)", timestamp2LocalTime(certificate.expiresAt)),
      this._certificateRow("Expires (UTC)", timestamp2UtcTime(certificate.expiresAt)),
      this._certificateRow("Last attempted (local)", timestamp2LocalTime(certificate.lastAttemptedAt)),
      this._certificateRow("Last attempted (UTC)", timestamp2UtcTime(certificate.lastAttemptedAt)),
      this._certificateRow("Last issued (local)", timestamp2LocalTime(certificate.lastIssuedAt)),
      this._certificateRow("Last issued (UTC)", timestamp2UtcTime(certificate.lastIssuedAt)),
      this._certificateRow("Last renewed (local)", timestamp2LocalTime(certificate.lastRenewedAt)),
      this._certificateRow("Last renewed (UTC)", timestamp2UtcTime(certificate.lastRenewedAt)),
      this._certificateRow("Next retry (local)", timestamp2LocalTime(certificate.nextRetryAt)),
      this._certificateRow("Next retry (UTC)", timestamp2UtcTime(certificate.nextRetryAt)),
      this._certificateRow("Failure reason", certificate.failureReason),
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
              isNew ? "New Managed Domain" : "Managed Domain Modification",
            ),
            this.model.isLoading
              ? m("div", "Loading domain...")
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
                        m("label.form-label", { for: "domainHostname" }, "Hostname"),
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
                          m("label.form-label", { for: "domainPurpose" }, "Purpose"),
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
                          "Disabled",
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
        m(".col-12.col-xl-5", [
          m(".bg-light.rounded.h-100.p-4", [
            m("h6.mb-4", "Domain Status"),
            this._certificateRow("A Record", this._aRecordBadge()),
            this._certificatePanel(),
          ]),
        ]),
      ]),
    );
  }
}

module.exports = DomainView;
