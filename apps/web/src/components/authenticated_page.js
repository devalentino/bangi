var m = require("mithril");
var Sidebar = require("./sidebar");
var Navbar = require("./navbar");

class AuthenticatedPage {
  view(vnode) {
    return [
      m(Sidebar),
      m(
        ".content",
        [m(Navbar, { auth: vnode.attrs.auth, alerts: vnode.attrs.alerts }), m(vnode.attrs.page)],
      ),
    ];
  }
}

module.exports = AuthenticatedPage;
