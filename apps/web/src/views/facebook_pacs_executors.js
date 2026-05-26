let m = require("mithril");
let FacebookPacsExecutorsModel = require("../models/facebook_pacs_executors");
let Pagination = require("../components/pagination");
let i18n = require("../i18n");

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
                m("h6.mb-0", i18n.t("facebook.executors.title")),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/facebook/pacs/executors/new" },
                  i18n.t("facebook.executors.new"),
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", i18n.t("facebook.executors.loading"))
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
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 3 },
                                i18n.t("facebook.executors.notFound"),
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
                                        title: i18n.t("common.banned"),
                                      })
                                    : m("i", {
                                        class: "fa fa-check text-success",
                                        title: i18n.t("common.active"),
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
