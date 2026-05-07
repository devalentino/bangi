var m = require("mithril");
var AlertsBell = require("./alerts_bell");

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
                m("span.d-none.d-lg-inline-flex", "Admin"),
              ],
            ),
            m(
              ".dropdown-menu.dropdown-menu-end.bg-light.border-0.rounded-0.rounded-bottom.m-0",
              m(
                "a.dropdown-item",
                {
                  href: "#",
                  onclick: function () {
                    auth.signOut();
                  },
                },
                "Log Out",
              ),
            ),
          ]),
        ],
      ),
    );
  }
}

module.exports = Navbar;
