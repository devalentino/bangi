var m = require("mithril");
var AlertsBell = require("./alerts_bell");
var i18n = require("../i18n");

function languageItem(locale) {
  var isActive = i18n.getLocale() === locale;

  return m(
    "button.dropdown-item.d-flex.align-items-center.justify-content-between",
    {
      type: "button",
      onclick: function () {
        i18n.setLocale(locale);
      },
    },
    [
      m("span", i18n.t("language." + locale)),
      isActive ? m("i.fa.fa-check.ms-3", { "aria-hidden": "true" }) : null,
    ],
  );
}

class Navbar {
  view(vnode) {
    var auth = vnode.attrs.auth;
    var alerts = vnode.attrs.alerts;
    return m(
      "nav.navbar.navbar-expand.bg-light.navbar-light.sticky-top.px-4.py-0",
      m(
        ".navbar-nav.align-items-center.ms-auto",
        [
          m(AlertsBell, { alerts: alerts }),
          m(".nav-item.dropdown", [
            m(
              "a.nav-link.dropdown-toggle",
              { href: "#", "data-bs-toggle": "dropdown" },
              [
                m(
                  "span.rounded-circle.bg-primary.text-white.d-inline-flex.align-items-center.justify-content-center.me-lg-2",
                  {
                    "aria-hidden": "true",
                    style: "width: 40px; height: 40px; font-weight: 600;",
                  },
                  "A",
                ),
                m("span.d-none.d-lg-inline-flex", i18n.t("nav.account.admin")),
              ],
            ),
            m(
              ".dropdown-menu.dropdown-menu-end.bg-light.border-0.rounded-0.rounded-bottom.m-0",
              [
                m("h6.dropdown-header", i18n.t("language.label")),
                languageItem("en"),
                languageItem("uk"),
                m(".dropdown-divider"),
                m(
                  "a.dropdown-item",
                  {
                    href: "#",
                    onclick: function () {
                      auth.signOut();
                    },
                  },
                  i18n.t("nav.logout"),
                ),
              ],
            ),
          ]),
        ],
      ),
    );
  }
}

module.exports = Navbar;
