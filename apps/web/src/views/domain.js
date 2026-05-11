let m = require("mithril");
let DomainModel = require("../models/domain");

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
            m("label.form-label", { for: "domainARecord" }, "A Record"),
            m(
              "#domainARecord.form-control-plaintext",
              this._aRecordBadge(),
            ),
          ]),
        ]),
      ]),
    );
  }
}

module.exports = DomainView;
