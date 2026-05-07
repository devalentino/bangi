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
                m("img.rounded-circle.me-lg-2", {
                  src: "img/user.jpg",
                  alt: "",
                  style: "width: 40px; height: 40px;",
                }),
                m("span.d-none.d-lg-inline-flex", "Ileana Cosânzeana"),
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
