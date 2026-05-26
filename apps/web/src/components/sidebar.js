var m = require("mithril");
var i18n = require("../i18n");

class Sidebar {
  view() {
    let currentRoute = m.route.get();
    let isHealthRoute = currentRoute === "/health";
    let isDomainsRoute = currentRoute.indexOf("/domains") === 0;
    let isFacebookPacsRoute = currentRoute.indexOf("/facebook/pacs") === 0;
    let isStatisticsRoute = currentRoute === "/statistics";
    let isExpensesReportRoute = currentRoute === "/reports/expenses";
    let isDiscardReportRoute = currentRoute === "/reports/discard";
    let isReportsLeadsRoute = currentRoute.indexOf("/reports/leads") === 0;
    let isCoreCampaignsRoute = currentRoute.indexOf("/core/campaigns") === 0;

    function linkClass(isActive) {
      return isActive ? "nav-link active fw-bold" : "nav-link";
    }

    return m(
      ".sidebar.pe-4.pb-3",
      m(
        ".sidebar.pe-4.pb-3",
        m("nav.navbar.bg-light.navbar-light", [
          m(
            "a.navbar-brand.mx-4.mb-3",
            { href: "index.html" },
            m("h3.text-primary", [m("i.fa.fa-hashtag.me-2"), "Bangi"]),
          ),
          m(
            ".navbar-nav.w-100",
            [
              m(
                "a.nav-item.nav-link",
                { href: "#!/statistics", class: linkClass(isStatisticsRoute) },
                [
                m("i.fa.fa-tachometer-alt.me-2"),
                i18n.t("nav.statistics"),
              ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/reports/leads", class: linkClass(isReportsLeadsRoute) },
                [
                  m("i.fa.fa-address-card.me-2"),
                  i18n.t("nav.leads"),
                ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/core/campaigns", class: linkClass(isCoreCampaignsRoute) },
                [
                m("i.fa.fa-bullhorn.me-2"),
                i18n.t("nav.facebookPacs.campaigns"),
              ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/reports/expenses", class: linkClass(isExpensesReportRoute) },
                [
                  m("i.fa.fa-receipt.me-2"),
                  i18n.t("nav.expenses"),
                ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/reports/discard", class: linkClass(isDiscardReportRoute) },
                [
                  m("i.fa.fa-filter.me-2"),
                  i18n.t("nav.reports.discards"),
                ]),
              m(".nav-item.dropdown", [
                m(
                  "a.nav-link.dropdown-toggle",
                  {
                    href: "#",
                    "data-bs-toggle": "dropdown",
                    "aria-expanded": isFacebookPacsRoute ? "true" : "false",
                    class: isFacebookPacsRoute
                      ? "nav-link dropdown-toggle active fw-bold"
                      : "nav-link dropdown-toggle",
                  },
                  [m("i.fa.fa-laptop.me-2"), i18n.t("nav.facebookPacs")],
                ),
                m(
                  ".dropdown-menu.bg-transparent.border-0",
                  { class: isFacebookPacsRoute ? "dropdown-menu bg-transparent border-0 show" : "dropdown-menu bg-transparent border-0" },
                  [
                  m(
                    "a.dropdown-item",
                    {
                      href: "#!/facebook/pacs/executors",
                      class:
                        currentRoute.indexOf("/facebook/pacs/executors") === 0
                          ? "dropdown-item active fw-bold"
                          : "dropdown-item",
                    },
                    i18n.t("nav.facebookPacs.executors"),
                  ),
                  m(
                    "a.dropdown-item",
                    {
                      href: "#!/facebook/pacs/business-portfolios",
                      class:
                        currentRoute.indexOf("/facebook/pacs/business-portfolios") === 0
                          ? "dropdown-item active fw-bold"
                          : "dropdown-item",
                    },
                    i18n.t("nav.facebookPacs.businessPortfolios"),
                  ),
                  m(
                    "a.dropdown-item",
                    {
                      href: "#!/facebook/pacs/ad-cabinets",
                      class:
                        currentRoute.indexOf("/facebook/pacs/ad-cabinets") === 0
                          ? "dropdown-item active fw-bold"
                          : "dropdown-item",
                    },
                    i18n.t("nav.facebookPacs.adCabinets"),
                  ),
                  m(
                    "a.dropdown-item",
                    {
                      href: "#!/facebook/pacs/campaigns",
                      class:
                        currentRoute.indexOf("/facebook/pacs/campaigns") === 0
                          ? "dropdown-item active fw-bold"
                          : "dropdown-item",
                    },
                    i18n.t("nav.facebookPacs.campaigns"),
                  ),
                  m(
                    "a.dropdown-item",
                    {
                      href: "#!/facebook/pacs/business-pages",
                      class:
                        currentRoute.indexOf("/facebook/pacs/business-pages") === 0
                          ? "dropdown-item active fw-bold"
                          : "dropdown-item",
                    },
                    i18n.t("nav.facebookPacs.businessPages"),
                  ),
                ],
                ),
              ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/domains", class: linkClass(isDomainsRoute) },
                [
                  m("i.fa.fa-globe.me-2"),
                  i18n.t("nav.domains"),
                ],
              ),
              m(
                "a.nav-item.nav-link",
                { href: "#!/health", class: linkClass(isHealthRoute) },
                [
                    m("i.fa.fa-heartbeat.me-2"),
                    i18n.t("nav.health"),
                ],
              ),
            ],
          ),
        ]),
      ),
    );
  }
}

module.exports = Sidebar;
