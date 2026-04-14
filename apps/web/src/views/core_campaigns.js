let m = require("mithril");
let CoreCampaignsModel = require("../models/core_campaigns");
let Pagination = require("../components/pagination");

class CoreCampaignsView {
  constructor(vnode) {
    this.model = new CoreCampaignsModel();
  }

  oninit() {
    this.model.fetch();
  }

  view() {
    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12", [
          m(".bg-light.rounded.h-100.p-4", [
            m(
              ".d-flex.align-items-center.justify-content-between.mb-4",
              [
                m("h6.mb-0", "Core Campaigns"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/core/campaigns/new" },
                  "New Campaign",
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", "Loading campaigns...")
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
                          m("th", { scope: "col" }, "ID"),
                          m("th", { scope: "col" }, "Name"),
                          m("th", { scope: "col" }, "Cost Model"),
                          m("th", { scope: "col" }, "Cost Value"),
                          m("th", { scope: "col" }, "Currency"),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 5 },
                                "No campaigns found.",
                              ),
                            ])
                          : this.model.items.map(function (campaign) {
                              return m("tr", [
                                m("td", campaign.id),
                                m(
                                  "td",
                                  m(
                                    "a",
                                    { href: `#!/core/campaigns/${campaign.id}` },
                                    campaign.name,
                                  ),
                                ),
                                m("td", campaign.costModel),
                                m("td", campaign.costValue),
                                m("td", campaign.currency),
                              ]);
                            }),
                      ),
                    ]),
                  ),
                  m(Pagination, { pagination: this.model.pagination }),
                ],
          ]),
        ]),
      ]),
    );
  }
}

module.exports = CoreCampaignsView;
