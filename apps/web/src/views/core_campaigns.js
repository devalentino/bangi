let m = require("mithril");
let CoreCampaignsModel = require("../models/core_campaigns");
let Pagination = require("../components/pagination");
let { timestamp2LocalTime } = require("../utils/date");
let i18n = require("../i18n");

function formatClickShare(clickShare) {
  return `${(clickShare * 100).toFixed(2)}%`;
}

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
                m("h6.mb-0", i18n.t("campaigns.core.title")),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/core/campaigns/new" },
                  i18n.t("campaigns.new"),
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
                          m("th", { scope: "col" }, i18n.t("common.costModel")),
                          m("th", { scope: "col" }, i18n.t("common.costValue")),
                          m("th", { scope: "col" }, i18n.t("common.currency")),
                          m("th", { scope: "col" }, i18n.t("statistics.clicks")),
                          m("th", { scope: "col" }, i18n.t("campaigns.clickShare")),
                          m("th", { scope: "col" }, i18n.t("campaigns.lastActivity")),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 8 },
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
                                    { href: `#!/core/campaigns/${campaign.id}` },
                                    campaign.name,
                                  ),
                                ),
                                m("td", campaign.costModel),
                                m("td", campaign.costValue),
                                m("td", campaign.currency),
                                m("td", campaign.summary ? campaign.summary.clickCount : "-"),
                                m(
                                  "td",
                                  campaign.summary
                                    ? formatClickShare(campaign.summary.clickShare)
                                    : "-",
                                ),
                                m(
                                  "td",
                                  campaign.summary
                                    ? timestamp2LocalTime(campaign.summary.lastActivityAt)
                                    : "-",
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

module.exports = CoreCampaignsView;
module.exports.formatClickShare = formatClickShare;
