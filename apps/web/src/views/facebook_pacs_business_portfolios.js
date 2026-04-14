let m = require("mithril");
let FacebookPacsBusinessPortfoliosModel = require("../models/facebook_pacs_business_portfolios");
let Pagination = require("../components/pagination");

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
                m("h6.mb-0", "Facebook PACS Business Portfolios"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/business-portfolios/new" },
                  "New Business Portfolio",
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", "Loading business portfolios...")
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
                          m("th", { scope: "col" }, "Active"),
                          m("th", { scope: "col" }, "Executors"),
                          m("th", { scope: "col" }, "Ad Cabinets"),
                          m("th", { scope: "col" }, "Access URLs"),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 6 },
                                "No business portfolios found.",
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
                                        title: "Banned",
                                      })
                                    : m("i", {
                                        class: "fa fa-check text-success",
                                        title: "Active",
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
                                      title: "Access URLs",
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
