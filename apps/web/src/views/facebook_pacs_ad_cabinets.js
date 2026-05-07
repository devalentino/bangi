let m = require("mithril");
let FacebookPacsAdCabinetsModel = require("../models/facebook_pacs_ad_cabinets");
let Pagination = require("../components/pagination");

class FacebookPacsAdCabinetsView {
  constructor() {
    this.model = new FacebookPacsAdCabinetsModel();
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
                m("h6.mb-0", "Facebook PACS Ad Cabinets"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/ad-cabinets/new" },
                  "New Ad Cabinet",
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", "Loading ad cabinets...")
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
                          m("th", { scope: "col" }, "Business Portfolio"),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 4 },
                                "No ad cabinets found.",
                              ),
                            ])
                          : this.model.items.map(function (adCabinet) {
                              return m("tr", [
                                m("td", adCabinet.id),
                                m(
                                  "td",
                                  m(
                                    "a",
                                    {
                                      href: `#!/facebook/pacs/ad-cabinets/${adCabinet.id}`,
                                    },
                                    adCabinet.name,
                                  ),
                                ),
                                m(
                                  "td",
                                  adCabinet.isBanned
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
                                  adCabinet.businessPortfolio
                                    ? adCabinet.businessPortfolio.name
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

module.exports = FacebookPacsAdCabinetsView;
