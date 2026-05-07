let m = require("mithril");
let FacebookPacsBusinessPagesModel = require("../models/facebook_pacs_business_pages");
let Pagination = require("../components/pagination");

class FacebookPacsBusinessPagesView {
  constructor() {
    this.model = new FacebookPacsBusinessPagesModel();
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
                m("h6.mb-0", "Facebook PACS Business Pages"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/business-pages/new" },
                  "New Business Page",
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", "Loading business pages...")
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
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 3 },
                                "No business pages found.",
                              ),
                            ])
                          : this.model.items.map(function (businessPage) {
                              return m("tr", [
                                m("td", businessPage.id),
                                m(
                                  "td",
                                  m(
                                    "a",
                                    {
                                      href: `#!/facebook/pacs/business-pages/${businessPage.id}`,
                                    },
                                    businessPage.name,
                                  ),
                                ),
                                m(
                                  "td",
                                  businessPage.isBanned
                                    ? m("i", {
                                        class: "fa fa-ban text-danger",
                                        title: "Banned",
                                      })
                                    : m("i", {
                                        class: "fa fa-check text-success",
                                        title: "Active",
                                      }),
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

module.exports = FacebookPacsBusinessPagesView;
