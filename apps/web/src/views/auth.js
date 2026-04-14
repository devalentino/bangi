var m = require("mithril");

class SignInView {
  constructor(vnode) {
    this.auth = vnode.attrs.auth;
    this.username = "";
    this.password = "";
  }

  view() {
    return m(
      ".container-fluid",
      m(
        ".row.h-100.align-items-center.justify-content-center",
        { style: "min-height: 100vh;" },
        m(
          ".col-12.col-sm-8.col-md-6.col-lg-5.col-xl-4",
          m(".bg-light.rounded.p-4.p-sm-5.my-4.mx-3", [
            m(
              ".d-flex.align-items-center.justify-content-between.mb-3",
              m("h3", "SignIn"),
            ),
            m(".form-floating.mb-3", [
              m("input.form-control", {
                id: "floatingInput",
                placeholder: "username",
                oninput: function (event) {
                  this.username = event.target.value;
                }.bind(this),
              }),
              m("label", { for: "floatingInput" }, "Username"),
            ]),
            m(".form-floating.mb-4", [
              m("input.form-control", {
                type: "password",
                id: "floatingPassword",
                placeholder: "Password",
                oninput: function (event) {
                  this.password = event.target.value;
                }.bind(this),
              }),
              m("label", { for: "floatingPassword" }, "Password"),
            ]),
            m(
              "button.btn.btn-primary.py-3.w-100.mb-4",
              {
                type: "submit",
                onclick: function () {
                  this.auth.signIn(this.username, this.password);
                }.bind(this),
              },
              "Sign In",
            ),
          ]),
        ),
      ),
    );
  }
}

module.exports = { SignIn: SignInView };
