let m = require("mithril");
let ReportsLeadModel = require("../models/reports_lead");
let { timestamp2LocalTime, timestamp2UtcTime } = require("../utils/date");
let { formatCurrency } = require("../utils/currency");

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
    return m(".text-muted", "No parameters.");
  }

  return m(
    "div.table-responsive",
    m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
      m(
        "thead",
        m("tr", [
          m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, "Parameter"),
          m("th", { scope: "col" }, "Value"),
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
              m(".bg-light.rounded.h-100.p-4", "Loading lead..."),
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
                    m("h6.mb-4", "Click"),
                    m(
                      "div.table-responsive",
                      m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
                        m(
                          "thead",
                          m("tr", [
                            m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, "Attribute"),
                            m("th", { scope: "col" }, "Value"),
                          ]),
                        ),
                        m("tbody", [
                          m("tr", [
                            m("td", { style: FIRST_COLUMN_STYLE }, "Click ID"),
                            m("td", { style: VALUE_COLUMN_STYLE }, String(lead.clickId)),
                          ]),
                          m("tr", [
                            m("td", { style: FIRST_COLUMN_STYLE }, "Campaign"),
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
                            m("td", { style: FIRST_COLUMN_STYLE }, "Time (Local)"),
                            m("td", { style: VALUE_COLUMN_STYLE }, String(timestamp2LocalTime(lead.createdAt))),
                          ]),
                          m("tr", [
                            m("td", { style: FIRST_COLUMN_STYLE }, "Time (UTC)"),
                            m("td", { style: VALUE_COLUMN_STYLE }, String(timestamp2UtcTime(lead.createdAt))),
                          ]),
                        ]),
                      ]),
                    ),
                    m("h6.mt-4.mb-3", "Parameters"),
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
                        m("h6.mb-0", "Postbacks"),
                        m(".text-muted.mt-3", "No postbacks found."),
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
                          m("h6.mb-4", `Postback #${postbackNumber}`),
                          m(
                            "div.table-responsive",
                            m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
                              m(
                                "thead",
                                m("tr", [
                                  m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, "Attribute"),
                                  m("th", { scope: "col" }, "Value"),
                                ]),
                              ),
                              m("tbody", [
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, "Status"),
                                  m("td", { style: VALUE_COLUMN_STYLE }, String(postback.status || "-")),
                                ]),
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, "Payout"),
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
                                  m("td", { style: FIRST_COLUMN_STYLE }, "Time (Local)"),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(
                                      timestamp2LocalTime(postback.createdAt),
                                    ),
                                  ),
                                ]),
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, "Time (UTC)"),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(timestamp2UtcTime(postback.createdAt)),
                                  ),
                                ]),
                              ]),
                            ]),
                          ),
                          m("h6.mt-4.mb-3", "Parameters"),
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
                        m("h6.mb-0", "Leads"),
                        m(".text-muted.mt-3", "No leads found."),
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
                          m("h6.mb-4", `Lead #${leadNumber}`),
                          m(
                            "div.table-responsive",
                            m("table.table.table-sm.mb-0", { style: DETAILS_TABLE_STYLE }, [
                              m(
                                "thead",
                                m("tr", [
                                  m("th", { scope: "col", style: FIRST_COLUMN_STYLE }, "Attribute"),
                                  m("th", { scope: "col" }, "Value"),
                                ]),
                              ),
                              m("tbody", [
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, "Time (Local)"),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(timestamp2LocalTime(leadItem.createdAt)),
                                  ),
                                ]),
                                m("tr", [
                                  m("td", { style: FIRST_COLUMN_STYLE }, "Time (UTC)"),
                                  m(
                                    "td",
                                    { style: VALUE_COLUMN_STYLE },
                                    String(timestamp2UtcTime(leadItem.createdAt)),
                                  ),
                                ]),
                              ]),
                            ]),
                          ),
                          m("h6.mt-4.mb-3", "Parameters"),
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
