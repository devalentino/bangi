let m = require("mithril");
let FacebookPacsBusinessPortfoliosModel = require("../models/facebook_pacs_business_portfolios");
let Pagination = require("../components/pagination");
let i18n = require("../i18n");

class FacebookPacsBusinessPortfoliosView {
  constructor() {
    this.model = new FacebookPacsBusinessPortfoliosModel();
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
                m("h6.mb-0", i18n.t("facebook.businessPortfolios.title")),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/business-portfolios/new" },
                  i18n.t("facebook.businessPortfolios.new"),
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", i18n.t("facebook.businessPortfolios.loading"))
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
                          m("th", { scope: "col" }, i18n.t("common.active")),
                          m("th", { scope: "col" }, i18n.t("facebook.executors")),
                          m("th", { scope: "col" }, i18n.t("facebook.adCabinets")),
                          m("th", { scope: "col" }, i18n.t("facebook.accessUrls")),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 6 },
                                i18n.t("facebook.businessPortfolios.notFound"),
                              ),
                            ])
                          : this.model.items.map(function (portfolio) {
                              return m("tr", [
                                m("td", portfolio.id),
                                m(
                                  "td",
                                  m(
                                    "a",
                                    {
                                      href: `#!/facebook/pacs/business-portfolios/${portfolio.id}`,
                                    },
                                    portfolio.name,
                                  ),
                                ),
                                m(
                                  "td",
                                  portfolio.isBanned
                                    ? m("i", {
                                        class: "fa fa-ban text-danger",
                                        title: i18n.t("common.banned"),
                                      })
                                    : m("i", {
                                        class: "fa fa-check text-success",
                                        title: i18n.t("common.active"),
                                      }),
                                ),
                                m(
                                  "td",
                                  (portfolio.executors || []).length,
                                ),
                                m(
                                  "td",
                                  (portfolio.adCabinets || []).length,
                                ),
                                m(
                                  "td",
                                  m(
                                    "a",
                                    {
                                      href: `#!/facebook/pacs/business-portfolios/${portfolio.id}/access-urls`,
                                    },
                                    m("i", {
                                      class: "fa fa-link",
                                      title: i18n.t("facebook.accessUrls"),
                                    }),
                                  ),
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

module.exports = FacebookPacsBusinessPortfoliosView;
