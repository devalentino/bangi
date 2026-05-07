let m = require("mithril");
let FacebookPacsBusinessPortfolioAccessUrlsModel = require("../models/facebook_pacs_business_portfolio_access_urls");
let Pagination = require("../components/pagination");

class FacebookPacsBusinessPortfolioAccessUrlsView {
  constructor() {
    this.businessPortfolioId = m.route.param("businessPortfolioId");
    this.model = new FacebookPacsBusinessPortfolioAccessUrlsModel(
      this.businessPortfolioId,
    );
  }

  oninit() {
    this.model.fetch();
  }

  shortenUrl(url) {
    if (!url || url.length <= 60) {
      return url;
    }

    return `${url.slice(0, 60)}...`;
  }

  handleDelete(accessUrlId) {
    if (!window.confirm("Delete this access URL?")) {
      return;
    }

    this.model
      .deleteAccessUrl(accessUrlId)
      .then(function () {
        this.model.fetch();
      }.bind(this))
      .catch(function () {
        this.model.error = "Failed to delete access URL.";
      }.bind(this));
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
                m("h6.mb-0", "Business Portfolio Access URLs"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  {
                    href: `#!/facebook/pacs/business-portfolios/${this.businessPortfolioId}/access-urls/new`,
                  },
                  "New Access URL",
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", "Loading access URLs...")
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
                          m("th", { scope: "col" }, "URL"),
                          m("th", { scope: "col" }, "Email"),
                          m("th", { scope: "col" }, "Expires At"),
                          m("th", { scope: "col" }, ""),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 4 },
                                "No access URLs found.",
                              ),
                            ])
                          : this.model.items.map(function (accessUrl) {
                              return m("tr", [
                                m(
                                  "td",
                                  m(".d-flex.align-items-center.gap-2", [
                                    m(
                                      "span",
                                      { title: accessUrl.url },
                                      this.shortenUrl(accessUrl.url),
                                    ),
                                    m(
                                      "button.btn.btn-link.btn-sm.p-0",
                                      {
                                        type: "button",
                                        title: "Copy full URL",
                                        "aria-label": "Copy full URL",
                                        onclick: function () {
                                            navigator.clipboard.writeText(accessUrl.url);
                                        }.bind(this),
                                      },
                                      m("i", { class: "fa fa-copy" }),
                                    ),
                                  ]),
                                ),
                                m("td", accessUrl.email || "-"),
                                m("td", accessUrl.expiresAt),
                                m(
                                  "td",
                                  m(
                                    "button.btn.btn-link.btn-sm.p-0.text-danger",
                                    {
                                      type: "button",
                                      onclick: function () {
                                        this.handleDelete(accessUrl.id);
                                      }.bind(this),
                                      title: "Delete access URL",
                                      "aria-label": "Delete access URL",
                                    },
                                    m("i", { class: "fa fa-trash" }),
                                  ),
                                ),
                              ]);
                            }.bind(this)),
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

module.exports = FacebookPacsBusinessPortfolioAccessUrlsView;
