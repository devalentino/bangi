let m = require("mithril");
let FacebookPacsExecutorsModel = require("../models/facebook_pacs_executors");
let Pagination = require("../components/pagination");

class FacebookPacsExecutorsView {
  constructor() {
    this.model = new FacebookPacsExecutorsModel();
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
                m("h6.mb-0", "Facebook PACS Executors"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/executors/new" },
                  "New Executor",
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", "Loading executors...")
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
                                "No executors found.",
                              ),
                            ])
                          : this.model.items.map(function (executor) {
                              return m("tr", [
                                m("td", executor.id),
                                m(
                                  "td",
                                  m(
                                    "a",
                                    {
                                      href: `#!/facebook/pacs/executors/${executor.id}`,
                                    },
                                    executor.name,
                                  ),
                                ),
                                m(
                                  "td",
                                  executor.isBanned
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

module.exports = FacebookPacsExecutorsView;
