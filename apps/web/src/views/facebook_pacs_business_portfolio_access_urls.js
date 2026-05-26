let m = require("mithril");
let FacebookPacsBusinessPortfolioAccessUrlsModel = require("../models/facebook_pacs_business_portfolio_access_urls");
let Pagination = require("../components/pagination");
let i18n = require("../i18n");

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
    if (!window.confirm(i18n.t("facebook.accessUrls.deleteConfirm"))) {
      return;
    }

    this.model
      .deleteAccessUrl(accessUrlId)
      .then(function () {
        this.model.fetch();
      }.bind(this))
      .catch(function () {
        this.model.error = i18n.t("facebook.accessUrls.deleteFailed");
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
                m("h6.mb-0", i18n.t("facebook.accessUrls.title")),
                m(
                  "a.btn.btn-primary.btn-sm",
                  {
                    href: `#!/facebook/pacs/business-portfolios/${this.businessPortfolioId}/access-urls/new`,
                  },
                  i18n.t("facebook.accessUrls.new"),
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", i18n.t("facebook.accessUrls.loading"))
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
                          m("th", { scope: "col" }, i18n.t("common.url")),
                          m("th", { scope: "col" }, i18n.t("common.email")),
                          m("th", { scope: "col" }, i18n.t("facebook.accessUrls.expiresAt")),
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
                                i18n.t("facebook.accessUrls.notFound"),
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
                                        title: i18n.t("facebook.accessUrls.copyFull"),
                                        "aria-label": i18n.t("facebook.accessUrls.copyFull"),
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
                                      title: i18n.t("facebook.accessUrls.delete"),
                                      "aria-label": i18n.t("facebook.accessUrls.delete"),
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
