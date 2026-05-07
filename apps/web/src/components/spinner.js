var m = require("mithril");

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
        m("span.sr-only", "Loading..."),
      ),
    );
  }
}

module.exports = Spinner;
