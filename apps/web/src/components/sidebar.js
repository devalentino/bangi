var m = require("mithril");

class Sidebar {
  view() {
    let currentRoute = m.route.get();
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
                "Statistics",
              ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/reports/leads", class: linkClass(isReportsLeadsRoute) },
                [
                  m("i.fa.fa-address-card.me-2"),
                  "Leads",
                ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/core/campaigns", class: linkClass(isCoreCampaignsRoute) },
                [
                m("i.fa.fa-bullhorn.me-2"),
                "Campaigns",
              ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/reports/expenses", class: linkClass(isExpensesReportRoute) },
                [
                  m("i.fa.fa-receipt.me-2"),
                  "Expenses",
                ]),
              m(
                "a.nav-item.nav-link",
                { href: "#!/reports/discard", class: linkClass(isDiscardReportRoute) },
                [
                  m("i.fa.fa-filter.me-2"),
                  "Discards",
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
                  [m("i.fa.fa-laptop.me-2"), "Facebook PACS"],
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
                    "Executors",
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
                    "Business Portfolios",
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
                    "Ad Cabinets",
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
                    "Campaigns",
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
                    "Business Pages",
                  ),
                ],
                ),
              ]),
            ],
          ),
        ]),
      ),
    );
  }
}

module.exports = Sidebar;
