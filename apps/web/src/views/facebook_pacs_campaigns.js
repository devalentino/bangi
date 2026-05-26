let m = require("mithril");
let FacebookPacsCampaignsModel = require("../models/facebook_pacs_campaigns");
let Pagination = require("../components/pagination");
let i18n = require("../i18n");

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
                m("h6.mb-0", i18n.t("facebook.campaigns.title")),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/campaigns/new" },
                  i18n.t("facebook.campaigns.new"),
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", i18n.t("common.loading.campaigns"))
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
                          m("th", { scope: "col" }, i18n.t("common.id")),
                          m("th", { scope: "col" }, i18n.t("common.name")),
                          m("th", { scope: "col" }, i18n.t("facebook.executor")),
                          m("th", { scope: "col" }, i18n.t("facebook.adCabinet")),
                          m("th", { scope: "col" }, i18n.t("facebook.businessPage")),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 5 },
                                i18n.t("campaigns.notFound"),
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
