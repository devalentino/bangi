let m = require("mithril");
let api = require("../models/api");
let FacebookPacsCampaignModel = require("../models/facebook_pacs_campaign");
var config = require("../config");
let i18n = require("../i18n");

class FacebookPacsCampaignView {
  constructor() {
    this.model = new FacebookPacsCampaignModel(m.route.param("campaignId"));
    this.executors = [];
    this.adCabinets = [];
    this.businessPages = [];
    this.optionsError = null;
    this.optionsLoading = false;
  }

  oninit() {
    let campaignId = m.route.param("campaignId");
    if (campaignId === "new") {
      this.fetchOptions();
      return;
    }

    // Load options before binding existing ids to selects,
    // otherwise the browser can keep the placeholder selected.
    this.model.isLoading = true;
    this.fetchOptions().then(function () {
      this.model.loadCampaign();
    }.bind(this));
  }

  fetchOptions() {
    this.optionsError = null;
    this.optionsLoading = true;

    return Promise.all([
      api.request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/facebook/pacs/executors`,
        params: { page: 1, pageSize: 1000, sortBy: "id", sortOrder: "asc" },
      }),
      api.request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/facebook/pacs/ad-cabinets`,
        params: { page: 1, pageSize: 1000, sortBy: "id", sortOrder: "asc" },
      }),
      api.request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/facebook/pacs/business-pages`,
        params: { page: 1, pageSize: 1000, sortBy: "id", sortOrder: "asc" },
      }),
    ])
      .then(function (responses) {
        this.executors = responses[0].content || [];
        this.adCabinets = responses[1].content || [];
        this.businessPages = responses[2].content || [];
        this.optionsLoading = false;
      }.bind(this))
      .catch(function () {
        this.optionsError = i18n.t("facebook.campaigns.optionsLoadFailed");
        this.optionsLoading = false;
      }.bind(this));
  }

  view() {
    let isNew = this.model.campaignId === "new";

    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-6", [
          m(".bg-light.rounded.h-100.p-4", [
            m("h6.mb-4", isNew ? i18n.t("facebook.campaigns.new") : i18n.t("facebook.campaigns.modify")),
            this.model.isLoading
              ? m("div", i18n.t("campaigns.loading"))
              : [
                  this.model.error
                    ? m(".alert.alert-danger", this.model.error)
                    : null,
                  this.model.successMessage
                    ? m(".alert.alert-success", this.model.successMessage)
                    : null,
                  this.optionsError
                    ? m(".alert.alert-warning", this.optionsError)
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
                        m("label.form-label", { for: "campaignName" }, i18n.t("common.name")),
                        m("input.form-control", {
                          type: "text",
                          id: "campaignName",
                          placeholder: i18n.t("campaigns.namePlaceholder"),
                          value: this.model.form.name,
                          oninput: function (event) {
                            this.model.form.name = event.target.value;
                          }.bind(this),
                        }),
                      ]),
                      m(".row.g-3", [
                        m(".col-sm-12.col-md-6", [
                          m(
                            "label.form-label",
                            { for: "campaignCostModel" },
                            i18n.t("common.costModel"),
                          ),
                          m(
                            "select.form-select",
                            {
                              id: "campaignCostModel",
                              value: this.model.form.costModel,
                              onchange: function (event) {
                                this.model.form.costModel = event.target.value;
                              }.bind(this),
                            },
                            [
                              m("option", { value: "cpc" }, "CPC"),
                              m("option", { value: "cpm" }, "CPM"),
                              m("option", { value: "cpl" }, "CPL"),
                              m("option", { value: "cpa" }, "CPA"),
                              m("option", { value: "cpi" }, "CPI"),
                            ],
                          ),
                        ]),
                      ]),
                      m(".row.g-3.mt-1", [
                        m(".col-sm-12.col-md-6", [
                          m(
                            "label.form-label",
                            { for: "campaignCostValue" },
                            i18n.t("common.costValue"),
                          ),
                          m("input.form-control", {
                            type: "number",
                            id: "campaignCostValue",
                            placeholder: i18n.t("common.costValue"),
                            value: this.model.form.costValue,
                            oninput: function (event) {
                              this.model.form.costValue = event.target.value;
                            }.bind(this),
                          }),
                        ]),
                        m(".col-sm-12.col-md-6", [
                          m(
                            "label.form-label",
                            { for: "campaignCurrency" },
                            i18n.t("common.currency"),
                          ),
                          m(
                            "select.form-select",
                            {
                              id: "campaignCurrency",
                              value: this.model.form.currency,
                              onchange: function (event) {
                                this.model.form.currency = event.target.value;
                              }.bind(this),
                            },
                            [
                              m("option", { value: "usd" }, "USD"),
                              m("option", { value: "eur" }, "EUR"),
                              m("option", { value: "uah" }, "UAH"),
                            ],
                          ),
                        ]),
                      ]),
                      m(".mb-3.mt-3", [
                        m(
                          "label.form-label",
                          { for: "campaignStatusMapper" },
                          i18n.t("campaigns.statusMapper"),
                        ),
                        m("textarea.form-control.font-monospace", {
                          id: "campaignStatusMapper",
                          rows: "4",
                          placeholder:
                            '{\n'
                            + '  "parameter": "state_on_the_cpa_side",\n'
                            + '  "mapping": {\n'
                            + '    "accept_on_the_cpa_side": "accept",\n'
                            + '    "reject_on_the_cpa_side": "reject",\n'
                            + '    "expect_on_the_cpa_ide": "expect"\n'
                            + '  }\n'
                            + '}',
                          value: this.model.form.statusMapperText,
                          oninput: function (event) {
                            this.model.form.statusMapperText =
                              event.target.value;
                          }.bind(this),
                        }),
                        m(
                          ".form-text",
                          i18n.t("facebook.campaigns.statusMapperHelp"),
                        ),
                      ]),
                      m(".mb-3", [
                        m(
                          "label.form-label",
                          { for: "campaignExecutor" },
                          i18n.t("facebook.executor"),
                        ),
                        m(
                          "select.form-select",
                          {
                            id: "campaignExecutor",
                            value: this.model.form.executorId,
                            onchange: function (event) {
                              this.model.form.executorId = event.target.value;
                            }.bind(this),
                            disabled: this.optionsLoading,
                          },
                          [
                            m("option", { value: "" }, i18n.t("facebook.campaigns.selectExecutor")),
                          ].concat(
                            this.executors.map(function (executor) {
                              return m(
                                "option",
                                { value: executor.id },
                                executor.name,
                              );
                            }),
                          ),
                        ),
                      ]),
                      m(".mb-3", [
                        m(
                          "label.form-label",
                          { for: "campaignAdCabinet" },
                          i18n.t("facebook.adCabinet"),
                        ),
                        m(
                          "select.form-select",
                          {
                            id: "campaignAdCabinet",
                            value: this.model.form.adCabinetId,
                            onchange: function (event) {
                              this.model.form.adCabinetId = event.target.value;
                            }.bind(this),
                            disabled: this.optionsLoading,
                          },
                          [
                            m("option", { value: "" }, i18n.t("facebook.campaigns.selectAdCabinet")),
                          ].concat(
                            this.adCabinets.map(function (adCabinet) {
                              return m(
                                "option",
                                { value: adCabinet.id },
                                adCabinet.name,
                              );
                            }),
                          ),
                        ),
                      ]),
                      m(".mb-3", [
                        m(
                          "label.form-label",
                          { for: "campaignBusinessPage" },
                          i18n.t("facebook.businessPage"),
                        ),
                        m(
                          "select.form-select",
                          {
                            id: "campaignBusinessPage",
                            value: this.model.form.businessPageId,
                            onchange: function (event) {
                              this.model.form.businessPageId = event.target.value;
                            }.bind(this),
                            disabled: this.optionsLoading,
                          },
                          [
                            m("option", { value: "" }, i18n.t("facebook.campaigns.selectBusinessPage")),
                          ].concat(
                            this.businessPages.map(function (businessPage) {
                              return m(
                                "option",
                                { value: businessPage.id },
                                businessPage.name,
                              );
                            }),
                          ),
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

module.exports = FacebookPacsCampaignView;
