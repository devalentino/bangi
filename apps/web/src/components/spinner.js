var m = require("mithril");
var i18n = require("../i18n");

class Spinner {
  view() {
    return m(
      "#spinner",
      {
        class:
          "show bg-white position-fixed translate-middle w-100 vh-100 top-50 start-50 d-flex align-items-center justify-content-center",
      },
      m(
        ".spinner-border.text-primary",
        { style: "width: 3rem; height: 3rem;", role: "status" },
        m("span.sr-only", i18n.t("common.loading")),
      ),
    );
  }
}

module.exports = Spinner;
