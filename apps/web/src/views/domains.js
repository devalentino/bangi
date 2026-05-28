let m = require("mithril");
let DomainsModel = require("../models/domains");
let Pagination = require("../components/pagination");
let i18n = require("../i18n");

class DomainsView {
  constructor() {
    this.model = new DomainsModel();
  }

  oninit() {
    this.model.fetch();
  }

  _purposeBadge(domain) {
    return domain.purpose === "dashboard" ? i18n.t("domains.dashboard") : i18n.t("nav.facebookPacs.campaigns");
  }

  _aRecordBadge(domain) {
    if (domain.isARecordSet === true) {
      return i18n.t("domains.set");
    }

    if (domain.isARecordSet === false) {
      return i18n.t("domains.missing");
    }

    return i18n.t("domains.unchecked");
  }

  _disabledBadge(domain) {
    return domain.isDisabled
      ? m("i", {
          class: "fa fa-ban text-danger",
          title: i18n.t("common.disabled"),
        })
      : m("i", {
          class: "fa fa-check text-success",
          title: i18n.t("common.enabled"),
        });
  }

  _certificateBadge(domain) {
    if (!domain.certificateStatus) {
      return m("span.text-muted", "-");
    }

    let statusClasses = {
      pending: "badge bg-secondary",
      active: "badge bg-success",
      failed: "badge bg-danger",
      expired: "badge bg-danger",
    };
    let labels = {
      pending: i18n.t("status.pending"),
      active: i18n.t("status.active"),
      failed: i18n.t("status.failed"),
      expired: i18n.t("status.expired"),
    };

    return m(
      "span",
      { class: statusClasses[domain.certificateStatus] || "badge bg-secondary" },
      labels[domain.certificateStatus] || domain.certificateStatus,
    );
  }

  _campaignBadge(domain) {
    if (domain.campaignId && domain.campaignName) {
      return m(
        "a",
        { href: `#!/core/campaigns/${domain.campaignId}` },
        domain.campaignName,
      );
    }

    return m("span.text-muted", "-");
  }

  _targetUrl(hostname) {
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(hostname)) {
      return hostname;
    }

    return `https://${hostname}`;
  }

  _hostnameCell(domain) {
    let openTargetLabel = i18n.t("domains.openTarget");

    return m(".d-flex.align-items-center.gap-2", [
      m(
        "a",
        { href: `#!/domains/${domain.id}` },
        domain.hostname,
      ),
      m(
        "a.btn.btn-link.btn-sm.p-0",
        {
          href: this._targetUrl(domain.hostname),
          target: "_blank",
          rel: "noopener noreferrer",
          title: openTargetLabel,
          "aria-label": openTargetLabel,
        },
        m("i", { class: "fa fa-external-link-alt" }),
      ),
    ]);
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
                m("h6.mb-0", i18n.t("domains.managed")),
                m(
                  "a.btn.btn-primary.btn-sm",
                  { href: "#!/domains/new" },
                  i18n.t("domains.new"),
                ),
              ],
            ),
            this.model.isLoading
              ? m("div", i18n.t("domains.loading"))
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
                          m("th", { scope: "col" }, i18n.t("domains.hostname")),
                          m("th", { scope: "col" }, i18n.t("domains.purpose")),
                          m("th", { scope: "col" }, i18n.t("nav.facebookPacs.campaigns")),
                          m("th", { scope: "col" }, i18n.t("domains.aRecord")),
                          m("th", { scope: "col" }, i18n.t("domains.certificate")),
                          m("th", { scope: "col" }, i18n.t("domains.state")),
                        ]),
                      ),
                      m(
                        "tbody",
                        this.model.items.length === 0
                          ? m("tr", [
                              m(
                                "td.text-center",
                                { colspan: 7 },
                                i18n.t("domains.notFound"),
                              ),
                            ])
                          : this.model.items.map(
                              function (domain) {
                                return m("tr", [
                                  m("td", domain.id),
                                  m(
                                    "td",
                                    this._hostnameCell(domain),
                                  ),
                                  m("td", this._purposeBadge(domain)),
                                  m("td", this._campaignBadge(domain)),
                                  m("td", this._aRecordBadge(domain)),
                                  m("td", this._certificateBadge(domain)),
                                  m("td", this._disabledBadge(domain)),
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
