let m = require("mithril");
let ReportsLeadModel = require("../models/reports_lead");
let { timestamp2LocalTime, timestamp2UtcTime } = require("../utils/date");
let { formatCurrency } = require("../utils/currency");
let i18n = require("../i18n");

const FIRST_COLUMN_STYLE = "width: 220px;";
const DETAILS_TABLE_STYLE = "table-layout: fixed; width: 100%;";
const VALUE_COLUMN_STYLE = "overflow-wrap: anywhere; word-break: break-word;";

function renderParameterValue(value) {
  if (value === null || typeof value === "undefined") {
    return "-";
  }

  if (typeof value === "object") {
    return m(
      "pre.mb-0.small",
      { style: "white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word;" },
      JSON.stringify(value, null, 2),
    );
  }

  return String(value);
}

function renderParametersTable(parameters) {
  let parameterKeys = Object.keys(parameters || {});

  if (parameterKeys.length === 0) {
    return m(".text-muted", i18n.t("reports.lead.noParameters"));
  }

  return m(
    "div.table-responsive",
    m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
      m(
        "thead",
        m("tr", [
          m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, i18n.t("reports.lead.parameter")),
          m("th", { scope: "col" }, i18n.t("common.value")),
        ]),
      ),
      m(
        "tbody",
        parameterKeys.map(function (key) {
          return m("tr", [
            m("td", { style: FIRST_COLUMN_STYLE }, key),
            m("td", { style: VALUE_COLUMN_STYLE }, renderParameterValue(parameters[key])),
          ]);
        }),
      ),
    ]),
  );
}

class ReportsLeadView {
  constructor() {
    this.model = new ReportsLeadModel(m.route.param("clickId"));
  }

  oninit() {
    this.model.getLead();
  }

  view() {
    let lead = this.model.lead;

    return this.model.isLoading
      ? m(".container-fluid.pt-4.px-4", [
          m(".row.g-4", [
            m(".col-12", [
              m(".bg-light.rounded.h-100.p-4", i18n.t("reports.lead.loading")),
            ]),
          ]),
        ])
      : this.model.error
        ? m(".container-fluid.pt-4.px-4", [
            m(".row.g-4", [
              m(".col-12", [
                m(".bg-light.rounded.h-100.p-4", [
                  m(".alert.alert-danger.mb-0", this.model.error),
                ]),
              ]),
            ]),
          ])
        : [
            m(".container-fluid.pt-4.px-4", [
              m(".row.g-4", [
                m(".col-12", [
                  m(".bg-light.rounded.h-100.p-4", [
                    m("h6.mb-4", i18n.t("reports.lead.click")),
                    m(
                      "div.table-responsive",
                      m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
                        m(
                          "thead",
                          m("tr", [
                            m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, i18n.t("reports.lead.attribute")),
                            m("th", { scope: "col" }, i18n.t("common.value")),
                          ]),
                        ),
                        m("tbody", [
                          m("tr", [
                            m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.leads.clickId")),
                            m("td", { style: VALUE_COLUMN_STYLE }, String(lead.clickId)),
                          ]),
                          m("tr", [
                            m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("nav.facebookPacs.campaigns")),
                            m(
                              "td",
                              { style: VALUE_COLUMN_STYLE },
                              m(
                                "a",
                                { href: `#!/core/campaigns/${lead.campaignId}` },
                                lead.campaignName,
                              ),
                            ),
                          ]),
                          m("tr", [
                            m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.timeLocal")),
                            m("td", { style: VALUE_COLUMN_STYLE }, String(timestamp2LocalTime(lead.createdAt))),
                          ]),
                          m("tr", [
                            m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.timeUtc")),
                            m("td", { style: VALUE_COLUMN_STYLE }, String(timestamp2UtcTime(lead.createdAt))),
                          ]),
                        ]),
                      ]),
                    ),
                    m("h6.mt-4.mb-3", i18n.t("reports.lead.parameters")),
                    renderParametersTable(lead.parameters),
                  ]),
                ]),
              ]),
            ]),
            lead.postbacks.length === 0
              ? m(".container-fluid.pt-4.px-4", [
                  m(".row.g-4", [
                    m(".col-12", [
                      m(".bg-light.rounded.h-100.p-4", [
                        m("h6.mb-0", i18n.t("reports.lead.postbacks")),
                        m(".text-muted.mt-3", i18n.t("reports.lead.noPostbacks")),
                      ]),
                    ]),
                  ]),
                ])
              : lead.postbacks.map(function (postback, index) {
                  let postbackNumber = lead.postbacks.length - index;

                  return m(".container-fluid.pt-4.px-4", [
                    m(".row.g-4", [
                      m(".col-12", [
                        m(".bg-light.rounded.h-100.p-4", [
                          m("h6.mb-4", i18n.t("reports.lead.postbackNumber", { number: postbackNumber })),
                          m(
                            "div.table-responsive",
                            m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
                              m(
                                "thead",
                                m("tr", [
                                  m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, i18n.t("reports.lead.attribute")),
                                  m("th", { scope: "col" }, i18n.t("common.value")),
                                ]),
                              ),
                              m("tbody", [
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("common.status")),
                                  m("td", { style: VALUE_COLUMN_STYLE }, String(postback.status || "-")),
                                ]),
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.leads.payout")),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(
                                      formatCurrency(
                                        postback.costValue,
                                        postback.currency,
                                      ),
                                    ),
                                  ),
                                ]),
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.timeLocal")),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(
                                      timestamp2LocalTime(postback.createdAt),
                                    ),
                                  ),
                                ]),
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.timeUtc")),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(timestamp2UtcTime(postback.createdAt)),
                                  ),
                                ]),
                              ]),
                            ]),
                          ),
                          m("h6.mt-4.mb-3", i18n.t("reports.lead.parameters")),
                          renderParametersTable(postback.parameters),
                        ]),
                      ]),
                    ]),
                  ]);
                }),
            lead.leads.length === 0
              ? m(".container-fluid.pt-4.px-4", [
                  m(".row.g-4", [
                    m(".col-12", [
                      m(".bg-light.rounded.h-100.p-4", [
                        m("h6.mb-0", i18n.t("nav.leads")),
                        m(".text-muted.mt-3", i18n.t("reports.lead.noLeads")),
                      ]),
                    ]),
                  ]),
                ])
              : lead.leads.map(function (leadItem, index) {
                  let leadNumber = lead.leads.length - index;

                  return m(".container-fluid.pt-4.px-4", [
                    m(".row.g-4", [
                      m(".col-12", [
                        m(".bg-light.rounded.h-100.p-4", [
                          m("h6.mb-4", i18n.t("reports.lead.leadNumber", { number: leadNumber })),
                          m(
                            "div.table-responsive",
                            m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
                              m(
                                "thead",
                                m("tr", [
                                  m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, i18n.t("reports.lead.attribute")),
                                  m("th", { scope: "col" }, i18n.t("common.value")),
                                ]),
                              ),
                              m("tbody", [
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.timeLocal")),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(timestamp2LocalTime(leadItem.createdAt)),
                                  ),
                                ]),
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, i18n.t("reports.timeUtc")),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(timestamp2UtcTime(leadItem.createdAt)),
                                  ),
                                ]),
                              ]),
                            ]),
                          ),
                          m("h6.mt-4.mb-3", i18n.t("reports.lead.parameters")),
                          renderParametersTable(leadItem.parameters),
                        ]),
                      ]),
                    ]),
                  ]);
                }),
          ];
  }
}

module.exports = ReportsLeadView;
