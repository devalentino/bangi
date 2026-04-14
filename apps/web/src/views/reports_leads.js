let m = require("mithril");
let Pagination = require("../components/pagination");
let ReportsLeadsModel = require("../models/reports_leads");
let { timestamp2LocalTime, timestamp2UtcTime } = require("../utils/date");
let { formatCurrency } = require("../utils/currency");

function renderStatus(status) {
  if (!status) {
    return "-";
  }

  let mapping = {
    accept: m("i.fa.fa-check.text-success", { title: "accept" }),
    expect: m("i.fa.fa-clock.text-warning", { title: "expect" }),
    reject: m("i.fa.fa-times.text-danger", { title: "reject" }),
    trash: m("i.fa.fa-trash", { title: "trash", style: "color: magenta;" }),
  };

  return mapping[status] || status;
}

class ReportsLeadsView {
  constructor() {
    this.model = new ReportsLeadsModel();
    this.routeKeyCurrent = null;
  }

  oninit() {
    this.model.loadCampaigns().then(
      function () {
        return this.ensureRouteDefaults();
      }.bind(this),
    );
  }

  onupdate() {
    let routeKey = this.routeKey();

    if (routeKey !== this.routeKeyCurrent && !this.model.isLoadingCampaigns) {
      this.routeKeyCurrent = routeKey;
      this.model.loadLeads();
    }
  }

  routeKey() {
    return JSON.stringify({
      campaignId: m.route.param("campaignId") || null,
      page: m.route.param("page") || 1,
      pageSize: m.route.param("pageSize") || 20,
      sortBy: m.route.param("sortBy") || "createdAt",
      sortOrder: m.route.param("sortOrder") || "desc",
    });
  }

  ensureRouteDefaults() {
    if (this.model.campaigns.length === 0) {
      return Promise.resolve();
    }

    let campaignId = Number(m.route.param("campaignId"));
    let page = Number(m.route.param("page") || 1);
    let hasSelectedCampaign = this.model.campaigns.some(function (campaign) {
      return Number(campaign.id) === campaignId;
    });

    if (!hasSelectedCampaign) {
      m.route.set("/reports/leads", {
        campaignId: Number(this.model.campaigns[0].id),
        page: 1,
      });
      return Promise.resolve();
    }

    if (page < 1) {
      m.route.set("/reports/leads", {
        campaignId: campaignId,
        page: 1,
      });
      return Promise.resolve();
    }

    this.routeKeyCurrent = this.routeKey();
    return this.model.loadLeads();
  }

  onCampaignChange(event) {
    let campaignId = Number(event.target.value);

    m.route.set("/reports/leads", {
      campaignId: campaignId,
      page: 1,
      pageSize: m.route.param("pageSize") || 20,
      sortBy: m.route.param("sortBy") || "createdAt",
      sortOrder: m.route.param("sortOrder") || "desc",
    });
  }

  view() {
    return m(
      ".container-fluid.pt-4.px-4",
      [
        m(".row.g-4", [
          m(
            ".col-sm-12.col-md-6.col-xl-4",
            m(".h-100.bg-light.rounded.p-4", [
              m(
                ".d-flex.align-items-center.justify-content-between.mb-4",
                m("h6.mb-0", "Campaign"),
              ),
              m(
                ".d-flex.mb-2",
                m(
                  "select.form-select.mb-3",
                  {
                    id: "leadCampaignId",
                    "aria-label": "Campaign",
                    value: m.route.param("campaignId") || "",
                    oninput: this.onCampaignChange.bind(this),
                    disabled:
                      this.model.isLoadingCampaigns ||
                      this.model.campaigns.length === 0,
                  },
                  this.model.campaigns.length === 0
                    ? [
                        m(
                          "option",
                          { value: "" },
                          this.model.isLoadingCampaigns
                            ? "Loading campaigns..."
                            : "No campaigns",
                        ),
                      ]
                    : this.model.campaigns.map(function (campaign) {
                        return m(
                          "option",
                          { value: campaign.id },
                          campaign.name || `Campaign #${campaign.id}`,
                        );
                      }),
                ),
              ),
            ]),
          ),
        ]),
        m(".row.g-4.mt-1", [
          m(".col-12", [
            m(".bg-light.rounded.h-100.p-4", [
              m("h6.mb-4", "Reports Leads"),
            this.model.campaignError
              ? m(".alert.alert-danger", this.model.campaignError)
              : null,
            this.model.isLoading
              ? m("div", "Loading leads...")
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
                          m("th", { scope: "col" }, "Click ID"),
                          m("th", { scope: "col" }, "Status"),
                          m("th", { scope: "col" }, "Payout"),
                          m("th", { scope: "col" }, "Time (Local)"),
                          m("th", { scope: "col" }, "Time (UTC)"),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.leads.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 5 },
                                "No leads found.",
                              ),
                            ])
                          : this.model.leads.map(function (lead) {
                              return m("tr", [
                                m(
                                  "td",
                                  m(
                                    "a",
                                    { href: `#!/reports/leads/${lead.clickId}` },
                                    lead.clickId,
                                  ),
                                ),
                                m("td", renderStatus(lead.status)),
                                m(
                                  "td",
                                  formatCurrency(lead.costValue, lead.currency),
                                ),
                                m("td", timestamp2LocalTime(lead.createdAt)),
                                m("td", timestamp2UtcTime(lead.createdAt)),
                              ]);
                            }.bind(this)),
                      ),
                    ]),
                  ),
                  this.model.pagination
                    ? m(Pagination, { pagination: this.model.pagination })
                    : null,
                ],
            ]),
          ]),
        ]),
      ],
    );
  }
}

module.exports = ReportsLeadsView;
