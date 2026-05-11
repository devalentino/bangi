let m = require("mithril");
let DomainsModel = require("../models/domains");
let Pagination = require("../components/pagination");

class DomainsView {
  constructor() {
    this.model = new DomainsModel();
  }

  oninit() {
    this.model.fetch();
  }

  _purposeBadge(domain) {
    return domain.purpose === "dashboard" ? "Dashboard" : "Campaign";
  }

  _aRecordBadge(domain) {
    if (domain.isARecordSet === true) {
      return "Set";
    }

    if (domain.isARecordSet === false) {
      return "Missing";
    }

    return "Unchecked";
  }

  _disabledBadge(domain) {
    return domain.isDisabled ? "Disabled" : "Enabled";
  }

  _campaignBadge(domain) {
    if (domain.campaignName) {
      return domain.campaignName;
    }

    return m("span.text-muted", "-");
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
                m("h6.mb-0", "Managed Domains"),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/domains/new" },
                  "New Domain",
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", "Loading domains...")
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
                          m("th", { scope: "col" }, "Hostname"),
                          m("th", { scope: "col" }, "Purpose"),
                          m("th", { scope: "col" }, "Campaign"),
                          m("th", { scope: "col" }, "A Record"),
                          m("th", { scope: "col" }, "State"),
                          m("th", { scope: "col" }, "Actions"),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 7 },
                                "No domains found.",
                              ),
                            ])
                          : this.model.items.map(
                              function (domain) {
                                return m("tr", [
                                  m("td", domain.id),
                                  m(
                                    "td",
                                    m(
                                      "a",
                                      { href: `#!/domains/${domain.id}` },
                                      domain.hostname,
                                    ),
                                  ),
                                  m("td", this._purposeBadge(domain)),
                                  m("td", this._campaignBadge(domain)),
                                  m("td", this._aRecordBadge(domain)),
                                  m("td", this._disabledBadge(domain)),
                                  m(
                                    "td",
                                    m(
                                      "a.btn.btn-outline-primary.btn-sm",
                                      { href: `#!/domains/${domain.id}` },
                                      "Edit",
                                    ),
                                  ),
                                ]);
                              }.bind(this),
                            ),
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

module.exports = DomainsView;
