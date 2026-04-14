let m = require("mithril");
let FacebookPacsCampaignsModel = require("../models/facebook_pacs_campaigns");
let Pagination = require("../components/pagination");

class FacebookPacsCampaignsView {
  constructor() {
    this.model = new FacebookPacsCampaignsModel();
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
                m("h6.mb-0", "Facebook PACS Campaigns"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/campaigns/new" },
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
                          m("th", { scope: "col" }, "Executor"),
                          m("th", { scope: "col" }, "Ad Cabinet"),
                          m("th", { scope: "col" }, "Business Page"),
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
                                    {
                                      href: `#!/facebook/pacs/campaigns/${campaign.id}`,
                                    },
                                    campaign.name,
                                  ),
                                ),
                                m(
                                  "td",
                                  campaign.executor ? campaign.executor.name : "—",
                                ),
                                m(
                                  "td",
                                  campaign.adCabinet ? campaign.adCabinet.name : "—",
                                ),
                                m(
                                  "td",
                                  campaign.businessPage
                                    ? campaign.businessPage.name
                                    : "—",
                                ),
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

module.exports = FacebookPacsCampaignsView;
